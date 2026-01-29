from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ..styles import EXIT_CONFIRM_CSS, NEW_MANIFEST_CONFIRM_CSS, RESET_CONFIRM_CSS


class ExitConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm exit and optionally save."""

    BINDINGS = [
        Binding("s", "select_save", "Save & Exit", show=True),
        Binding("e", "select_exit", "Exit", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = EXIT_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Save changes before exit?")
            with Horizontal(id="button_row"):
                yield Button("Save & Exit (S)", id="save", variant="success")
                yield Button("Exit (E)", id="discard", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_save(self) -> None:
        """Handle S key press."""
        self.dismiss("save")

    def action_select_exit(self) -> None:
        """Handle E key press."""
        self.dismiss("discard")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")


class NewManifestConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm creating a new manifest."""

    BINDINGS = [
        Binding("d", "select_discard", "Discard", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = NEW_MANIFEST_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Discard current settings and start new?")
            with Horizontal(id="button_row"):
                yield Button("Discard (D)", id="discard", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_discard(self) -> None:
        """Handle D key press."""
        self.dismiss("discard")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")


class ResetConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm resetting/reloading manifest from disk."""

    BINDINGS = [
        Binding("r", "select_reset", "Reset", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = RESET_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Discard unsaved changes and reload manifest?")
            with Horizontal(id="button_row"):
                yield Button("Reset (R)", id="reset", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_reset(self) -> None:
        """Handle R key press."""
        self.dismiss("reset")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")
