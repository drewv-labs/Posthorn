import logging

import httpx

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost

logger = logging.getLogger(__name__)


class DiscordCarrier:
    """
    Discord webhook alert dispatcher.
    Structurally fulfills the AlertCarrier protocol.
    """

    def __init__(self, webhook_url: str) -> None:
        """
        Args:
            webhook_url: The full webhook URL generated from Discord
                         (Server Settings -> Integrations -> Webhooks).
        """
        self.webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "discord"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        """
        Transmits the job payload to the configured Discord channel via webhook.

        Raises:
            RuntimeError: If the HTTP request fails, allowing the orchestrator
                          to catch the error and transition the DB state to FAILED.
        """
        # Using Discord's rich embed format provides a significantly
        # cleaner UI experience than raw markdown text.
        payload = {
            "embeds": [
                {
                    "title": job.title,
                    "url": job.url,
                    "color": 3447003,  # Posthorn Blue (Hex: #3498DB)
                    "author": {
                        "name": f"🚨 New Match: {campaign.name}"
                    },
                    "fields": [
                        {
                            "name": "Company",
                            "value": job.company,
                            "inline": True
                        },
                        {
                            "name": "Board",
                            "value": job.board,
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "Posthorn Alerting Daemon"
                    }
                }
            ]
        }

        # Instantiating the client per-dispatch is optimal for low-frequency sweeps.
        async with httpx.AsyncClient() as client:
            try:
                # Discord requires a standard JSON POST to the webhook endpoint
                response = await client.post(self.webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                error_msg = f"Discord webhook rejected payload (Status {e.response.status_code}): {e.response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except httpx.RequestError as e:
                error_msg = f"Network error connecting to Discord webhook: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
