from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import TabbedContent

if TYPE_CHECKING:
    from ..tui import BAApp


class TabNavigationMixin:
    """Mixin for tab navigation actions."""

    def action_show_tab_1(self: "BAApp") -> None:
        self._set_tab("setup")

    def action_show_tab_2(self: "BAApp") -> None:
        self._set_tab("science")

    def action_show_tab_3(self: "BAApp") -> None:
        self._set_tab("admin")

    def action_show_tab_4(self: "BAApp") -> None:
        self._set_tab("outputs")

    def action_show_tab_5(self: "BAApp") -> None:
        self._set_tab("hub")

    def action_show_tab_6(self: "BAApp") -> None:
        self._set_tab("log")

    def action_show_tab_7(self: "BAApp") -> None:
        self._set_tab("idea")

    def action_next_tab(self: "BAApp") -> None:
        self._cycle_tab(1)

    def action_prev_tab(self: "BAApp") -> None:
        self._cycle_tab(-1)

    def _set_tab(self: "BAApp", tab_id: str) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        tabbed.active = tab_id

    def _cycle_tab(self: "BAApp", delta: int) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        tabs = ["setup", "science", "admin", "outputs", "hub", "log", "idea"]
        try:
            current = tabs.index(tabbed.active)
        except ValueError:
            current = 0
        tabbed.active = tabs[(current + delta) % len(tabs)]
