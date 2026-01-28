"""Admin tab: billing, timeline."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)


def compose_admin_tab(app: object) -> ComposeResult:
    """Compose the Admin tab with billing and timeline sections."""
    with TabPane("Admin (F3)", id="admin"):
        with TabbedContent(id="admin_sections"):
            # ─────────────────────────────────────────────────────────────
            # Billing Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Billing", id="admin_billing"):
                with VerticalScroll(id="billing_form"):
                    yield Static("Funding", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Fund code:")
                        yield Input(
                            app._defaults.get("fund_code", ""),
                            placeholder="Institutional fund/grant code",
                            id="fund_code",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Hourly rate:")
                        yield Input(
                            app._defaults.get("hourly_rate", ""),
                            placeholder="If applicable",
                            id="hourly_rate",
                        )

                    yield Static("Hours", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Budget hours:")
                        yield Input(
                            app._defaults.get("budget_hours", ""),
                            placeholder="Allocated hours",
                            id="budget_hours",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Spent hours:")
                        yield Input(
                            app._defaults.get("spent_hours", ""),
                            placeholder="Auto-calculated from worklog",
                            id="spent_hours",
                            disabled=True,
                        )

                    yield Static("Project Dates", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Start date:")
                        yield Input(
                            app._defaults.get("billing_start_date", ""),
                            placeholder="YYYY-MM-DD",
                            id="billing_start_date",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("End date:")
                        yield Input(
                            app._defaults.get("billing_end_date", ""),
                            placeholder="YYYY-MM-DD",
                            id="billing_end_date",
                        )

                    yield Static("Notes")
                    yield TextArea(
                        app._defaults.get("billing_notes", ""),
                        id="billing_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Timeline Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Timeline", id="admin_timeline"):
                with VerticalScroll(id="timeline_form"):
                    yield Static(
                        "Milestones (one per line: name | target_date | actual_date | status)"
                    )
                    yield TextArea(
                        app._defaults.get("milestones_text", ""),
                        id="milestones_text",
                    )
                    yield Static(
                        "Status: pending | in-progress | completed | delayed",
                        classes="form-hint",
                    )
                    yield Static(
                        "Example: Data acquisition | 2024-03-01 | 2024-03-05 | completed",
                        classes="form-hint",
                    )

                    yield Static("Timeline Notes")
                    yield TextArea(
                        app._defaults.get("timeline_notes", ""),
                        id="timeline_notes",
                    )
