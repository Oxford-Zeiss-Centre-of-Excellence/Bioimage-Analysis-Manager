from __future__ import annotations

from datetime import datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Callable, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListView,
    OptionList,
    Select,
    SelectionList,
    Static,
    TabbedContent,
    TextArea,
)
from textual.widgets.selection_list import Selection

import pendulum

from .handlers import (
    AcquisitionMixin,
    CollaboratorsMixin,
    DatasetsMixin,
    HardwareMixin,
    IdeaArtifactMixin,
    MethodPreviewMixin,
    MilestonesMixin,
    PersistenceMixin,
    SyncMixin,
    TabNavigationMixin,
    UIStateMixin,
    WorklogMixin,
)

from .config import (
    load_dataset_format_options,
    load_endpoint_options,
    load_role_options,
)
from .models import Artifact, LogEntry, Manifest
from .screens import (
    AcquisitionSessionModal,
    ChannelModal,
    CollaboratorModal,
    CustomInputModal,
    DatasetModal,
    DirectoryPickerScreen,
    ExitConfirmScreen,
    HardwareModal,
    MilestoneModal,
    NewManifestConfirmScreen,
    ResetConfirmScreen,
)
from .styles import APP_CSS
from .utils import detect_git_remote
from .tabs.admin import compose_admin_tab
from .tabs.hub import compose_hub_tab
from .tabs.idea import compose_idea_tab
from .tabs.log import compose_log_tab
from .tabs.outputs import compose_outputs_tab
from .tabs.science import compose_science_tab
from .tabs.setup import compose_setup_tab


