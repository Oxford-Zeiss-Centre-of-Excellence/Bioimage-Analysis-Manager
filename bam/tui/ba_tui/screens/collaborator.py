from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, Select, Static

from ..styles import COLLABORATOR_MODAL_CSS
from .base import FormModal


class CollaboratorModal(FormModal):
    """Modal to add or edit a collaborator."""

    CSS = COLLABORATOR_MODAL_CSS

    def __init__(
        self,
        role_options: list[tuple[str, str]],
        initial_data: dict[str, str] | None = None,
        allow_remove: bool = False,
    ) -> None:
        super().__init__()
        self.role_options = role_options
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove

    def compose(self) -> ComposeResult:
        title = "Edit Collaborator" if self.initial_data else "Add Collaborator"
        option_values = {value for _, value in self.role_options}
        initial_role = str(self.initial_data.get("role", "")).strip()
        custom_role = ""
        role_value = Select.BLANK
        show_custom = False

        if initial_role:
            if initial_role in option_values:
                role_value = initial_role
                show_custom = initial_role.lower() == "other"
            else:
                role_value = "Other" if "Other" in option_values else Select.BLANK
                custom_role = initial_role
                show_custom = True
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    self.initial_data.get("name", ""), id="name", placeholder="Name"
                )

            with Horizontal(classes="form-row"):
                yield Label("Role:")
                yield Select(
                    self.role_options,
                    value=role_value,
                    allow_blank=True,
                    id="role",
                )

            with Horizontal(
                id="role_custom_row",
                classes="form-row" + ("" if show_custom else " hidden"),
            ):
                yield Label("Custom role:")
                yield Input(custom_role, id="role_custom", placeholder="Enter role")

            with Horizontal(classes="form-row"):
                yield Label("Email:")
                yield Input(
                    self.initial_data.get("email", ""), id="email", placeholder="Email"
                )

            with Horizontal(classes="form-row"):
                yield Label("Affiliation:")
                yield Input(
                    self.initial_data.get("affiliation", ""),
                    id="affiliation",
                    placeholder="Affiliation",
                )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "role":
            return
        try:
            row = self.query_one("#role_custom_row", Horizontal)
            value = event.value
            if value and str(value).lower() == "other":
                row.remove_class("hidden")
            else:
                row.add_class("hidden")
        except Exception:
            pass

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        selected_role = self.query_one("#role", Select).value
        custom_role = self.query_one("#role_custom", Input).value.strip()
        role_value = ""
        if selected_role and selected_role != Select.BLANK:
            role_value = str(selected_role)
        if role_value.lower() == "other" and custom_role:
            role_value = custom_role
        elif not role_value and custom_role:
            role_value = custom_role

        data = {
            "name": name,
            "role": role_value,
            "email": self.query_one("#email", Input).value.strip(),
            "affiliation": self.query_one("#affiliation", Input).value.strip(),
        }
        self.dismiss(data)
