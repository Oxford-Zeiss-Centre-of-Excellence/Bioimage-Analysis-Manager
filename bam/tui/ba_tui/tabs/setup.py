"""Setup tab: project, people, data, tags."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Input,
    Label,
    OptionList,
    ProgressBar,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)


def compose_setup_tab(app: object) -> ComposeResult:
    """Compose the Setup tab with project, people, data, tags sections."""
    with TabPane("Setup (F1)", id="setup"):
        with TabbedContent(id="setup_sections"):
            # ─────────────────────────────────────────────────────────────
            # Project Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Project", id="setup_project"):
                with Vertical(id="project_form"):
                    yield Static("Project Metadata", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Name*:")
                        yield Input(
                            app._defaults.get("project_name", ""),
                            placeholder="Enter project name (required)",
                            id="project_name",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Status:")
                        yield Select(
                            [
                                ("Active", "active"),
                                ("Completed", "completed"),
                                ("Archived", "archived"),
                                ("On-hold", "on-hold"),
                            ],
                            value=app._defaults.get("project_status", "active"),
                            id="project_status",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Tags:")
                        yield Input(
                            app._defaults.get("tags", ""),
                            placeholder="Comma-separated tags (e.g., microscopy, segmentation)",
                            id="project_tags",
                        )

            # ─────────────────────────────────────────────────────────────
            # People Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("People", id="setup_people"):
                with Vertical(id="people_form"):
                    yield Static("Team Members", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Analyst*:")
                        yield Input(
                            app._defaults.get("analyst", ""),
                            placeholder="Primary analyst name",
                            id="analyst",
                        )
                    yield Static(
                        "Collaborators (Ctrl+A: Add, Ctrl+D: Remove)",
                        classes="section-header",
                    )
                    yield DataTable(id="collaborators_table", cursor_type="row")

            # ─────────────────────────────────────────────────────────────
            # Data Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Data", id="setup_data"):
                with VerticalScroll(id="data_form"):
                    with Horizontal(classes="form-row"):
                        yield Label("")
                        yield Checkbox(
                            "Project Has Data",
                            app._defaults.get("data_enabled", False),
                            id="data_enabled",
                        )

                    with Vertical(id="data_sections"):
                        yield Static("Data Source", classes="section-header")
                        with Horizontal(classes="form-row"):
                            yield Label("Endpoint:")
                            yield Select(
                                app._load_endpoint_options(),
                                value=app._defaults.get("data_endpoint", "") or "Local",
                                id="data_endpoint",
                            )
                            yield Checkbox(
                                "Locally Mounted",
                                app._defaults.get("locally_mounted", False),
                                id="locally_mounted",
                            )

                        with Horizontal(classes="form-row"):
                            yield Label("Source Path:")
                            yield Input(
                                app._defaults.get("data_source", ""),
                                placeholder="Original data path",
                                id="data_source",
                            )
                            yield Button(
                                "Browse", id="browse_source", variant="primary"
                            )

                        yield OptionList(id="path_suggestions")

                        yield Static("Local Cache", classes="section-header")
                        with Horizontal(classes="form-row"):
                            yield Label("Cache Path:")
                            yield Input(
                                app._defaults.get("data_local", ""),
                                placeholder="Local cache path",
                                id="data_local",
                            )
                            yield Button("Browse", id="browse_local", variant="primary")

                        with Horizontal(id="sync_row"):
                            yield Button(
                                "Sync Source > Cache", id="sync_btn", variant="default"
                            )
                            yield ProgressBar(
                                total=100, show_eta=False, id="sync_progress"
                            )
                        yield Static("", id="sync_pct")

                        yield Static("Data Description", classes="section-header")
                        with Horizontal(classes="form-row"):
                            yield Label("Description:")
                            yield Input(
                                app._defaults.get("data_description", ""),
                                placeholder="What the data contains",
                                id="data_description",
                            )
                        with Horizontal(classes="form-row"):
                            yield Label("Format:")
                            yield Select(
                                [
                                    ("TIFF", "tiff"),
                                    ("Zarr", "zarr"),
                                    ("HDF5", "hdf5"),
                                    ("ND2", "nd2"),
                                    ("CZI", "czi"),
                                    ("OME-TIFF", "ome-tiff"),
                                    ("Other", "other"),
                                ],
                                value=app._defaults.get("data_format", Select.BLANK),
                                allow_blank=True,
                                id="data_format",
                            )
                        with Horizontal(classes="form-row"):
                            yield Label("Raw Size:")
                            yield Input(
                                app._defaults.get("data_size_gb", ""),
                                placeholder="Approximate raw data size",
                                id="data_size_gb",
                            )
                            yield Select(
                                [("GB", "gb"), ("TB", "tb")],
                                value=app._defaults.get("data_size_unit", "gb"),
                                id="data_size_unit",
                            )

                        with Horizontal(classes="form-row"):
                            yield Label("Compression:")
                            yield Checkbox(
                                "Yes",
                                app._defaults.get("data_compressed", False),
                                id="data_compressed",
                            )

                        with Horizontal(
                            classes="form-row"
                            + (
                                ""
                                if app._defaults.get("data_compressed", False)
                                else " hidden"
                            ),
                            id="data_uncompressed_row",
                        ):
                            yield Label("Uncompressed Size:")
                            yield Input(
                                app._defaults.get("data_uncompressed_size_gb", ""),
                                placeholder="Uncompressed size",
                                id="data_uncompressed_size_gb",
                            )
                            yield Select(
                                [("GB", "gb"), ("TB", "tb")],
                                value=app._defaults.get(
                                    "data_uncompressed_size_unit", "gb"
                                ),
                                id="data_uncompressed_size_unit",
                            )

        app._init_error = Static("", id="init_error")
        yield app._init_error
