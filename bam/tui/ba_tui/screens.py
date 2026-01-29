from __future__ import annotations

from datetime import date

import pendulum
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    DirectoryTree,
    Input,
    Label,
    OptionList,
    Select,
    Static,
)

from .styles import (
    CHANNEL_MODAL_CSS,
    COLLABORATOR_MODAL_CSS,
    CUSTOM_INPUT_MODAL_CSS,
    DATASET_MODAL_CSS,
    DIRECTORY_PICKER_CSS,
    EXIT_CONFIRM_CSS,
    HARDWARE_MODAL_CSS,
    MILESTONE_MODAL_CSS,
    SESSION_MODAL_CSS,
    NEW_MANIFEST_CONFIRM_CSS,
    RESET_CONFIRM_CSS,
)

from textual.widgets.option_list import Option
from .widgets import DateSelect


class ExitConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm exit and optionally save."""

    BINDINGS = [
        Binding("s", "select_save", "Save & Exit", show=True),
        Binding("e", "select_exit", "Exit", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = EXIT_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Save changes before exit?")
            with Horizontal(id="button_row"):
                yield Button("Save & Exit (S)", id="save", variant="success")
                yield Button("Exit (E)", id="discard", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_save(self) -> None:
        """Handle S key press."""
        self.dismiss("save")

    def action_select_exit(self) -> None:
        """Handle E key press."""
        self.dismiss("discard")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")


class NewManifestConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm creating a new manifest."""

    BINDINGS = [
        Binding("d", "select_discard", "Discard", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = NEW_MANIFEST_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Discard current settings and start new?")
            with Horizontal(id="button_row"):
                yield Button("Discard (D)", id="discard", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_discard(self) -> None:
        """Handle D key press."""
        self.dismiss("discard")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")


class ResetConfirmScreen(ModalScreen[str]):
    """Modal screen to confirm resetting/reloading manifest from disk."""

    BINDINGS = [
        Binding("r", "select_reset", "Reset", show=True),
        Binding("c", "select_cancel", "Cancel", show=True),
    ]

    CSS = RESET_CONFIRM_CSS

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Discard unsaved changes and reload manifest?")
            with Horizontal(id="button_row"):
                yield Button("Reset (R)", id="reset", variant="error")
                yield Button("Cancel (C)", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_select_reset(self) -> None:
        """Handle R key press."""
        self.dismiss("reset")

    def action_select_cancel(self) -> None:
        """Handle C key press."""
        self.dismiss("cancel")


class DirectoryPickerScreen(ModalScreen[str]):
    """Modal directory picker using DirectoryTree."""

    CSS = DIRECTORY_PICKER_CSS

    def __init__(self, start_path: Path) -> None:
        super().__init__()
        self._start_path = start_path
        self._selected_path = str(start_path)

    def compose(self) -> ComposeResult:
        with Vertical(id="picker"):
            yield Static("Select a directory (click to select, Enter to expand)")
            yield DirectoryTree(self._start_path, id="dir_tree")
            yield Static(self._selected_path, id="selected_path")
            with Horizontal(id="picker_buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Select", id="select", variant="success")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle when a directory is clicked/selected in the tree."""
        self._selected_path = str(event.path)
        self.query_one("#selected_path", Static).update(
            f"Selected: {self._selected_path}"
        )

    def on_tree_node_highlighted(self, event) -> None:
        """Handle when a node is highlighted (cursor moved to it)."""
        if hasattr(event, "node") and event.node.data:
            path = (
                event.node.data.path
                if hasattr(event.node.data, "path")
                else str(event.node.data)
            )
            self._selected_path = str(path)
            self.query_one("#selected_path", Static).update(
                f"Selected: {self._selected_path}"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select":
            self.dismiss(self._selected_path)
        else:
            self.dismiss("")


class CollaboratorModal(ModalScreen[dict[str, str] | None]):
    """Modal to add or edit a collaborator."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = COLLABORATOR_MODAL_CSS

    def __init__(
        self,
        role_options: list[tuple[str, str]],
        initial_data: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.role_options = role_options
        self.initial_data = initial_data or {}

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

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

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

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

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


class ChannelModal(ModalScreen[dict[str, str] | None]):
    """Modal to add or edit an imaging channel."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = CHANNEL_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}

    def compose(self) -> ComposeResult:
        title = "Edit Channel" if self.initial_data else "Add Channel"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    self.initial_data.get("name", ""),
                    id="name",
                    placeholder="e.g., DAPI, GFP",
                )

            with Horizontal(classes="form-row"):
                yield Label("Fluorophore:")
                yield Input(
                    self.initial_data.get("fluorophore", ""),
                    id="fluorophore",
                    placeholder="e.g., DAPI, Alexa488",
                )

            with Horizontal(classes="form-row"):
                yield Label("Excitation (nm):")
                yield Input(
                    self.initial_data.get("excitation_nm", ""),
                    id="excitation_nm",
                    placeholder="e.g., 405",
                )

            with Horizontal(classes="form-row"):
                yield Label("Emission (nm):")
                yield Input(
                    self.initial_data.get("emission_nm", ""),
                    id="emission_nm",
                    placeholder="e.g., 461",
                )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Channel name is required", severity="error")
            return

        data = {
            "name": name,
            "fluorophore": self.query_one("#fluorophore", Input).value.strip(),
            "excitation_nm": self.query_one("#excitation_nm", Input).value.strip(),
            "emission_nm": self.query_one("#emission_nm", Input).value.strip(),
        }
        self.dismiss(data)


class HardwareModal(ModalScreen[dict[str, str | bool] | None]):
    """Modal to add or edit a hardware profile."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = HARDWARE_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, str | bool] | None = None,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}

    def compose(self) -> ComposeResult:
        title = "Edit Hardware" if self.initial_data else "Add Hardware"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")

            with Horizontal(classes="form-row"):
                yield Label("Name*:")
                yield Input(
                    str(self.initial_data.get("name", "")),
                    id="name",
                    placeholder="e.g., local, cluster-gpu",
                )

            with Horizontal(classes="form-row"):
                yield Label("CPU:")
                yield Input(
                    str(self.initial_data.get("cpu", "")),
                    id="cpu",
                    placeholder="e.g., Intel i9, AMD EPYC",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cores:")
                yield Input(
                    str(self.initial_data.get("cores", "")),
                    id="cores",
                    placeholder="e.g., 16",
                )

            with Horizontal(classes="form-row"):
                yield Label("RAM:")
                yield Input(
                    str(self.initial_data.get("ram", "")),
                    id="ram",
                    placeholder="e.g., 64 GB",
                )

            with Horizontal(classes="form-row"):
                yield Label("GPU:")
                yield Input(
                    str(self.initial_data.get("gpu", "")),
                    id="gpu",
                    placeholder="e.g., RTX 4090",
                )

            with Horizontal(classes="form-row"):
                yield Label("Notes:")
                yield Input(
                    str(self.initial_data.get("notes", "")),
                    id="notes",
                    placeholder="Optional",
                )

            with Horizontal(classes="form-row"):
                yield Label("Cluster:")
                yield Checkbox(
                    "Yes",
                    bool(self.initial_data.get("is_cluster", False)),
                    id="is_cluster",
                )

            with Horizontal(classes="form-row"):
                yield Label("Partition:")
                yield Input(
                    str(self.initial_data.get("partition", "")),
                    id="partition",
                    placeholder="e.g., gpu, long",
                )

            with Horizontal(classes="form-row"):
                yield Label("Node type:")
                yield Input(
                    str(self.initial_data.get("node_type", "")),
                    id="node_type",
                    placeholder="e.g., a100, cpu",
                )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        data = {
            "name": name,
            "cpu": self.query_one("#cpu", Input).value.strip(),
            "cores": self.query_one("#cores", Input).value.strip(),
            "ram": self.query_one("#ram", Input).value.strip(),
            "gpu": self.query_one("#gpu", Input).value.strip(),
            "notes": self.query_one("#notes", Input).value.strip(),
            "is_cluster": bool(self.query_one("#is_cluster", Checkbox).value),
            "partition": self.query_one("#partition", Input).value.strip(),
            "node_type": self.query_one("#node_type", Input).value.strip(),
        }
        self.dismiss(data)


class CustomInputModal(ModalScreen[list[str] | None]):
    """Modal to enter comma-separated values."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = CUSTOM_INPUT_MODAL_CSS

    def __init__(self, title: str | None, placeholder: str = "") -> None:
        super().__init__()
        self.title = title
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self.title or "", classes="header")
            with Horizontal(classes="form-row"):
                yield Input(
                    "",
                    id="custom_input",
                    placeholder=self.placeholder or "Comma-separated",
                )
            with Horizontal(id="buttons"):
                yield Button("Add (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#custom_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        text = self.query_one("#custom_input", Input).value.strip()
        if not text:
            self.dismiss(None)
            return
        items = [item.strip() for item in text.split(",") if item.strip()]
        self.dismiss(items)


class DatasetModal(ModalScreen[dict[str, object] | None]):
    """Modal to add or edit a dataset."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = DATASET_MODAL_CSS

    def __init__(
        self,
        endpoint_options: list[tuple[str, str]],
        format_options: list[tuple[str, str]],
        initial_data: dict[str, object] | None = None,
    ) -> None:
        super().__init__()
        self.endpoint_options = endpoint_options
        self.format_options = format_options
        self.initial_data = initial_data or {}
        self._browse_target: str | None = None
        self._active_path_input: str | None = None
        self._path_suggestions_visible: dict[str, bool] = {
            "source": False,
            "local": False,
        }

    def compose(self) -> ComposeResult:
        title = "Edit Dataset" if self.initial_data else "Add Dataset"
        endpoint_values = {value for _, value in self.endpoint_options}
        format_values = {value for _, value in self.format_options}
        initial_endpoint = str(self.initial_data.get("endpoint", "")).strip()
        initial_format = str(self.initial_data.get("format", "")).strip()
        endpoint_value = Select.BLANK
        format_value = Select.BLANK
        endpoint_custom = ""
        format_custom = ""
        show_endpoint_custom = False
        show_format_custom = False

        if initial_endpoint:
            if initial_endpoint in endpoint_values:
                endpoint_value = initial_endpoint
                show_endpoint_custom = initial_endpoint.lower() == "other"
            else:
                endpoint_value = "Other" if "Other" in endpoint_values else Select.BLANK
                endpoint_custom = initial_endpoint
                show_endpoint_custom = True

        is_local_endpoint = str(endpoint_value).lower() == "local"

        if initial_format:
            if initial_format in format_values:
                format_value = initial_format
                show_format_custom = initial_format.lower() == "other"
            else:
                format_value = "other" if "other" in format_values else Select.BLANK
                format_custom = initial_format
                show_format_custom = True

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("Name*:")
                    yield Input(
                        str(self.initial_data.get("name", "")),
                        id="name",
                        placeholder="Dataset name",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Endpoint:")
                    yield Select(
                        self.endpoint_options,
                        value=endpoint_value,
                        allow_blank=True,
                        id="endpoint",
                    )

                with Horizontal(
                    id="endpoint_custom_row",
                    classes="form-row" + ("" if show_endpoint_custom else " hidden"),
                ):
                    yield Label("Custom endpoint:")
                    yield Input(
                        endpoint_custom,
                        id="endpoint_custom",
                        placeholder="Enter endpoint",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Locally mounted:")
                    yield Checkbox(
                        "Yes",
                        True
                        if is_local_endpoint
                        else bool(self.initial_data.get("locally_mounted", False)),
                        id="locally_mounted",
                        disabled=is_local_endpoint,
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Source path:")
                    yield Input(
                        str(self.initial_data.get("source", "")),
                        id="source",
                        placeholder="Original data path",
                    )
                    yield Button("Browse", id="browse_source", variant="primary")
                yield OptionList(id="source_suggestions")

                with Horizontal(classes="form-row"):
                    yield Label("Local path:")
                    yield Input(
                        str(self.initial_data.get("local", "")),
                        id="local",
                        placeholder="Local cache path",
                    )
                    yield Button("Browse", id="browse_local", variant="primary")
                yield OptionList(id="local_suggestions")

                with Horizontal(classes="form-row"):
                    yield Label("Description:")
                    yield Input(
                        str(self.initial_data.get("description", "")),
                        id="description",
                        placeholder="What the data contains",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Format:")
                    yield Select(
                        self.format_options,
                        value=format_value,
                        allow_blank=True,
                        id="format",
                    )

                with Horizontal(
                    id="format_custom_row",
                    classes="form-row" + ("" if show_format_custom else " hidden"),
                ):
                    yield Label("Custom format:")
                    yield Input(
                        format_custom,
                        id="format_custom",
                        placeholder="Enter format",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Raw size:")
                    yield Input(
                        str(self.initial_data.get("raw_size_gb", "")),
                        id="raw_size_gb",
                        placeholder="Approximate raw data size",
                    )
                    yield Select(
                        [("GB", "gb"), ("TB", "tb")],
                        value=str(self.initial_data.get("raw_size_unit", "gb")),
                        id="raw_size_unit",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Compression:")
                    yield Checkbox(
                        "Yes",
                        bool(self.initial_data.get("compressed", False)),
                        id="compressed",
                    )

                with Horizontal(
                    id="uncompressed_row",
                    classes="form-row"
                    + ("" if self.initial_data.get("compressed", False) else " hidden"),
                ):
                    yield Label("Uncompressed size:")
                    yield Input(
                        str(self.initial_data.get("uncompressed_size_gb", "")),
                        id="uncompressed_size_gb",
                        placeholder="Uncompressed size",
                    )
                    yield Select(
                        [("GB", "gb"), ("TB", "tb")],
                        value=str(
                            self.initial_data.get("uncompressed_size_unit", "gb")
                        ),
                        id="uncompressed_size_unit",
                    )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
            return
        if event.button.id == "browse_source":
            self._open_directory_picker("source")
            return
        if event.button.id == "browse_local":
            self._open_directory_picker("local")
            return
        self.dismiss(None)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "endpoint":
            value = event.value
            try:
                row = self.query_one("#endpoint_custom_row", Horizontal)
                if value and str(value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
            try:
                checkbox = self.query_one("#locally_mounted", Checkbox)
                if value and str(value).lower() == "local":
                    checkbox.value = True
                    checkbox.disabled = True
                else:
                    checkbox.disabled = False
            except Exception:
                pass
        elif event.select.id == "format":
            value = event.value
            try:
                row = self.query_one("#format_custom_row", Horizontal)
                if value and str(value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "locally_mounted":
            # Hide source suggestions when locally_mounted is unchecked
            if not event.value:
                self._hide_path_suggestions("source")
            return
        if event.checkbox.id == "compressed":
            try:
                row = self.query_one("#uncompressed_row", Horizontal)
                if event.value:
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
            return

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()
        elif event.key in ("down", "up"):
            try:
                if self._active_path_input in ("source", "local"):
                    suggestions = self.query_one(
                        f"#{self._active_path_input}_suggestions", OptionList
                    )
                    if event.key == "down":
                        focused = self.focused
                        if focused and getattr(focused, "id", "") == self._active_path_input:
                            suggestions.focus()
                            if suggestions.option_count > 0:
                                suggestions.highlighted = 0
                            event.prevent_default()
                            event.stop()
                    elif event.key == "up":
                        if self.focused == suggestions and suggestions.highlighted == 0:
                            input_widget = self.query_one(
                                f"#{self._active_path_input}", Input
                            )
                            input_widget.focus()
                            event.prevent_default()
                            event.stop()
            except Exception:
                pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "source":
            # Source path: only show suggestions when locally_mounted is checked
            if self.focused != event.input:
                self._hide_path_suggestions(event.input.id)
                return
            try:
                locally_mounted = self.query_one("#locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_path_suggestions(event.input.id, event.value)
                else:
                    self._hide_path_suggestions(event.input.id)
            except Exception:
                self._hide_path_suggestions(event.input.id)
        elif event.input.id == "local":
            # Local path: always show suggestions
            if self.focused != event.input:
                self._hide_path_suggestions(event.input.id)
                return
            self._update_path_suggestions(event.input.id, event.value)

    def on_input_focused(self, event: Input.Focused) -> None:
        if event.input.id == "source":
            # Source path: only show suggestions when locally_mounted is checked
            try:
                locally_mounted = self.query_one("#locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_path_suggestions(event.input.id, event.input.value)
            except Exception:
                pass
        elif event.input.id == "local":
            # Local path: always show suggestions
            self._update_path_suggestions(event.input.id, event.input.value)

    def on_input_blurred(self, event: Input.Blurred) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id in ("source", "local"):
            focused = self.focused
            # Don't hide if focus moved to suggestions list
            if focused and getattr(focused, "id", "") == f"{input_id}_suggestions":
                return
            self._hide_path_suggestions(input_id)

    def on_option_list_blurred(self, event: OptionList.Blurred) -> None:
        if event.option_list.id in ("source_suggestions", "local_suggestions"):
            input_id = "source" if event.option_list.id == "source_suggestions" else "local"
            focused = self.focused
            # Don't hide if focus moved back to input
            if focused and getattr(focused, "id", "") == input_id:
                return
            self._hide_path_suggestions(input_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id in ("source_suggestions", "local_suggestions"):
            input_id = "source" if event.option_list.id == "source_suggestions" else "local"
            try:
                input_widget = self.query_one(f"#{input_id}", Input)
                selected = str(event.option.prompt)
                input_widget.value = selected
                self._hide_path_suggestions(input_id)
                input_widget.focus()
                try:
                    input_widget.cursor_position = len(selected)
                except Exception:
                    pass
            except Exception:
                pass

    def _open_directory_picker(self, target_input_id: str) -> None:
        self._browse_target = target_input_id
        start = Path.home()
        self.app.push_screen(DirectoryPickerScreen(start), self._handle_directory_pick)

    def _handle_directory_pick(self, path: str | None) -> None:
        if not path or not self._browse_target:
            self._browse_target = None
            return
        try:
            input_widget = self.query_one(f"#{self._browse_target}", Input)
            input_widget.value = path
        except Exception:
            pass
        self._browse_target = None

    def _update_path_suggestions(self, input_id: str, current_value: str) -> None:
        try:
            suggestions = self.query_one(f"#{input_id}_suggestions", OptionList)
            suggestions.clear_options()

            if not current_value:
                self._hide_path_suggestions(input_id)
                return

            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()

            if not search_dir.exists():
                self._hide_path_suggestions(input_id)
                return

            entries = []
            try:
                for entry in sorted(search_dir.iterdir()):
                    if entry.is_dir():
                        name = entry.name
                        if not prefix or name.lower().startswith(prefix):
                            entries.append(str(entry))
                            if len(entries) >= 10:
                                break
            except PermissionError:
                pass

            if entries:
                for entry in entries:
                    suggestions.add_option(Option(entry))
                suggestions.add_class("visible")
                self._path_suggestions_visible[input_id] = True
                self._active_path_input = input_id
            else:
                self._hide_path_suggestions(input_id)
        except Exception:
            self._hide_path_suggestions(input_id)

    def _hide_path_suggestions(self, input_id: str) -> None:
        try:
            suggestions = self.query_one(f"#{input_id}_suggestions", OptionList)
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._path_suggestions_visible[input_id] = False
        except Exception:
            pass

    def _submit(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        endpoint_value = self.query_one("#endpoint", Select).value
        endpoint_custom = self.query_one("#endpoint_custom", Input).value.strip()
        endpoint = ""
        if endpoint_value and endpoint_value != Select.BLANK:
            endpoint = str(endpoint_value)
        if endpoint.lower() == "other" and endpoint_custom:
            endpoint = endpoint_custom
        elif not endpoint and endpoint_custom:
            endpoint = endpoint_custom

        format_value = self.query_one("#format", Select).value
        format_custom = self.query_one("#format_custom", Input).value.strip()
        data_format = ""
        if format_value and format_value != Select.BLANK:
            data_format = str(format_value)
        if data_format.lower() == "other" and format_custom:
            data_format = format_custom
        elif not data_format and format_custom:
            data_format = format_custom

        data = {
            "name": name,
            "endpoint": endpoint,
            "locally_mounted": bool(self.query_one("#locally_mounted", Checkbox).value),
            "source": self.query_one("#source", Input).value.strip(),
            "local": self.query_one("#local", Input).value.strip(),
            "description": self.query_one("#description", Input).value.strip(),
            "format": data_format,
            "raw_size_gb": self.query_one("#raw_size_gb", Input).value.strip(),
            "raw_size_unit": str(self.query_one("#raw_size_unit", Select).value or ""),
            "compressed": bool(self.query_one("#compressed", Checkbox).value),
            "uncompressed_size_gb": self.query_one(
                "#uncompressed_size_gb", Input
            ).value.strip(),
            "uncompressed_size_unit": str(
                self.query_one("#uncompressed_size_unit", Select).value or ""
            ),
        }
        self.dismiss(data)


class MilestoneModal(ModalScreen[dict[str, object] | None]):
    """Modal to add or edit a milestone."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = MILESTONE_MODAL_CSS

    STATUS_OPTIONS = [
        ("Pending", "pending"),
        ("In Progress", "in-progress"),
        ("Completed", "completed"),
        ("Delayed", "delayed"),
        ("Cancelled", "cancelled"),
    ]

    def __init__(self, initial_data: dict[str, object] | None = None) -> None:
        super().__init__()
        self.initial_data = initial_data or {}

    def compose(self) -> ComposeResult:
        title = "Edit Milestone" if self.initial_data else "Add Milestone"
        target_value = self._coerce_date(self.initial_data.get("target_date"))
        actual_value = self._coerce_date(self.initial_data.get("actual_date"))

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                with Horizontal(classes="form-row"):
                    yield Label("Name*:")
                    yield Input(
                        str(self.initial_data.get("name", "")),
                        id="milestone_name",
                        placeholder="Milestone name",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Target date:")
                    yield DateSelect(
                        "#milestone_datepicker_mount",
                        date=target_value,
                        id="milestone_target_date",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Actual date:")
                    yield DateSelect(
                        "#milestone_datepicker_mount",
                        date=actual_value,
                        id="milestone_actual_date",
                    )

                yield Static("", id="milestone_datepicker_mount")

                with Horizontal(classes="form-row"):
                    yield Label("Status:")
                    yield Select(
                        self.STATUS_OPTIONS,
                        value=str(self.initial_data.get("status", "pending")),
                        id="milestone_status",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notes:")
                    yield Input(
                        str(self.initial_data.get("notes", "")),
                        id="milestone_notes",
                        placeholder="Optional",
                    )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        name = self.query_one("#milestone_name", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="error")
            return

        target = self.query_one("#milestone_target_date", DateSelect).value
        actual = self.query_one("#milestone_actual_date", DateSelect).value
        if target:
            target = target.date()
        if actual:
            actual = actual.date()
        status_value = self.query_one("#milestone_status", Select).value
        status = str(status_value) if status_value else "pending"

        data = {
            "name": name,
            "target_date": target,
            "actual_date": actual,
            "status": status,
            "notes": self.query_one("#milestone_notes", Input).value.strip(),
        }
        self.dismiss(data)

    @staticmethod
    def _coerce_date(value: object) -> pendulum.DateTime | None:
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, date):
            return pendulum.datetime(value.year, value.month, value.day)
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                return parsed if isinstance(parsed, pendulum.DateTime) else None
            except Exception:
                return None
        return None


class AcquisitionSessionModal(ModalScreen[dict[str, object] | None]):
    """Modal to add or edit an acquisition session."""

    BINDINGS = [
        Binding("ctrl+a", "save", "Save", show=True, priority=True),
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
    ]

    CSS = SESSION_MODAL_CSS

    MODALITY_OPTIONS = [
        ("Confocal", "confocal"),
        ("Widefield", "widefield"),
        ("Light-sheet", "light-sheet"),
        ("Two-photon", "two-photon"),
        ("Super-resolution", "super-resolution"),
        ("EM", "em"),
        ("Brightfield", "brightfield"),
        ("Phase contrast", "phase-contrast"),
        ("DIC", "dic"),
        ("Other", "other"),
    ]

    def __init__(self, initial_data: dict[str, object] | None = None) -> None:
        super().__init__()
        self.initial_data = initial_data or {}

    def compose(self) -> ComposeResult:
        title = "Edit Imaging Session" if self.initial_data else "Add Imaging Session"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                imaging_date = self._coerce_date(self.initial_data.get("imaging_date"))
                yield Static("", id="session_datepicker_mount")
                with Horizontal(classes="form-row"):
                    yield Label("Imaging date:")
                    yield DateSelect(
                        "#session_datepicker_mount",
                        date=imaging_date,
                        id="session_imaging_date",
                    )
                with Horizontal(classes="form-row"):
                    yield Label("Microscope:")
                    yield Input(
                        str(self.initial_data.get("microscope", "")),
                        id="session_microscope",
                        placeholder="Microscope model/name",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Modality:")
                    modality_value = self.initial_data.get("modality")
                    yield Select(
                        self.MODALITY_OPTIONS,
                        value=modality_value if modality_value else Select.BLANK,
                        allow_blank=True,
                        id="session_modality",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Objective:")
                    yield Input(
                        str(self.initial_data.get("objective", "")),
                        id="session_objective",
                        placeholder="e.g., 40x/1.3 Oil",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel X (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_x", "")),
                        id="session_voxel_x",
                        placeholder="X dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel Y (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_y", "")),
                        id="session_voxel_y",
                        placeholder="Y dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel Z (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_z", "")),
                        id="session_voxel_z",
                        placeholder="Z dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Time interval (s):")
                    yield Input(
                        str(self.initial_data.get("time_interval_s", "")),
                        id="session_time_interval",
                        placeholder="For timelapse imaging",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notes:")
                    yield Input(
                        str(self.initial_data.get("notes", "")),
                        id="session_notes",
                        placeholder="Optional",
                    )

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                yield Button("Cancel (Esc)", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self._submit()
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_key(self, event) -> None:
        if event.key == "ctrl+a":
            self.action_save()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            self.action_cancel()
            event.prevent_default()
            event.stop()

    def _submit(self) -> None:
        microscope = self.query_one("#session_microscope", Input).value.strip()
        modality = self.query_one("#session_modality", Select).value
        modality_value = "" if modality in (None, Select.BLANK) else str(modality)

        data: dict[str, object] = {
            "imaging_date": self.query_one("#session_imaging_date", DateSelect).value,
            "microscope": microscope,
            "modality": modality_value,
            "objective": self.query_one("#session_objective", Input).value.strip(),
            "voxel_x": self.query_one("#session_voxel_x", Input).value.strip(),
            "voxel_y": self.query_one("#session_voxel_y", Input).value.strip(),
            "voxel_z": self.query_one("#session_voxel_z", Input).value.strip(),
            "time_interval_s": self.query_one(
                "#session_time_interval", Input
            ).value.strip(),
            "notes": self.query_one("#session_notes", Input).value.strip(),
        }
        self.dismiss(data)

    @staticmethod
    def _coerce_date(value: object) -> pendulum.DateTime | None:
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, date):
            return pendulum.datetime(value.year, value.month, value.day)
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                if isinstance(parsed, pendulum.DateTime):
                    return parsed
                return None
            except Exception:
                return None
        return None
