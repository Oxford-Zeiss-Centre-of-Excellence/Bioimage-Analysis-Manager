from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, ListView, Select, Static, TabPane


def compose_artifact_tab(_: object) -> ComposeResult:
    with TabPane("Artifacts (F4)", id="artifact"):
        with Horizontal():
            with Vertical():
                yield Static("Artifacts")
                yield ListView(id="artifact_list")
            with Vertical():
                yield Input(placeholder="Artifact path", id="artifact_path")
                yield Input(placeholder="Artifact type", id="artifact_type")
                yield Select(
                    [
                        ("draft", "draft"),
                        ("ready", "ready"),
                        ("delivered", "delivered"),
                        ("archived", "archived"),
                    ],
                    id="artifact_status",
                )
                yield Button("Add Artifact", id="artifact_add", variant="success")
                yield Select(
                    [
                        ("draft", "draft"),
                        ("ready", "ready"),
                        ("delivered", "delivered"),
                        ("archived", "archived"),
                    ],
                    id="artifact_update_status",
                )
                yield Button("Update Status", id="artifact_update", variant="primary")
