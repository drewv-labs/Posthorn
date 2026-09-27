import dataclasses
from collections.abc import AsyncGenerator

from posthorn import (
    Campaign,
    CampaignManager,
    JobBoardManager,
    JobPost,
    Posthorn,
)
from posthorn.adapters import DuckDB


class MockBoard:
    """A fake job board that yields a specific list of jobs for testing."""
    def __init__(self, jobs: list[JobPost]) -> None:
        self.jobs = jobs

    @property
    def name(self) -> str:
        return "mock_board"

    async def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        for job in self.jobs:
            yield job


async def test_posthorn_end_to_end_sweep(
    memory_db: DuckDB,
    mock_carrier,
    sample_campaign: Campaign,
    sample_job: JobPost
):
    """
    Proves that Posthorn coordinates the polling, state transition,
    and dispatching correctly across a full sweep.
    """
    # 0. Guarantee a unique job so previous tests don't trigger the novelty filter
    fresh_job = dataclasses.replace(sample_job, id="unique_e2e_job_999")

    # 1. Wire up the Posthorn application with our test doubles
    app = Posthorn(
        alert_carrier=mock_carrier,
        job_boards=JobBoardManager([MockBoard([fresh_job])]),
        campaigns=CampaignManager([sample_campaign]),
        state_db=memory_db
    )

    # 2. Execute a single sweep
    await app.sweep()

    # 3. Verify the job was successfully passed to the carrier
    assert len(mock_carrier.dispatched_jobs) == 1
    dispatched_job, dispatched_campaign = mock_carrier.dispatched_jobs[0]

    assert dispatched_job.id == fresh_job.id
    assert dispatched_campaign.name == sample_campaign.name

    # 4. Verify state was updated in DuckDB
    metrics = await memory_db.get_campaign_metrics(sample_campaign.name)
    assert metrics["total_discovered"] == 1
    assert metrics["novel_alerts_sent"] == 1

    # 5. Prove idempotency: running sweep again shouldn't send a second alert
    await app.sweep()

    assert len(mock_carrier.dispatched_jobs) == 1

    metrics_after = await memory_db.get_campaign_metrics(sample_campaign.name)
    assert metrics_after["duplicates_suppressed"] == 1
