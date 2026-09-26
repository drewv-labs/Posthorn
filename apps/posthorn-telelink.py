"""
This represents a Posthorn implementation using:
    LinkedIn job board
    Telegram alert carrier
"""
from __future__ import annotations

from posthorn import (
    Campaign,
    CampaignManager,
    JobBoardManager,
    Posthorn,
)
from posthorn.adapters import (
    LinkedIn,
    Telegram,
)


def main():
    posthorn = Posthorn(
        alert_carrier=Telegram(
            token="",
            chat_id="",
        ),
        job_boards=JobBoardManager(
            job_boards=[
                LinkedIn(),
            ]
        ),
        campaigns=CampaignManager(
            campaigns=[
                Campaign(),
            ]
        ),
    )
    posthorn.start()


if __name__ == "__main__":
    main()
