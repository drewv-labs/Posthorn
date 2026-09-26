from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .campaign_manager import CampaignManager
    from .job_board_manager import JobBoardManager

__all__ = [
    "CampaignManager",
    "JobBoardManager",
]
