from __future__ import annotations

import httpx

from posthorn.core import AiProvider, ScreeningDecision


class AnthropicProvider(AiProvider):
    """
    AI Provider adapter for Anthropic's Claude models.
    Utilizes direct REST calls via httpx to avoid SDK bloat.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # 60s timeout for cloud API calls
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def provider_id(self) -> str:
        return "anthropic"

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """Standard fluid completion for CVs and cover letters."""
        payload = {
            "model": model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096, # Anthropic requires this parameter
        }

        response = await self._client.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        return data["content"][0]["text"]

    async def generate_structured(self, system_prompt: str, user_prompt: str, model: str) -> ScreeningDecision:
        """Strict JSON completion using Anthropic's Tool Calling."""
        tool_name = "record_decision"

        payload = {
            "model": model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1024,
            "tools": [
                {
                    "name": tool_name,
                    "description": "Record the final screening decision based on campaign criteria.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "is_relevant": {"type": "boolean"},
                            "reason": {"type": "string"}
                        },
                        "required": ["is_relevant", "reason"]
                    }
                }
            ],
            # This explicitly forces Claude to output ONLY the tool schema
            "tool_choice": {"type": "tool", "name": tool_name}
        }

        response = await self._client.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()

        # Anthropic returns the JSON payload inside a specific tool_use block
        for block in data.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") == tool_name:
                inputs = block.get("input", {})
                return ScreeningDecision(
                    is_relevant=inputs.get("is_relevant", False),
                    reason=inputs.get("reason", "Failed to parse reasoning from model.")
                )

        # Failsafe fallback
        return ScreeningDecision(
            is_relevant=False,
            reason="Anthropic API failed to return the requested tool payload."
        )
