"""Outputs tab: publication, archive, artifacts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Input,
    Label,
    OptionList,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
    Tree,
)

from ..config import load_endpoint_options
from ..widgets import DateSelect


def compose_outputs_tab(app) -> ComposeResult:
    """Compose the Outputs tab with publication, archive, artifacts sections."""
    with TabPane("Outputs (F4)", id="outputs"):
        with TabbedContent(id="outputs_sections"):
            # ─────────────────────────────────────────────────────────────
            # Publication Section (with Figure Tree)
            # ─────────────────────────────────────────────────────────────
            with TabPane("Publication", id="outputs_publication"):
                with VerticalScroll(id="publication_form"):
                    yield Static("Publication Status", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Status:")
                        yield Select(
                            [
                                ("None", "none"),
                                ("In Preparation", "in-prep"),
                                ("Submitted", "submitted"),
                                ("Revision", "revision"),
                                ("Accepted", "accepted"),
                                ("Published", "published"),
                            ],
                            value=str(app._defaults.get("pub_status", "none")),
                            id="pub_status",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Target journal:")
                        yield Input(
                            str(app._defaults.get("target_journal", "")),
                            placeholder="Journal name",
                            id="target_journal",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Manuscript:")
                        yield Input(
                            str(app._defaults.get("manuscript_path", "")),
                            placeholder="Path to manuscript file",
                            id="manuscript_path",
                        )

                    yield Static("Figures", classes="section-header")
                    yield Tree("Figures", id="figure_tree")

                    with Horizontal(classes="form-row"):
                        yield Button(
                            "Add Figure (A)", id="fig_add_root", variant="success"
                        )
                        yield Button(
                            "Add Panel (P)", id="fig_add_child", variant="primary"
                        )
                        yield Button(
                            "Add Element (E)", id="fig_add_element", variant="primary"
                        )
                        yield Button("Edit (R)", id="fig_edit", variant="default")
                        yield Button("Delete (D)", id="fig_delete", variant="error")

                    yield Static("DOIs & Links", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Preprint DOI:")
                        yield Input(
                            str(app._defaults.get("preprint_doi", "")),
                            placeholder="e.g., 10.1101/...",
                            id="preprint_doi",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Published DOI:")
                        yield Input(
                            str(app._defaults.get("published_doi", "")),
                            placeholder="e.g., 10.1038/...",
                            id="published_doi",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("GitHub repo:")
                        yield Input(
                            str(app._defaults.get("github_repo", "")),
                            placeholder="Repository URL",
                            id="github_repo",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Zenodo DOI:")
                        yield Input(
                            str(app._defaults.get("zenodo_doi", "")),
                            placeholder="Data/code archive DOI",
                            id="zenodo_doi",
                        )

                    yield Static("Publication Notes")
                    yield TextArea(
                        str(app._defaults.get("pub_notes", "")),
                        id="pub_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Archive Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Archive", id="outputs_archive"):
                with VerticalScroll(id="archive_form"):
                    yield Static("Archive Status", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Status:")
                        yield Select(
                            [
                                ("Active", "active"),
                                ("Pending Archive", "pending-archive"),
                                ("Archived", "archived"),
                            ],
                            value=str(app._defaults.get("archive_status", "active")),
                            id="archive_status",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Archive date:")
                        yield DateSelect(
                            "#archive_datepicker_mount",
                            date=app._coerce_date(
                                app._defaults.get("archive_date", "")
                            ),
                            id="archive_date",
                        )
                    yield Static("", id="archive_datepicker_mount")
                    endpoint_options = load_endpoint_options()
                    endpoint_values = {value for _, value in endpoint_options}
                    initial_endpoint = str(
                        app._defaults.get("archive_endpoint", "")
                    ).strip()
                    endpoint_value = Select.BLANK
                    endpoint_custom = ""
                    show_endpoint_custom = False
                    if initial_endpoint:
                        if initial_endpoint in endpoint_values:
                            endpoint_value = initial_endpoint
                            show_endpoint_custom = initial_endpoint.lower() == "other"
                        else:
                            endpoint_value = (
                                "Other" if "Other" in endpoint_values else Select.BLANK
                            )
                            endpoint_custom = initial_endpoint
                            show_endpoint_custom = True
                    is_local_endpoint = str(endpoint_value).lower() == "local"
                    with Horizontal(classes="form-row"):
                        yield Label("Endpoint:")
                        yield Select(
                            endpoint_options,
                            value=endpoint_value,
                            allow_blank=True,
                            id="archive_endpoint",
                        )
                        yield Checkbox(
                            "Locally mounted",
                            is_local_endpoint,
                            id="archive_locally_mounted",
                            disabled=is_local_endpoint,
                        )
                    with Horizontal(
                        id="archive_endpoint_custom_row",
                        classes="form-row"
                        + ("" if show_endpoint_custom else " hidden"),
                    ):
                        yield Label("Custom endpoint:")
                        yield Input(
                            endpoint_custom
                            or str(app._defaults.get("archive_endpoint_custom", "")),
                            id="archive_endpoint_custom",
                            placeholder="Enter endpoint",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Location:")
                        yield Input(
                            str(app._defaults.get("archive_location", "")),
                            placeholder="Archive storage path",
                            id="archive_location",
                        )
                        yield Button(
                            "Browse",
                            id="archive_browse",
                            variant="primary",
                            disabled=not is_local_endpoint,
                        )
                    yield OptionList(id="archive_location_suggestions")
                    with Horizontal(classes="form-row"):
                        yield Label("Retention (years):")
                        yield Input(
                            str(app._defaults.get("retention_years", "")),
                            placeholder="Data retention period",
                            id="retention_years",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("")
                        yield Checkbox(
                            "Backup verified",
                            bool(app._defaults.get("backup_verified", False)),
                            id="backup_verified",
                        )

                    yield Static("Archive Notes")
                    yield TextArea(
                        str(app._defaults.get("archive_notes", "")),
                        id="archive_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Artifacts Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Artifacts", id="outputs_artifacts"):
                with VerticalScroll():
                    yield Static(
                        "Artifacts",
                        classes="section-header",
                    )
                    with Center():
                        yield DataTable(id="artifacts_table", cursor_type="row")
                    with Horizontal(id="artifact_actions"):
                        yield Button("Add (A)", id="artifact_add", variant="success")
                        yield Button(
                            "Edit (Enter)", id="artifact_edit", variant="default"
                        )
                        yield Button(
                            "Remove (D)",
                            id="artifact_remove",
                            variant="error",
                        )
