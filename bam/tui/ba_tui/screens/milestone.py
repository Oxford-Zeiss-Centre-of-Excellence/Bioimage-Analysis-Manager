from __future__ import annotations

from datetime import date

import pendulum
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Input, Label, Select, Static

from ..styles import MILESTONE_MODAL_CSS
from ..widgets import DateSelect
from .base import FormModal


class MilestoneModal(FormModal):
    """Modal to add or edit a milestone."""

    CSS = MILESTONE_MODAL_CSS

    STATUS_OPTIONS = [
        ("Pending", "pending"),
        ("In Progress", "in-progress"),
        ("Completed", "completed"),
        ("Delayed", "delayed"),
        ("Cancelled", "cancelled"),
    ]

    def __init__(
        self, initial_data: dict[str, object] | None = None, allow_remove: bool = False
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove

    def compose(self) -> ComposeResult:
        title = "Edit Milestone" if self.initial_data else "Add Milestone"
        target_value = self._coerce_date(self.initial_data.get("target_date"))
        actual_value = self._coerce_date(self.initial_data.get("actual_date"))

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("Name*:")
                    yield Input(
                        str(self.initial_data.get("name", "")),
                        id="milestone_name",
                        placeholder="Milestone name",
                    )

                yield Static("", id="milestone_datepicker_mount")

                with Horizontal(classes="form-row"):
                    yield Label("Target date:")
                    yield DateSelect(
                        "#milestone_datepicker_mount",
                        date=target_value,
                        id="milestone_target_date",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Actual date:")
                    yield DateSelect(
                        "#milestone_datepicker_mount",
                        date=actual_value,
                        id="milestone_actual_date",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Status:")
                    yield Select(
                        self.STATUS_OPTIONS,
                        value=str(self.initial_data.get("status", "pending")),
                        id="milestone_status",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notes:")
                    yield Input(
                        str(self.initial_data.get("notes", "")),
                        id="milestone_notes",
                        placeholder="Optional",
                    )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def _submit(self) -> None:
        name = self.query_one("#milestone_name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        target = self.query_one("#milestone_target_date", DateSelect).value
        actual = self.query_one("#milestone_actual_date", DateSelect).value
        if target:
            target = target.date()
        if actual:
            actual = actual.date()
        status_value = self.query_one("#milestone_status", Select).value
        status = str(status_value) if status_value else "pending"

        data = {
            "name": name,
            "target_date": target,
            "actual_date": actual,
            "status": status,
            "notes": self.query_one("#milestone_notes", Input).value.strip(),
        }
        self.dismiss(data)

    @staticmethod
    def _coerce_date(value: object) -> pendulum.DateTime | None:
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, date):
            return pendulum.datetime(value.year, value.month, value.day)
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                return parsed if isinstance(parsed, pendulum.DateTime) else None
            except Exception:
                return None
        return None
