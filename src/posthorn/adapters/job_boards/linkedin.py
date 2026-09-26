from __future__ import annotations

from posthorn.core import Campaign


class LinkedIn:

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "linkedin-job-board"

    async def poll(self, campaign: Campaign) -> None:
        pass
