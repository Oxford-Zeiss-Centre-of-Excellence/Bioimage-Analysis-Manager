from __future__ import annotations

from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button


class FormModal(ModalScreen[object]):
    """Base modal with common form behavior.

    Subclasses must implement `_submit()` method.
    """

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("ctrl+d", "remove", "Remove", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remove":
            self.dismiss({"__delete__": True})
            return
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_remove(self) -> None:
        self.dismiss({"__delete__": True})

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()
        elif event.key == "ctrl+d":
            self.action_remove()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        """Collect values and dismiss with result. Override in subclass."""
        raise NotImplementedError("Subclasses must implement _submit()")
