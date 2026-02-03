"""Idea tab: markdown idea file management."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, TabPane


def compose_idea_tab(app: object) -> ComposeResult:
    """Compose the Idea tab with placeholder for alpha release."""
    del app  # unused for placeholder
    with TabPane("Idea (F7)", id="idea"):
        with Container(id="idea_placeholder"):
            yield Static("Feature arriving soon...", classes="placeholder-title")
            yield Static(
                "Markdown-based idea capture and management",
                classes="placeholder-description",
            )


# =============================================================================
# Original Idea Tab Implementation (Sprint 2)
# =============================================================================
# The code below is preserved for future development.
# Uncomment and restore when Idea feature is ready.
#
# from textual.containers import Horizontal, Vertical, VerticalScroll
# from textual.widgets import Button, Input, ListView, Select, TextArea
#
# def compose_idea_tab_full(app: object) -> ComposeResult:
#     """Compose the Idea tab for managing markdown idea files."""
#     with TabPane("Idea (F7)", id="idea"):
#         with VerticalScroll():
#             with Horizontal():
#                 # Left: List of existing ideas
#                 with Vertical(id="idea_list_panel"):
#                     yield Static("Existing Ideas")
#                     yield ListView(id="idea_list")
#                     yield Button("Refresh", id="idea_refresh", variant="default")
#
#                 # Right: Create/Edit form
#                 with Vertical(id="idea_form"):
#                     yield Static("Create/Edit Idea", classes="section-header")
#                     yield Input(
#                         app._idea_title, placeholder="Idea title", id="idea_title"
#                     )
#                     yield Select(
#                         [("High", "high"), ("Medium", "medium"), ("Low", "low")],
#                         value="medium",
#                         id="idea_priority",
#                     )
#
#                     yield Static("Problem")
#                     yield TextArea(id="idea_problem")
#
#                     yield Static("Proposed Approach")
#                     yield TextArea(id="idea_approach")
#
#                     with Horizontal(classes="form-row"):
#                         yield Button("Save Idea", id="idea_save", variant="success")
#                         yield Button("New", id="idea_new", variant="primary")
#                         yield Button("Delete", id="idea_delete", variant="error")
