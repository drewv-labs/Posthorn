from __future__ import annotations

from .interfaces import AlertCarrier
from .managers import CampaignManager, JobBoardManager


class Posthorn:

    def __init__(self, alert_carrier: AlertCarrier, job_boards: JobBoardManager, campaigns: CampaignManager):
        self.alert_carrier: AlertCarrier = alert_carrier
        self.job_boards: JobBoardManager = job_boards
        self.campaigns: CampaignManager = campaigns

    def run(self) -> None:
        for campaign in self.campaigns:
            for job_board in self.job_boards:
                if job_post := job_board.poll(campaign):
                    result = self.alert_carrier.dispatch(job_post, campaign)
