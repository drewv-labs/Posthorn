import tomllib
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".posthorn"
CONFIG_PATH = CONFIG_DIR / "config.toml"

def load_config() -> dict[str, Any] | None:
    """Loads the TOML config. Returns None if it doesn't exist."""
    if not CONFIG_PATH.exists():
        return None

    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        # For now, just print to terminal before TUI takes over.
        # You could route this to a dedicated error screen later.
        print(f"Error parsing config.toml: {e}")
        return None

def generate_default_config(webhook_url: str, job_title: str) -> None:
    """Generates the baseline TOML file for a first-time user."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    toml_content = f"""[daemon]
sweep_interval_minutes = 15

[carrier]
type = "discord"
webhook_url = "{webhook_url}"

[[job_boards]]
type = "mock_board" # TODO: Map this to your real board adapters

[[campaigns]]
name = "Primary Search"
keywords = ["{job_title}"]
locations = ["Remote"]
"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(toml_content)
