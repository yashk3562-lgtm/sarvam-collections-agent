from __future__ import annotations

import base64
import json
import re
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="Sarvam Collections Agent", layout="wide")

SARVAM_API_KEY = st.secrets.get("SARVAM_API_KEY", "")
CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
STT_URL = "https://api.sarvam.ai/speech-to-text"

LANG_CODES = {"Hindi": "hi-IN", "English": "en-IN", "Hinglish": "hi-IN", "Tamil": "ta-IN"}
SPEAKERS = {"Hindi": "shubh", "English": "anand", "Hinglish": "shubh", "Tamil": "shreya"}

ACCOUNTS = {
    "BRW001": {"name": "Ramesh Kumar", "language": "Hindi", "city": "Lucknow", "product": "Two-wheeler loan", "emi_amount": 4850, "overdue_days": 7, "risk": "Medium", "attempts": 2},
    "BRW002": {"name": "Priya Sharma", "language": "English", "city": "Bengaluru", "product": "Personal loan", "emi_amount": 9200, "overdue_days": 14, "risk": "High", "attempts": 4},
    "BRW003": {"name": "Suresh Iyer", "language": "Tamil", "city": "Chennai", "product": "Consumer durable loan", "emi_amount": 3150, "overdue_days": 5, "risk": "Low", "attempts": 1},
}


def init_state():
    for k, v in {
        "messages": [],
        "crm": [],
        "reminders": [],
        "escalations": [],
        "analytics": {"Calls": 0, "Promise-to-Pay": 0, "Escalations": 0, "Restructure Requests": 0},
    }.items():
        st.session_state.setdefault(k, v)


def require_key():
    if not SARVAM_API_KEY:
        st.error("Add SARVAM_API_KEY in Streamlit Secrets.")
        st.stop()


def sarvam_chat(messages: list[dict[str, str]]) -> str:
    require_key()
    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sarvam-105b",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 400,
        "reasoning_effort": "medium",
    }
    r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(r.text)
    return r.json()["choices"][0]["message"]["content"]


