"""Idea tab: markdown idea file management."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, ListView, Select, Static, TabPane, TextArea


def compose_idea_tab(app: object) -> ComposeResult:
    """Compose the Idea tab for managing markdown idea files."""
    with TabPane("Idea (F7)", id="idea"):
        with Horizontal():
            # Left: List of existing ideas
            with Vertical(id="idea_list_panel"):
                yield Static("Existing Ideas")
                yield ListView(id="idea_list")
                yield Button("Refresh", id="idea_refresh", variant="default")

            # Right: Create/Edit form
            with Vertical(id="idea_form"):
                yield Static("Create/Edit Idea", classes="section-header")
                yield Input(app._idea_title, placeholder="Idea title", id="idea_title")
                yield Select(
                    [("High", "high"), ("Medium", "medium"), ("Low", "low")],
                    value="medium",
                    id="idea_priority",
                )

                yield Static("Problem")
                yield TextArea(id="idea_problem")

                yield Static("Proposed Approach")
                yield TextArea(id="idea_approach")

                with Horizontal(classes="form-row"):
                    yield Button("Save Idea", id="idea_save", variant="success")
                    yield Button("New", id="idea_new", variant="primary")
                    yield Button("Delete", id="idea_delete", variant="error")
