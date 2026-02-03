from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    OptionList,
    Select,
    Static,
    TextArea,
)

from ..styles import FIGURE_ELEMENT_MODAL_CSS
from ..widgets import DateSelect
from .base import FormModal
from .directory_picker import DirectoryPickerScreen
from .path_suggestions import PathSuggestionsMixin


class FigureElementModal(PathSuggestionsMixin, FormModal):
    """Modal to add or edit a figure element (leaf node)."""

    CSS = FIGURE_ELEMENT_MODAL_CSS

    SOURCE_OPTIONS = [
        ("Script", "script"),
        ("Software", "software"),
        ("Manual", "manual"),
        ("Raw", "raw"),
    ]

    STATUS_OPTIONS = [
        ("Draft", "draft"),
        ("Ready", "ready"),
        ("Submitted", "submitted"),
        ("Published", "published"),
    ]

    def __init__(self, initial_data: dict[str, object] | None = None) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = bool(initial_data)
        self._browse_target: str | None = None
        self._active_path_input: str | None = None
        self._path_suggestions_visible: dict[str, bool] = {"output_path": False}

    def compose(self) -> ComposeResult:
        title = "Edit Element" if self.initial_data else "Add Element"
        locally_mounted = bool(self.initial_data.get("locally_mounted", True))

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("ID*:")
                    yield Input(
                        str(self.initial_data.get("id", "")),
                        id="element_id",
                        placeholder="Element id",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Locally mounted:")
                    yield Checkbox("Yes", locally_mounted, id="locally_mounted")
                with Horizontal(classes="form-row"):
                    yield Label("Output path:")
                    yield Input(
                        str(self.initial_data.get("output_path", "")),
                        id="output_path",
                        placeholder="Output file path",
                    )
                    yield Button(
                        "Browse",
                        id="browse_output",
                        variant="primary",
                        disabled=not locally_mounted,
                    )
                yield OptionList(id="output_path_suggestions")
                with Horizontal(classes="form-row"):
                    yield Label("Source type:")
                    yield Select(
                        self.SOURCE_OPTIONS,
                        value=str(self.initial_data.get("source_type", "script")),
                        id="source_type",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Source ref:")
                    yield Input(
                        str(self.initial_data.get("source_ref", "")),
                        id="source_ref",
                        placeholder="Script path or software name",
                    )
                yield Static("Input files (comma-separated)")
                initial_files = self.initial_data.get("input_files")
                files_list: list[str] = []
                if isinstance(initial_files, list):
                    files_list = [str(entry) for entry in initial_files]
                files_text = ", ".join(entry for entry in files_list if entry)
                yield TextArea(
                    files_text,
                    id="input_files",
                )
                yield Static("Parameters")
                yield TextArea(
                    str(self.initial_data.get("parameters", "")),
                    id="parameters",
                )
                with Horizontal(classes="form-row"):
                    yield Label("Status:")
                    yield Select(
                        self.STATUS_OPTIONS,
                        value=str(self.initial_data.get("status", "draft")),
                        id="status",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Expected delivery:")
                    yield DateSelect(
                        "#element_delivery_datepicker_mount",
                        date=self.initial_data.get("expected_delivery_date"),
                        id="expected_delivery_date",
                    )
                yield Static("", id="element_delivery_datepicker_mount")
                yield Static("Description")
                yield TextArea(
                    str(self.initial_data.get("description", "")),
                    id="description",
                )
            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse_output":
            self._open_directory_picker("output_path")
            return
        super().on_button_pressed(event)

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "locally_mounted":
            self._set_output_browse_enabled(event.value)
            if not event.value:
                self._hide_path_suggestions("output_path")
            return

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "output_path":
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

    def on_input_focused(self, event: Input.Focused) -> None:
        if event.input.id == "output_path":
            try:
                locally_mounted = self.query_one("#locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_path_suggestions(event.input.id, event.input.value)
            except Exception:
                pass

    def on_input_blurred(self, event: Input.Blurred) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id == "output_path":
            focused = self.focused
            if focused and getattr(focused, "id", "") == f"{input_id}_suggestions":
                return
            self._hide_path_suggestions(input_id)

    def on_option_list_blurred(self, event) -> None:
        if event.option_list.id == "output_path_suggestions":
            focused = self.focused
            if focused and getattr(focused, "id", "") == "output_path":
                return
            self._hide_path_suggestions("output_path")

    def on_option_list_option_selected(self, event) -> None:
        if event.option_list.id == "output_path_suggestions":
            try:
                input_widget = self.query_one("#output_path", Input)
                # Use the option id which contains the full path
                selected = (
                    str(event.option.id)
                    if event.option.id
                    else str(event.option.prompt)
                )
                input_widget.value = selected
                self._hide_path_suggestions("output_path")
                input_widget.focus()
                try:
                    input_widget.cursor_position = len(selected)
                except Exception:
                    pass
            except Exception:
                pass

    def on_key(self, event) -> None:
        if event.key in ("down", "up"):
            try:
                if self._active_path_input == "output_path":
                    suggestions = self.query_one("#output_path_suggestions", OptionList)
                    if event.key == "down":
                        focused = self.focused
                        if focused and getattr(focused, "id", "") == "output_path":
                            suggestions.focus()
                            if suggestions.option_count > 0:
                                suggestions.highlighted = 0
                            event.prevent_default()
                            event.stop()
                    elif event.key == "up":
                        if self.focused == suggestions and suggestions.highlighted == 0:
                            input_widget = self.query_one("#output_path", Input)
                            input_widget.focus()
                            event.prevent_default()
                            event.stop()
            except Exception:
                pass
        super().on_key(event)

    def _set_output_browse_enabled(self, enabled: bool) -> None:
        try:
            button = self.query_one("#browse_output", Button)
            button.disabled = not enabled
        except Exception:
            pass

    def _update_path_suggestions(self, input_id: str, current_value: str) -> None:
        """Override to show both files and directories."""
        try:
            from pathlib import Path
            from textual.widgets.option_list import Option

            suggestions = self.query_one(f"#{input_id}_suggestions", OptionList)
            suggestions.clear_options()

            if not current_value:
                self._hide_path_suggestions(input_id)
                return

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
                # Collect both directories and files
                for entry in sorted(search_dir.iterdir()):
                    name = entry.name
                    if not prefix or name.lower().startswith(prefix):
                        if entry.is_dir():
                            entries.append((str(entry), f"📁 {name}/"))
                        else:
                            entries.append((str(entry), f"📄 {name}"))
                        if len(entries) >= 20:
                            break
            except PermissionError:
                pass

            if entries:
                for entry_path, display_name in entries:
                    suggestions.add_option(Option(display_name, id=entry_path))
                suggestions.add_class("visible")
                self._path_suggestions_visible[input_id] = True
                self._active_path_input = input_id
            else:
                self._hide_path_suggestions(input_id)
        except Exception:
            self._hide_path_suggestions(input_id)

    def _open_directory_picker(self, target_input_id: str) -> None:
        from pathlib import Path

        self._browse_target = target_input_id

        # Check if input has a current value and use it as starting path
        start_path = Path.home()
        try:
            input_widget = self.query_one(f"#{target_input_id}", Input)
            current_value = input_widget.value.strip()
            if current_value:
                current_path = Path(current_value).expanduser().resolve()
                if current_path.exists():
                    # If it's a file, start from parent directory
                    if current_path.is_file():
                        start_path = current_path.parent
                    # If it's a directory, start from that directory
                    elif current_path.is_dir():
                        start_path = current_path
        except Exception:
            pass

        self.app.push_screen(
            DirectoryPickerScreen(start_path), self._handle_directory_pick
        )

    def _handle_directory_pick(self, path: str | None) -> None:
        if not path or not self._browse_target:
            self._browse_target = None
            return
        try:
            input_widget = self.query_one(f"#{self._browse_target}", Input)
            input_widget.value = path
        except Exception:
            pass
        self._browse_target = None

    def _submit(self) -> None:
        element_id = self.query_one("#element_id", Input).value.strip()
        if not element_id:
            self.notify("ID is required", severity="error")
            return
        output_path = self.query_one("#output_path", Input).value.strip()
        input_files = [
            part.strip()
            for part in self.query_one("#input_files", TextArea).text.split(",")
            if part.strip()
        ]
        expected_delivery = self.query_one("#expected_delivery_date", DateSelect).date
        data = {
            "id": element_id,
            "locally_mounted": bool(self.query_one("#locally_mounted", Checkbox).value),
            "output_path": output_path,
            "source_type": str(self.query_one("#source_type", Select).value or ""),
            "source_ref": self.query_one("#source_ref", Input).value.strip(),
            "input_files": input_files,
            "parameters": self.query_one("#parameters", TextArea).text.strip(),
            "status": str(self.query_one("#status", Select).value or ""),
            "expected_delivery_date": expected_delivery,
            "description": self.query_one("#description", TextArea).text.strip(),
        }
        self.dismiss(data)
