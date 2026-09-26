from __future__ import annotations

from .alert_carriers import Discord, Telegram
from .job_boards import Indeed, LinkedIn, ZipRecruiter
from .state_dbs import DuckDB, PostgresDB

__all__ = [
    # Alert Carriers
    "Discord",
    "Telegram",
    # Job Boards
    "Indeed",
    "LinkedIn",
    "ZipRecruiter",
    # State DBs
    "DuckDB",
    "PostgresDB",
]
