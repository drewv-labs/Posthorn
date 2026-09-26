from __future__ import annotations

from posthorn import (
    CampaignManager,
    CampaignManagerConfig,
    JobBoardManager,
    JobBoardManagerConfig,
    Posthorn,
    PosthornConfig,
)
from posthorn.adapters import (
    LinkedIn,
    LinkedInConfig,
    Telegram,
    TelegramConfig,
)


def main():
    posthorn = Posthorn.from_config(PosthornConfig(
        alert_carrier=Telegram.from_config(TelegramConfig(
            token="",
            chat_id="",
        )),
        job_boards=JobBoardManager.from_config(JobBoardManagerConfig(

        )),
        campaigns=CampaignManager.from_config(CampaignManagerConfig(
            
        )),
    ))
    posthorn.run()


if __name__ == "__main__":
    main()