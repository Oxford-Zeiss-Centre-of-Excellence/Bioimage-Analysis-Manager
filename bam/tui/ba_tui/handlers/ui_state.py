from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from textual.widgets import TabbedContent

if TYPE_CHECKING:
    from ..tui import BAApp


class UIStateMixin:
    """Mixin for persisting UI state."""

    _project_root: Path
    _ui_state_path: Path

    def _get_project_state_key(self: "BAApp") -> str:
        """Return a unique key for this project's UI state."""
        return str(self._project_root.resolve())

    def _apply_ui_state(self: "BAApp") -> None:
        try:
            if not self._ui_state_path.exists():
                return
            with open(self._ui_state_path) as f:
                all_state = yaml.safe_load(f) or {}
        except Exception:
            return

        # Get project-specific state
        project_key = self._get_project_state_key()
        data = all_state.get(project_key, {})
        if not data:
            return

        tab_id = data.get("active_tab")
        focus_id = data.get("focused_id")

        if tab_id:
            try:
                tabbed = self.query_one("#tabs", TabbedContent)
                tabbed.active = str(tab_id)
            except Exception:
                pass

        if focus_id:

            def _focus_later() -> None:
                try:
                    widget = self.query_one(f"#{focus_id}")
                    widget.focus()
                except Exception:
                    pass

            # Use set_timer with small delay to ensure tab content is ready
            self.set_timer(0.1, _focus_later)

    def _store_ui_state(self: "BAApp") -> None:
        try:
            if not self.screen_stack:
                return
        except Exception:
            return
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            active_tab = tabbed.active
        except Exception:
            active_tab = ""

        focused_id = ""
        if self.focused is not None and getattr(self.focused, "id", None):
            focused_id = str(self.focused.id)

        project_key = self._get_project_state_key()
        project_state = {"active_tab": active_tab, "focused_id": focused_id}

        try:
            self._ui_state_path.parent.mkdir(parents=True, exist_ok=True)
            # Load existing state for all projects
            all_state = {}
            if self._ui_state_path.exists():
                with open(self._ui_state_path) as f:
                    all_state = yaml.safe_load(f) or {}
            # Update state for this project
            all_state[project_key] = project_state
            with open(self._ui_state_path, "w") as f:
                yaml.safe_dump(all_state, f, sort_keys=False)
        except Exception:
            pass
