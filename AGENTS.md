# Posthorn: Agent Context & Directives

## 1. Mission & Core Philosophy
Posthorn is a Python-based, adapter-driven job post alerting daemon. It is a **passive observation framework**, not an aggressive web scraper or auto-applier. 
*   **The Goal:** Silently poll job boards, track state immutably, and dispatch alerts to external carriers (Telegram, Discord) immediately when novel matches are found.
*   **The Vibe:** Old-school UNIX daemon. Reliable, stateless outside of its DB, strictly typed, and completely modular.

## 2. Toolchain & Environment
*   **Runtime:** Python 3.11+ strictly. 
*   **Package Management:** Astral's `uv`.
    *   *Agent Directive:* Never use `pip install`, `poetry`, or `requirements.txt`. Use `uv add <pkg>` or `uv run` exclusively.
*   **Linting & Formatting:** `ruff`. 
    *   *Agent Directive:* Run `uv run ruff check --fix` and `uv run ruff format` before committing.
*   **Type Checking:** `mypy` (Strict mode).
    *   *Agent Directive:* All new code must be fully type-hinted and pass `uv run mypy .` without errors.

## 3. Architectural Invariants
*   **Structural Subtyping:** Core components (`JobBoard`, `AlertCarrier`, `StateDB`) are defined using `typing.Protocol`. Adapters must structurally fulfill these protocols—do not use classic inheritance or base classes.
*   **Immutable Payloads:** Data structures crossing protocol boundaries (`JobPost`, `Campaign`) MUST be defined as `@dataclasses.dataclass(frozen=True)`.
*   **Async First:** I/O operations (polling APIs, dispatching webhooks, database transitions) must use `async`/`await` and `AsyncGenerator`. Prefer `httpx` over `requests`.
*   **Idempotent State Management:** The `StateDB` (DuckDB/SQLite) is the single source of truth for the state machine. Race conditions or duplicate scrapes must be resolved by idempotent database constraints, not Python memory logic.

## 4. Judgment Boundaries

**NEVER (Hard Limits):**
*   **Never implement auto-apply features.** Posthorn is an early-warning radar, not an automated actor. Doing so risks account bans for the user.
*   **Never use heavy browser automation** (e.g., Selenium, Playwright) for adapters unless explicitly authorized. Default to undocumented guest APIs, RSS feeds, or lightweight HTML parsing (`BeautifulSoup`).
*   **Never swallow exceptions silently.** If an `AlertCarrier` fails, transition the DB state to `FAILED` and log the error context so the retry mechanism can handle it later.

**ALWAYS (Proactive Requirements):**
*   **Always use timezone-aware datetimes.** Never use naive datetimes. Use the system's internal `current_local_datetime()` and `to_datetime()` utilities for normalization.
*   **Always sanitize outputs for the carrier.** `AlertCarrier` adapters (like Telegram) are sensitive to unescaped special characters in job titles (like `<` or `_`). Always use appropriate HTML/Markdown escaping before dispatch.

## 5. Directory Map & Component Responsibilities

```text
Posthorn/
├── apps/
│   └── posthorn-telelink.py         # Entrypoint daemon/app linking Telegram carrier to Posthorn pipeline
├── poc/
│   └── jimmy_script.py              # Exploratory prototypes and scratchpad scripts (never import into src)
├── src/posthorn/
│   ├── adapters/                    # Concrete structural implementations of core interfaces
│   │   ├── alert_carriers/          # Outbound dispatchers (discord.py, telegram.py)
│   │   ├── job_boards/              # Inbound polling engines (indeed.py, linkedin.py, ziprecruiter.py)
│   │   └── state_dbs/               # Persistent state machine ledgers (duckdb.py, postgres.py)
│   ├── core/                        # Pure domain logic and structural types (zero external adapter dependencies)
│   │   ├── interfaces/              # typing.Protocol definitions (alert_carrier.py, job_board.py, state_db.py)
│   │   ├── managers/                # Orchestration handlers (campaign_manager.py, job_board_manager.py)
│   │   ├── models/                  # Frozen data containers & enums (campaign_model.py, job_post_model.py, job_state_enum.py)
│   │   └── posthorn.py              # Main Posthorn daemon coordinator / runtime engine
│   └── sugar/                       # Pure utility helpers (current_local_datetime.py, to_date.py, to_datetime.py)
└── tests/                           # Unit and integration test suite
```
