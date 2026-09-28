from __future__ import annotations

import json

import httpx

from posthorn.core import AiProvider, ScreeningDecision


class OpenAIProvider(AiProvider):
    """
    AI Provider adapter for OpenAI (ChatGPT).
    Utilizes direct REST calls via httpx to avoid SDK bloat,
    and uses the native Strict JSON Schema for structured outputs.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # 60s timeout for cloud API calls
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def provider_id(self) -> str:
        return "openai"

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Standard fluid completion for CVs and cover letters."""
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        response = await self._client.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate_structured(self, system_prompt: str, user_prompt: str, model: str) -> ScreeningDecision:
        """Strict JSON completion using OpenAI's response_format JSON Schema."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "screening_decision",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "is_relevant": {"type": "boolean"},
                            "reason": {"type": "string"}
                        },
                        "required": ["is_relevant", "reason"],
                        "additionalProperties": False
                    }
                }
            }
        }

        response = await self._client.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            result_dict = json.loads(content)
            return ScreeningDecision(
                is_relevant=result_dict.get("is_relevant", False),
                reason=result_dict.get("reason", "Parsed without valid reason string.")
            )
        except json.JSONDecodeError:
            # Failsafe fallback
            return ScreeningDecision(
                is_relevant=False,
                reason="OpenAI API returned malformed JSON despite strict mode."
            )
