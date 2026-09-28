from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widgets import Label, Static


class SplashScreen(Screen):
    """Temporary boot screen to mask state database initialization."""

    def compose(self) -> ComposeResult:
        # Dynamically load the .ans file
        ansi_path = Path(__file__).parent / "icon_dark_transparent.ans"

        if ansi_path.exists():
            with open(ansi_path, encoding="utf-8") as f:
                # Translates the terminal codes to Textual colors natively
                ansi_art = Text.from_ansi(f.read())
        else:
            ansi_art = "[ icon_dark_transparent.ans not found in cli directory ]"

        with Middle(), Center():
                yield Static(ansi_art, id="splash-icon")
                yield Label("Mounting DuckDB idempotency lock...", id="splash-status")

    def on_mount(self) -> None:
        self.set_timer(2.5, self.dismiss_splash)

    def dismiss_splash(self) -> None:
        self.app.pop_screen()
