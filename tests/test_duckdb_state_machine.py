from __future__ import annotations

import dataclasses

from posthorn import (
    Campaign,
    JobPost,
    JobState,
    StateMachine,
)


async def test_job_novelty_check(memory_db: StateMachine, sample_job: JobPost, sample_campaign: Campaign):
    """Ensures is_novel correctly identifies unseen vs existing jobs."""
    # Job should be novel initially
    assert await memory_db.is_novel(sample_job.id) is True

    # Transitioning the job writes it to the database
    await memory_db.transition_state(sample_job, sample_campaign, JobState.DISCOVERED)

    # Job should no longer be novel
    assert await memory_db.is_novel(sample_job.id) is False


async def test_idempotency_lock_prevents_duplicates(
    memory_db: StateMachine, sample_job: JobPost, sample_campaign: Campaign
):
    """
    Proves the core concurrency protection mechanism: the database must reject
    a transition to ALERT_QUEUED if the job is already queued or sent.
    """
    # 1. First adapter discovers and queues the job (Should succeed)
    success = await memory_db.transition_state(sample_job, sample_campaign, JobState.ALERT_QUEUED)
    assert success is True

    # 2. Simulate a race condition: a second adapter tries to queue the exact same job
    duplicate_success = await memory_db.transition_state(
        sample_job, sample_campaign, JobState.ALERT_QUEUED
    )
    # The database must reject the duplicate
    assert duplicate_success is False

    # 3. Simulate the job successfully dispatching via Telegram
    await memory_db.transition_state(sample_job, sample_campaign, JobState.ALERT_SENT)

    # 4. Another campaign sweep runs an hour later and tries to queue it again
    late_success = await memory_db.transition_state(sample_job, sample_campaign, JobState.ALERT_QUEUED)

    # The database must STILL reject it because it is already marked ALERT_SENT
    assert late_success is False


async def test_campaign_metrics_aggregation(
    memory_db: StateMachine, sample_job: JobPost, sample_campaign: Campaign
):
    """Verifies the reporting engine tallies states correctly."""
    # Generate three distinct jobs using dataclass replacement
    job_1 = sample_job
    job_2 = dataclasses.replace(sample_job, id="testboard_100")
    job_3 = dataclasses.replace(sample_job, id="testboard_101")
    job_4 = dataclasses.replace(sample_job, id="testboard_102")

    # 1 sent, 1 failed, 1 suppressed duplicate, 1 discovered
    await memory_db.transition_state(job_1, sample_campaign, JobState.ALERT_SENT)
    await memory_db.transition_state(job_2, sample_campaign, JobState.FAILED)
    await memory_db.transition_state(job_3, sample_campaign, JobState.DUPLICATE)
    await memory_db.transition_state(job_4, sample_campaign, JobState.DISCOVERED)

    metrics = await memory_db.get_campaign_metrics(sample_campaign.name)

    assert metrics["total_discovered"] == 4
    assert metrics["novel_alerts_sent"] == 1
    assert metrics["failed_dispatches"] == 1
    assert metrics["duplicates_suppressed"] == 1
    assert metrics["last_active"] is not None


async def test_pending_alerts_sweep(
    memory_db: StateMachine, sample_job: JobPost, sample_campaign: Campaign
):
    """Ensures jobs stuck in QUEUED or FAILED can be retrieved for a retry sweep."""
    job_queued = dataclasses.replace(sample_job, id="queued_1")
    job_failed = dataclasses.replace(sample_job, id="failed_1")
    job_sent = dataclasses.replace(sample_job, id="sent_1")

    await memory_db.transition_state(job_queued, sample_campaign, JobState.ALERT_QUEUED)
    await memory_db.transition_state(job_failed, sample_campaign, JobState.FAILED)
    await memory_db.transition_state(job_sent, sample_campaign, JobState.ALERT_SENT)

    pending_jobs = await memory_db.get_pending_alerts(limit=10)

    # Should only pull the queued and failed jobs
    assert len(pending_jobs) == 2
    pending_ids = {j.id for j in pending_jobs}
    assert "queued_1" in pending_ids
    assert "failed_1" in pending_ids
    assert "sent_1" not in pending_ids
