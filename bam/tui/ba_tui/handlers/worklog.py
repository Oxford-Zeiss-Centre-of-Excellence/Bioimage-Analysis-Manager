from __future__ import annotations

from datetime import date, datetime, timedelta
from textual.widgets import Input, ListItem, ListView, Select, Static

from ..models import LogEntry, TaskStatus


class WorklogMixin:
    """Mixin for worklog task management."""

    _worklog_entries: list[LogEntry]
    _selected_active_index: int | None
    _log_error: Static | None

    def _format_duration(self, seconds: int) -> str:
        duration = timedelta(seconds=seconds)
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    def _apply_entry_status(self, entry: LogEntry, status: TaskStatus) -> LogEntry:
        now = datetime.now()
        previous_status = entry.status
        if status == TaskStatus.paused and entry.status == TaskStatus.active:
            entry.elapsed_seconds += int((now - entry.checkin).total_seconds())
            entry.status = TaskStatus.paused
            entry.checkout = entry.checkin
            return entry
        if status == TaskStatus.active and entry.status == TaskStatus.paused:
            entry.status = TaskStatus.active
            entry.checkin = now
            entry.checkout = None
            return entry
        entry.status = status
        if status == TaskStatus.completed:
            entry.checkout = (
                entry.checkin if previous_status == TaskStatus.paused else now
            )
        return entry

    def _tick_worklog(self) -> None:
        self._refresh_worklog_lists()

    def _refresh_worklog_lists(self) -> None:
        try:
            active_list = self.query_one("#active_tasks", ListView)
            completed_list = self.query_one("#completed_tasks", ListView)
        except Exception:
            return

        active_list.clear()
        completed_list.clear()
        today = date.today()
        for idx, entry in enumerate(self._worklog_entries):
            duration = self._format_duration(entry.duration_seconds())
            label = f"{entry.task} [{entry.status.value}] ({duration})"
            if entry.status in (TaskStatus.active, TaskStatus.paused):
                active_list.append(ListItem(Static(label), id=f"active-{idx}"))
            if entry.status == TaskStatus.completed:
                checkout = entry.checkout or entry.checkin
                if checkout.date() == today:
                    completed_list.append(
                        ListItem(Static(label), id=f"completed-{idx}")
                    )

    def _add_task(self) -> None:
        description = self.query_one("#task_description", Input).value.strip()
        task_type = self.query_one("#task_type", Select).value
        notes = self.query_one("#task_notes", Input).value.strip() or None
        if not description:
            if self._log_error is not None:
                self._log_error.update("Task description is required.")
            return
        entry = LogEntry(
            checkin=datetime.now(),
            task=description,
            type=str(task_type),
            status=TaskStatus.active,
            notes=notes,
        )
        self._worklog_entries.append(entry)
        self.query_one("#task_description", Input).value = ""
        self.query_one("#task_notes", Input).value = ""
        self._refresh_worklog_lists()

    def _checkout_task(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to check out.")
            return
        entry = self._worklog_entries[self._selected_active_index]
        entry = self._apply_entry_status(entry, TaskStatus.completed)
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()

    def _toggle_pause_task(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to pause or resume.")
            return
        entry = self._worklog_entries[self._selected_active_index]
        if entry.status == TaskStatus.active:
            entry = self._apply_entry_status(entry, TaskStatus.paused)
        elif entry.status == TaskStatus.paused:
            entry = self._apply_entry_status(entry, TaskStatus.active)
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()

    def _set_task_status(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to update status.")
            return
        status_value = self.query_one("#task_status", Select).value
        entry = self._worklog_entries[self._selected_active_index]
        entry = self._apply_entry_status(entry, TaskStatus(str(status_value)))
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()
