"""Session note modal for worklog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static, TextArea

from ..styles import SESSION_NOTE_MODAL_CSS
from .base import FormModal


class SessionNoteModal(FormModal):
    """Modal to add or edit a session note."""

    CSS = SESSION_NOTE_MODAL_CSS

    def __init__(self, initial_note: str | None = None) -> None:
        super().__init__()
        self.initial_note = initial_note or ""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Add Session Note", classes="header")
            with VerticalScroll(id="dialog_scroll"):
                yield Label(
                    "Note (like a git commit message):", classes="section-label"
                )
                yield TextArea(
                    self.initial_note,
                    id="session_note",
                )

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Save (Ctrl+A)", id="save", variant="success")
                yield Button("Cancel (Esc)", id="cancel")

    def _submit(self) -> None:
        """Submit the note."""
        note = self.query_one("#session_note", TextArea).text.strip()
        self.dismiss({"note": note if note else None})
