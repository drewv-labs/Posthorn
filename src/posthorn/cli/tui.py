from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static


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
            ansi_art = "[ icon.ans not found in cli directory ]"

        with Middle(), Center():
            yield Static(ansi_art, id="splash-icon")
            yield Label("Mounting DuckDB idempotency lock...", id="splash-status")

    def on_mount(self) -> None:
        self.set_timer(2.5, self.dismiss_splash)

    def dismiss_splash(self) -> None:
        self.app.pop_screen()


class PosthornApp(App):
    """The main TUI for the Posthorn daemon."""

    CSS = """
    #splash-icon {
        content-align: center middle;
    }
    #splash-status {
        content-align: center middle;
        color: #f1c40f; /* Duck Yellow */
        margin-top: 2;
    }
    .main-container {
        padding: 1 2;
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit Daemon"),
        ("s", "toggle_sweep", "Force Sweep"),
    ]

    def on_mount(self) -> None:
        self.push_screen(SplashScreen())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="main-container"):
            yield Static("📯 Posthorn Daemon is idling.", id="daemon-status")
        yield Footer()


def main() -> None:
    app = PosthornApp()
    app.run()


if __name__ == "__main__":
    main()
