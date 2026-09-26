from __future__ import annotations

from typing import Any

from posthorn.core import JobPost


class DuckDB:

    @property
    def name(self) -> str:
        return "duckdb-state-db"

    def update(self, job_post: JobPost, context: dict[str, Any]):
        pass
