from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..core import PosthornDaemon
from .app import PosthornApp
from .config import load_config


def load_daemon_from_disk():
    raw_config = load_config()

    if not raw_config:
        return None # Triggers the TUI Setup Wizard

    return PosthornDaemon.from_config(raw_config)


def main():
    parser = argparse.ArgumentParser(description="Posthorn Alerting Daemon")
    parser.add_argument("--dev-reset", action="store_true", help="Wipes the DuckDB state machine and exits.")

    # parse_known_args prevents crashes if Textual or uv passes internal flags
    args, _ = parser.parse_known_args()

    if args.dev_reset:
            config = load_config()
            if not config:
                print("📯 No config found. Nothing to reset.")
                sys.exit(0)

            print("⚠️  WARNING: This will permanently wipe your job discovery history and campaign metrics.")
            confirm = input("Are you absolutely sure you want to proceed? [y/N]: ").strip().lower()

            if confirm not in ('y', 'yes'):
                print("Abort: Dev reset cancelled.")
                sys.exit(0)

            db_path_str = config.get("daemon", {}).get("statemachine_file")
            if db_path_str:
                db_path = Path(db_path_str)
                # Nuke both the base database and the Write-Ahead Log
                for p in [db_path, db_path.with_name(f"{db_path.name}.wal")]:
                    if p.exists():
                        p.unlink()
                        print(f"🧨 Dropped state file: {p}")

            print("✨ Dev reset complete. Backups were preserved. Ready for a fresh sweep.")
            sys.exit(0)

    daemon = load_daemon_from_disk()
    app = PosthornApp(daemon=daemon)
    app.run()


if __name__ == "__main__":
    main()
