"""Session editing modal for worklog."""

from __future__ import annotations

from datetime import datetime, date

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Static, TextArea

from ..styles import EDIT_SESSION_MODAL_CSS
from ..widgets import DateSelect
from .base import FormModal


class EditSessionModal(FormModal):
    """Modal to edit a work session's times and note."""

    CSS = EDIT_SESSION_MODAL_CSS

    def __init__(
        self,
        task_name: str,
        initial_punch_in: datetime | None = None,
        initial_punch_out: datetime | None = None,
        initial_note: str | None = None,
    ) -> None:
        super().__init__()
        self.task_name = task_name
        self.initial_punch_in = initial_punch_in
        self.initial_punch_out = initial_punch_out
        self.initial_note = initial_note or ""

    def compose(self) -> ComposeResult:
        # Format datetimes for input
        punch_in_date_val = (
            self.initial_punch_in.date() if self.initial_punch_in else date.today()
        )
        punch_in_time = (
            self.initial_punch_in.strftime("%H:%M") if self.initial_punch_in else ""
        )
        punch_out_date_val = (
            self.initial_punch_out.date() if self.initial_punch_out else None
        )
        punch_out_time = (
            self.initial_punch_out.strftime("%H:%M") if self.initial_punch_out else ""
        )

        with Vertical(id="dialog"):
            yield Static("Edit Session", classes="header")
            with VerticalScroll(id="dialog_scroll"):
                # Task name (read-only)
                with Horizontal(classes="form-row"):
                    yield Label("Task:")
                    yield Static(self.task_name, id="task_name_display")

                # Datepicker mount points
                yield Static("", id="punch_in_datepicker_mount")
                yield Static("", id="punch_out_datepicker_mount")

                # Check In
                yield Label("Check In*:", classes="section-label")
                with Horizontal(classes="form-row"):
                    yield Label("Date:")
                    yield DateSelect(
                        "#punch_in_datepicker_mount",
                        date=punch_in_date_val,
                        id="punch_in_date",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Time:")
                    yield Input(
                        punch_in_time,
                        id="punch_in_time",
                        placeholder="HH:MM",
                    )

                # Check Out
                yield Label("Check Out:", classes="section-label")
                with Horizontal(classes="form-row"):
                    yield Label("Date:")
                    yield DateSelect(
                        "#punch_out_datepicker_mount",
                        date=punch_out_date_val if punch_out_date_val else date.today(),
                        id="punch_out_date",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Time:")
                    yield Input(
                        punch_in_time,
                        id="punch_in_time",
                        placeholder="HH:MM",
                    )

                # Check Out
                yield Label("Check Out:", classes="section-label")
                with Horizontal(classes="form-row"):
                    yield Label("Date:")
                    yield DateSelect(
                        value=punch_out_date_val
                        if punch_out_date_val
                        else date.today(),
                        id="punch_out_date",
                        picker_mount="#punch_out_datepicker_mount",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Time:")
                    yield Input(
                        punch_out_time,
                        id="punch_out_time",
                        placeholder="HH:MM",
                    )

                # Note
                with Horizontal(classes="form-row"):
                    yield Label("Note:")
                with Horizontal(classes="form-row"):
                    yield TextArea(
                        self.initial_note,
                        id="session_note",
                    )

                # Validation error display
                yield Static("", id="validation_error", classes="error-message")

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Save (Ctrl+A)", id="save", variant="success")
                yield Button("Remove (Ctrl+D)", id="remove", variant="error")
                yield Button("Cancel (Esc)", id="cancel")

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime | None:
        """Parse date and time strings into datetime."""
        if not date_str or not time_str:
            return None
        try:
            combined = f"{date_str} {time_str}"
            return datetime.strptime(combined, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def _submit(self) -> None:
        """Validate and submit session edits."""
        error_display = self.query_one("#validation_error", Static)
        error_display.update("")

        # Get inputs
        punch_in_date_select = self.query_one("#punch_in_date", DateSelect)
        punch_in_date_val = punch_in_date_select.value
        punch_in_time = self.query_one("#punch_in_time", Input).value.strip()

        punch_out_date_select = self.query_one("#punch_out_date", DateSelect)
        punch_out_date_val = punch_out_date_select.value
        punch_out_time = self.query_one("#punch_out_time", Input).value.strip()

        note = self.query_one("#session_note", TextArea).text.strip()

        # Parse check_in (required)
        if not punch_in_date_val or not punch_in_time:
            error_display.update("❌ Check In date and time are required")
            return

        punch_in_date_str = punch_in_date_val.strftime("%Y-%m-%d")
        punch_in = self._parse_datetime(punch_in_date_str, punch_in_time)
        if not punch_in:
            error_display.update("❌ Check In date and time are required")
            return

        # Parse check_out (optional)
        punch_out = None
        if punch_out_date_val and punch_out_time:
            punch_out_date_str = punch_out_date_val.strftime("%Y-%m-%d")
            punch_out = self._parse_datetime(punch_out_date_str, punch_out_time)
            if not punch_out:
                error_display.update("❌ Invalid Check Out date/time format")
                return

        # Validate: check_out > check_in
        if punch_out and punch_out <= punch_in:
            error_display.update("❌ End time must be after start time")
            return

        # Warn if duration > 24h
        if punch_out:
            duration_hours = (punch_out - punch_in).total_seconds() / 3600
            if duration_hours > 24:
                # Show warning but allow user to proceed
                # In a real implementation, you might want a confirmation dialog here
                error_display.update(
                    "⚠️ Session is longer than 24 hours. Saving anyway..."
                )

        result = {
            "punch_in": punch_in,
            "punch_out": punch_out,
            "note": note if note else None,
        }

        self.dismiss(result)
