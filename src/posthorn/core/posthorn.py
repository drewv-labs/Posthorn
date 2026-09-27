import asyncio

from ..adapters import DuckDB
from .interfaces import AlertCarrier, StateDB
from .managers import CampaignManager, JobBoardManager
from .models.job_state_enum import JobState


class Posthorn:

    def __init__(
        self,
        alert_carrier: AlertCarrier,
        job_boards: JobBoardManager,
        campaigns: CampaignManager,
        state_db: StateDB | None = None
    ):
        """Initializes the Posthorn instance with the given alert carrier, job boards, and campaigns."""
        self.alert_carrier: AlertCarrier = alert_carrier
        self.job_boards: JobBoardManager = job_boards
        self.campaigns: CampaignManager = campaigns
        self.state_db: StateDB = state_db or DuckDB()

    async def run(self, interval_seconds: int = 900) -> None:
        """
        Executes the main asynchronous polling and dispatch loop.
        Coordinates the JobBoard generators, state machine transitions, and AlertCarrier.
        """
        await self.state_db.connect()
        try:
            while True:
                await self.sweep()
                await asyncio.sleep(interval_seconds)
        finally:
            # Ensure WAL/buffers are flushed even if a keyboard interrupt occurs
            await self.state_db.disconnect()

    async def sweep(self) -> None:
        """Executes exactly one full polling and dispatch cycle."""
        for campaign in self.campaigns:
            for board in self.job_boards:
                async for job in board.poll(campaign):

                    # 1. Fast check to skip already processed jobs
                    if not await self.state_db.is_novel(job.id):
                        await self.state_db.transition_state(job, campaign, JobState.DUPLICATE)
                        continue

                    # 2. Mark as discovered (critical for total_discovered metrics)
                    await self.state_db.transition_state(job, campaign, JobState.DISCOVERED)

                    # 3. Attempt to lock the job for this sweep
                    lock_acquired = await self.state_db.transition_state(job, campaign, JobState.ALERT_QUEUED)
                    if not lock_acquired:
                        # Another process/sweep grabbed it first
                        await self.state_db.transition_state(job, campaign, JobState.DUPLICATE)
                        continue

                    # 4. Dispatch and commit final state
                    try:
                        await self.alert_carrier.dispatch(job, campaign)
                        await self.state_db.transition_state(job, campaign, JobState.ALERT_SENT)
                    except Exception:
                        await self.state_db.transition_state(job, campaign, JobState.FAILED)