class BAApp(
    CollaboratorsMixin,
    DatasetsMixin,
    AcquisitionMixin,
    MilestonesMixin,
    HardwareMixin,
    WorklogMixin,
    PersistenceMixin,
    SyncMixin,
    MethodPreviewMixin,
    IdeaArtifactMixin,
    UIStateMixin,
    TabNavigationMixin,
    App[dict[str, object] | None],
):
    CSS = APP_CSS

    BINDINGS = [
        Binding("ctrl+n", "new_manifest", "New", show=True, priority=True),
        Binding("ctrl+s", "save_current", "Save", show=True, priority=True),
        Binding("ctrl+r", "reset_manifest", "Reset", show=True, priority=True),
        Binding("ctrl+x", "exit_app", "Exit", show=True, priority=True),
        Binding("f1", "show_tab_1", "", show=False),
        Binding("f2", "show_tab_2", "", show=False),
        Binding("f3", "show_tab_3", "", show=False),
        Binding("f4", "show_tab_4", "", show=False),
        Binding("f5", "show_tab_5", "", show=False),
        Binding("f6", "show_tab_6", "", show=False),
        Binding("f7", "show_tab_7", "", show=False),
    ]

    def __init__(
        self,
        *,
        mode: str,
        recent_entries: list[str],
        project_root: Optional[Path] = None,
        project_name: str = "",
        analyst: str = "",
        data_enabled: bool = True,
        data_endpoint: str = "",
        data_source: str = "",
        data_local: str = "",
        locally_mounted: bool = False,
        worklog_entries: Optional[list[LogEntry]] = None,
        task_types: Optional[list[dict[str, str]]] = None,
        idea_title: str = "",
        artifacts: Optional[list[Artifact]] = None,
        manifest: Optional[Manifest] = None,
        initial_data: Optional[dict[str, object]] = None,
    ) -> None:
        super().__init__()
        self._mode = mode
        self._recent_entries = recent_entries
        self._project_root = project_root or Path.cwd()
        self._defaults = {
            "project_name": project_name,
            "analyst": analyst,
            "data_enabled": data_enabled,
        }
        if initial_data:
            self._defaults.update(initial_data)
        else:
            if any([data_endpoint, data_source, data_local]):
                self._defaults["datasets"] = [
                    {
                        "name": "dataset-1",
                        "endpoint": data_endpoint,
                        "source": data_source,
                        "local": data_local,
                        "locally_mounted": locally_mounted,
                    }
                ]
        self._init_error: Optional[Static] = None
        self._log_error: Optional[Static] = None
        self._syncing = False
        self._worklog_entries: list[LogEntry] = worklog_entries or []
        self._task_types = task_types or []
        self._idea_title = idea_title
        self._artifact_entries: list[Artifact] = artifacts or []
        self._manifest = manifest
        self._selected_active_index: Optional[int] = None
        self._selected_artifact_index: Optional[int] = None
        self._manifest_errors: Optional[Static] = None
        self._browse_target: Optional[str] = None
        self._active_method_input: Optional[str] = None
        self._method_path_suggestions_visible = False
        self._method_path_suggestions: Optional[OptionList] = None
        self._ui_state_path = Path.home() / ".config" / "bam" / "ui_state.yaml"
        self._hardware_profiles: list[dict[str, str | bool]] = []
        self._method_path: str = ""
        self._method_template_used: str = ""
        self._method_preview_path: str = ""
        self._method_preview_mtime: float | None = None
        self._selected_hardware_index: Optional[int] = None
        self._collaborator_rows: list[dict[str, str]] = []
        self._dataset_rows: list[dict[str, object]] = []
        self._milestone_rows: list[dict[str, object]] = []
        self._acquisition_rows: list[dict[str, object]] = []
        self._selected_acquisition_index: Optional[int] = None
        self._init_row_data()
        if self._defaults.get("method_path"):
            self._method_path = str(self._defaults.get("method_path"))

        self._channel_rows: list[dict[str, str]] = []
        self._init_channel_rows()

        version = "unknown"
        try:
            version = metadata.version("bam")
        except metadata.PackageNotFoundError:
            pass
        self.title = f"BAM - Bioimage Analysis Manager {version}"

    def _init_row_data(self) -> None:
        self._init_collaborator_rows()
        self._init_dataset_rows()
        self._init_acquisition_rows()
        self._init_milestone_rows()
        self._init_hardware_rows()

    def _init_collaborator_rows(self) -> None:
        collaborators = self._defaults.get("collaborators")
        if not isinstance(collaborators, list):
            return
        self._collaborator_rows = [
            {
                "name": str(item.get("name", "")) if isinstance(item, dict) else "",
                "role": str(item.get("role", "")) if isinstance(item, dict) else "",
                "email": str(item.get("email", "")) if isinstance(item, dict) else "",
                "affiliation": str(item.get("affiliation", ""))
                if isinstance(item, dict)
                else "",
            }
            for item in collaborators
        ]

    def _init_dataset_rows(self) -> None:
        datasets = self._defaults.get("datasets")
        if not isinstance(datasets, list):
            return
        self._dataset_rows = [
            {
                "name": str(item.get("name", "")) if isinstance(item, dict) else "",
                "endpoint": str(item.get("endpoint", ""))
                if isinstance(item, dict)
                else "",
                "source": str(item.get("source", "")) if isinstance(item, dict) else "",
                "local": str(item.get("local", "")) if isinstance(item, dict) else "",
                "locally_mounted": bool(item.get("locally_mounted", False))
                if isinstance(item, dict)
                else False,
                "description": str(item.get("description", ""))
                if isinstance(item, dict)
                else "",
                "format": str(item.get("format", "")) if isinstance(item, dict) else "",
                "raw_size_gb": str(item.get("raw_size_gb", ""))
                if isinstance(item, dict)
                else "",
                "raw_size_unit": str(item.get("raw_size_unit", "gb"))
                if isinstance(item, dict)
                else "gb",
                "compressed": bool(item.get("compressed", False))
                if isinstance(item, dict)
                else False,
                "uncompressed_size_gb": str(item.get("uncompressed_size_gb", ""))
                if isinstance(item, dict)
                else "",
                "uncompressed_size_unit": str(item.get("uncompressed_size_unit", "gb"))
                if isinstance(item, dict)
                else "gb",
            }
            for item in datasets
        ]

    def _init_acquisition_rows(self) -> None:
        acquisition_sessions = self._defaults.get("acquisition_sessions")
        if not isinstance(acquisition_sessions, list):
            return
        self._acquisition_rows = [
            {
                "imaging_date": item.get("imaging_date")
                if isinstance(item, dict)
                else None,
                "microscope": str(item.get("microscope", ""))
                if isinstance(item, dict)
                else "",
                "modality": str(item.get("modality", ""))
                if isinstance(item, dict)
                else "",
                "objective": str(item.get("objective", ""))
                if isinstance(item, dict)
                else "",
                "voxel_x": str(item.get("voxel_x", ""))
                if isinstance(item, dict)
                else "",
                "voxel_y": str(item.get("voxel_y", ""))
                if isinstance(item, dict)
                else "",
                "voxel_z": str(item.get("voxel_z", ""))
                if isinstance(item, dict)
                else "",
                "time_interval_s": str(item.get("time_interval_s", ""))
                if isinstance(item, dict)
                else "",
                "notes": str(item.get("notes", "")) if isinstance(item, dict) else "",
                "channels": item.get("channels", []) if isinstance(item, dict) else [],
            }
            for item in acquisition_sessions
        ]

    def _init_milestone_rows(self) -> None:
        milestones = self._defaults.get("milestones")
        if not isinstance(milestones, list):
            return
        self._milestone_rows = [
            {
                "name": str(item.get("name", "")) if isinstance(item, dict) else "",
                "target_date": item.get("target_date")
                if isinstance(item, dict)
                else None,
                "actual_date": item.get("actual_date")
                if isinstance(item, dict)
                else None,
                "status": str(item.get("status", "pending"))
                if isinstance(item, dict)
                else "pending",
                "notes": str(item.get("notes", "")) if isinstance(item, dict) else "",
            }
            for item in milestones
        ]

    def _init_hardware_rows(self) -> None:
        hardware_profiles = self._defaults.get("hardware_profiles")
        if not isinstance(hardware_profiles, list):
            return
        self._hardware_profiles = [
            {
                "name": str(item.get("name", "")) if isinstance(item, dict) else "",
                "cpu": str(item.get("cpu", "")) if isinstance(item, dict) else "",
                "cores": str(item.get("cores", "")) if isinstance(item, dict) else "",
                "ram": str(item.get("ram", "")) if isinstance(item, dict) else "",
                "gpu": str(item.get("gpu", "")) if isinstance(item, dict) else "",
                "notes": str(item.get("notes", "")) if isinstance(item, dict) else "",
                "is_cluster": bool(item.get("is_cluster", False))
                if isinstance(item, dict)
                else False,
                "partition": str(item.get("partition", ""))
                if isinstance(item, dict)
                else "",
                "node_type": str(item.get("node_type", ""))
                if isinstance(item, dict)
                else "",
            }
            for item in hardware_profiles
        ]

    def _init_channel_rows(self) -> None:
        channels = self._defaults.get("channels")
        if not isinstance(channels, list):
            return
        self._channel_rows = [
            {
                "name": str(item.get("name", "")) if isinstance(item, dict) else "",
                "fluorophore": str(item.get("fluorophore", ""))
                if isinstance(item, dict)
                else "",
                "excitation_nm": str(item.get("excitation_nm", ""))
                if isinstance(item, dict)
                else "",
                "emission_nm": str(item.get("emission_nm", ""))
                if isinstance(item, dict)
                else "",
            }
            for item in channels
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            yield from compose_setup_tab(self)
            yield from compose_science_tab(self)
            yield from compose_admin_tab(self)
            yield from compose_outputs_tab(self)
            yield from compose_hub_tab(self)
            yield from compose_log_tab(self)
            yield from compose_idea_tab(self)
        yield Footer()

    def on_mount(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if self._mode in ("log", "idea", "outputs", "hub"):
            tabbed.active = self._mode
        else:
            tabbed.active = "setup"
            # Only restore saved UI state for menu mode
            if self._mode == "menu":
                self._apply_ui_state()

        self._refresh_init_validation()
        self._refresh_worklog_lists()
        self._refresh_artifact_list()
        self._load_manifest_sections()
        self.set_interval(1, self._tick_worklog)
        self.set_interval(1, self._poll_method_preview)

        try:
            task_type_select = self.query_one("#task_type", Select)
            if task_type_select.value is None and task_type_select.options:
                task_type_select.value = task_type_select.options[0][1]
        except Exception:
            pass

        try:
            self._manifest_errors = self.query_one("#manifest_error", Static)
        except Exception:
            self._manifest_errors = None

        try:
            self._method_path_suggestions = self.query_one(
                "#method_path_suggestions", OptionList
            )
        except Exception:
            self._method_path_suggestions = None

        try:
            self._ensure_collaborator_rows()
            self._populate_collaborators_table()
        except Exception:
            pass

        try:
            self._populate_channels_table()
        except Exception:
            pass

        try:
            self._populate_acquisition_table()
        except Exception:
            pass

        try:
            self._ensure_dataset_rows()
        except Exception:
            pass

        try:
            self._populate_datasets_table()
        except Exception:
            pass

        try:
            self._populate_milestones_table()
        except Exception:
            pass

        try:
            self._populate_hardware_table()
        except Exception:
            pass

        try:
            self._populate_milestones_table()
        except Exception:
            pass

        # Set initial visibility of data sections
        self._toggle_data_sections(bool(self._defaults.get("data_enabled", True)))

        try:
            self._ensure_collaborator_rows()
        except Exception:
            pass

        # Notify if existing manifest was loaded
        if self._defaults.get("project_name"):
            self.notify("Manifest loaded", severity="information")

        try:
            git_remote_input = self.query_one("#git_remote", Input)
            if not git_remote_input.value.strip():
                git_remote_input.value = detect_git_remote(self._project_root)
        except Exception:
            pass

    def on_shutdown(self) -> None:
        self._store_ui_state()

    def on_unmount(self) -> None:
        self._store_ui_state()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if not button_id:
            return
        handlers: dict[str, Callable[[], None]] = {
            "add_collaborator": self.action_add_collaborator_row,
            "remove_collaborator": self.action_remove_collaborator_row,
            "add_dataset": self.action_add_dataset,
            "remove_dataset": self.action_remove_dataset,
            "sync_dataset": self.action_sync_dataset,
            "add_acquisition": self.action_add_acquisition,
            "remove_acquisition": self.action_remove_acquisition,
            "add_channel": self.action_add_channel_row,
            "remove_channel": self.action_remove_channel_row,
            "add_milestone": self.action_add_milestone,
            "remove_milestone": self.action_remove_milestone,
            "browse_method": lambda: self._open_directory_picker("method_path"),
            "method_template": self._create_method_template,
            "hardware_add": self._add_hardware_profile,
            "hardware_remove": self._remove_selected_hardware,
            "hardware_detect": self._detect_hardware_profile,
            "languages_add": lambda: self._add_list_entries(
                "languages_list", "Add Languages"
            ),
            "software_add": lambda: self._add_list_entries(
                "software_list", "Add Software"
            ),
            "cluster_packages_add": lambda: self._add_list_entries(
                "cluster_packages_list", "Add Cluster Packages"
            ),
            "idea_cancel": lambda: self.exit(None),
            "task_add": self._add_task,
            "task_checkout": self._checkout_task,
            "task_pause": self._toggle_pause_task,
            "task_set_status": self._set_task_status,
            "artifact_add": self._add_artifact,
            "artifact_update": self._update_artifact_status,
        }
        handler = handlers.get(button_id)
        if handler:
            handler()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message":
            self._submit_log()
        elif event.input.id in ("project_name", "analyst"):
            self._refresh_init_validation()
        elif event.input.id == "method_path":
            self._hide_method_path_suggestions()
            self._load_method_preview()
            self._maybe_sync_method_path()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in ("project_name", "analyst"):
            self._refresh_init_validation()

        if event.input.id == "method_path":
            try:
                focused = self.focused
                if focused is event.input:
                    self._update_method_path_suggestions(event.input.id, event.value)
                else:
                    self._hide_method_path_suggestions()
            except Exception:
                pass
            self._load_method_preview_if_exists(event.value)

    def on_input_focused(self, event) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id == "method_path":
            try:
                self._update_method_path_suggestions(input_id, event.input.value)
            except Exception:
                pass

    def on_input_blurred(self, event) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id == "method_path":
            focused = self.focused
            if (
                self._method_path_suggestions
                and focused is self._method_path_suggestions
            ):
                return
            if focused and getattr(focused, "id", "") == "method_path_suggestions":
                return
            self._hide_method_path_suggestions()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "collab_role_select":
            pass
        elif event.select.id == "modality":
            try:
                row = self.query_one("#modality_other_row", Horizontal)
                if event.value and str(event.value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
        elif event.select.id == "environment":
            try:
                row = self.query_one("#environment_other_row", Horizontal)
                if event.value and str(event.value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "data_enabled":
            self._toggle_data_sections(event.value)
            if not event.value:
                self._dataset_rows = []
                self._populate_datasets_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in collaborators or channels table."""
        row_key = event.row_key.value
        if row_key is None:
            return
        table_id = event.data_table.id
        if not table_id:
            return
        handlers: dict[str, Callable[[int], None]] = {
            "collaborators_table": self._handle_collaborator_row_selected,
            "channels_table": self._handle_channel_row_selected,
            "hardware_table": self._handle_hardware_row_selected,
            "datasets_table": self._handle_dataset_row_selected,
            "milestones_table": self._handle_milestone_row_selected,
            "acquisition_table": self._handle_acquisition_row_selected,
        }
        handler = handlers.get(table_id)
        if not handler:
            return
        try:
            idx = int(row_key)
        except (ValueError, TypeError):
            return
        handler(idx)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "acquisition_table":
            return
        row_key = event.row_key.value
        if row_key is None:
            return
        try:
            idx = int(row_key)
        except (ValueError, TypeError):
            return
        if not (0 <= idx < len(self._acquisition_rows)):
            return
        if (
            self._selected_acquisition_index is not None
            and self._selected_acquisition_index != idx
        ):
            self._store_channels_for_session(self._selected_acquisition_index)
        self._load_session_channels(idx)

    def _handle_collaborator_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._collaborator_rows)):
            return
        row_data = self._collaborator_rows[idx]
        self.push_screen(
            CollaboratorModal(load_role_options(), row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_collaborator(i, data),
        )

    def _handle_channel_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._channel_rows)):
            return
        row_data = self._channel_rows[idx]
        self.push_screen(
            ChannelModal(row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_channel(i, data),
        )

    def _handle_hardware_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._hardware_profiles)):
            return
        self._selected_hardware_index = idx
        row_data = self._hardware_profiles[idx]
        self.push_screen(
            HardwareModal(row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_hardware(i, data),
        )

    def _handle_dataset_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._dataset_rows)):
            return
        row_data = self._dataset_rows[idx]
        self.push_screen(
            DatasetModal(
                load_endpoint_options(),
                load_dataset_format_options(),
                row_data,
                allow_remove=True,
            ),
            lambda data, i=idx: self._handle_edit_dataset(i, data),
        )

    def _handle_milestone_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._milestone_rows)):
            return
        row_data = self._milestone_rows[idx]
        self.push_screen(
            MilestoneModal(row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_milestone(i, data),
        )

    def _handle_acquisition_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._acquisition_rows)):
            return
        if (
            self._selected_acquisition_index is not None
            and self._selected_acquisition_index != idx
        ):
            self._store_channels_for_session(self._selected_acquisition_index)
        row_data = self._acquisition_rows[idx]
        self.push_screen(
            AcquisitionSessionModal(row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_acquisition(i, data),
        )
        self._load_session_channels(idx)

    def _add_list_entries(self, list_id: str, title: str) -> None:
        """Open modal to add comma-separated entries."""
        self.push_screen(
            CustomInputModal(title, placeholder="Comma-separated"),
            lambda items, lid=list_id: self._handle_list_entries(lid, items),
        )

    def _handle_list_entries(self, list_id: str, items: list[str] | None) -> None:
        if not items:
            return
        try:
            selection_list = self.query_one(f"#{list_id}", SelectionList)
            existing = {str(opt.id) for opt in selection_list._options}
            for item in items:
                if item not in existing:
                    selection_list.add_option(Selection(item, item, True))
                selection_list.select(item)
        except Exception:
            pass

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "method_path_suggestions":
            if self._active_method_input:
                try:
                    input_widget = self.query_one(
                        f"#{self._active_method_input}", Input
                    )
                    selected = str(event.option.prompt)
                    input_widget.value = selected
                    self._hide_method_path_suggestions()
                    input_widget.focus()

                    def _move_cursor() -> None:
                        try:
                            input_widget.cursor_position = len(selected)
                        except Exception:
                            pass

                    try:
                        self.call_later(_move_cursor)
                    except Exception:
                        _move_cursor()
                    self._load_method_preview()
                except Exception:
                    pass

    def on_key(self, event) -> None:
        if event.key == "ctrl+v":
            try:
                if isinstance(self.focused, Input):
                    return
                tabbed = self.query_one("#tabs", TabbedContent)
                if tabbed.active == "setup":
                    setup_sections = self.query_one("#setup_sections", TabbedContent)
                    if setup_sections.active == "setup_data":
                        self.action_sync_dataset()
                        event.prevent_default()
                        event.stop()
                        return
            except Exception:
                pass

        if event.key in ("ctrl+a", "ctrl+d"):
            try:
                tabbed = self.query_one("#tabs", TabbedContent)
                # Handle collaborators table in setup tab
                if tabbed.active == "setup":
                    table = self.query_one("#datasets_table", DataTable)
                    if table.has_focus:
                        if event.key == "ctrl+a":
                            self.action_add_dataset()
                        elif event.key == "ctrl+d":
                            self.action_remove_dataset()
                        event.prevent_default()
                        event.stop()
                        return
                    table = self.query_one("#collaborators_table", DataTable)
                    if table.has_focus:
                        if event.key == "ctrl+a":
                            self.action_add_collaborator_row()
                        elif event.key == "ctrl+d":
                            self.action_remove_collaborator_row()
                        event.prevent_default()
                        event.stop()
                        return
                # Handle channels table in science tab
                elif tabbed.active == "science":
                    science_sections = self.query_one(
                        "#science_sections", TabbedContent
                    )
                    if science_sections.active == "science_acquisition":
                        table = self.query_one("#acquisition_table", DataTable)
                        if table.has_focus:
                            if event.key == "ctrl+a":
                                self.action_add_acquisition()
                            elif event.key == "ctrl+d":
                                self.action_remove_acquisition()
                            event.prevent_default()
                            event.stop()
                            return
                    table = self.query_one("#channels_table", DataTable)
                    if table.has_focus:
                        if event.key == "ctrl+a":
                            self.action_add_channel_row()
                        else:
                            self.action_remove_channel_row()
                        event.prevent_default()
                        event.stop()
                        return
                    hardware_table = self.query_one("#hardware_table", DataTable)
                    if hardware_table.has_focus:
                        if event.key == "ctrl+a":
                            self._add_hardware_profile()
                        else:
                            self._remove_selected_hardware()
                        event.prevent_default()
                        event.stop()
                        return
                elif tabbed.active == "admin":
                    admin_sections = self.query_one("#admin_sections", TabbedContent)
                    if admin_sections.active == "admin_timeline":
                        table = self.query_one("#milestones_table", DataTable)
                        if table.has_focus:
                            if event.key == "ctrl+a":
                                self.action_add_milestone()
                            elif event.key == "ctrl+d":
                                self.action_remove_milestone()
                            event.prevent_default()
                            event.stop()
                            return
            except Exception:
                pass

        # Handle path suggestions keyboard navigation
        # Handle method path suggestions
        try:
            if self._method_path_suggestions_visible:
                suggestions = self._method_path_suggestions or self.query_one(
                    "#method_path_suggestions", OptionList
                )
                if suggestions.has_class("visible"):
                    if event.key == "escape":
                        if self._active_method_input:
                            input_widget = self.query_one(
                                f"#{self._active_method_input}", Input
                            )
                            self._hide_method_path_suggestions()
                            input_widget.focus()
                            event.prevent_default()
                            event.stop()
                    elif event.key == "down" and self._active_method_input:
                        focused = self.focused
                        if focused and focused.id == self._active_method_input:
                            suggestions.focus()
                            if suggestions.option_count > 0:
                                suggestions.highlighted = 0
                            event.prevent_default()
                            event.stop()
                    elif event.key == "up":
                        if self.focused == suggestions and suggestions.highlighted == 0:
                            if self._active_method_input:
                                input_widget = self.query_one(
                                    f"#{self._active_method_input}", Input
                                )
                                input_widget.focus()
                                event.prevent_default()
                                event.stop()
        except Exception:
            pass

    def action_new_manifest(self) -> None:
        """Create a new blank manifest."""
        self.push_screen(NewManifestConfirmScreen(), self._handle_new_manifest_confirm)

    def action_reset_manifest(self) -> None:
        """Show confirmation dialog before reloading manifest from disk."""
        self.push_screen(ResetConfirmScreen(), self._handle_reset_confirm)

    def _handle_reset_confirm(self, result: str | None) -> None:
        """Handle the confirmation result from ResetConfirmScreen."""
        if result == "reset":
            self._do_reset_manifest()

    def _do_reset_manifest(self) -> None:
        """Reload manifest from disk, discarding unsaved changes."""
        from .io import load_manifest

        manifest_path = self._project_root / "manifest.yaml"
        manifest = load_manifest(manifest_path)
        if manifest is None:
            self.notify("No manifest.yaml found to reload", severity="warning")
            return

        self._manifest = manifest
        self._reload_form_from_manifest(manifest)
        self._load_manifest_sections()
        self.notify("Manifest reloaded from disk", severity="information")

    def _handle_new_manifest_confirm(self, result: str | None) -> None:
        """Handle the confirmation result from NewManifestConfirmScreen."""
        if result == "discard":
            # Clear all form fields
            try:
                self.query_one("#project_name", Input).value = ""
                self.query_one("#analyst", Input).value = ""
                self.query_one("#data_enabled", Checkbox).value = True
                self._dataset_rows = []
                self._populate_datasets_table()
                self._collaborator_rows = [
                    {"name": "", "role": "", "email": "", "affiliation": ""}
                ]
                self._populate_collaborators_table()
                self._set_tab("init")
                self._refresh_init_validation()
                self.notify("New manifest - fill in the form", severity="information")
            except Exception as e:
                self.notify(
                    f"Could not reset form: {e}", severity="error", markup=False
                )
        # "cancel" does nothing, just closes the modal

    def action_submit(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active == "init":
            self._submit_init()
        else:
            self._submit_log()

    def action_save_current(self) -> None:
        """Save current tab without exiting."""
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active == "init":
            self._save_init()
        elif tabbed.active == "log":
            self._save_log()
        elif tabbed.active == "idea":
            self._submit_idea()
        elif tabbed.active == "artifact":
            self._submit_artifact()
        elif tabbed.active == "manifest":
            self._save_manifest()
        elif tabbed.active in ("setup", "science", "admin", "outputs", "hub"):
            # For manifest editing tabs, save the manifest
            self._save_init()
        else:
            self.notify("Save not available for this tab", severity="warning")

    def action_exit_app(self) -> None:
        self.push_screen(ExitConfirmScreen(), self._handle_exit_confirm)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "active_tasks":
            if event.item and event.item.id:
                _, idx = event.item.id.split("-", 1)
                self._selected_active_index = int(idx)
        elif event.list_view.id == "artifact_list":
            if event.item and event.item.id:
                _, idx = event.item.id.split("-", 1)
                self._selected_artifact_index = int(idx)

    def _handle_exit_confirm(self, result: str | None) -> None:
        if result == "save":
            # Save UI state before exiting
            self._store_ui_state()
            tabbed = self.query_one("#tabs", TabbedContent)
            if tabbed.active == "init":
                self._submit_init()
            elif tabbed.active == "log":
                self._submit_log()
            elif tabbed.active == "idea":
                self._submit_idea()
            elif tabbed.active == "artifact":
                self._submit_artifact()
            elif tabbed.active in ("setup", "science", "admin", "outputs", "hub"):
                # For manifest editing tabs, save and then exit
                self._save_init()
                self.exit(None)
            else:
                # Unknown tab, just exit
                self.exit(None)
        elif result == "discard":
            # Save UI state before exiting
            self._store_ui_state()
            self.exit(None)
        # "cancel" does nothing, just closes the modal

    def _open_directory_picker(self, target_input_id: str) -> None:
        self._browse_target = target_input_id
        start = Path.home()
        self.push_screen(DirectoryPickerScreen(start), self._handle_directory_pick)

    def _handle_directory_pick(self, path: str | None) -> None:
        if not path or not self._browse_target:
            self._browse_target = None
            return
        try:
            input_widget = self.query_one(f"#{self._browse_target}", Input)
            input_widget.value = path
            self._refresh_init_validation()
            if self._browse_target == "method_path":
                self._load_method_preview()
        except Exception:
            pass
        self._browse_target = None

    def _refresh_init_validation(self) -> None:
        for field_id in ("project_name", "analyst"):
            widget = self.query_one(f"#{field_id}", Input)
            widget.remove_class("valid")
            widget.remove_class("invalid")
            if widget.value.strip():
                widget.add_class("valid")
            else:
                widget.add_class("invalid")

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection (Enter key or click) in collaborators table for inline editing."""
        if event.data_table.id != "collaborators_table":
            return
        # Start editing when Enter is pressed or cell is clicked
        self._edit_collaborator_cell()
