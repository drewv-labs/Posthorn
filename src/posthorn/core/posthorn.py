from __future__ import annotations

from ..adapters import DuckDB
from .interfaces import AlertCarrier, StateDB
from .managers import CampaignManager, JobBoardManager


class Posthorn:

    def __init__(self,
        alert_carrier: AlertCarrier,
        job_boards: JobBoardManager,
        campaigns: CampaignManager,
        state_db: StateDB | None = None):
        """Initializes the Posthorn instance with the given alert carrier, job boards, and campaigns."""

        self.alert_carrier: AlertCarrier = alert_carrier
        self.job_boards: JobBoardManager = job_boards
        self.campaigns: CampaignManager = campaigns
        self.state_db: StateDB = state_db or DuckDB()

    def run(self) -> None:
        for campaign in self.campaigns:
            for job_board in self.job_boards:
                if job_post := job_board.poll(campaign):
                    result = self.alert_carrier.dispatch(job_post, campaign)
                    self.state_db.update(job_post, result)
