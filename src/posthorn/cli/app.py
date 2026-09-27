from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, RichLog

from ..core import PosthornDaemon
from .config import generate_default_config, load_config
from .screens import SetupScreen, SplashScreen


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

    /* Dashboard Layout */
    #dashboard-grid {
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 2fr; /* Left column 1 part, Right column 2 parts */
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
        color: #888888;
        margin-bottom: 1;
        border-bottom: solid #444444;
    }

    /* Left Panel Metrics */
    #stats-panel { column-span: 1; }

    .stat-label {
        color: #3498db; /* Posthorn Blue */
        text-style: bold;
    }
    .stat-value {
        color: #f1c40f; /* Duck Yellow */
        margin-bottom: 1;
    }

    /* Right Panel Log */
    #log-panel { column-span: 2; }
    #event-log { height: 100%; }
    """

    BINDINGS = [
        ("q", "quit", "Quit Daemon"),
        ("s", "toggle_sweep", "Force Sweep"),
    ]

    def __init__(self, daemon: PosthornDaemon | None = None, **kwargs):
        super().__init__(**kwargs)
        self.daemon = daemon
        self.auto_sweep_interval = 900

    async def on_ready(self) -> None:
        """Fires when the UI is fully loaded."""
        log = self.query_one("#event-log", RichLog)
        log.write("[bold #3498db]📯 Posthorn Orchestrator v1.0[/]")
        log.write("[#888888]System initialized. Awaiting next sweep cycle...[/]")

        if self.daemon:
            # MOVED the initialization here where the DOM is guaranteed ready
            self.run_worker(self.initialize_metrics_and_loop())

    @work(exclusive=True)
    async def action_toggle_sweep(self) -> None:
        """Triggered automatically by the interval, or manually by the 's' hotkey."""
        log = self.query_one("#event-log", RichLog)
        status = self.query_one("#status-indicator", Label)

        if not self.daemon:
            log.write("[bold red]Error:[/] No daemon configured. Running in UI-only mode.")
            return

        status.update("SWEEPING")
        log.write("\n[bold #f1c40f]Initiating job board sweep...[/]")

        try:
            # 1. Execute the core business logic
            await self.daemon.sweep()

            # 2. Update the UI with fresh DuckDB metrics
            await self.update_metrics()

            log.write("[bold #2ecc71]Sweep complete.[/] Sleeping...")
        except Exception as e:
            log.write(f"[bold red]Sweep failed:[/] {e}")
        finally:
            status.update("IDLING")

    async def update_metrics(self) -> None:
        """Pulls aggregated metrics from DuckDB and updates the side panel."""
        if not self.daemon or not self.daemon.campaigns:
            return

        total_disc = total_sent = total_supp = 0

        # Aggregate metrics across all configured campaigns
        for campaign in self.daemon.campaigns:
            metrics = await self.daemon.state_db.get_campaign_metrics(campaign.name)
            total_disc += metrics.get("total_discovered", 0)
            total_sent += metrics.get("novel_alerts_sent", 0)
            total_supp += metrics.get("duplicates_suppressed", 0)

        # Push to the UI widgets
        self.query_one("#stat-discovered", Label).update(str(total_disc))
        self.query_one("#stat-sent", Label).update(str(total_sent))
        self.query_one("#stat-dupes", Label).update(str(total_supp))

    def on_mount(self) -> None:
        """Route to setup wizard if no config exists, otherwise boot normally."""
        if not self.daemon:
            self.push_screen(SetupScreen(), self.handle_setup_complete)
        else:
            self.push_screen(SplashScreen())

    def handle_setup_complete(self, setup_data: tuple[str, str] | None) -> None:
        """Fires when SetupScreen is dismissed with data."""
        if not setup_data:
            self.exit() # User quit the setup wizard
            return

        webhook_url, job_title = setup_data

        # 1. Write the TOML file
        generate_default_config(webhook_url, job_title)

        # 2. Reload and build the daemon dynamically
        raw_config = load_config()
        if raw_config is None:
            raise RuntimeError(
                "Failed to load config immediately after generation. "
                "Check disk permissions for ~/.posthorn/"
            )
        self.daemon = PosthornDaemon.from_config(raw_config)

        # 3. Transition to the splash screen and start the engine
        self.push_screen(SplashScreen())
        self.run_worker(self.initialize_metrics_and_loop())

    async def initialize_metrics_and_loop(self) -> None:
        """Connects DuckDB and starts the background loop."""
        if self.daemon:
            await self.daemon.state_db.connect()
            await self.update_metrics()
            self.set_interval(self.auto_sweep_interval, self.action_toggle_sweep)

    def compose(self) -> ComposeResult:
        """Lays out the main dashboard."""
        yield Header(show_clock=True)

        with Horizontal(id="dashboard-grid"):
            # Left Column: State & Metrics
            with Vertical(id="stats-panel", classes="panel"):
                yield Label("DAEMON STATE", classes="panel-title")
                yield Label("IDLING", id="status-indicator", classes="stat-value")

                yield Label("CAMPAIGN METRICS", classes="panel-title")
                yield Label("Discovered Jobs", classes="stat-label")
                yield Label("0", id="stat-discovered", classes="stat-value")

                yield Label("Alerts Sent", classes="stat-label")
                yield Label("0", id="stat-sent", classes="stat-value")

                yield Label("Duplicates Suppressed", classes="stat-label")
                yield Label("0", id="stat-dupes", classes="stat-value")

            # Right Column: Live Event Log
            with Vertical(id="log-panel", classes="panel"):
                yield Label("LIVE EVENT STREAM", classes="panel-title")
                # RichLog automatically handles scrolling and text formatting
                yield RichLog(id="event-log", highlight=True, markup=True)

        yield Footer()
