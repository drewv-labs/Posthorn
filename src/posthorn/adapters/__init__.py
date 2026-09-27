from __future__ import annotations

from .alert_carriers import (
    DiscordCarrier,
    TelegramCarrier,
)
from .job_boards import (
    IndeedBoard,
    LinkedInBoard,
    ZipRecruiterBoard,
)

CARRIER_REGISTRY = {
    "discord": DiscordCarrier,
    # "slack": Slack,
    "telegram": TelegramCarrier,
}

JOB_BOARD_REGISTRY = {
    "linkedin": LinkedInBoard,
    "indeed": IndeedBoard,
    "ziprecruiter": ZipRecruiterBoard,
    "zip": ZipRecruiterBoard,
}


__all__ = [
    # Alert Carriers
    "DiscordCarrier",
    "TelegramCarrier",
    # Job Boards
    "IndeedBoard",
    "LinkedInBoard",
    "ZipRecruiterBoard",
]
