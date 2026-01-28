"""Outputs tab: quality, publication, archive, artifacts."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    ListView,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
    Tree,
)


def compose_outputs_tab(app: object) -> ComposeResult:
    """Compose the Outputs tab with quality, publication, archive, artifacts sections."""
    with TabPane("Outputs (F4)", id="outputs"):
        with TabbedContent(id="outputs_sections"):
            # ─────────────────────────────────────────────────────────────
            # Quality Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Quality", id="outputs_quality"):
                with Vertical(id="quality_form"):
                    yield Static("QC Status", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Overall status:")
                        yield Select(
                            [
                                ("Pending", "pending"),
                                ("In Progress", "in-progress"),
                                ("Passed", "passed"),
                                ("Failed", "failed"),
                            ],
                            value=app._defaults.get("qc_status", "pending"),
                            id="qc_status",
                        )

                    yield Static("QC Checks (one per line: name | status | date | notes)")
                    yield TextArea(
                        app._defaults.get("qc_checks_text", ""),
                        id="qc_checks_text",
                    )
                    yield Static(
                        "Status: pending | passed | failed | skipped",
                        classes="form-hint",
                    )

                    yield Static("Review", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Reviewer:")
                        yield Input(
                            app._defaults.get("qc_reviewer", ""),
                            placeholder="Reviewer name",
                            id="qc_reviewer",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Review date:")
                        yield Input(
                            app._defaults.get("qc_review_date", ""),
                            placeholder="YYYY-MM-DD",
                            id="qc_review_date",
                        )

                    yield Static("QC Notes")
                    yield TextArea(
                        app._defaults.get("qc_notes", ""),
                        id="qc_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Publication Section (with Figure Tree)
            # ─────────────────────────────────────────────────────────────
            with TabPane("Publication", id="outputs_publication"):
                with Vertical(id="publication_form"):
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
                            value=app._defaults.get("pub_status", "none"),
                            id="pub_status",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Target journal:")
                        yield Input(
                            app._defaults.get("target_journal", ""),
                            placeholder="Journal name",
                            id="target_journal",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Manuscript:")
                        yield Input(
                            app._defaults.get("manuscript_path", ""),
                            placeholder="Path to manuscript file",
                            id="manuscript_path",
                        )

                    yield Static("Figures", classes="section-header")
                    yield Static(
                        "Tree: a=add, e=edit, d=delete, Enter=expand/collapse",
                        classes="form-hint",
                    )
                    yield Tree("Figures", id="figure_tree")

                    with Horizontal(classes="form-row"):
                        yield Button("Add Figure", id="fig_add_root", variant="success")
                        yield Button("Add Panel", id="fig_add_child", variant="primary")
                        yield Button("Add Element", id="fig_add_element", variant="primary")
                        yield Button("Edit", id="fig_edit", variant="default")
                        yield Button("Delete", id="fig_delete", variant="error")

                    yield Static("DOIs & Links", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Preprint DOI:")
                        yield Input(
                            app._defaults.get("preprint_doi", ""),
                            placeholder="e.g., 10.1101/...",
                            id="preprint_doi",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Published DOI:")
                        yield Input(
                            app._defaults.get("published_doi", ""),
                            placeholder="e.g., 10.1038/...",
                            id="published_doi",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("GitHub repo:")
                        yield Input(
                            app._defaults.get("github_repo", ""),
                            placeholder="Repository URL",
                            id="github_repo",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Zenodo DOI:")
                        yield Input(
                            app._defaults.get("zenodo_doi", ""),
                            placeholder="Data/code archive DOI",
                            id="zenodo_doi",
                        )

                    yield Static("Publication Notes")
                    yield TextArea(
                        app._defaults.get("pub_notes", ""),
                        id="pub_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Archive Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Archive", id="outputs_archive"):
                with Vertical(id="archive_form"):
                    yield Static("Archive Status", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Status:")
                        yield Select(
                            [
                                ("Active", "active"),
                                ("Pending Archive", "pending-archive"),
                                ("Archived", "archived"),
                            ],
                            value=app._defaults.get("archive_status", "active"),
                            id="archive_status",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Archive date:")
                        yield Input(
                            app._defaults.get("archive_date", ""),
                            placeholder="YYYY-MM-DD",
                            id="archive_date",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Location:")
                        yield Input(
                            app._defaults.get("archive_location", ""),
                            placeholder="Archive storage path",
                            id="archive_location",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Retention (years):")
                        yield Input(
                            app._defaults.get("retention_years", ""),
                            placeholder="Data retention period",
                            id="retention_years",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("")
                        yield Checkbox(
                            "Backup verified",
                            app._defaults.get("backup_verified", False),
                            id="backup_verified",
                        )

                    yield Static("Archive Notes")
                    yield TextArea(
                        app._defaults.get("archive_notes", ""),
                        id="archive_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Artifacts Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Artifacts", id="outputs_artifacts"):
                with Horizontal():
                    with Vertical():
                        yield Static("Artifacts Registry")
                        yield ListView(id="artifact_list")
                    with Vertical():
                        yield Static("Add Artifact", classes="section-header")
                        yield Input(placeholder="Artifact path", id="artifact_path")
                        yield Input(placeholder="Type (figure/table/dataset/model/report/script)", id="artifact_type")
                        yield Input(placeholder="Description", id="artifact_description")
                        yield Select(
                            [
                                ("Draft", "draft"),
                                ("Ready", "ready"),
                                ("Delivered", "delivered"),
                                ("Published", "published"),
                            ],
                            id="artifact_status",
                        )
                        yield Button("Add Artifact", id="artifact_add", variant="success")

                        yield Static("Update Selected", classes="section-header")
                        yield Select(
                            [
                                ("Draft", "draft"),
                                ("Ready", "ready"),
                                ("Delivered", "delivered"),
                                ("Published", "published"),
                            ],
                            id="artifact_update_status",
                        )
                        yield Button("Update Status", id="artifact_update", variant="primary")
