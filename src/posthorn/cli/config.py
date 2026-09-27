import tomllib
from pathlib import Path
from typing import Any

import tomli_w

CONFIG_DIR = Path.home() / ".posthorn"
CONFIG_PATH = CONFIG_DIR / "config.toml"

def load_config() -> dict[str, Any] | None:
    """Loads the TOML config. Returns None if it doesn't exist."""
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

def save_config(config_data: dict[str, Any]) -> None:
    """Serializes a configuration dictionary and writes it to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "wb") as f:
        tomli_w.dump(config_data, f)

def generate_default_config(webhook_url: str, job_title: str) -> None:
    """Generates the baseline configuration for a first-time user."""
    db_path = (CONFIG_DIR / "posthorn.duckdb").as_posix()

    baseline_config = {
        "daemon": {
            "sweep_interval_minutes": 15,
            "statemachine_file": db_path,
        },
        "carrier": {
            "type": "discord",
            "webhook_url": webhook_url,
        },
        "job_boards": [
            {"type": "linkedin"},
            {"type": "ziprecruiter"},
        ],
        "campaigns": [
            {
                "name": "Primary Search",
                "keywords": [job_title],
                "locations": ["Remote"],
            }
        ]
    }

    save_config(baseline_config)
