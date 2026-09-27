import asyncio
import logging
import urllib.parse
from collections.abc import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost

logger = logging.getLogger(__name__)


class LinkedInBoard:
    """
    LinkedIn job board adapter using the unauthenticated guest API.
    Structurally fulfills the JobBoard protocol without using Selenium or triggering ATS bans.
    """

    @property
    def name(self) -> str:
        return "linkedin"

    async def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        """
        Sweeps the LinkedIn guest API for all permutations of campaign keywords and locations.
        Yields normalized JobPost objects.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Use a single async client session to connection-pool across the campaign sweep
        async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:

            for keyword in campaign.keywords:
                for location in campaign.locations:
                    kw_encoded = urllib.parse.quote(keyword)
                    loc_encoded = urllib.parse.quote(location)

                    # We only fetch start=0. Because Posthorn acts as an early-warning daemon
                    # running frequently (e.g., every 15 mins), any novel jobs will always be on page 1.
                    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw_encoded}&location={loc_encoded}&start=0"

                    try:
                        response = await client.get(url)
                        response.raise_for_status()

                        # The guest API returns bare HTML snippets (<li>/<div> tags), not a full document.
                        soup = BeautifulSoup(response.text, "html.parser")
                        job_cards = soup.find_all("div", class_="base-card")

                        for card in job_cards:
                            try:
                                # Narrow type for data-entity-urn
                                urn = card.get("data-entity-urn")
                                if not isinstance(urn, str) or not urn:
                                    continue
                                raw_id = urn.split(":")[-1]

                                title_elem = card.find("h3", class_="base-search-card__title")
                                company_elem = card.find("h4", class_="base-search-card__subtitle")
                                link_elem = card.find("a", class_="base-card__full-link")

                                # If any critical element is missing, skip to the next card
                                if not (raw_id and title_elem and company_elem and link_elem):
                                    continue

                                # Narrow type for href to avoid the same split() error
                                href = link_elem.get("href")
                                if not isinstance(href, str) or not href:
                                    continue
                                clean_url = href.split("?")[0]

                                yield JobPost(
                                    # Prefix ID with board name to prevent collisions with other job boards
                                    id=f"{self.name}_{raw_id}",
                                    title=title_elem.text.strip(),
                                    company=company_elem.text.strip(),
                                    url=clean_url,
                                    board=self.name,
                                    published_at=None # Guest card snippets don't cleanly expose ISO timestamps
                                )

                            except AttributeError as e:
                                logger.debug(f"Failed to parse a specific LinkedIn job card: {e}")
                                continue

                    except httpx.HTTPStatusError as e:
                        # 429 Too Many Requests means LinkedIn is rate limiting the IP.
                        # Log it, but don't crash the generator.
                        logger.warning(f"LinkedIn HTTP {e.response.status_code} for '{keyword}' in '{location}'.")
                    except httpx.RequestError as e:
                        logger.error(f"Network error polling LinkedIn for '{keyword}': {e}")

                    # Polite polling: yield control to the event loop and pause briefly
                    # before hitting the next keyword/location permutation.
                    await asyncio.sleep(2.5)
