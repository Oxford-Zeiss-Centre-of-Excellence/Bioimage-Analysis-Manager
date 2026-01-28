from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    OptionList,
    ProgressBar,
    Select,
    Static,
    TabPane,
)


def compose_init_tab(app: object) -> ComposeResult:
    with TabPane("Init (F1)", id="init"):
        with VerticalScroll(id="form"):
            yield Static("Project initialization")
            # Project name row
            with Horizontal(classes="form-row"):
                yield Label("Project Name*:")
                yield Input(
                    app._defaults["project_name"],
                    placeholder="Enter project name",
                    id="project_name",
                )
            # Analyst row
            with Horizontal(classes="form-row"):
                yield Label("Analyst*:")
                yield Input(
                    app._defaults["analyst"],
                    placeholder="Enter analyst name",
                    id="analyst",
                )

            # Data enabled checkbox
            with Horizontal(classes="form-row"):
                yield Label("")
                yield Checkbox(
                    "Has Data", app._defaults["data_enabled"], id="data_enabled"
                )

            # Data sections container (shown/hidden based on data_enabled)
            with Vertical(id="data_sections"):
                # Data Source section
                yield Static("─── Data Source ───", classes="section-header")
                # Endpoint row with locally mounted checkbox
                with Horizontal(classes="form-row"):
                    yield Label("Endpoint:")
                    yield Select(
                        app._load_endpoint_options(),
                        value=app._defaults["data_endpoint"] or "Local",
                        id="data_endpoint",
                    )
                    yield Checkbox(
                        "Locally Mounted",
                        app._defaults["locally_mounted"],
                        id="locally_mounted",
                    )
                # Source path row with browse
                with Horizontal(classes="form-row"):
                    yield Label("Source Path:")
                    yield Input(
                        app._defaults["data_source"],
                        placeholder="Enter source path",
                        id="data_source",
                    )
                    yield Button("Browse", id="browse_source", variant="primary")
                # Path suggestions dropdown
                yield OptionList(id="path_suggestions")

                # Local Cache section
                yield Static("─── Local Cache ───", classes="section-header")
                # Cache path row with browse
                with Horizontal(classes="form-row"):
                    yield Label("Cache Path:")
                    yield Input(
                        app._defaults["data_local"],
                        placeholder="Enter cache path",
                        id="data_local",
                    )
                    yield Button("Browse", id="browse_local", variant="primary")

                # Sync row with progress bar
                with Horizontal(id="sync_row"):
                    yield Button(
                        "Sync Source > Cache", id="sync_btn", variant="default"
                    )
                    yield ProgressBar(total=100, show_eta=False, id="sync_progress")
                yield Static("", id="sync_pct")

            app._init_error = Static("", id="init_error")
            yield app._init_error
