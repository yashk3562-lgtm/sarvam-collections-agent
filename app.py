from __future__ import annotations

import pandas as pd
import streamlit as st

from mock_crm import ACCOUNTS, CRM_EVENTS, REMINDER_QUEUE, ESCALATION_QUEUE, get_account, list_accounts
from policies import COLLECTIONS_POLICY
from sarvam_client import SarvamClient
from workflow import execute_workflow

st.set_page_config(page_title="Sarvam Collections Agent", layout="wide")

st.title("Sarvam AI Collections & Recovery Agent")
st.caption("Multilingual EMI reminder and recovery workflow for NBFCs and banks")

client = SarvamClient()

with st.sidebar:
    st.header("Demo Controls")
    borrower_id = st.selectbox("Borrower", list(ACCOUNTS.keys()))
    language = st.selectbox("Conversation language", ["Hindi", "English", "Hinglish"])
    st.info("MOCK_MODE is enabled by default. Add SARVAM_API_KEY and set MOCK_MODE=false for live APIs.")

account = get_account(borrower_id)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Borrower Account")
    st.dataframe(pd.DataFrame([account.__dict__]), use_container_width=True, hide_index=True)

with col2:
    st.subheader("Agent Objective")
    st.write(
        f"Recover or schedule EMI payment of INR {account.emi_amount} for {account.product}. "
        f"Account is {account.overdue_days} days overdue. Use {language}."
    )

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.subheader("Live Conversation")

starter = (
    f"You are calling {account.name}. EMI amount is INR {account.emi_amount}, "
    f"overdue by {account.overdue_days} days. Start a compliant collections call in {language}."
)

if st.button("Start Call"):
    agent_text = client.chat(COLLECTIONS_POLICY, starter)
    st.session_state.messages.append({"role": "agent", "text": agent_text})

for m in st.session_state.messages:
    with st.chat_message("assistant" if m["role"] == "agent" else "user"):
        st.write(m["text"])

borrower_text = st.chat_input("Type borrower response, e.g., 'Salary abhi nahi aayi, Friday ko pay kar dunga'")
if borrower_text:
    st.session_state.messages.append({"role": "borrower", "text": borrower_text})
    prompt = (
        f"Borrower account: {account.__dict__}\n"
        f"Conversation language: {language}\n"
        f"Borrower said: {borrower_text}\n"
        "Respond as a compliant EMI collections voice agent. Keep it concise."
    )
    agent_text = client.chat(COLLECTIONS_POLICY, prompt)
    st.session_state.messages.append({"role": "agent", "text": agent_text})
    result = execute_workflow(borrower_id, borrower_text, agent_text)
    st.rerun()

st.divider()

col3, col4, col5 = st.columns(3)
with col3:
    st.subheader("CRM Events")
    st.dataframe(pd.DataFrame(CRM_EVENTS), use_container_width=True, hide_index=True)
with col4:
    st.subheader("Reminder Queue")
    st.dataframe(pd.DataFrame(REMINDER_QUEUE), use_container_width=True, hide_index=True)
with col5:
    st.subheader("Escalation Queue")
    st.dataframe(pd.DataFrame(ESCALATION_QUEUE), use_container_width=True, hide_index=True)

st.divider()

if st.button("Generate Post-call Summary"):
    transcript = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.messages])
    summary_prompt = f"Create a post-call collections summary with outcome, risk score, reason, next action. Transcript:\n{transcript}"
    st.subheader("Post-call Analytics")
    st.write(client.chat(COLLECTIONS_POLICY, summary_prompt))
