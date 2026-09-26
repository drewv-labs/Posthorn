from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import duckdb

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost
from ...core.models.job_state_enum import JobState
from ...sugar.current_local_datetime import current_local_datetime
from ...sugar.to_datetime import to_datetime


class DuckDB:
    """
    DuckDB state machine and persistent ledger implementation.

    Operations are wrapped in `asyncio.to_thread` with an internal asyncio.Lock
    to guarantee safe thread handoff and keep the event loop unblocked.
    """

    def __init__(self, db_path: str | Path = "posthorn.duckdb") -> None:
        self.db_path = Path(db_path)
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_connect)

    def _sync_connect(self) -> None:
        self._conn = duckdb.connect(str(self.db_path))
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id VARCHAR PRIMARY KEY,
                title VARCHAR NOT NULL,
                company VARCHAR NOT NULL,
                url VARCHAR NOT NULL,
                board VARCHAR NOT NULL,
                published_at TIMESTAMPTZ,
                state VARCHAR NOT NULL,
                campaign_name VARCHAR NOT NULL,
                error_msg VARCHAR,
                discovered_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
            CREATE INDEX IF NOT EXISTS idx_jobs_campaign ON jobs(campaign_name);
            """
        )

    async def disconnect(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_disconnect)

    def _sync_disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    async def is_novel(self, job_id: str) -> bool:
        async with self._lock:
            return await asyncio.to_thread(self._sync_is_novel, job_id)

    def _sync_is_novel(self, job_id: str) -> bool:
        if not self._conn:
            raise RuntimeError("Database is not connected. Call connect() first.")

        result = self._conn.execute(
            "SELECT 1 FROM jobs WHERE id = ? LIMIT 1;", [job_id]
        ).fetchone()
        return result is None

    async def transition_state(
        self,
        job: JobPost,
        campaign: Campaign,
        new_state: JobState,
        error_msg: str | None = None,
    ) -> bool:
        async with self._lock:
            return await asyncio.to_thread(
                self._sync_transition_state, job, campaign, new_state, error_msg
            )

    def _sync_transition_state(
        self,
        job: JobPost,
        campaign: Campaign,
        new_state: JobState,
        error_msg: str | None = None,
    ) -> bool:
        if not self._conn:
            raise RuntimeError("Database is not connected. Call connect() first.")

        now = current_local_datetime()

        # Check existing state
        row = self._conn.execute(
            "SELECT state FROM jobs WHERE id = ?;", [job.id]
        ).fetchone()
        current_state = row[0] if row else None

        # Lock check: Prevent duplicate alerts if already queued or sent
        if new_state == JobState.ALERT_QUEUED and current_state in (JobState.ALERT_SENT, JobState.ALERT_QUEUED):
            return False

        if current_state is None:
            # First time seeing this job, record it
            published_dt = to_datetime(job.published_at) if job.published_at else None
            self._conn.execute(
                """
                INSERT INTO jobs (
                    id, title, company, url, board, published_at,
                    state, campaign_name, error_msg, discovered_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                [
                    job.id,
                    job.title,
                    job.company,
                    job.url,
                    job.board,
                    published_dt,
                    str(new_state),
                    campaign.name,
                    error_msg,
                    now,
                    now,
                ],
            )
            return True

        # Existing record update
        self._conn.execute(
            """
            UPDATE jobs
            SET state = ?,
                campaign_name = ?,
                error_msg = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            [str(new_state), campaign.name, error_msg, now, job.id],
        )
        return True

    async def get_campaign_metrics(self, campaign_name: str) -> dict[str, Any]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_campaign_metrics, campaign_name)

    def _sync_get_campaign_metrics(self, campaign_name: str) -> dict[str, Any]:
        if not self._conn:
            raise RuntimeError("Database is not connected. Call connect() first.")

        result = self._conn.execute(
            """
            SELECT
                COUNT(*) AS total_discovered,
                COUNT(CASE WHEN state = 'alert_sent' THEN 1 END) AS novel_alerts_sent,
                COUNT(CASE WHEN state = 'failed' THEN 1 END) AS failed_dispatches,
                COUNT(CASE WHEN state = 'duplicate' THEN 1 END) AS duplicates_suppressed,
                MAX(updated_at) AS last_active
            FROM jobs
            WHERE campaign_name = ?;
            """,
            [campaign_name],
        ).fetchone()

        if not result or result[0] == 0:
            return {
                "campaign_name": campaign_name,
                "total_discovered": 0,
                "novel_alerts_sent": 0,
                "failed_dispatches": 0,
                "duplicates_suppressed": 0,
                "last_active": None,
            }

        return {
            "campaign_name": campaign_name,
            "total_discovered": result[0],
            "novel_alerts_sent": result[1],
            "failed_dispatches": result[2],
            "duplicates_suppressed": result[3],
            "last_active": result[4].isoformat() if result[4] else None,
        }

    async def get_pending_alerts(self, limit: int = 50) -> Sequence[JobPost]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_pending_alerts, limit)

    def _sync_get_pending_alerts(self, limit: int = 50) -> Sequence[JobPost]:
        if not self._conn:
            raise RuntimeError("Database is not connected. Call connect() first.")

        rows = self._conn.execute(
            """
            SELECT id, title, company, url, board, published_at
            FROM jobs
            WHERE state IN ('alert_queued', 'failed')
            ORDER BY updated_at ASC
            LIMIT ?;
            """,
            [limit],
        ).fetchall()

        return [
            JobPost(
                id=row[0],
                title=row[1],
                company=row[2],
                url=row[3],
                board=row[4],
                published_at=to_datetime(row[5]) if row[5] else None,
            )
            for row in rows
        ]
