from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Label, OptionList, Select, Static
from textual.widgets.option_list import Option

from ..styles import ARTIFACT_MODAL_CSS
from .base import FormModal
from .directory_picker import DirectoryPickerScreen


class ArtifactModal(FormModal):
    """Modal to add or edit an artifact entry."""

    CSS = ARTIFACT_MODAL_CSS

    TYPE_OPTIONS = [
        ("Figure", "figure"),
        ("Table", "table"),
        ("Dataset", "dataset"),
        ("Model", "model"),
        ("Report", "report"),
        ("Script", "script"),
    ]

    STATUS_OPTIONS = [
        ("Draft", "draft"),
        ("Ready", "ready"),
        ("Delivered", "delivered"),
        ("Published", "published"),
    ]

    def __init__(
        self,
        endpoint_options: list[tuple[str, str]],
        initial_data: dict[str, object] | None = None,
        allow_remove: bool = False,
    ) -> None:
        super().__init__()
        self.endpoint_options = endpoint_options
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove
        self._browse_target: str | None = None
        self._path_suggestions_visible = False

    def compose(self) -> ComposeResult:
        title = "Edit Artifact" if self.initial_data else "Add Artifact"
        endpoint_value = str(self.initial_data.get("endpoint", ""))
        endpoint_custom = ""
        show_endpoint_custom = False
        endpoint_values = {value for _, value in self.endpoint_options}
        locally_mounted = bool(self.initial_data.get("locally_mounted", True))

        if endpoint_value:
            if endpoint_value in endpoint_values:
                show_endpoint_custom = endpoint_value.lower() == "other"
            else:
                endpoint_custom = endpoint_value
                endpoint_value = "Other" if "Other" in endpoint_values else ""
                show_endpoint_custom = True

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("Endpoint:")
                    yield Select(
                        self.endpoint_options,
                        value=endpoint_value or Select.BLANK,
                        allow_blank=True,
                        id="artifact_endpoint",
                    )

                with Horizontal(
                    id="artifact_endpoint_custom_row",
                    classes="form-row" + ("" if show_endpoint_custom else " hidden"),
                ):
                    yield Label("Custom endpoint:")
                    yield Input(
                        endpoint_custom,
                        id="artifact_endpoint_custom",
                        placeholder="Enter endpoint",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Locally mounted:")
                    yield Checkbox("Yes", locally_mounted, id="artifact_locally_mounted")

                with Horizontal(classes="form-row"):
                    yield Label("Path*:")
                    yield Input(
                        str(self.initial_data.get("path", "")),
                        id="artifact_path",
                        placeholder="Artifact path",
                    )
                    yield Button(
                        "Browse",
                        id="artifact_browse",
                        variant="primary",
                        disabled=not locally_mounted,
                    )
                yield OptionList(id="artifact_path_suggestions")

                with Horizontal(classes="form-row"):
                    yield Label("Type:")
                    yield Select(
                        self.TYPE_OPTIONS,
                        value=str(self.initial_data.get("type", "figure")),
                        id="artifact_type",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Status:")
                    yield Select(
                        self.STATUS_OPTIONS,
                        value=str(self.initial_data.get("status", "draft")),
                        id="artifact_status",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Description:")
                    yield Input(
                        str(self.initial_data.get("description", "")),
                        id="artifact_description",
                        placeholder="Short description",
                    )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "artifact_browse":
            self._open_directory_picker("artifact_path")
            return
        super().on_button_pressed(event)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "artifact_endpoint":
            try:
                row = self.query_one("#artifact_endpoint_custom_row", Horizontal)
                if event.value and str(event.value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "artifact_locally_mounted":
            self._set_browse_enabled(event.value)
            if not event.value:
                self._hide_path_suggestions()

    def _set_browse_enabled(self, enabled: bool) -> None:
        try:
            button = self.query_one("#artifact_browse", Button)
            button.disabled = not enabled
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "artifact_path":
            if self.focused is event.input:
                try:
                    locally_mounted = self.query_one("#artifact_locally_mounted", Checkbox)
                    if locally_mounted.value:
                        self._update_path_suggestions(event.value)
                    else:
                        self._hide_path_suggestions()
                except Exception:
                    self._hide_path_suggestions()
            else:
                self._hide_path_suggestions()

    def on_input_focused(self, event: Input.Focused) -> None:
        if event.input.id == "artifact_path":
            self._update_path_suggestions(event.input.value)

    def on_input_blurred(self, event: Input.Blurred) -> None:
        if event.input.id == "artifact_path":
            focused = self.focused
            if focused and getattr(focused, "id", "") == "artifact_path_suggestions":
                return
            self._hide_path_suggestions()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "artifact_path_suggestions":
            try:
                input_widget = self.query_one("#artifact_path", Input)
                # Use the option id which contains the full path
                selected = str(event.option.id) if event.option.id else str(event.option.prompt)
                input_widget.value = selected
                self._hide_path_suggestions()
                input_widget.focus()
                try:
                    input_widget.cursor_position = len(selected)
                except Exception:
                    pass
            except Exception:
                pass

    def on_option_list_blurred(self, event) -> None:
        if event.option_list.id == "artifact_path_suggestions":
            focused = self.focused
            if focused and getattr(focused, "id", "") == "artifact_path":
                return
            self._hide_path_suggestions()

    def on_key(self, event) -> None:
        if event.key in ("down", "up"):
            try:
                suggestions = self.query_one("#artifact_path_suggestions", OptionList)
                if event.key == "down":
                    focused = self.focused
                    if focused and getattr(focused, "id", "") == "artifact_path":
                        suggestions.focus()
                        if suggestions.option_count > 0:
                            suggestions.highlighted = 0
                        event.prevent_default()
                        event.stop()
                elif event.key == "up":
                    if self.focused == suggestions and suggestions.highlighted == 0:
                        input_widget = self.query_one("#artifact_path", Input)
                        input_widget.focus()
                        event.prevent_default()
                        event.stop()
            except Exception:
                pass
        super().on_key(event)

    def _open_directory_picker(self, target_input_id: str) -> None:
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

    def _update_path_suggestions(self, current_value: str) -> None:
        try:
            suggestions = self.query_one("#artifact_path_suggestions", OptionList)
            suggestions.clear_options()
            if not current_value:
                self._hide_path_suggestions()
                return
            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()
            if not search_dir.exists():
                self._hide_path_suggestions()
                return
            entries: list[tuple[str, str]] = []
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
                self._path_suggestions_visible = True
            else:
                self._hide_path_suggestions()
        except Exception:
            self._hide_path_suggestions()

    def _hide_path_suggestions(self) -> None:
        try:
            suggestions = self.query_one("#artifact_path_suggestions", OptionList)
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._path_suggestions_visible = False
        except Exception:
            pass

    def _submit(self) -> None:
        path = self.query_one("#artifact_path", Input).value.strip()
        if not path:
            self.notify("Path is required", severity="error")
            return

        endpoint_value = self.query_one("#artifact_endpoint", Select).value
        endpoint_custom = self.query_one(
            "#artifact_endpoint_custom", Input
        ).value.strip()
        endpoint = ""
        if endpoint_value and endpoint_value != Select.BLANK:
            endpoint = str(endpoint_value)
        if endpoint.lower() == "other" and endpoint_custom:
            endpoint = endpoint_custom
        elif not endpoint and endpoint_custom:
            endpoint = endpoint_custom

        data = {
            "endpoint": endpoint,
            "locally_mounted": bool(self.query_one("#artifact_locally_mounted", Checkbox).value),
            "path": path,
            "type": str(self.query_one("#artifact_type", Select).value or ""),
            "status": str(self.query_one("#artifact_status", Select).value or ""),
            "description": self.query_one("#artifact_description", Input).value.strip(),
        }
        self.dismiss(data)
