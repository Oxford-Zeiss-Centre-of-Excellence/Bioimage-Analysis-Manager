from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from textual.widgets import TabbedContent, Tree

if TYPE_CHECKING:
    from ..tui import BAApp

# Sub-tab containers for each main tab that has sections
SUB_TAB_IDS = {
    "setup": "#setup_sections",
    "science": "#science_sections",
    "outputs": "#outputs_sections",
    "manifest": "#manifest_sections",
}


class UIStateMixin:
    """Mixin for persisting UI state."""

    _project_root: Path
    _ui_state_path: Path
    _figure_expanded_ids: set[str]
    _figure_selected_id: str | None
    _last_working_task_id: str | None
    _task_expanded_ids: set[str]
    _task_selected_task_id: str | None
    _task_selected_session_index: int | None

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
        sub_tabs = data.get("sub_tabs", {})
        focus_id = data.get("focused_id")

        # Restore figure tree state
        figure_expanded = data.get("figure_expanded_ids", [])
        if isinstance(figure_expanded, list):
            self._figure_expanded_ids = set(str(x) for x in figure_expanded)
        self._figure_selected_id = data.get("figure_selected_id")

        # Restore last working task
        self._last_working_task_id = data.get("last_working_task_id")

        # Restore task tree state
        task_expanded = data.get("task_expanded_ids", [])
        if isinstance(task_expanded, list):
            self._task_expanded_ids = set(str(x) for x in task_expanded)
        self._task_selected_task_id = data.get("task_selected_task_id")
        if "task_selected_session_index" in data:
            try:
                self._task_selected_session_index = int(
                    data.get("task_selected_session_index")
                )
            except Exception:
                self._task_selected_session_index = None

        if tab_id:
            try:
                tabbed = self.query_one("#tabs", TabbedContent)
                tabbed.active = str(tab_id)
            except Exception:
                pass

        # Restore sub-tabs for all main tabs that have sections
        for main_tab, sub_tab_selector in SUB_TAB_IDS.items():
            sub_tab_id = sub_tabs.get(main_tab)
            if sub_tab_id:
                try:
                    sub_tabbed = self.query_one(sub_tab_selector, TabbedContent)
                    sub_tabbed.active = str(sub_tab_id)
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

        # Collect sub-tab states for all main tabs that have sections
        sub_tabs: dict[str, str] = {}
        for main_tab, sub_tab_selector in SUB_TAB_IDS.items():
            try:
                sub_tabbed = self.query_one(sub_tab_selector, TabbedContent)
                if sub_tabbed.active:
                    sub_tabs[main_tab] = str(sub_tabbed.active)
            except Exception:
                pass

        # Collect figure tree state
        figure_expanded_ids: list[str] = []
        figure_selected_id: str | None = None
        try:
            tree = self.query_one("#figure_tree", Tree)
            # Collect expanded node IDs
            def collect_expanded(node) -> None:
                if node.is_expanded and node.data:
                    node_id = node.data.get("id")
                    if node_id:
                        figure_expanded_ids.append(str(node_id))
                for child in node.children:
                    collect_expanded(child)
            collect_expanded(tree.root)
            # Get selected node ID
            if tree.cursor_node and tree.cursor_node.data:
                sel_id = tree.cursor_node.data.get("id")
                if sel_id:
                    figure_selected_id = str(sel_id)
        except Exception:
            pass

        # Collect task tree state
        task_expanded_ids: list[str] = []
        task_selected_task_id: str | None = None
        task_selected_session_index: int | None = None
        try:
            task_tree = self.query_one("#task_tree", Tree)
            def collect_task_expanded(node) -> None:
                if node.is_expanded and node.data:
                    node_id = node.data.get("id")
                    if node_id:
                        task_expanded_ids.append(str(node_id))
                for child in node.children:
                    collect_task_expanded(child)
            collect_task_expanded(task_tree.root)
            if task_tree.cursor_node and task_tree.cursor_node.data:
                node_data = task_tree.cursor_node.data
                if isinstance(node_data, dict):
                    if node_data.get("type") == "task":
                        task_selected_task_id = node_data.get("id")
                    elif node_data.get("type") == "session":
                        task_selected_task_id = node_data.get("task_id")
                        task_selected_session_index = node_data.get("session_index")
        except Exception:
            pass
        # Merge cached expansion state to avoid teardown-time collapse from overwriting it.
        if hasattr(self, "_task_expanded_ids") and self._task_expanded_ids:
            merged = set(task_expanded_ids)
            merged.update(str(x) for x in self._task_expanded_ids)
            task_expanded_ids = sorted(merged)

        project_key = self._get_project_state_key()
        project_state: dict[str, object] = {
            "active_tab": active_tab,
            "focused_id": focused_id,
        }
        if sub_tabs:
            project_state["sub_tabs"] = sub_tabs
        if figure_expanded_ids:
            project_state["figure_expanded_ids"] = figure_expanded_ids
        if figure_selected_id:
            project_state["figure_selected_id"] = figure_selected_id

        # Save last working task
        if hasattr(self, "_last_working_task_id") and self._last_working_task_id:
            project_state["last_working_task_id"] = self._last_working_task_id

        if task_expanded_ids:
            project_state["task_expanded_ids"] = task_expanded_ids
        if task_selected_task_id:
            project_state["task_selected_task_id"] = task_selected_task_id
        if task_selected_session_index is not None:
            project_state["task_selected_session_index"] = task_selected_session_index

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
