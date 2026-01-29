"""Admin tab: billing, timeline."""

from __future__ import annotations

from datetime import date

import pendulum

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, VerticalScroll
from textual.widgets import (
    DataTable,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
    Button,
)

from ..widgets import DateSelect


def _coerce_date(value: object) -> pendulum.DateTime | None:
    if isinstance(value, date):
        return pendulum.datetime(value.year, value.month, value.day)
    if isinstance(value, str) and value:
        try:
            return pendulum.parse(value)
        except (ValueError, pendulum.parsing.exceptions.ParserError):
            return None
    return None


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
                    with Horizontal(id="billing_dates_row"):
                        with Horizontal(classes="form-row"):
                            yield Label("Start date:")
                            yield DateSelect(
                                "#billing_datepicker_mount",
                                date=_coerce_date(
                                    app._defaults.get("billing_start_date", "")
                                ),
                                id="billing_start_date",
                            )
                        with Horizontal(classes="form-row"):
                            yield Label("End date:")
                            yield DateSelect(
                                "#billing_datepicker_mount",
                                date=_coerce_date(
                                    app._defaults.get("billing_end_date", "")
                                ),
                                id="billing_end_date",
                            )
                    yield Static("", id="billing_datepicker_mount")

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
                        "Milestones (Ctrl+A: Add, Enter: Edit, Ctrl+D: Remove)",
                        classes="section-header",
                    )
                    with Center():
                        yield DataTable(id="milestones_table", cursor_type="row")
                    with Horizontal(id="milestone_actions"):
                        yield Button(
                            "Add Milestone",
                            id="add_milestone",
                            variant="success",
                        )
                        yield Button(
                            "Remove",
                            id="remove_milestone",
                            variant="error",
                        )
