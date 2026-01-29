from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from textual.widgets import Input, ListItem, ListView, Select, Static, TextArea

from ..models import Artifact

if TYPE_CHECKING:
    from ..tui import BAApp


class IdeaArtifactMixin:
    """Mixin for idea submission and artifact management."""

    _artifact_entries: list[Artifact]
    _selected_artifact_index: Optional[int]

    def _submit_idea(self: "BAApp") -> None:
        title = self.query_one("#idea_title", Input).value.strip()
        priority = self.query_one("#idea_priority", Select).value
        problem = self.query_one("#idea_problem", TextArea).text.strip()
        approach = self.query_one("#idea_approach", TextArea).text.strip()
        if not title:
            self.notify("Idea title is required", severity="error")
            return
        self._store_ui_state()
        self.exit(
            {
                "action": "idea",
                "data": {
                    "title": title,
                    "priority": str(priority),
                    "problem": problem,
                    "approach": approach,
                },
            }
        )

    def _refresh_artifact_list(self: "BAApp") -> None:
        try:
            list_view = self.query_one("#artifact_list", ListView)
        except Exception:
            return
        list_view.clear()
        for idx, artifact in enumerate(self._artifact_entries):
            label = f"{artifact.path} [{artifact.status}] ({artifact.type})"
            list_view.append(ListItem(Static(label), id=f"artifact-{idx}"))

    def _add_artifact(self: "BAApp") -> None:
        path = self.query_one("#artifact_path", Input).value.strip()
        artifact_type = (
            self.query_one("#artifact_type", Input).value.strip() or "unknown"
        )
        status = self.query_one("#artifact_status", Select).value or "draft"
        if not path:
            self.notify("Artifact path is required", severity="error")
            return
        artifact = Artifact(path=path, type=artifact_type, status=str(status))
        self._artifact_entries.append(artifact)
        self.query_one("#artifact_path", Input).value = ""
        self.query_one("#artifact_type", Input).value = ""
        self._refresh_artifact_list()

    def _update_artifact_status(self: "BAApp") -> None:
        if self._selected_artifact_index is None:
            self.notify("Select an artifact to update", severity="warning")
            return
        status = self.query_one("#artifact_update_status", Select).value
        artifact = self._artifact_entries[self._selected_artifact_index]
        artifact.status = str(status)
        artifact.updated = date.today()
        self._artifact_entries[self._selected_artifact_index] = artifact
        self._refresh_artifact_list()

    def _submit_artifact(self: "BAApp") -> None:
        self._store_ui_state()
        self.exit(
            {
                "action": "artifact",
                "artifacts": [artifact for artifact in self._artifact_entries],
            }
        )
