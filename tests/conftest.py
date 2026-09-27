from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest

from posthorn.adapters.state_dbs.duckdb import DuckDB
from posthorn.core.models.campaign_model import Campaign
from posthorn.core.models.job_post_model import JobPost


class MockCarrier:
    """
    A fake AlertCarrier that fulfills the protocol but just stores
    dispatched jobs in memory so tests can verify they were sent.
    """
    def __init__(self) -> None:
        self.dispatched_jobs: list[tuple[JobPost, Campaign]] = []

    @property
    def name(self) -> str:
        return "mock_carrier"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        self.dispatched_jobs.append((job, campaign))


@pytest.fixture
def mock_carrier() -> MockCarrier:
    """Provides a fresh MockCarrier for each test."""
    return MockCarrier()


@pytest.fixture
async def memory_db() -> AsyncGenerator[DuckDB, None]:
    """
    Provides a fresh, isolated, in-memory DuckDB database for each test.
    Automatically connects before the test and disconnects after.
    """
    db = DuckDB(db_path=":memory:")
    await db.connect()

    yield db  # Hands control to the test function

    await db.disconnect()  # Cleanup runs automatically after the test finishes


@pytest.fixture
def sample_campaign() -> Campaign:
    return Campaign(
        name="Test-EdgeAI-Campaign",
        keywords=["Edge AI", "Rust"],
        locations=["Remote", "Texas"]
    )


@pytest.fixture
def sample_job() -> JobPost:
    return JobPost(
        id="testboard_998877",
        title="Senior Edge AI Engineer",
        company="DarkSilicon Labs",
        url="https://darksilicon.local/careers/998877",
        board="testboard",
        published_at=datetime.now(UTC)
    )
