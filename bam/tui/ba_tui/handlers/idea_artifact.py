from __future__ import annotations

from typing import Any, Callable

from textual.widgets import Input, Select, TextArea


class IdeaArtifactMixin:
    """Mixin for idea submission."""

    def __getattr__(self, name: str):
        raise AttributeError(name)

    query_one: Callable[..., Any]
    notify: Callable[..., Any]
    _store_ui_state: Callable[..., Any]
    exit: Callable[..., Any]

    def _submit_idea(self) -> None:
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
