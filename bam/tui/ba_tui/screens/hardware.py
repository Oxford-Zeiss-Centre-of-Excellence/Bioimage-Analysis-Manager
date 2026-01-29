from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Checkbox, Input, Label, Static

from ..styles import HARDWARE_MODAL_CSS
from .base import FormModal


class HardwareModal(FormModal):
    """Modal to add or edit a hardware profile."""

    CSS = HARDWARE_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, str | bool] | None = None,
        allow_remove: bool = False,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove

    def compose(self) -> ComposeResult:
        title = "Edit Hardware" if self.initial_data else "Add Hardware"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    str(self.initial_data.get("name", "")),
                    id="name",
                    placeholder="e.g., local, cluster-gpu",
                )

            with Horizontal(classes="form-row"):
                yield Label("CPU:")
                yield Input(
                    str(self.initial_data.get("cpu", "")),
                    id="cpu",
                    placeholder="e.g., Intel i9, AMD EPYC",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cores:")
                yield Input(
                    str(self.initial_data.get("cores", "")),
                    id="cores",
                    placeholder="e.g., 16",
                )

            with Horizontal(classes="form-row"):
                yield Label("RAM:")
                yield Input(
                    str(self.initial_data.get("ram", "")),
                    id="ram",
                    placeholder="e.g., 64 GB",
                )

            with Horizontal(classes="form-row"):
                yield Label("GPU:")
                yield Input(
                    str(self.initial_data.get("gpu", "")),
                    id="gpu",
                    placeholder="e.g., RTX 4090",
                )

            with Horizontal(classes="form-row"):
                yield Label("Notes:")
                yield Input(
                    str(self.initial_data.get("notes", "")),
                    id="notes",
                    placeholder="Optional",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cluster:")
                yield Checkbox(
                    "Yes",
                    bool(self.initial_data.get("is_cluster", False)),
                    id="is_cluster",
                )

            with Horizontal(classes="form-row"):
                yield Label("Partition:")
                yield Input(
                    str(self.initial_data.get("partition", "")),
                    id="partition",
                    placeholder="e.g., gpu, long",
                )

            with Horizontal(classes="form-row"):
                yield Label("Node type:")
                yield Input(
                    str(self.initial_data.get("node_type", "")),
                    id="node_type",
                    placeholder="e.g., a100, cpu",
                )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        data = {
            "name": name,
            "cpu": self.query_one("#cpu", Input).value.strip(),
            "cores": self.query_one("#cores", Input).value.strip(),
            "ram": self.query_one("#ram", Input).value.strip(),
            "gpu": self.query_one("#gpu", Input).value.strip(),
            "notes": self.query_one("#notes", Input).value.strip(),
            "is_cluster": bool(self.query_one("#is_cluster", Checkbox).value),
            "partition": self.query_one("#partition", Input).value.strip(),
            "node_type": self.query_one("#node_type", Input).value.strip(),
        }
        self.dismiss(data)