def sarvam_tts(text: str, language: str) -> bytes | None:
    require_key()
    headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text[:2400],
        "target_language_code": LANG_CODES.get(language, "hi-IN"),
        "speaker": SPEAKERS.get(language, "shubh"),
        "model": "bulbul:v3",
        "pace": 0.95,
        "speech_sample_rate": 24000,
        "output_audio_codec": "wav",
        "temperature": 0.4,
    }
    r = requests.post(TTS_URL, headers=headers, json=payload, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(r.text)
    audios = r.json().get("audios", [])
    return base64.b64decode(audios[0]) if audios else None


def sarvam_stt(audio_file) -> str:
    require_key()
    headers = {"api-subscription-key": SARVAM_API_KEY}
    files = {"file": (audio_file.name, audio_file.read(), audio_file.type or "audio/wav")}
    data = {"model": "saaras:v3", "mode": "codemix"}
    r = requests.post(STT_URL, headers=headers, files=files, data=data, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(r.text)
    return r.json().get("transcript", "")


def prompt(account: dict[str, Any], language: str) -> str:
    return f"""
You are a compliant Indian NBFC loan collections voice agent.

Borrower:
Name: {account["name"]}
City: {account["city"]}
Loan: {account["product"]}
Overdue EMI: INR {account["emi_amount"]}
Overdue days: {account["overdue_days"]}
Risk: {account["risk"]}
Previous attempts: {account["attempts"]}

Objective:
Collect payment today or capture promise-to-pay date.
If unable to pay fully, offer a practical payment plan.
If borrower refuses, disputes, threatens legal action, mentions fraud, hospitalization, death, or severe distress, escalate to human.

Language:
Respond in {language}. For Hinglish, use natural Hindi-English code-mix.

Rules:
Be polite, short, non-threatening, RBI-compliant, and under 80 words.
Never shame or threaten the borrower.
Ask for one clear next step.
"""


def greeting(account: dict[str, Any], language: str) -> str:
    if language == "English":
        return f"Hello {account['name']}, this is an automated reminder from your lender. Your EMI of INR {account['emi_amount']} is {account['overdue_days']} days overdue. Can you make the payment today or confirm a payment date?"
    if language == "Tamil":
        return f"Vanakkam {account['name']}. Ungal INR {account['emi_amount']} EMI {account['overdue_days']} naal overdue. Indru payment panna mudiyuma, illai payment date confirm pannalama?"
    return f"Namaste {account['name']}, aapki ₹{account['emi_amount']} EMI {account['overdue_days']} din se overdue hai. Kya aap aaj payment kar sakte hain, ya payment ke liye koi date confirm karna chahenge?"


def classify(text: str) -> dict[str, Any]:
    t = text.lower()
    if any(x in t for x in ["fraud", "legal", "complaint", "nahi karunga", "not pay", "wrong loan", "galat"]):
        return {"outcome": "Escalation", "risk": 90, "promise_date": "", "next": "Human callback"}
    if any(x in t for x in ["installment", "part payment", "partial", "plan", "extension", "cannot pay full", "time chahiye"]):
        return {"outcome": "Restructure Requested", "risk": 75, "promise_date": "To confirm", "next": "Payment plan"}
    if any(x in t for x in ["friday", "monday", "tomorrow", "kal", "salary", "pay", "payment", "de dunga", "kar dunga"]):
        return {"outcome": "Promise-to-Pay", "risk": 45, "promise_date": extract_date(t), "next": "Reminder scheduled"}
    return {"outcome": "Follow-up Needed", "risk": 60, "promise_date": "", "next": "Continue conversation"}


def extract_date(t: str) -> str:
    for x in ["today", "tomorrow", "friday", "monday", "kal", "parso", "10th"]:
        if x in t:
            return x
    return "Customer committed date"


def workflow(account_id: str, account: dict[str, Any], user_text: str, agent_reply: str):
    c = classify(user_text + " " + agent_reply)
    event = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "borrower": account_id,
        "customer": account["name"],
        "outcome": c["outcome"],
        "risk_score": c["risk"],
        "next_action": c["next"],
    }
    st.session_state.crm.append(event)

    if c["outcome"] == "Promise-to-Pay":
        st.session_state.reminders.append({
            "borrower": account_id,
            "channel": "WhatsApp/SMS",
            "promise_date": c["promise_date"],
            "message": f"Reminder queued for {account['name']}",
        })
        st.session_state.analytics["Promise-to-Pay"] += 1

    if c["outcome"] == "Escalation":
        st.session_state.escalations.append({
            "borrower": account_id,
            "reason": "High-risk refusal/dispute",
            "owner": "Human collections manager",
        })
        st.session_state.analytics["Escalations"] += 1

    if c["outcome"] == "Restructure Requested":
        st.session_state.analytics["Restructure Requests"] += 1


init_state()

st.title("Sarvam AI Collections & Recovery Agent")
st.caption("Multilingual EMI reminder and recovery workflow for NBFCs and banks")

with st.sidebar:
    st.header("Demo Controls")
    account_id = st.selectbox("Borrower", list(ACCOUNTS.keys()))
    language = st.selectbox("Conversation language", ["Hindi", "English", "Hinglish", "Tamil"])
    voice_on = st.toggle("Play Sarvam TTS voice", value=True)
    st.success("Live Sarvam API mode enabled" if SARVAM_API_KEY else "Add SARVAM_API_KEY in Secrets")

account = ACCOUNTS[account_id]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Borrower", account["name"])
col2.metric("Overdue EMI", f"₹{account['emi_amount']:,}")
col3.metric("Overdue Days", account["overdue_days"])
col4.metric("Risk", account["risk"])

st.divider()

left, right = st.columns([1.3, 1])

with left:
    st.subheader("Live Conversation")

    if st.button("Start Call"):
        st.session_state.analytics["Calls"] += 1
        first = greeting(account, language)
        st.session_state.messages.append({"role": "assistant", "content": first})
        if voice_on:
            try:
                audio = sarvam_tts(first, language)
                if audio:
                    st.audio(audio, format="audio/wav")
            except Exception as e:
                st.error(f"TTS failed: {e}")

    for m in st.session_state.messages:
        label = "Agent" if m["role"] == "assistant" else "Borrower"
        st.chat_message(m["role"]).write(f"**{label}:** {m['content']}")

    uploaded_audio = st.file_uploader("Optional: upload borrower audio for Sarvam STT", type=["wav", "mp3", "m4a"])
    stt_text = ""
    if uploaded_audio and st.button("Transcribe Audio"):
        try:
            stt_text = sarvam_stt(uploaded_audio)
            st.success(stt_text)
        except Exception as e:
            st.error(f"STT failed: {e}")

    user_text = st.chat_input("Type borrower response, e.g. Salary kal aa jayegi, Friday ko payment kar dunga")

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})

        messages = [{"role": "system", "content": prompt(account, language)}]
        messages += st.session_state.messages[-8:]

        try:
            reply = sarvam_chat(messages)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            workflow(account_id, account, user_text, reply)

            if voice_on:
                audio = sarvam_tts(reply, language)
                if audio:
                    st.audio(audio, format="audio/wav")

            st.rerun()
        except Exception as e:
            st.error(f"Sarvam API failed: {e}")

with right:
    st.subheader("Agent Objective")
    st.write(
        f"Recover or schedule EMI payment of ₹{account['emi_amount']:,} "
        f"for {account['product']}. Account is {account['overdue_days']} days overdue."
    )

    st.subheader("Analytics")
    st.dataframe(pd.DataFrame([st.session_state.analytics]), use_container_width=True, hide_index=True)

    latest_risk = st.session_state.crm[-1]["risk_score"] if st.session_state.crm else 50
    st.progress(latest_risk / 100, text=f"Current Risk Score: {latest_risk}/100")

st.divider()

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("CRM Events")
    st.dataframe(pd.DataFrame(st.session_state.crm) if st.session_state.crm else pd.DataFrame(["empty"]), use_container_width=True)

with c2:
    st.subheader("Reminder Queue")
    st.dataframe(pd.DataFrame(st.session_state.reminders) if st.session_state.reminders else pd.DataFrame(["empty"]), use_container_width=True)

with c3:
    st.subheader("Escalation Queue")
    st.dataframe(pd.DataFrame(st.session_state.escalations) if st.session_state.escalations else pd.DataFrame(["empty"]), use_container_width=True)

st.divider()

if st.button("Generate Post-call Summary"):
    if not st.session_state.messages:
        st.warning("Start a call first.")
    else:
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
        summary_prompt = [
            {"role": "system", "content": "Create a concise collections call summary with disposition, promise date, risk, next action, and compliance notes."},
            {"role": "user", "content": transcript},
        ]
        try:
            st.write(sarvam_chat(summary_prompt))
        except Exception as e:
            st.error(f"Summary failed: {e}")
