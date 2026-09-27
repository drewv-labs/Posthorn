"""
This represents a Posthorn implementation using:
    LinkedIn job board
    Telegram alert carrier
"""
from __future__ import annotations

import asyncio

import posthorn as horn
from posthorn.adapters import (
    LinkedIn,
    Telegram,
)


async def main():
    posthorn = horn.Posthorn(
        alert_carrier=Telegram(
            bot_token="",
            chat_id="",
        ),
        job_boards=horn.JobBoardManager(
            job_boards=[
                LinkedIn(),
            ]
        ),
        campaigns=horn.CampaignManager(
            campaigns=[
                horn.Campaign(
                    name="Telelink-EdgeAI-Engineer",
                    keywords=["Edge AI", "Engineer"],
                ),
                horn.Campaign(
                    name="Telelink-EdgeAI-Architect",
                    keywords=["Edge AI", "Architect"],
                ),
            ]
        ),
    )
    await posthorn.run()


if __name__ == "__main__":
    asyncio.run(main())
