from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label, Select, Static

from .styles import (
    COLLABORATOR_MODAL_CSS,
    DIRECTORY_PICKER_CSS,
    EXIT_CONFIRM_CSS,
    NEW_MANIFEST_CONFIRM_CSS,
    RESET_CONFIRM_CSS,
)


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


class DirectoryPickerScreen(ModalScreen[str]):
    """Modal directory picker using DirectoryTree."""

    CSS = DIRECTORY_PICKER_CSS

    def __init__(self, start_path: Path) -> None:
        super().__init__()
        self._start_path = start_path
        self._selected_path = str(start_path)

    def compose(self) -> ComposeResult:
        with Vertical(id="picker"):
            yield Static("Select a directory (click to select, Enter to expand)")
            yield DirectoryTree(self._start_path, id="dir_tree")
            yield Static(self._selected_path, id="selected_path")
            with Horizontal(id="picker_buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Select", id="select", variant="success")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle when a directory is clicked/selected in the tree."""
        self._selected_path = str(event.path)
        self.query_one("#selected_path", Static).update(
            f"Selected: {self._selected_path}"
        )

    def on_tree_node_highlighted(self, event) -> None:
        """Handle when a node is highlighted (cursor moved to it)."""
        if hasattr(event, "node") and event.node.data:
            path = (
                event.node.data.path
                if hasattr(event.node.data, "path")
                else str(event.node.data)
            )
            self._selected_path = str(path)
            self.query_one("#selected_path", Static).update(
                f"Selected: {self._selected_path}"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            self.dismiss(self._selected_path)
        else:
            self.dismiss("")


class CollaboratorModal(ModalScreen[dict[str, str] | None]):
    """Modal to add or edit a collaborator."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = COLLABORATOR_MODAL_CSS

    def __init__(
        self,
        role_options: list[tuple[str, str]],
        initial_data: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.role_options = role_options
        self.initial_data = initial_data or {}

    def compose(self) -> ComposeResult:
        title = "Edit Collaborator" if self.initial_data else "Add Collaborator"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    self.initial_data.get("name", ""), id="name", placeholder="Name"
                )

            with Horizontal(classes="form-row"):
                yield Label("Role:")
                role_value = self.initial_data.get("role") or Select.BLANK
                yield Select(
                    self.role_options,
                    value=role_value,
                    allow_blank=True,
                    id="role",
                )

            with Horizontal(classes="form-row"):
                yield Label("Email:")
                yield Input(
                    self.initial_data.get("email", ""), id="email", placeholder="Email"
                )

            with Horizontal(classes="form-row"):
                yield Label("Affiliation:")
                yield Input(
                    self.initial_data.get("affiliation", ""),
                    id="affiliation",
                    placeholder="Affiliation",
                )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        data = {
            "name": name,
            "role": str(self.query_one("#role", Select).value or ""),
            "email": self.query_one("#email", Input).value.strip(),
            "affiliation": self.query_one("#affiliation", Input).value.strip(),
        }
        self.dismiss(data)
