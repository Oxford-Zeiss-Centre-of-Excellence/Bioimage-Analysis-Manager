from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ..styles import DELETE_CONFIRM_MODAL_CSS


class DeleteConfirmModal(ModalScreen[str]):
    """Modal to confirm deletions with a short message."""

    CSS = DELETE_CONFIRM_MODAL_CSS

    BINDINGS = [
        Binding("y", "confirm", "Confirm", show=True),
        Binding("n", "cancel", "Cancel", show=True),
    ]

    def __init__(self, label: str) -> None:
        super().__init__()
        self._label = label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(f"Remove {self._label}?", classes="header")
            with Horizontal(id="buttons"):
                yield Button("Remove (Y)", id="confirm", variant="error")
                yield Button("Cancel (N)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_confirm(self) -> None:
        self.dismiss("confirm")

    def action_cancel(self) -> None:
        self.dismiss("cancel")
