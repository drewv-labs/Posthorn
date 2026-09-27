from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Label

from ..config import load_config, save_config


class CampaignScreen(Screen):
    """Manage active job search campaigns dynamically."""

    CSS = """
    #campaign-grid {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 2fr 1fr;
        height: 100%;
        padding: 1 2;
    }
    .panel {
        border: solid #333333;
        background: $surface;
        padding: 1;
        height: 100%;
    }
    .panel-title {
        text-style: bold;
        color: #f1c40f; /* Duck Yellow */
        margin-bottom: 1;
        border-bottom: solid #444444;
    }
    Input { margin-bottom: 1; }
    Button { margin-top: 1; width: 100%; }
    #btn-delete { background: $error; margin-top: 1; }
    """

    BINDINGS = [("escape", "close_manager", "Back to Dashboard")]

    def compose(self) -> ComposeResult:
        with Horizontal(id="campaign-grid"):
            # Left Panel: The Data Table
            with Vertical(classes="panel"):
                yield Label("ACTIVE CAMPAIGNS", classes="panel-title")
                yield DataTable(id="campaign-table", cursor_type="row")
                yield Button("Delete Selected Campaign", id="btn-delete", variant="error")

            # Right Panel: The Add Form
            with Vertical(classes="panel"):
                yield Label("ADD NEW CAMPAIGN", classes="panel-title")
                yield Label("Campaign Name")
                yield Input(placeholder="e.g. Python Backend", id="inp-name")

                yield Label("Keywords (comma separated)")
                yield Input(placeholder="e.g. Python, Django, FastAPI", id="inp-keywords")

                yield Label("Locations (comma separated)")
                yield Input(placeholder="e.g. Remote, Texas", id="inp-locations")

                yield Button("Save Campaign", id="btn-save", variant="primary")

    def on_mount(self) -> None:
        self.raw_config = load_config() or {}
        table = self.query_one(DataTable)
        table.add_columns("Name", "Keywords", "Locations")
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        campaigns = self.raw_config.get("campaigns", [])
        for c in campaigns:
            # Join lists into readable strings for the UI
            kws = ", ".join(c.get("keywords", []))
            locs = ", ".join(c.get("locations", []))
            table.add_row(c.get("name"), kws, locs)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            name = self.query_one("#inp-name", Input).value.strip()
            # Split by comma and strip whitespace
            kws = [k.strip() for k in self.query_one("#inp-keywords", Input).value.split(",") if k.strip()]
            locs = [loc.strip() for loc in self.query_one("#inp-locations", Input).value.split(",") if loc.strip()]

            if name and kws:
                campaigns = self.raw_config.setdefault("campaigns", [])
                campaigns.append({"name": name, "keywords": kws, "locations": locs})

                save_config(self.raw_config)
                self.refresh_table()

                # Clear form
                for inp in ["#inp-name", "#inp-keywords", "#inp-locations"]:
                    self.query_one(inp, Input).value = ""

        elif event.button.id == "btn-delete":
            table = self.query_one(DataTable)
            try:
                row_idx = table.cursor_row
                campaigns = self.raw_config.get("campaigns", [])
                if 0 <= row_idx < len(campaigns):
                    campaigns.pop(row_idx)
                    save_config(self.raw_config)
                    self.refresh_table()
            except Exception:
                pass # Triggered if they click delete while table is empty

    def action_close_manager(self) -> None:
        """Dismiss the screen and pass True to tell the app to reload."""
        self.dismiss(True)
