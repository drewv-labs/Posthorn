from __future__ import annotations

import asyncio
from typing import Any

from posthorn.adapters import CARRIER_REGISTRY, JOB_BOARD_REGISTRY

from .interfaces import AlertCarrier
from .managers import CampaignManager, JobBoardManager
from .models import Campaign, JobState
from .state_mx import StateMachine


class PosthornDaemon:

    def __init__(
        self,
        alert_carrier: AlertCarrier,
        job_boards: JobBoardManager,
        campaigns: CampaignManager,
        statemachine_file: str | None,
    ):
        """Initializes the Posthorn instance with the given alert carrier, job boards, and campaigns."""
        self.alert_carrier: AlertCarrier = alert_carrier
        self.job_boards: JobBoardManager = job_boards
        self.campaigns: CampaignManager = campaigns
        self.state_db: StateMachine = StateMachine(statemachine_file)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PosthornDaemon:
        """Instantiates the daemon dynamically from a parsed TOML dictionary."""

        # 1. Morph the Carrier
        carrier_cfg = config.get("carrier", {})
        carrier_type = carrier_cfg.pop("type", "discord") # default fallback

        if carrier_type not in CARRIER_REGISTRY:
            raise ValueError(f"Unknown carrier type: {carrier_type}")

        # Instantiates DiscordCarrier(**{"webhook_url": "..."})
        carrier = CARRIER_REGISTRY[carrier_type](**carrier_cfg)

        # 2. Morph the Job Boards
        boards_cfg = config.get("job_boards", [])
        active_boards = []
        for b_cfg in boards_cfg:
            b_type = b_cfg.pop("type")
            if b_type in JOB_BOARD_REGISTRY:
                active_boards.append(JOB_BOARD_REGISTRY[b_type](**b_cfg))

        # 3. Morph the Campaigns
        campaigns_cfg = config.get("campaigns", [])
        active_campaigns = [Campaign(**c) for c in campaigns_cfg]

        return cls(
            alert_carrier=carrier,
            job_boards=JobBoardManager(active_boards),
            campaigns=CampaignManager(active_campaigns),
            statemachine_file=config.get("statemachine_file") or None,
        )

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
