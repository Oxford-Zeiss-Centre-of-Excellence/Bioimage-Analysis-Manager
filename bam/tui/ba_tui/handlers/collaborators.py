from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import DataTable, Input, Select

from ..config import load_role_options
from ..screens import CollaboratorModal

if TYPE_CHECKING:
    from ..tui import BAApp


class CollaboratorsMixin:
    """Mixin for collaborator table management."""

    def _handle_edit_collaborator(
        self: "BAApp", idx: int, data: dict[str, str] | None
    ) -> None:
        """Update collaborator data after modal close."""
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._collaborator_rows):
                self._collaborator_rows.pop(idx)
                self._populate_collaborators_table()
            return
        if data and 0 <= idx < len(self._collaborator_rows):
            self._collaborator_rows[idx] = data
            self._populate_collaborators_table()

    def _collect_collaborators(self: "BAApp") -> list[dict[str, str]]:
        collaborators = []
        for row in self._collaborator_rows:
            name = row.get("name", "").strip()
            role = row.get("role", "").strip()
            email = row.get("email", "").strip()
            affiliation = row.get("affiliation", "").strip()
            if not any([name, role, email, affiliation]):
                continue
            collab = {"name": name}
            if role:
                collab["role"] = role
            if email:
                collab["email"] = email
            if affiliation:
                collab["affiliation"] = affiliation
            collaborators.append(collab)
        return collaborators

    def _ensure_collaborator_rows(self: "BAApp") -> None:
        if self._collaborator_rows:
            return
        # Removed the fallback empty row logic
        self._collaborator_rows = []

    def _populate_collaborators_table(self: "BAApp") -> None:
        """Populate the DataTable with collaborator data."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if not table.columns:
                # Add columns with proportional widths
                table.add_column("Name", width=20)
                table.add_column("Role", width=15)
                table.add_column("Email", width=25)
                table.add_column("Affiliation", width=20)
            table.clear()
            for idx, row in enumerate(self._collaborator_rows):
                table.add_row(
                    row.get("name", ""),
                    row.get("role", ""),
                    row.get("email", ""),
                    row.get("affiliation", ""),
                    key=str(idx),
                )
        except Exception:
            pass

    def action_add_collaborator_row(self: "BAApp") -> None:
        """Action to add a new collaborator row (Ctrl+A)."""
        # Always allow adding, even if table not focused (as long as we are in setup tab)
        if self.query_one("#tabs").active != "setup":
            return

        self.push_screen(
            CollaboratorModal(load_role_options()), self._handle_new_collaborator
        )

    def _handle_new_collaborator(self: "BAApp", data: dict[str, str] | None) -> None:
        """Add new collaborator after modal close."""
        if data:
            self._collaborator_rows.append(data)
            self._populate_collaborators_table()

    def action_remove_collaborator_row(self: "BAApp") -> None:
        """Action to remove the selected collaborator row (Ctrl+D)."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            # Only remove if table is focused or active
            if not table.has_focus and self.query_one("#tabs").active != "setup":
                return

            if table.cursor_row is None:
                return

            idx = table.cursor_row
            if 0 <= idx < len(self._collaborator_rows):
                self._collaborator_rows.pop(idx)

            self._populate_collaborators_table()

            # Adjust cursor position
            if self._collaborator_rows:
                idx = min(idx, len(self._collaborator_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _edit_collaborator_cell(self: "BAApp") -> None:
        """Open an input dialog to edit the current cell."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None or table.cursor_column is None:
                return

            row_idx = table.cursor_row
            col_idx = table.cursor_column

            if row_idx >= len(self._collaborator_rows):
                return

            column_names = ["name", "role", "email", "affiliation"]
            if col_idx >= len(column_names):
                return

            field_name = column_names[col_idx]
            current_value = self._collaborator_rows[row_idx].get(field_name, "")

            # For role column, show select dialog
            if field_name == "role":
                self._edit_role_cell(row_idx, col_idx, current_value)
            else:
                self._edit_text_cell(row_idx, col_idx, field_name, current_value)
        except Exception as exc:
            self.notify(f"Error editing cell: {exc}", severity="error", markup=False)

    def _edit_text_cell(
        self: "BAApp", row_idx: int, col_idx: int, field_name: str, current_value: str
    ) -> None:
        """Deprecated: inline cell editor removed."""
        return

    def _edit_role_cell(
        self: "BAApp", row_idx: int, col_idx: int, current_value: str
    ) -> None:
        """Deprecated: inline cell editor removed."""
        return

    def _update_collaborator_from_inputs(self: "BAApp") -> None:
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            name = self.query_one("#collab_name_input", Input).value.strip()
            role = self.query_one("#collab_role_select", Select).value
            email = self.query_one("#collab_email_input", Input).value.strip()
            affiliation = self.query_one(
                "#collab_affiliation_input", Input
            ).value.strip()
            role_value = "" if role in (None, Select.BLANK) else str(role)
            self._collaborator_rows[idx] = {
                "name": name,
                "role": role_value,
                "email": email,
                "affiliation": affiliation,
            }
            self._populate_collaborators_table()
        except Exception:
            pass

    def _remove_selected_collaborator(self: "BAApp") -> None:
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._collaborator_rows):
                self._collaborator_rows.pop(idx)
            if not self._collaborator_rows:
                self._collaborator_rows = [
                    {"name": "", "role": "", "email": "", "affiliation": ""}
                ]
            self._populate_collaborators_table()
        except Exception:
            pass
