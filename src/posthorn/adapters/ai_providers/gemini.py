from __future__ import annotations

import json

import httpx

from posthorn.core import AiProvider, ScreeningDecision


class GeminiProvider(AiProvider):
    """
    AI Provider adapter for Google's Gemini models.
    Utilizes direct REST calls via httpx and enforces strict JSON
    via generationConfig response schemas.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.headers = {
            "Content-Type": "application/json"
        }
        # 60s timeout for cloud API calls
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def provider_id(self) -> str:
        return "gemini"

    def _build_url(self, model: str) -> str:
        """Gemini requires the model name in the URL path."""
        return f"{self.base_url}/{model}:generateContent?key={self.api_key}"

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Standard fluid completion for CVs and cover letters."""
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "role": "user",
                "parts": [{"text": user_prompt}]
            }]
        }

        response = await self._client.post(
            self._build_url(model),
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_structured(self, system_prompt: str, user_prompt: str, model: str) -> ScreeningDecision:
        """Strict JSON completion using Gemini's responseSchema."""
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "role": "user",
                "parts": [{"text": user_prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "is_relevant": {"type": "BOOLEAN"},
                        "reason": {"type": "STRING"}
                    },
                    "required": ["is_relevant", "reason"]
                }
            }
        }

        response = await self._client.post(
            self._build_url(model),
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]

        try:
            result_dict = json.loads(content)
            return ScreeningDecision(
                is_relevant=result_dict.get("is_relevant", False),
                reason=result_dict.get("reason", "Parsed without valid reason string.")
            )
        except json.JSONDecodeError:
            return ScreeningDecision(
                is_relevant=False,
                reason="Gemini API returned malformed JSON despite schema enforcement."
            )
