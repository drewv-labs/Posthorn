from __future__ import annotations

from posthorn.core import Campaign


class Indeed:

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "indeed-job-board"

    async def poll(self, campaign: Campaign) -> None:
        pass
