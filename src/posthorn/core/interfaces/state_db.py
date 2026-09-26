from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..models import Campaign, JobPost, JobState


@runtime_checkable
class StateDB(Protocol):
    """
    Structural type for the Posthorn state machine and ledger.
    Responsible for state transition management, deduplication, and lightweight reporting.

    Implementations (e.g., DuckDB, SQLite) should ensure operations are idempotent.
    """

    async def connect(self) -> None:
        """
        Initialize the database connection.
        Implementations should handle schema creation and migrations here.
        """
        ...

    async def disconnect(self) -> None:
        """Safely close the database connection and flush WAL/buffers."""
        ...

    async def transition_state(
        self,
        job: JobPost,
        campaign: Campaign,
        new_state: JobState,
        error_msg: str | None = None
    ) -> bool:
        """
        Moves a JobPost through the state machine.

        This is the core ledger method. If new_state == ALERT_QUEUED and the job
        already exists in the DB as ALERT_SENT, the DB should reject the transition
        and return False (preventing duplicate alerts).

        Args:
            job: The normalized job payload.
            campaign: The campaign session that discovered the job.
            new_state: The target state for the job.
            error_msg: Optional context if transitioning to FAILED.

        Returns:
            bool: True if the state transition was successful, False if rejected.
        """
        ...

    async def is_novel(self, job_id: str) -> bool:
        """
        Fast check to see if a job has ever been seen by the system.
        Useful for dropping payloads early before executing heavier state transitions.
        """
        ...

    # --- Reporting Engine Interface ---

    async def get_campaign_metrics(self, campaign_name: str) -> dict[str, Any]:
        """
        Retrieve performance statistics for a specific campaign.
        Example return:
        {
            "total_discovered": 140,
            "novel_alerts_sent": 3,
            "last_active": "2026-09-26T08:14:00Z"
        }
        """
        ...

    async def get_pending_alerts(self, limit: int = 50) -> Sequence[JobPost]:
        """
        Retrieve jobs stuck in ALERT_QUEUED or FAILED states.
        Useful if Posthorn crashes midway and needs to resume dispatching on startup.
        """
        ...
