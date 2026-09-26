import html
import logging

import httpx

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost

logger = logging.getLogger(__name__)


class Telegram:
    """
    Telegram alert dispatcher.
    Structurally fulfills the AlertCarrier protocol.
    """

    def __init__(self, bot_token: str, chat_id: str | int) -> None:
        """
        Args:
            bot_token: The API token provided by @BotFather.
            chat_id: The destination chat ID (can be a user, group, or channel).
        """
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self._url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    @property
    def name(self) -> str:
        return "telegram"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        """
        Transmits the job payload to the configured Telegram chat.

        Raises:
            RuntimeError: If the HTTP request fails, allowing the orchestrator
                          to catch the error and transition the DB state to FAILED.
        """
        # HTML parsing mode handles unescaped characters (like ampersands or brackets
        # in job titles) much more reliably than Telegram's MarkdownV2.
        text = (
            f"🚨 <b>New Match: {html.escape(campaign.name)}</b>\n\n"
            f"<b>Role:</b> {html.escape(job.title)}\n"
            f"<b>Company:</b> {html.escape(job.company)}\n"
            f"<b>Board:</b> {html.escape(job.board)}\n\n"
            f"<a href=\"{job.url}\">View Job Posting</a>"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        # Instantiating the client per-dispatch is perfectly fine for a low-frequency
        # alerting daemon. If volume increases, this could be refactored to accept
        # a shared httpx.AsyncClient() injected during __init__.
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self._url, json=payload, timeout=10.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                error_msg = f"Telegram API rejected payload: {e.response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except httpx.RequestError as e:
                error_msg = f"Network error connecting to Telegram: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
