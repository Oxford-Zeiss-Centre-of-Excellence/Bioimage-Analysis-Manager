from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static

from ..styles import CUSTOM_INPUT_MODAL_CSS
from .base import FormModal


class CustomInputModal(FormModal):
    """Modal to enter comma-separated values."""

    CSS = CUSTOM_INPUT_MODAL_CSS

    def __init__(self, title: str | None, placeholder: str = "") -> None:
        super().__init__()
        self.title = title
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.title or "", classes="header")
            with Horizontal(classes="form-row"):
                yield Input(
                    "",
                    id="custom_input",
                    placeholder=self.placeholder or "Comma-separated",
                )
            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Add (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#custom_input", Input).focus()

    def _submit(self) -> None:
        text = self.query_one("#custom_input", Input).value.strip()
        if not text:
            self.dismiss(None)
            return
        items = [item.strip() for item in text.split(",") if item.strip()]
        self.dismiss(items)
