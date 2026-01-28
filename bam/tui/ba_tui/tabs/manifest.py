from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, TabbedContent, TabPane, TextArea


def compose_manifest_tab(_: object) -> ComposeResult:
    with TabPane("Manifest (F5)", id="manifest"):
        with VerticalScroll():
            with TabbedContent(id="manifest_sections"):
                for section in (
                    "project",
                    "people",
                    "tags",
                    "data",
                    "acquisition",
                    "tools",
                    "billing",
                    "quality",
                    "publication",
                    "archive",
                    "timeline",
                    "artifacts",
                    "hub",
                ):
                    with TabPane(section.title(), id=f"manifest_{section}"):
                        yield TextArea(id=f"manifest_{section}_area")
            yield Static("", id="manifest_error")
