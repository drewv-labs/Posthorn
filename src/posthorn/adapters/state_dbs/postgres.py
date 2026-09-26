from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import asyncpg

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost
from ...core.models.job_state_enum import JobState
from ...sugar.current_local_datetime import current_local_datetime
from ...sugar.to_datetime import to_datetime


class PostgresDB:
    """
    PostgreSQL state machine and persistent ledger implementation.

    Utilizes asyncpg for native, non-blocking I/O. Concurrency and race
    conditions are handled natively by PostgreSQL using row-level locks.
    """

    def __init__(self, dsn: str) -> None:
        """
        Args:
            dsn: PostgreSQL connection string
                 (e.g., 'postgres://user:pass@localhost:5432/posthorn')
        """
        self.dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=10)

        async with self._pool.acquire() as conn:
            await conn.execute(
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
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def is_novel(self, job_id: str) -> bool:
        if not self._pool:
            raise RuntimeError("Database is not connected. Call connect() first.")

        # fetchval returns the first column of the first row, or None if no rows match.
        result = await self._pool.fetchval(
            "SELECT 1 FROM jobs WHERE id = $1 LIMIT 1;",
            job_id
        )
        return result is None

    async def transition_state(
        self,
        job: JobPost,
        campaign: Campaign,
        new_state: JobState,
        error_msg: str | None = None,
    ) -> bool:
        if not self._pool:
            raise RuntimeError("Database is not connected. Call connect() first.")

        now = current_local_datetime()

        async with self._pool.acquire() as conn, conn.transaction():
            current_state = await conn.fetchval(
                "SELECT state FROM jobs WHERE id = $1 FOR UPDATE;",
                job.id
            )

            # FOR UPDATE locks this specific row across all Postgres connections
            # until this transaction commits or rolls back.
            current_state = await conn.fetchval(
                "SELECT state FROM jobs WHERE id = $1 FOR UPDATE;",
                job.id
            )

            # Lock check: Prevent duplicate alerts if already queued or sent
            if ((new_state == JobState.ALERT_QUEUED) and
                (current_state in (str(JobState.ALERT_SENT), str(JobState.ALERT_QUEUED)))):
                return False

            if current_state is None:
                # First time seeing this job, record it
                published_dt = to_datetime(job.published_at) if job.published_at else None
                await conn.execute(
                    """
                    INSERT INTO jobs (
                        id, title, company, url, board, published_at,
                        state, campaign_name, error_msg, discovered_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11);
                    """,
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
                )
                return True

            # Existing record update
            await conn.execute(
                """
                UPDATE jobs
                SET state = $1,
                    campaign_name = $2,
                    error_msg = $3,
                    updated_at = $4
                WHERE id = $5;
                """,
                str(new_state),
                campaign.name,
                error_msg,
                now,
                job.id,
            )
            return True

    async def get_campaign_metrics(self, campaign_name: str) -> dict[str, Any]:
        if not self._pool:
            raise RuntimeError("Database is not connected. Call connect() first.")

        row = await self._pool.fetchrow(
            """
            SELECT
                COUNT(*) AS total_discovered,
                COUNT(CASE WHEN state = 'alert_sent' THEN 1 END) AS novel_alerts_sent,
                COUNT(CASE WHEN state = 'failed' THEN 1 END) AS failed_dispatches,
                COUNT(CASE WHEN state = 'duplicate' THEN 1 END) AS duplicates_suppressed,
                MAX(updated_at) AS last_active
            FROM jobs
            WHERE campaign_name = $1;
            """,
            campaign_name,
        )

        if not row or row["total_discovered"] == 0:
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
            "total_discovered": row["total_discovered"],
            "novel_alerts_sent": row["novel_alerts_sent"],
            "failed_dispatches": row["failed_dispatches"],
            "duplicates_suppressed": row["duplicates_suppressed"],
            "last_active": row["last_active"].isoformat() if row["last_active"] else None,
        }

    async def get_pending_alerts(self, limit: int = 50) -> Sequence[JobPost]:
        if not self._pool:
            raise RuntimeError("Database is not connected. Call connect() first.")

        # asyncpg natively handles IN clauses using Postgres ANY($1::varchar[]) syntax
        rows = await self._pool.fetch(
            """
            SELECT id, title, company, url, board, published_at
            FROM jobs
            WHERE state = ANY($1::varchar[])
            ORDER BY updated_at ASC
            LIMIT $2;
            """,
            [str(JobState.ALERT_QUEUED), str(JobState.FAILED)],
            limit,
        )

        return [
            JobPost(
                id=row["id"],
                title=row["title"],
                company=row["company"],
                url=row["url"],
                board=row["board"],
                # asyncpg natively returns timezone-aware datetime objects for TIMESTAMPTZ
                published_at=to_datetime(row["published_at"]) if row["published_at"] else None,
            )
            for row in rows
        ]
