import tomllib
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".posthorn"
CONFIG_PATH = CONFIG_DIR / "config.toml"

def load_config() -> dict[str, Any] | None:
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

def generate_default_config(webhook_url: str, job_title: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Use .as_posix() to prevent Windows backslash escaping in the TOML string
    db_path = (CONFIG_DIR / 'posthorn.duckdb').as_posix()

    toml_content = f"""[daemon]
sweep_interval_minutes = 15
statemachine_file = "{db_path}"

[carrier]
type = "discord"
webhook_url = "{webhook_url}"

[[job_boards]]
type = "mock_board"

[[campaigns]]
name = "Primary Search"
keywords = ["{job_title}"]
locations = ["Remote"]
"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(toml_content)
