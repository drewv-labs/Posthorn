from __future__ import annotations

from posthorn.core import (
    Campaign,
    JobPost,
)


class Telegram:

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return "telegram-alert-carrier"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        pass
