from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, Static

from ..styles import CHANNEL_MODAL_CSS
from .base import FormModal


class ChannelModal(FormModal):
    """Modal to add or edit an imaging channel."""

    CSS = CHANNEL_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, str] | None = None,
        allow_remove: bool = False,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove

    def compose(self) -> ComposeResult:
        title = "Edit Channel" if self.initial_data else "Add Channel"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    self.initial_data.get("name", ""),
                    id="name",
                    placeholder="e.g., DAPI, GFP",
                )

            with Horizontal(classes="form-row"):
                yield Label("Fluorophore:")
                yield Input(
                    self.initial_data.get("fluorophore", ""),
                    id="fluorophore",
                    placeholder="e.g., DAPI, Alexa488",
                )

            with Horizontal(classes="form-row"):
                yield Label("Excitation (nm):")
                yield Input(
                    self.initial_data.get("excitation_nm", ""),
                    id="excitation_nm",
                    placeholder="e.g., 405",
                )

            with Horizontal(classes="form-row"):
                yield Label("Emission (nm):")
                yield Input(
                    self.initial_data.get("emission_nm", ""),
                    id="emission_nm",
                    placeholder="e.g., 461",
                )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Channel name is required", severity="error")
            return

        data = {
            "name": name,
            "fluorophore": self.query_one("#fluorophore", Input).value.strip(),
            "excitation_nm": self.query_one("#excitation_nm", Input).value.strip(),
            "emission_nm": self.query_one("#emission_nm", Input).value.strip(),
        }
        self.dismiss(data)
