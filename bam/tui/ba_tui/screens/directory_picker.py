from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Static

from ..styles import DIRECTORY_PICKER_CSS


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
