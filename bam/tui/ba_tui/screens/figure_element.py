from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from ..styles import FIGURE_ELEMENT_MODAL_CSS
from .base import FormModal
from .directory_picker import DirectoryPickerScreen


class FigureElementModal(FormModal):
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

    def compose(self) -> ComposeResult:
        title = "Edit Element" if self.initial_data else "Add Element"
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
                    yield Label("Output path*:")
                    yield Input(
                        str(self.initial_data.get("output_path", "")),
                        id="output_path",
                        placeholder="Output file path",
                    )
                    yield Button("Browse", id="browse_output", variant="primary")
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
                yield Static("Description")
                yield TextArea(
                    str(self.initial_data.get("description", "")),
                    id="description",
                )
            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Delete (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse_output":
            self._open_directory_picker("output_path")
            return
        super().on_button_pressed(event)

    def _open_directory_picker(self, target_input_id: str) -> None:
        self._browse_target = target_input_id
        self.app.push_screen(
            DirectoryPickerScreen(Path.home()), self._handle_directory_pick
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
        output_path = self.query_one("#output_path", Input).value.strip()
        if not element_id or not output_path:
            self.notify("ID and output path are required", severity="error")
            return
        input_files = [
            part.strip()
            for part in self.query_one("#input_files", TextArea).text.split(",")
            if part.strip()
        ]
        data = {
            "id": element_id,
            "output_path": output_path,
            "source_type": str(self.query_one("#source_type", Select).value or ""),
            "source_ref": self.query_one("#source_ref", Input).value.strip(),
            "input_files": input_files,
            "parameters": self.query_one("#parameters", TextArea).text.strip(),
            "status": str(self.query_one("#status", Select).value or ""),
            "description": self.query_one("#description", TextArea).text.strip(),
        }
        self.dismiss(data)
