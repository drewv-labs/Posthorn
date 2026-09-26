import asyncio
import logging
import re
import urllib.parse
from collections.abc import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost

logger = logging.getLogger(__name__)


class ZipRecruiter:
    """
    ZipRecruiter job board adapter using lightweight HTML parsing.
    Structurally fulfills the JobBoard protocol.
    """

    @property
    def name(self) -> str:
        return "ziprecruiter"

    async def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        """
        Sweeps ZipRecruiter for all permutations of campaign keywords and locations.
        Yields normalized JobPost objects.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:

            for keyword in campaign.keywords:
                for location in campaign.locations:
                    kw_encoded = urllib.parse.quote(keyword)
                    loc_encoded = urllib.parse.quote(location)

                    # 'days=1' ensures we only pull recent listings, keeping the payload small
                    # for the early-warning daemon pattern.
                    url = f"https://www.ziprecruiter.com/jobs-search?search={kw_encoded}&location={loc_encoded}&days=1"

                    try:
                        response = await client.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")

                        # ZipRecruiter frequently rotates its DOM structure.
                        # They commonly wrap job cards in <article> tags or <div> tags with a data-job-id.
                        job_cards = soup.find_all(lambda tag: tag.has_attr("data-job-id") and tag.name in ["article", "div"])

                        for card in job_cards:
                            try:
                                # Narrow type for data-job-id
                                raw_id = card.get("data-job-id")
                                if not isinstance(raw_id, str) or not raw_id:
                                    continue

                                # Use compiled regex instead of lambdas for type-safe substring matching
                                title_elem = card.find("h2") or card.find("a", class_=re.compile(r"job_link", re.IGNORECASE))
                                title = title_elem.text.strip() if title_elem else "Unknown Title"

                                # Pass `True` as the tag name when searching purely by class attributes
                                company_elem = card.find(True, class_=re.compile(r"company", re.IGNORECASE))
                                company = company_elem.text.strip() if company_elem else "Unknown Company"

                                link_elem = card.find("a", href=True)
                                if not link_elem:
                                    continue

                                # Narrow type for href
                                raw_url = link_elem.get("href")
                                if not isinstance(raw_url, str) or not raw_url:
                                    continue

                                if raw_url.startswith("/"):
                                    raw_url = f"https://www.ziprecruiter.com{raw_url}"
                                clean_url = raw_url.split("?")[0]

                                yield JobPost(
                                    id=f"{self.name}_{raw_id}",
                                    title=title,
                                    company=company,
                                    url=clean_url,
                                    board=self.name,
                                    published_at=None
                                )

                            except Exception as e:
                                logger.debug(f"Failed to parse a specific ZipRecruiter job card: {e}")
                                continue

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code in (403, 429):
                            logger.warning(f"ZipRecruiter rate limit or block (HTTP {e.response.status_code}) for '{keyword}'.")
                        else:
                            logger.warning(f"ZipRecruiter HTTP {e.response.status_code} for '{keyword}' in '{location}'.")
                    except httpx.RequestError as e:
                        logger.error(f"Network error polling ZipRecruiter for '{keyword}': {e}")

                    # Polite polling delay
                    await asyncio.sleep(3.0)
