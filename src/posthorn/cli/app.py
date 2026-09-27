from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Label, RichLog

from ..core import PosthornDaemon
from .config import generate_default_config, load_config
from .screens import CampaignScreen, SetupScreen, SplashScreen


class CampaignStatBlock(Vertical):
    """A dynamically mounted widget for individual campaign metrics."""

    def __init__(self, name: str, discovered: int, sent: int, dupes: int, **kwargs):
        super().__init__(**kwargs)
        self.campaign_name = name
        self.discovered = discovered
        self.sent = sent
        self.dupes = dupes

    def compose(self) -> ComposeResult:
        yield Label(f"🎯 {self.campaign_name}", classes="campaign-name")
        yield Label(f"Discovered: {self.discovered}", classes="stat-item")
        yield Label(f"Alerts Sent: {self.sent}", classes="stat-item")
        yield Label(f"Duplicates: {self.dupes}", classes="stat-item")


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

    #metrics-container {
        height: 1fr;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }

    CampaignStatBlock {
        height: auto;
        margin-bottom: 1;
        padding-bottom: 1;
        border-bottom: dashed #444444;
    }

    CampaignStatBlock:last-of-type {
        border-bottom: none;
    }

    .campaign-name {
        color: #3498db; /* Posthorn Blue */
        text-style: bold;
    }
    .stat-value {
        color: #f1c40f; /* Duck Yellow */
        margin-bottom: 3; /* Increased from 1 to push the CAMPAIGN METRICS section down */
    }

    /* Right Panel Log */
    #log-panel { column-span: 2; }
    #event-log { height: 100%; }
    """

    BINDINGS = [
        ("q", "quit", "Quit Daemon"),
        ("s", "toggle_sweep", "Force Sweep"),
        ("c", "manage_campaigns", "Manage Campaigns"), # New hotkey
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

    def action_manage_campaigns(self) -> None:
            """Pops the campaign manager screen."""
            self.push_screen(CampaignScreen(), self.handle_campaigns_closed)

    async def handle_campaigns_closed(self, config_changed: bool | None) -> None:
        """Fires when the CampaignScreen is dismissed."""
        if config_changed:
            log = self.query_one("#event-log", RichLog)
            log.write("[bold #f1c40f]Reloading daemon configuration...[/]")

            # 1. Safely close the old DuckDB connection to release the file lock
            if self.daemon:
                await self.daemon.state_db.disconnect()

            # 2. Hot-swap the engine
            raw_config = load_config()
            if raw_config is None:
                raise RuntimeError(
                    "Failed to load config after CampaignScreen closed. "
                    "Check disk permissions for ~/.posthorn/"
                )
            self.daemon = PosthornDaemon.from_config(raw_config)

            # 3. Boot the new state machine connection BEFORE querying metrics
            await self.daemon.state_db.connect()

            # 4. Repopulate the DuckDB side-panel metrics
            await self.update_metrics()

            log.write("[bold #2ecc71]Daemon hot-swapped successfully.[/]")

    async def update_metrics(self) -> None:
        """Pulls metrics from DuckDB and rebuilds the side panel."""
        if not self.daemon or not self.daemon.campaigns:
            return

        container = self.query_one("#metrics-container", VerticalScroll)

        # Suspend updates to the DOM to prevent visual flickering
        with container.app.batch_update():
            # Wipe the old metric blocks
            await container.query("*").remove()

            # Query DuckDB and mount fresh blocks for every campaign
            for campaign in self.daemon.campaigns:
                metrics = await self.daemon.state_db.get_campaign_metrics(campaign.name)

                disc = metrics.get("total_discovered", 0)
                sent = metrics.get("novel_alerts_sent", 0)
                supp = metrics.get("duplicates_suppressed", 0)

                await container.mount(
                    CampaignStatBlock(campaign.name, disc, sent, supp)
                    )

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
            # Left Column: State & Dynamic Metrics
            with Vertical(id="stats-panel", classes="panel"):
                yield Label("DAEMON STATE", classes="panel-title")
                yield Label("IDLING", id="status-indicator", classes="stat-value")

                yield Label("CAMPAIGN METRICS", classes="panel-title")
                # This container will dynamically hold the CampaignStatBlocks
                yield VerticalScroll(id="metrics-container")

            # Right Column: Live Event Log
            with Vertical(id="log-panel", classes="panel"):
                yield Label("LIVE EVENT STREAM", classes="panel-title")
                yield RichLog(id="event-log", highlight=True, markup=True)

        yield Footer()
