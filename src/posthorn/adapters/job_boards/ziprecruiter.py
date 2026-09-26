from __future__ import annotations

from posthorn.core import Campaign


class ZipRecruiter:

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "ziprecruiter-job-board"

    async def poll(self, campaign: Campaign) -> None:
        pass
