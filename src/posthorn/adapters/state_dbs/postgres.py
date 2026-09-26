from __future__ import annotations


class PostgresDB:

    @property
    def name(self) -> str:
        return "postgres-state-db"
