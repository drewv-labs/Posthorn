from __future__ import annotations

from ..core import PosthornDaemon
from .app import PosthornApp
from .config import load_config


def load_daemon_from_disk():
    raw_config = load_config()

    if not raw_config:
        return None # Triggers the TUI Setup Wizard

    return PosthornDaemon.from_config(raw_config)


def main():
    daemon = load_daemon_from_disk()
    app = PosthornApp(daemon=daemon)
    app.run()


if __name__ == "__main__":
    main()
