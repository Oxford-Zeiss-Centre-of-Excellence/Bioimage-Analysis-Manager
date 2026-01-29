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
)

from ..styles import DATASET_MODAL_CSS
from .base import FormModal
from .directory_picker import DirectoryPickerScreen
from .path_suggestions import PathSuggestionsMixin


class DatasetModal(PathSuggestionsMixin, FormModal):
    """Modal to add or edit a dataset."""

    CSS = DATASET_MODAL_CSS

    def __init__(
        self,
        endpoint_options: list[tuple[str, str]],
        format_options: list[tuple[str, str]],
        initial_data: dict[str, object] | None = None,
        allow_remove: bool = False,
    ) -> None:
        super().__init__()
        self.endpoint_options = endpoint_options
        self.format_options = format_options
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove
        self._browse_target: str | None = None
        self._active_path_input: str | None = None
        self._path_suggestions_visible: dict[str, bool] = {
            "source": False,
            "local": False,
        }

    def compose(self) -> ComposeResult:
        title = "Edit Dataset" if self.initial_data else "Add Dataset"
        endpoint_values = {value for _, value in self.endpoint_options}
        format_values = {value for _, value in self.format_options}
        initial_endpoint = str(self.initial_data.get("endpoint", "")).strip()
        initial_format = str(self.initial_data.get("format", "")).strip()
        endpoint_value = Select.BLANK
        format_value = Select.BLANK
        endpoint_custom = ""
        format_custom = ""
        show_endpoint_custom = False
        show_format_custom = False

        if initial_endpoint:
            if initial_endpoint in endpoint_values:
                endpoint_value = initial_endpoint
                show_endpoint_custom = initial_endpoint.lower() == "other"
            else:
                endpoint_value = "Other" if "Other" in endpoint_values else Select.BLANK
                endpoint_custom = initial_endpoint
                show_endpoint_custom = True

        is_local_endpoint = str(endpoint_value).lower() == "local"

        if initial_format:
            if initial_format in format_values:
                format_value = initial_format
                show_format_custom = initial_format.lower() == "other"
            else:
                format_value = "other" if "other" in format_values else Select.BLANK
                format_custom = initial_format
                show_format_custom = True

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("Name*:")
                    yield Input(
                        str(self.initial_data.get("name", "")),
                        id="name",
                        placeholder="Dataset name",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Endpoint:")
                    yield Select(
                        self.endpoint_options,
                        value=endpoint_value,
                        allow_blank=True,
                        id="endpoint",
                    )

                with Horizontal(
                    id="endpoint_custom_row",
                    classes="form-row" + ("" if show_endpoint_custom else " hidden"),
                ):
                    yield Label("Custom endpoint:")
                    yield Input(
                        endpoint_custom,
                        id="endpoint_custom",
                        placeholder="Enter endpoint",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Locally mounted:")
                    yield Checkbox(
                        "Yes",
                        True
                        if is_local_endpoint
                        else bool(self.initial_data.get("locally_mounted", False)),
                        id="locally_mounted",
                        disabled=is_local_endpoint,
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Source path:")
                    yield Input(
                        str(self.initial_data.get("source", "")),
                        id="source",
                        placeholder="Original data path",
                    )
                    yield Button("Browse", id="browse_source", variant="primary")
                yield OptionList(id="source_suggestions")

                with Horizontal(classes="form-row"):
                    yield Label("Local path:")
                    yield Input(
                        str(self.initial_data.get("local", "")),
                        id="local",
                        placeholder="Local cache path",
                    )
                    yield Button("Browse", id="browse_local", variant="primary")
                yield OptionList(id="local_suggestions")

                with Horizontal(classes="form-row"):
                    yield Label("Description:")
                    yield Input(
                        str(self.initial_data.get("description", "")),
                        id="description",
                        placeholder="What the data contains",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Format:")
                    yield Select(
                        self.format_options,
                        value=format_value,
                        allow_blank=True,
                        id="format",
                    )

                with Horizontal(
                    id="format_custom_row",
                    classes="form-row" + ("" if show_format_custom else " hidden"),
                ):
                    yield Label("Custom format:")
                    yield Input(
                        format_custom,
                        id="format_custom",
                        placeholder="Enter format",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Raw size:")
                    yield Input(
                        str(self.initial_data.get("raw_size_gb", "")),
                        id="raw_size_gb",
                        placeholder="Approximate raw data size",
                    )
                    yield Select(
                        [("GB", "gb"), ("TB", "tb")],
                        value=str(self.initial_data.get("raw_size_unit", "gb")),
                        id="raw_size_unit",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Compression:")
                    yield Checkbox(
                        "Yes",
                        bool(self.initial_data.get("compressed", False)),
                        id="compressed",
                    )

                with Horizontal(
                    id="uncompressed_row",
                    classes="form-row"
                    + ("" if self.initial_data.get("compressed", False) else " hidden"),
                ):
                    yield Label("Uncompressed size:")
                    yield Input(
                        str(self.initial_data.get("uncompressed_size_gb", "")),
                        id="uncompressed_size_gb",
                        placeholder="Uncompressed size",
                    )
                    yield Select(
                        [("GB", "gb"), ("TB", "tb")],
                        value=str(
                            self.initial_data.get("uncompressed_size_unit", "gb")
                        ),
                        id="uncompressed_size_unit",
                    )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse_source":
            self._open_directory_picker("source")
            return
        if event.button.id == "browse_local":
            self._open_directory_picker("local")
            return
        super().on_button_pressed(event)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "endpoint":
            value = event.value
            try:
                row = self.query_one("#endpoint_custom_row", Horizontal)
                if value and str(value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
            try:
                checkbox = self.query_one("#locally_mounted", Checkbox)
                if value and str(value).lower() == "local":
                    checkbox.value = True
                    checkbox.disabled = True
                else:
                    checkbox.disabled = False
            except Exception:
                pass
        elif event.select.id == "format":
            value = event.value
            try:
                row = self.query_one("#format_custom_row", Horizontal)
                if value and str(value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "locally_mounted":
            if not event.value:
                self._hide_path_suggestions("source")
            return
        if event.checkbox.id == "compressed":
            try:
                row = self.query_one("#uncompressed_row", Horizontal)
                if event.value:
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
            return

    def on_key(self, event) -> None:
        if event.key in ("down", "up"):
            try:
                if self._active_path_input in ("source", "local"):
                    suggestions = self.query_one(
                        f"#{self._active_path_input}_suggestions", OptionList
                    )
                    if event.key == "down":
                        focused = self.focused
                        if (
                            focused
                            and getattr(focused, "id", "") == self._active_path_input
                        ):
                            suggestions.focus()
                            if suggestions.option_count > 0:
                                suggestions.highlighted = 0
                            event.prevent_default()
                            event.stop()
                    elif event.key == "up":
                        if self.focused == suggestions and suggestions.highlighted == 0:
                            input_widget = self.query_one(
                                f"#{self._active_path_input}", Input
                            )
                            input_widget.focus()
                            event.prevent_default()
                            event.stop()
            except Exception:
                pass
        super().on_key(event)

    def _open_directory_picker(self, target_input_id: str) -> None:
        self._browse_target = target_input_id
        start = Path.home()
        self.app.push_screen(DirectoryPickerScreen(start), self._handle_directory_pick)

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
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        endpoint_value = self.query_one("#endpoint", Select).value
        endpoint_custom = self.query_one("#endpoint_custom", Input).value.strip()
        endpoint = ""
        if endpoint_value and endpoint_value != Select.BLANK:
            endpoint = str(endpoint_value)
        if endpoint.lower() == "other" and endpoint_custom:
            endpoint = endpoint_custom
        elif not endpoint and endpoint_custom:
            endpoint = endpoint_custom

        format_value = self.query_one("#format", Select).value
        format_custom = self.query_one("#format_custom", Input).value.strip()
        data_format = ""
        if format_value and format_value != Select.BLANK:
            data_format = str(format_value)
        if data_format.lower() == "other" and format_custom:
            data_format = format_custom
        elif not data_format and format_custom:
            data_format = format_custom

        data = {
            "name": name,
            "endpoint": endpoint,
            "locally_mounted": bool(self.query_one("#locally_mounted", Checkbox).value),
            "source": self.query_one("#source", Input).value.strip(),
            "local": self.query_one("#local", Input).value.strip(),
            "description": self.query_one("#description", Input).value.strip(),
            "format": data_format,
            "raw_size_gb": self.query_one("#raw_size_gb", Input).value.strip(),
            "raw_size_unit": str(self.query_one("#raw_size_unit", Select).value or ""),
            "compressed": bool(self.query_one("#compressed", Checkbox).value),
            "uncompressed_size_gb": self.query_one(
                "#uncompressed_size_gb", Input
            ).value.strip(),
            "uncompressed_size_unit": str(
                self.query_one("#uncompressed_size_unit", Select).value or ""
            ),
        }
        self.dismiss(data)
