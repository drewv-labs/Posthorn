<div align="center">
  <img src="https://raw.githubusercontent.com/drewv-labs/Posthorn/main/.github/images/icon.svg" alt="Posthorn Logo" width="220"/>

  <h1>Posthorn</h1>
  <p><b>An extensible, async-first job monitoring and alerting daemon.</b></p>
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

**Start the app** using `posthorn` command. 

If you encounter any issues, try restarting your terminal session or re-sourcing your startup file.
* `source ~/.zshrc` for MacOS
* `source ~/.bashrc` for Linux

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
