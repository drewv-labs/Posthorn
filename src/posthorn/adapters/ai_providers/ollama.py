from __future__ import annotations

import json

import httpx

from posthorn.core import AiProvider, ScreeningDecision


class OllamaProvider(AiProvider):
    """
    AI Provider adapter for local Ollama instances.
    Requires no external dependencies beyond the existing httpx client.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        # 120s timeout ensures large open-weight models have time to generate full CVs
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    @property
    def provider_id(self) -> str:
        return "ollama"

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Standard fluid completion for CVs and cover letters."""
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        return data["message"]["content"]

    async def generate_structured(self, system_prompt: str, user_prompt: str, model: str) -> ScreeningDecision:
        """Strict JSON completion for binary job screening."""

        # Ollama supports passing a JSON schema directly to force structure
        schema = {
            "type": "object",
            "properties": {
                "is_relevant": {"type": "boolean"},
                "reason": {"type": "string"}
            },
            "required": ["is_relevant", "reason"]
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": schema,
            "stream": False
        }

        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()

        data = response.json()
        result_dict = json.loads(data["message"]["content"])

        return ScreeningDecision(
            is_relevant=result_dict.get("is_relevant", False),
            reason=result_dict.get("reason", "Failed to parse reasoning from model.")
        )
