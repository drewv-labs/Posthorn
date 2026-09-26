from __future__ import annotations

import dataclasses

from ..alert_carrier import AlertCarrierAdapter
from ..campaign_manager import CampaignManager
from ..job_board_manager import JobBoardManager


@dataclasses.dataclass(frozen=True)
class PosthornConfig:
    alert_carrier: AlertCarrierAdapter
    job_boards: JobBoardManager
    campaigns: CampaignManager
