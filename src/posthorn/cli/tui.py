from __future__ import annotations

import tomllib
from pathlib import Path

from ..core import PosthornDaemon
from .app import PosthornApp


def load_daemon_from_disk():
    config_path = Path.home() / ".posthorn" / "config.toml"

    if not config_path.exists():
        return None # Triggers the TUI Setup Wizard we discussed

    with open(config_path, "rb") as f:
        raw_config = tomllib.load(f)

    return PosthornDaemon.from_config(raw_config)


def main():
    daemon = load_daemon_from_disk()
    app = PosthornApp(daemon=daemon)
    app.run()


if __name__ == "__main__":
    main()
