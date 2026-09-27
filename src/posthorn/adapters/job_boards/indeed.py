import asyncio
import logging
import urllib.parse
from collections.abc import AsyncGenerator

import httpx
from bs4 import BeautifulSoup

from ...core.models.campaign_model import Campaign
from ...core.models.job_post_model import JobPost

logger = logging.getLogger(__name__)


class IndeedBoard:
    """
    Indeed job board adapter using lightweight HTML parsing.
    Structurally fulfills the JobBoard protocol.

    Note: Indeed aggressively utilizes Cloudflare. If 403 Forbidden errors occur
    frequently in production, this adapter's httpx client may need to be swapped
    for a TLS-impersonating client (like curl_cffi) or routed through a proxy.
    """

    @property
    def name(self) -> str:
        return "indeed"

    async def poll(self, campaign: Campaign) -> AsyncGenerator[JobPost, None]:
        """
        Sweeps Indeed for all permutations of campaign keywords and locations.
        Yields normalized JobPost objects.
        """
        # Standard browser headers to delay automated blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:

            for keyword in campaign.keywords:
                for location in campaign.locations:
                    kw_encoded = urllib.parse.quote(keyword)
                    loc_encoded = urllib.parse.quote(location)

                    # sort=date is critical for an alerting daemon to ensure novel jobs
                    # are always at the top of page 1.
                    url = f"https://www.indeed.com/jobs?q={kw_encoded}&l={loc_encoded}&sort=date"

                    try:
                        response = await client.get(url)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Indeed wraps job cards in a container that usually contains a 'job_seen_beacon' class
                        # or directly target the anchor tags holding the 'data-jk' (Job Key) attribute.
                        job_links = soup.find_all("a", attrs={"data-jk": True})

                        for link in job_links:
                            try:
                                raw_id = link["data-jk"]

                                # Title is typically nested in an h2 or span inside the anchor
                                title_elem = link.find("span", title=True)
                                title = title_elem.text.strip() if title_elem else link.text.strip()

                                # Company name is usually in a sibling div/span with specific test-ids
                                # We traverse up to the parent card to find it
                                card = link.find_parent("td", class_="resultContent") or link.find_parent("div", class_="cardOutline")
                                company = "Unknown Company"

                                if card:
                                    company_elem = card.find("span", attrs={"data-testid": "company-name"})
                                    if company_elem:
                                        company = company_elem.text.strip()

                                if not raw_id or not title:
                                    continue

                                # Reconstruct a clean URL using just the Job Key (jk) parameter
                                clean_url = f"https://www.indeed.com/viewjob?jk={raw_id}"

                                yield JobPost(
                                    id=f"{self.name}_{raw_id}",
                                    title=title,
                                    company=company,
                                    url=clean_url,
                                    board=self.name,
                                    published_at=None
                                )

                            except Exception as e:
                                logger.debug(f"Failed to parse a specific Indeed job card: {e}")
                                continue

                    except httpx.HTTPStatusError as e:
                        if e.response.status_code in (403, 429):
                            logger.warning(f"Indeed blocked the request (HTTP {e.response.status_code}) for '{keyword}'. Cloudflare challenge likely triggered.")
                        else:
                            logger.warning(f"Indeed HTTP {e.response.status_code} for '{keyword}' in '{location}'.")
                    except httpx.RequestError as e:
                        logger.error(f"Network error polling Indeed for '{keyword}': {e}")

                    # Polite polling: delay slightly longer for Indeed to avoid immediate IP bans
                    await asyncio.sleep(4.0)
