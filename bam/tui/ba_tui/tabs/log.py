"""Log tab: CSV worklog management."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, ListView, Select, Static, TabPane

from ..models import TaskStatus


def compose_log_tab(app: object) -> ComposeResult:
    """Compose the Log tab for CSV worklog management."""
    with TabPane("Log (F6)", id="log"):
        with VerticalScroll():
            entries = (
                "\n".join(app._recent_entries)
                if app._recent_entries
                else "(no entries yet)"
            )
            yield Static(entries, id="log_entries")

            with Horizontal(id="log_panels"):
                with Vertical():
                    yield Static("Active Tasks")
                    yield ListView(id="active_tasks")
                with Vertical():
                    yield Static("Today's Completed")
                    yield ListView(id="completed_tasks")

            with Vertical(id="log_controls"):
                yield Input(placeholder="Task description", id="task_description")
                task_options = [
                    (
                        entry.get("label", entry.get("id", "")),
                        entry.get("id", "analysis"),
                    )
                    for entry in app._task_types
                ]
                if not task_options:
                    task_options = [("Analysis", "analysis")]
                yield Select(task_options, id="task_type")
                yield Input(placeholder="Notes (optional)", id="task_notes")

                with Horizontal():
                    yield Button("New Task", id="task_add", variant="success")
                    yield Button("Check Out", id="task_checkout", variant="primary")
                    yield Button("Pause/Resume", id="task_pause", variant="warning")

                with Horizontal():
                    yield Select(
                        [
                            ("Active", TaskStatus.active.value),
                            ("Paused", TaskStatus.paused.value),
                            ("Completed", TaskStatus.completed.value),
                            ("Blocked", TaskStatus.blocked.value),
                            ("Interrupted", TaskStatus.interrupted.value),
                        ],
                        id="task_status",
                    )
                    yield Button("Set Status", id="task_set_status", variant="primary")

            app._log_error = Static("", id="log_error")
            yield app._log_error
