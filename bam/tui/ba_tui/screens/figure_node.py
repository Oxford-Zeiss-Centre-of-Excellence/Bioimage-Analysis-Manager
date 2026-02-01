from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Static, TextArea

from ..styles import FIGURE_NODE_MODAL_CSS
from .base import FormModal


class FigureNodeModal(FormModal):
    """Modal to add or edit a figure node (container)."""

    CSS = FIGURE_NODE_MODAL_CSS

    def __init__(self, initial_data: dict[str, object] | None = None) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = bool(initial_data)

    def compose(self) -> ComposeResult:
        title = "Edit Figure" if self.initial_data else "Add Figure"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("ID*:")
                    yield Input(
                        str(self.initial_data.get("id", "")),
                        id="node_id",
                        placeholder="Figure or panel id",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Title:")
                    yield Input(
                        str(self.initial_data.get("title", "")),
                        id="node_title",
                        placeholder="Optional title",
                    )
                yield Static("Description")
                yield TextArea(
                    str(self.initial_data.get("description", "")),
                    id="node_description",
                )
            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Delete (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def _submit(self) -> None:
        node_id = self.query_one("#node_id", Input).value.strip()
        if not node_id:
            self.notify("ID is required", severity="error")
            return
        data = {
            "id": node_id,
            "title": self.query_one("#node_title", Input).value.strip(),
            "description": self.query_one("#node_description", TextArea).text.strip(),
        }
        self.dismiss(data)
