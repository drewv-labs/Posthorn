# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "beautifulsoup4",
# ]
# ///

import html
import json
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

# Search parameters (URL encoded)
SEARCH_KEYWORD = "Tribology" # Or "Surface Mechanics"
LOCATION = "United States"

# File to track jobs we've already alerted on
SEEN_JOBS_FILE = Path("seen_jobs.json")

def load_seen_jobs():
    if SEEN_JOBS_FILE.exists():
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen_jobs):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen_jobs), f)

def fetch_latest_jobs():
    """Hits the LinkedIn guest API to bypass login walls and bot detection."""
    print(f"Polling LinkedIn for: {SEARCH_KEYWORD}...")

    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={SEARCH_KEYWORD}&location={LOCATION}&start=0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Failed to fetch jobs: {e}")
        return ""

def parse_jobs(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    job_cards = soup.find_all("div", class_="base-card")

    jobs = []
    for card in job_cards:
        try:
            job_id = card.get("data-entity-urn").split(":")[-1]
            title_element = card.find("h3", class_="base-search-card__title")
            company_element = card.find("h4", class_="base-search-card__subtitle")
            link_element = card.find("a", class_="base-card__full-link")

            if job_id and title_element and company_element and link_element:
                jobs.append({
                    "id": job_id,
                    "title": title_element.text.strip(),
                    "company": company_element.text.strip(),
                    "link": link_element["href"].split("?")[0] # Clean URL tracking tags
                })
        except AttributeError:
            continue

    return jobs

def send_telegram_alert(job):
    print(f"🚨 New Match Found: {job['title']} at {job['company']}")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # HTML parsing mode handles unescaped characters better than Markdown
    text = (
        f"🚨 <b>New High-Priority Job Alert!</b>\n\n"
        f"<b>Role:</b> {html.escape(job['title'])}\n"
        f"<b>Company:</b> {html.escape(job['company'])}\n\n"
        f"<a href=\"{job['link']}\">View Job Posting</a>"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True # Keeps the chat uncluttered
    }

    try:
        httpx.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def main():
    seen_jobs = load_seen_jobs()
    html_content = fetch_latest_jobs()

    if not html_content:
        return

    current_jobs = parse_jobs(html_content)

    new_jobs_found = False
    for job in current_jobs:
        if job["id"] not in seen_jobs:
            send_telegram_alert(job)
            seen_jobs.add(job["id"])
            new_jobs_found = True
            time.sleep(1) # Rate limit API calls

    if new_jobs_found:
        save_seen_jobs(seen_jobs)
    else:
        print("No new jobs found this cycle.")

if __name__ == "__main__":
    main()
