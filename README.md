<div align="center">
  <img src="https://raw.githubusercontent.com/drewv-labs/Posthorn/main/.github/images/icon.svg" alt="Posthorn Logo" width="220"/>

  <h1>Posthorn</h1>
  <p><b>Find a damn job like a boss.</b></p>
</div>

<br/>

Posthorn is a lightweight, TUI supported background service designed to poll job boards, filter for specific campaigns, and push early-warning alerts to webhooks or chat platforms. Built on modern Python concurrency, it relies on an embedded DuckDB state machine to enforce absolute idempotency—guaranteeing that a matched job is alerted on exactly once, even across overlapping sweeps or network failures.

## ⚡ Core Philosophy

* **Performance over Gimmicks:** Zero heavy headless browsers. Polling relies purely on `httpx` and lightweight `BeautifulSoup4` HTML parsing.
* **Structural Subtyping:** Core architecture relies entirely on `typing.Protocol`. Adapters for new job boards or carriers duck-type perfectly into the orchestrator without rigid inheritance hierarchies.
* **Strict Idempotency:** The DuckDB backend maintains a transactional state machine (`DISCOVERED` -> `ALERT_QUEUED` -> `ALERT_SENT`), acting as an airlock against duplicate alerts and race conditions.
* **Type-Safe & Tested:** 100% Pyright/Mypy compliant, backed by a comprehensive `pytest-asyncio` test suite utilizing memory-resident database fixtures.

---

## 🏗 Architecture

Posthorn is built around two interchangeable layers orchestrated by the main `PosthornDaemon` daemon loop:

1. **Job Boards (`JobBoard` Protocol):** Inbound data adapters.
* *Included:* `LinkedIn`, `Indeed`, `ZipRecruiter`.


2. **Alert Carriers (`AlertCarrier` Protocol):** Outbound notification dispatchers.
* *Included:* `Discord` (Rich Webhooks), `Telegram`.



---

## 🚀 Quick Start

Posthorn is a frictionless, terminal-native daemon. Because of its dynamic registry architecture, it requires zero Python scripting to configure and run.

### Installation

We recommend installing Posthorn globally as a standalone tool using Astral's `uv`:

```bash
uv tool install posthorn
```

### Launch & Zero-Friction Setup
Simply launch the orchestrator from your terminal:

```Bash
posthorn
```

If this is your first time booting the daemon, Posthorn will automatically intercept the boot sequence and launch a terminal UI wizard to capture your webhook/bot credentials and initial target job title. It will then generate your configuration, instantiate the adapters, and immediately start the background sweep.

### Example Configuration: The "Telelink" Setup
Configurations are securely stored in ~/.posthorn/config.toml. To replicate a daemon that sweeps LinkedIn and sends alerts via Telegram for multiple data and edge computing campaigns, your configuration file would look like this:

```Ini, TOML
[daemon]
sweep_interval_minutes = 15
statemachine_file = "~/.posthorn/posthorn.duckdb"

[carrier]
type = "telegram"
bot_token = "YOUR_BOT_TOKEN"
chat_id = "YOUR_CHAT_ID"

[[job_boards]]
type = "linkedin"

[[campaigns]]
name = "EdgeAI-Engineer"
keywords = ["Edge AI", "Engineer", "Rust", "Python"]
locations = ["Remote", "Richardson, TX"]

[[campaigns]]
name = "Data-Architect"
keywords = ["Data Architect", "Data Engineering"]
locations = ["Remote", "Dallas, TX"]
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

### Local Execution & State Management
When iterating on adapters or testing the TUI locally, you can launch the daemon directly via uv:

```bash
uv run posthorn
```

If you need to wipe your local job discovery history to trigger fresh alerts for testing, Posthorn includes a built-in developer reset flag. This command safely purges the active DuckDB database and Write-Ahead Log (.wal) while preserving your config.toml parameters and rolling .bak snapshots:

```bash
uv run posthorn --dev-reset
```

### Release Process
Posthorn uses strict, uv-native version management and GitHub Actions for automated OIDC publishing to PyPI. Before merging a feature branch to main, bump the version locally:

```bash
# Automatically increments pyproject.toml
uv version --bump patch  # or minor, major
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
