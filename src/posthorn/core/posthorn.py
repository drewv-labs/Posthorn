import asyncio
import logging

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

    async def run(self) -> None:
        """
        Executes the main asynchronous polling and dispatch loop.
        Coordinates the JobBoard generators, state machine transitions, and AlertCarrier.
        """
        await self.state_db.connect()

        try:
            for campaign in self.campaigns:  # Assuming synchronous iterable yielding campaigns
                for job_board in self.job_boards:  # Assuming synchronous iterable yielding boards
                    try:
                        # poll() returns an AsyncGenerator[JobPost, None]
                        async for job in job_board.poll(campaign):
                            # 1. Fast path: drop known jobs immediately to save I/O
                            if not await self.state_db.is_novel(job.id):
                                continue
                            # 2. Register discovery in the ledger
                            await self.state_db.transition_state(job, campaign, JobState.DISCOVERED)
                            # 3. Attempt to secure the queue lock.
                            # If False, DuckDB caught a race condition (duplicate).
                            if not await self.state_db.transition_state(job, campaign, JobState.ALERT_QUEUED):
                                await self.state_db.transition_state(job, campaign, JobState.DUPLICATE)
                                continue
                            # 4. Dispatch payload to the carrier
                            try:
                                await self.alert_carrier.dispatch(job, campaign)
                                await self.state_db.transition_state(job, campaign, JobState.ALERT_SENT)
                                # Respect carrier rate limits (e.g., Telegram/Discord)
                                await asyncio.sleep(1)
                            except Exception as e:
                                # 5. Fail gracefully so the next run() can sweep pending alerts
                                await self.state_db.transition_state(
                                    job,
                                    campaign,
                                    JobState.FAILED,
                                    error_msg=str(e)
                                )
                                logging.error(f"Carrier dispatch failed for {job.id}: {e}")
                    except Exception as e:
                        logging.error(f"Failed polling {job_board.name} for campaign {campaign.name}: {e}")
        finally:
            # Ensure WAL/buffers are flushed even if a keyboard interrupt occurs
            await self.state_db.disconnect()
