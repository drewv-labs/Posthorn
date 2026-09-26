from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .campaign_model import Campaign
    from .job_post_model import JobPost
    from .job_state_enum import JobState

__all__ = [
    "Campaign",
    "JobPost",
    "JobState",
]
