from __future__ import annotations

from typing import Protocol

from ..models import ScreeningDecision


class AiProvider(Protocol):
    """
    Core interface for all local and cloud LLM integrations.
    Any new provider added to Posthorn must satisfy this contract.
    """

    @property
    def provider_id(self) -> str:
        """Unique string identifier (e.g., 'ollama', 'anthropic', 'openai')."""
        ...

    async def generate_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        """
        Standard completion endpoint.
        Used for fluid text generation like tailoring CVs and cover letters.
        """
        ...

    async def generate_structured(self, system_prompt: str, user_prompt: str, model: str) -> ScreeningDecision:
        """
        Structured completion endpoint.
        Forces the LLM to return a strict JSON payload mapped to ScreeningDecision.
        """
        ...
