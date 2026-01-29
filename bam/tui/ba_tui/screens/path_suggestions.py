from __future__ import annotations

from typing import Optional

from textual.widgets import Checkbox, Input, OptionList
from textual.widgets.option_list import Option


class PathSuggestionsMixin:
    """Mixin for path suggestions in DatasetModal."""

    _active_path_input: Optional[str]
    _path_suggestions_visible: dict[str, bool]

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "source":
            if self.focused != event.input:
                self._hide_path_suggestions(event.input.id)
                return
            try:
                locally_mounted = self.query_one("#locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_path_suggestions(event.input.id, event.value)
                else:
                    self._hide_path_suggestions(event.input.id)
            except Exception:
                self._hide_path_suggestions(event.input.id)
        elif event.input.id == "local":
            if self.focused != event.input:
                self._hide_path_suggestions(event.input.id)
                return
            self._update_path_suggestions(event.input.id, event.value)

    def on_input_focused(self, event: Input.Focused) -> None:
        if event.input.id == "source":
            try:
                locally_mounted = self.query_one("#locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_path_suggestions(event.input.id, event.input.value)
            except Exception:
                pass
        elif event.input.id == "local":
            self._update_path_suggestions(event.input.id, event.input.value)

    def on_input_blurred(self, event: Input.Blurred) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id in ("source", "local"):
            focused = self.focused
            if focused and getattr(focused, "id", "") == f"{input_id}_suggestions":
                return
            self._hide_path_suggestions(input_id)

    def on_option_list_blurred(self, event: OptionList.Blurred) -> None:
        if event.option_list.id in ("source_suggestions", "local_suggestions"):
            input_id = (
                "source" if event.option_list.id == "source_suggestions" else "local"
            )
            focused = self.focused
            if focused and getattr(focused, "id", "") == input_id:
                return
            self._hide_path_suggestions(input_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id in ("source_suggestions", "local_suggestions"):
            input_id = (
                "source" if event.option_list.id == "source_suggestions" else "local"
            )
            try:
                input_widget = self.query_one(f"#{input_id}", Input)
                selected = str(event.option.prompt)
                input_widget.value = selected
                self._hide_path_suggestions(input_id)
                input_widget.focus()
                try:
                    input_widget.cursor_position = len(selected)
                except Exception:
                    pass
            except Exception:
                pass

    def _update_path_suggestions(self, input_id: str, current_value: str) -> None:
        try:
            suggestions = self.query_one(f"#{input_id}_suggestions", OptionList)
            suggestions.clear_options()

            if not current_value:
                self._hide_path_suggestions(input_id)
                return

            from pathlib import Path

            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()

            if not search_dir.exists():
                self._hide_path_suggestions(input_id)
                return

            entries = []
            try:
                for entry in sorted(search_dir.iterdir()):
                    if entry.is_dir():
                        name = entry.name
                        if not prefix or name.lower().startswith(prefix):
                            entries.append(str(entry))
                            if len(entries) >= 10:
                                break
            except PermissionError:
                pass

            if entries:
                for entry in entries:
                    suggestions.add_option(Option(entry))
                suggestions.add_class("visible")
                self._path_suggestions_visible[input_id] = True
                self._active_path_input = input_id
            else:
                self._hide_path_suggestions(input_id)
        except Exception:
            self._hide_path_suggestions(input_id)

    def _hide_path_suggestions(self, input_id: str) -> None:
        try:
            suggestions = self.query_one(f"#{input_id}_suggestions", OptionList)
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._path_suggestions_visible[input_id] = False
        except Exception:
            pass
