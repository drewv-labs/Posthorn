from __future__ import annotations

from .alert_carrier import AlertCarrierAdapter
from .campaign_manager import CampaignManager
from .job_board_manager import JobBoardManager
from .models import PosthornConfig


class Posthorn:

    @classmethod
    def from_config(cls, config: PosthornConfig):
        return cls(
            alert_carrier=config.alert_carrier,
            job_boards=config.job_boards,
            campaigns=config.campaigns,
        )

    def __init__(self, alert_carrier: AlertCarrierAdapter, job_boards: JobBoardManager, campaigns: CampaignManager):
        self.alert_carrier: AlertCarrierAdapter = alert_carrier
        self.job_boards: JobBoardManager = job_boards
        self.campaigns: CampaignManager = campaigns
