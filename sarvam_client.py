from __future__ import annotations

import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_BASE_URL = "https://api.sarvam.ai"


class SarvamClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("SARVAM_API_KEY", "")
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
        self.chat_model = os.getenv("SARVAM_CHAT_MODEL", "sarvam-105b")
        self.stt_model = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
        self.tts_model = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")

    def _headers(self) -> dict:
        if not self.api_key:
            raise RuntimeError("SARVAM_API_KEY missing. Set MOCK_MODE=true or add a key.")
        return {"api-subscription-key": self.api_key}

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if self.mock_mode:
            return self._mock_chat(user_prompt)

        # Endpoint shape may evolve. Keep this wrapper isolated so changes remain one-file edits.
        url = f"{SARVAM_BASE_URL}/v1/chat/completions"
        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 350,
        }
        response = requests.post(url, headers={**self._headers(), "Content-Type": "application/json"}, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def speech_to_text(self, audio_bytes: bytes, language_code: Optional[str] = None) -> str:
        if self.mock_mode:
            return "Salary abhi nahi aayi. Friday ko payment kar dunga."

        url = f"{SARVAM_BASE_URL}/speech-to-text"
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": self.stt_model, "mode": "codemix"}
        if language_code:
            data["language_code"] = language_code
        response = requests.post(url, headers=self._headers(), files=files, data=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("transcript") or result.get("text") or str(result)

    def text_to_speech(self, text: str, language_code: str = "hi-IN") -> bytes:
        if self.mock_mode:
            return b""

        url = f"{SARVAM_BASE_URL}/text-to-speech"
        payload = {
            "model": self.tts_model,
            "text": text,
            "target_language_code": language_code,
        }
        response = requests.post(url, headers={**self._headers(), "Content-Type": "application/json"}, json=payload, timeout=60)
        response.raise_for_status()
        return response.content

    @staticmethod
    def _mock_chat(user_prompt: str) -> str:
        prompt = user_prompt.lower()
        if "summary" in prompt or "post-call" in prompt:
            return (
                "Outcome: promise_to_pay\n"
                "Risk Score: 2/5\n"
                "Summary: Borrower acknowledged overdue EMI and requested time until Friday due to salary delay.\n"
                "Next Action: Queue payment reminder on Friday morning and suppress repeat calls until then.\n"
            )
        if "friday" in prompt or "salary" in prompt or "pay kar" in prompt:
            return "Samajh gaya. Main note kar raha hoon ki aap Friday ko ₹4,850 EMI pay karenge. Friday morning ek reminder bhej diya jayega. Dhanyavaad."
        if "wrong" in prompt or "fraud" in prompt or "galat" in prompt:
            return "Main isko dispute ke roop mein mark kar raha hoon. Hamara human support team aapse details verify karne ke liye contact karega."
        return "Aapki ₹4,850 EMI 7 din se overdue hai. Kya aap aaj payment kar sakte hain, ya payment ke liye koi date confirm karna chahenge?"
