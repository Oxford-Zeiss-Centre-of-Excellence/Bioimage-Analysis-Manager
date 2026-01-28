"""Hub tab: cross-project registry settings."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    Button,
    Checkbox,
    Input,
    Label,
    Static,
    TabPane,
)


def compose_hub_tab(app: object) -> ComposeResult:
    """Compose the Hub tab with registry settings."""
    with TabPane("Hub (F5)", id="hub"):
        with VerticalScroll(id="hub_form"):
            yield Static("Cross-Project Registry", classes="section-header")
            yield Static(
                "The hub registers this project with ~/.ba-hub for cross-project queries.",
                classes="form-hint",
            )

            with Horizontal(classes="form-row"):
                yield Label("")
                yield Checkbox(
                    "Registered with hub",
                    app._defaults.get("hub_registered", False),
                    id="hub_registered",
                    disabled=True,
                )

            with Horizontal(classes="form-row"):
                yield Label("Registered:")
                yield Input(
                    app._defaults.get("hub_registered_date", ""),
                    placeholder="Registration date",
                    id="hub_registered_date",
                    disabled=True,
                )

            with Horizontal(classes="form-row"):
                yield Label("Last sync:")
                yield Input(
                    app._defaults.get("hub_last_sync", ""),
                    placeholder="Last synchronization",
                    id="hub_last_sync",
                    disabled=True,
                )

            with Horizontal(classes="form-row"):
                yield Button("Register Project", id="hub_register", variant="success")
                yield Button("Sync Now", id="hub_sync", variant="primary")
                yield Button("Unregister", id="hub_unregister", variant="error")
