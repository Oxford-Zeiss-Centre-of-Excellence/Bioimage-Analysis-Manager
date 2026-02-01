"""Setup tab: project, people, data, tags."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Input,
    Label,
    ProgressBar,
    Select,
    Static,
    TabbedContent,
    TabPane,
)


def compose_setup_tab(app: object) -> ComposeResult:
    """Compose the Setup tab with project, people, data, tags sections."""
    with TabPane("Setup (F1)", id="setup"):
        with TabbedContent(id="setup_sections"):
            # ─────────────────────────────────────────────────────────────
            # Project Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Project", id="setup_project"):
                with VerticalScroll(id="project_form"):
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
                with VerticalScroll(id="people_form"):
                    yield Static("Team Members", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Analyst*:")
                        yield Input(
                            app._defaults.get("analyst", ""),
                            placeholder="Primary analyst name",
                            id="analyst",
                        )

                    yield Static(
                        "Collaborators",
                        classes="section-header",
                    )
                    with Center():
                        yield DataTable(id="collaborators_table", cursor_type="row")
                    with Horizontal(id="collaborator_actions"):
                        yield Button(
                            "Add (A)",
                            id="add_collaborator",
                            variant="success",
                        )
                        yield Button(
                            "Edit (Enter)",
                            id="edit_collaborator",
                            variant="default",
                        )
                        yield Button(
                            "Remove (D)",
                            id="remove_collaborator",
                            variant="error",
                        )

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
                        yield Static(
                            "Datasets",
                            classes="section-header",
                        )
                        with Center():
                            yield DataTable(id="datasets_table", cursor_type="row")
                        with Horizontal(id="dataset_actions"):
                            yield Button(
                                "Add (A)",
                                id="add_dataset",
                                variant="success",
                            )
                            yield Button(
                                "Edit (Enter)",
                                id="edit_dataset",
                                variant="default",
                            )
                            yield Button(
                                "Remove (D)",
                                id="remove_dataset",
                                variant="error",
                            )
                            yield Button(
                                "Sync (Ctrl+V)",
                                id="sync_dataset",
                                variant="primary",
                            )
                        with Horizontal(id="dataset_sync_row"):
                            yield ProgressBar(
                                total=100, show_eta=False, id="sync_progress"
                            )
                            yield Static("", id="sync_pct")

        app._init_error = Static("", id="init_error")
        yield app._init_error
