<div align="center">
  <img src=".github/images/icon.png" alt="Posthorn Logo" width="220"/>
  
  <h1>Posthorn</h1>
  <p><b>An extensible, async-first job monitoring and alerting daemon.</b></p>
</div>

<br/>

## ⚡ Core Philosophy

Posthorn is a lightweight, strictly-typed Python background service designed to poll job boards, filter for specific campaigns, and push early-warning alerts to webhooks or chat platforms. Built on modern Python concurrency, it relies on an embedded DuckDB state machine to enforce absolute idempotency—guaranteeing that a matched job is alerted on exactly once, even across overlapping sweeps or network failures.

## ⚡ Core Philosophy

* **Performance over Gimmicks:** Zero heavy headless browsers. Polling relies purely on `httpx` and lightweight `BeautifulSoup4` HTML parsing.
* **Structural Subtyping:** Core architecture relies entirely on `typing.Protocol`. Adapters for new job boards or carriers duck-type perfectly into the orchestrator without rigid inheritance hierarchies.
* **Strict Idempotency:** The DuckDB backend maintains a transactional state machine (`DISCOVERED` -> `ALERT_QUEUED` -> `ALERT_SENT`), acting as an airlock against duplicate alerts and race conditions.
* **Type-Safe & Tested:** 100% Pyright/Mypy compliant, backed by a comprehensive `pytest-asyncio` test suite utilizing memory-resident database fixtures.

---

## 🏗 Architecture

Posthorn is built around three interchangeable layers orchestrated by the main `Posthorn` daemon loop:

1. **Job Boards (`JobBoard` Protocol):** Inbound data adapters.
* *Included:* `LinkedIn`, `Indeed`, `ZipRecruiter`.


2. **Alert Carriers (`AlertCarrier` Protocol):** Outbound notification dispatchers.
* *Included:* `Discord` (Rich Webhooks), `Telegram`.


3. **State Database:** The idempotency lock and metrics tracker.
* *Included:* `DuckDB`.



---

## 🚀 Quick Start

### Installation

Posthorn is designed to be deployed into modern, isolated Python environments. We recommend using Astral's `uv`:

```bash
uv pip install posthorn

```

### Example Usage: The "Telelink" Daemon

Wiring up an alerting daemon requires simply declaring your carriers, boards, and campaigns, then awaiting the `run()` loop.

```python
import asyncio

import posthorn as horn
from posthorn.adapters import LinkedIn, Telegram

async def main():
    app = horn.Posthorn(
        # 1. Define where alerts should go
        alert_carrier=Telegram(
            bot_token="YOUR_BOT_TOKEN",
            chat_id="YOUR_CHAT_ID",
        ),
        
        # 2. Define which platforms to scrape
        job_boards=horn.JobBoardManager([
            LinkedIn(),
        ]),
        
        # 3. Define your target campaigns
        campaigns=horn.CampaignManager([
            horn.Campaign(
                name="EdgeAI-Engineer",
                keywords=["Edge AI", "Engineer", "Rust", "Python"],
                locations=["Remote", "Richardson, TX"]
            ),
            horn.Campaign(
                name="Data-Architect",
                keywords=["Data Architect", "Data Engineering"],
                locations=["Remote", "Dallas, TX"]
            ),
        ]),
    )
    
    # Fire up the daemon loop (defaults to a 15-minute sweep interval)
    await app.run(interval_seconds=900)

if __name__ == "__main__":
    asyncio.run(main())

```

---

## 🛠 Extending Posthorn

Adding a custom integration is as simple as fulfilling a Protocol. No subclassing required.

### Custom Alert Carrier

Just implement a `.name` property and an `async def dispatch()` method.

```python
class SlackCarrier:
    @property
    def name(self) -> str:
        return "slack"

    async def dispatch(self, job: JobPost, campaign: Campaign) -> None:
        payload = {"text": f"New match for {campaign.name}: {job.title} at {job.company}\n{job.url}"}
        async with httpx.AsyncClient() as client:
            await client.post(SLACK_WEBHOOK_URL, json=payload)

```

---

## 🧪 Development & Testing

Posthorn utilizes `pytest` with `pytest-asyncio` for its testing framework. The suite is designed to run locally with zero infrastructure footprint by injecting a transient, in-memory DuckDB database into the test context.

```bash
# Install development dependencies
uv sync --dev

# Run the test suite
uv run pytest -v

```

---

## 📝 License

MIT License. Build, extend, and deploy.

----

Made with ♥️ by
```py
DREW-V := {
  "Simplicity in the Architecture",
  "Efficiency in the Engineering",
  "Purity in the Science",
  "Audacity in the Art",
  "Life in the Logic"
}
```
