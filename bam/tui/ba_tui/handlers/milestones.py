from __future__ import annotations

from datetime import date, datetime
import pendulum
from textual.widgets import DataTable, TabbedContent

from ..screens import MilestoneModal


class MilestonesMixin:
    """Mixin for milestone table management."""

    _milestone_rows: list[dict[str, object]]

    def _populate_milestones_table(self) -> None:
        try:
            table = self.query_one("#milestones_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "Target", "Actual", "Status", "Notes")
            for idx, row in enumerate(self._milestone_rows):
                table.add_row(
                    str(row.get("name", "")),
                    self._format_date_cell(row.get("target_date")),
                    self._format_date_cell(row.get("actual_date")),
                    str(row.get("status", "pending")),
                    self._truncate_text(str(row.get("notes", ""))),
                    key=str(idx),
                )
        except Exception:
            pass

    def _format_date_cell(self, value: object) -> str:
        if isinstance(value, date):
            return value.isoformat()
        if value:
            return str(value)
        return ""

    def _normalize_date(self, value: object) -> date | None:
        if value is None:
            return None
        # Handle datetime (including pendulum.DateTime) - extract pure Python date
        if isinstance(value, datetime):
            return date(value.year, value.month, value.day)
        # Handle pure date objects (but not datetime subclasses)
        if type(value) is date:
            return value
        # Handle objects with .date() method (e.g., pendulum types)
        date_method = getattr(value, "date", None)
        if callable(date_method):
            try:
                result = date_method()
                # Convert to pure Python date
                if isinstance(result, date):
                    return date(result.year, result.month, result.day)
                return None
            except Exception:
                return None
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _to_pendulum_date(self, value: object) -> pendulum.DateTime | None:
        if value is None:
            return None
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, datetime):
            return pendulum.datetime(value.year, value.month, value.day)
        if type(value) is date:
            return pendulum.datetime(value.year, value.month, value.day)
        date_method = getattr(value, "date", None)
        if callable(date_method):
            try:
                result = date_method()
                if isinstance(result, date):
                    return pendulum.datetime(result.year, result.month, result.day)
            except Exception:
                return None
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                if isinstance(parsed, pendulum.DateTime):
                    return parsed
                return None
            except Exception:
                return None
        return None

    def _sanitize_manifest_dates(self, manifest_data: dict[str, object]) -> None:
        timeline = manifest_data.get("timeline")
        if isinstance(timeline, dict):
            milestones = timeline.get("milestones")
            if isinstance(milestones, list):
                for milestone in milestones:
                    if not isinstance(milestone, dict):
                        continue
                    for field in ("target_date", "actual_date"):
                        milestone[field] = self._normalize_date(milestone.get(field))

        billing = manifest_data.get("billing")
        if isinstance(billing, dict):
            for field in ("start_date", "end_date"):
                billing[field] = self._normalize_date(billing.get(field))

    def _truncate_text(self, value: str, max_len: int = 30) -> str:
        if len(value) <= max_len:
            return value
        return f"{value[: max_len - 3]}..."

    def action_add_milestone(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "admin":
            return
        admin_sections = self.query_one("#admin_sections", TabbedContent)
        if admin_sections.active != "admin_timeline":
            return
        initial_data = None
        try:
            table = self.query_one("#milestones_table", DataTable)
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self._milestone_rows):
                initial_data = dict(self._milestone_rows[idx])
                initial_data["name"] = ""
        except Exception:
            initial_data = None
        self.push_screen(MilestoneModal(initial_data), self._handle_new_milestone)

    def action_remove_milestone(self) -> None:
        try:
            table = self.query_one("#milestones_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._milestone_rows):
                self._milestone_rows.pop(idx)
            self._populate_milestones_table()
            if self._milestone_rows:
                idx = min(idx, len(self._milestone_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _handle_new_milestone(self, data: dict[str, object] | None) -> None:
        if data:
            self._milestone_rows.append(data)
            self._populate_milestones_table()

    def _handle_edit_milestone(self, idx: int, data: dict[str, object] | None) -> None:
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._milestone_rows):
                self._milestone_rows.pop(idx)
                self._populate_milestones_table()
            return
        if data and 0 <= idx < len(self._milestone_rows):
            self._milestone_rows[idx] = data
            self._populate_milestones_table()

    def _collect_milestones(self) -> list[dict[str, object]]:
        milestones: list[dict[str, object]] = []
        for row in self._milestone_rows:
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            milestone: dict[str, object] = {"name": name}
            target = self._normalize_date(row.get("target_date"))
            actual = self._normalize_date(row.get("actual_date"))
            if target:
                milestone["target_date"] = target
            if actual:
                milestone["actual_date"] = actual
            status = str(row.get("status", "")).strip()
            if status:
                milestone["status"] = status
            notes = str(row.get("notes", "")).strip()
            if notes:
                milestone["notes"] = notes
            milestones.append(milestone)
        return milestones
