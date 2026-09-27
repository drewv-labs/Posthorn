from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label


class SetupScreen(Screen):
    """First-time setup wizard for non-technical users."""

    CSS = """
    #setup-container {
        width: 60;
        height: auto;
        padding: 2 4;
        border: solid #3498db;
        background: $surface;
    }
    .setup-title {
        text-style: bold;
        content-align: center middle;
        margin-bottom: 2;
        color: #f1c40f;
    }
    .setup-label {
        margin-top: 1;
        color: #888888;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        margin-top: 2;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Middle(), Center(), Vertical(id="setup-container"):
            yield Label("📯 Posthorn Initial Setup", classes="setup-title")

            yield Label("Discord Webhook URL", classes="setup-label")
            yield Input(placeholder="https://discord.com/api/webhooks/...", id="input-webhook")

            yield Label("Target Job Title (e.g. Data Engineer)", classes="setup-label")
            yield Input(placeholder="Job Title", id="input-title")

            yield Button("Save & Start Daemon", variant="primary", id="btn-save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Triggered when the user hits 'Save & Start Daemon'."""
        if event.button.id == "btn-save":
            webhook = self.query_one("#input-webhook", Input).value.strip()
            title = self.query_one("#input-title", Input).value.strip()

            if webhook and title:
                # Dismiss the screen and pass the tuple back to PosthornApp
                self.dismiss((webhook, title))
