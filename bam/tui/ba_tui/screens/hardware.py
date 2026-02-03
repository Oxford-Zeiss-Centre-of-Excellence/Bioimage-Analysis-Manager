from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, Select, Static

from ..config import load_clusters
from ..styles import HARDWARE_MODAL_CSS
from .base import FormModal


class HardwareModal(FormModal):
    """Modal to add or edit a hardware profile."""

    CSS = HARDWARE_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, str | bool | int] | None = None,
        allow_remove: bool = False,
        project_root: Path | None = None,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove
        self._project_root = project_root
        self._initial_cluster = self.initial_data.get("cluster_name") or ""

    def compose(self) -> ComposeResult:
        title = "Edit Hardware" if self.initial_data else "Add Hardware"

        # Load cluster options
        cluster_options = load_clusters(self._project_root)
        cluster_value = (
            str(self._initial_cluster) if self._initial_cluster else Select.BLANK
        )

        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    str(self.initial_data.get("name") or ""),
                    id="name",
                    placeholder="e.g., local, cluster-gpu",
                )

            with Horizontal(classes="form-row"):
                yield Label("CPU:")
                yield Input(
                    str(self.initial_data.get("cpu") or ""),
                    id="cpu",
                    placeholder="e.g., Intel i9, AMD EPYC",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cores:")
                yield Input(
                    str(self.initial_data.get("cores") or ""),
                    id="cores",
                    placeholder="e.g., 16",
                )

            with Horizontal(classes="form-row"):
                yield Label("RAM:")
                yield Input(
                    str(self.initial_data.get("ram") or ""),
                    id="ram",
                    placeholder="e.g., 64 GB",
                )

            with Horizontal(classes="form-row"):
                yield Label("GPU:")
                yield Input(
                    str(self.initial_data.get("gpu") or ""),
                    id="gpu",
                    placeholder="e.g., RTX 4090",
                )

            with Horizontal(classes="form-row"):
                yield Label("GPU Count:")
                yield Input(
                    str(self.initial_data.get("gpu_count") or ""),
                    id="gpu_count",
                    placeholder="e.g., 2",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cluster:")
                yield Select(
                    cluster_options,
                    value=cluster_value,
                    id="cluster_name",
                    allow_blank=True,
                )

            # Other cluster field (conditional on "Other" cluster)
            with Horizontal(classes="form-row", id="other_cluster_row"):
                yield Label("Other Cluster:")
                yield Input(
                    str(self.initial_data.get("other_cluster") or ""),
                    id="other_cluster",
                    placeholder="Specify cluster name",
                )

            with Horizontal(classes="form-row"):
                yield Label("Partition:")
                yield Input(
                    str(self.initial_data.get("partition") or ""),
                    id="partition",
                    placeholder="e.g., gpu, long",
                )

            with Horizontal(classes="form-row"):
                yield Label("Node type:")
                yield Input(
                    str(self.initial_data.get("node_type") or ""),
                    id="node_type",
                    placeholder="e.g., a100, cpu",
                )

            with Horizontal(classes="form-row"):
                yield Label("Notes:")
                yield Input(
                    str(self.initial_data.get("notes") or ""),
                    id="notes",
                    placeholder="Optional",
                )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set initial visibility of Other cluster field."""
        other_cluster_row = self.query_one("#other_cluster_row")
        if self._initial_cluster != "Other":
            other_cluster_row.add_class("-hidden")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle cluster selection to show/hide Other cluster field."""
        if event.select.id == "cluster_name":
            cluster = str(event.value) if event.value != Select.BLANK else ""
            is_other = cluster == "Other"
            other_cluster_row = self.query_one("#other_cluster_row")
            if is_other:
                other_cluster_row.remove_class("-hidden")
            else:
                other_cluster_row.add_class("-hidden")

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        # Parse GPU count
        gpu_count_str = self.query_one("#gpu_count", Input).value.strip()
        gpu_count = 0
        if gpu_count_str:
            try:
                gpu_count = int(gpu_count_str)
            except ValueError:
                gpu_count = 0

        # Get cluster name
        cluster_select = self.query_one("#cluster_name", Select)
        cluster_name = (
            str(cluster_select.value) if cluster_select.value != Select.BLANK else ""
        )
        other_cluster = self.query_one("#other_cluster", Input).value.strip()

        data = {
            "name": name,
            "cluster_name": cluster_name,
            "other_cluster": other_cluster,
            "cpu": self.query_one("#cpu", Input).value.strip(),
            "cores": self.query_one("#cores", Input).value.strip(),
            "ram": self.query_one("#ram", Input).value.strip(),
            "gpu": self.query_one("#gpu", Input).value.strip(),
            "gpu_count": gpu_count,
            "partition": self.query_one("#partition", Input).value.strip(),
            "node_type": self.query_one("#node_type", Input).value.strip(),
            "notes": self.query_one("#notes", Input).value.strip(),
            "is_cluster": bool(cluster_name),  # True if cluster is selected
        }
        self.dismiss(data)
