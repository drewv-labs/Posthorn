from __future__ import annotations

import dataclasses

from posthorn.core import (
    AlertCarrierAdapter,
    AlertCarrierConfig,
    Campaign,
    JobPost,
)


@dataclasses.dataclass(frozen=True)
class TelegramConfig(AlertCarrierConfig):
    token: str
    chat_id: str


class Telegram(AlertCarrierAdapter):

    @classmethod
    def from_config(cls, config: AlertCarrierConfig) -> Telegram:
        if not isinstance(config, TelegramConfig):
            raise TypeError("Invalid config type for Telegram")
        return cls(token=config.token, chat_id=config.chat_id)

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return "TelegramAdapter"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        pass
