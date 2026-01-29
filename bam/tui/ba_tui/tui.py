from __future__ import annotations

import asyncio
import shutil
from datetime import date, datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Optional

import yaml
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
    ListItem,
    ListView,
    Markdown,
    OptionList,
    ProgressBar,
    Select,
    SelectionList,
    Static,
    TabbedContent,
    TextArea,
)
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection

import pendulum

from .widgets import DateSelect

from .io import dump_manifest
from .models import Artifact, Dataset, LogEntry, Manifest, TaskStatus, build_manifest
from .scaffold import ensure_data_symlink, ensure_directories, ensure_worklog
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
from .utils import detect_git_remote, detect_hardware
from .tabs.admin import compose_admin_tab
from .tabs.hub import compose_hub_tab
from .tabs.idea import compose_idea_tab
from .tabs.log import compose_log_tab
from .tabs.outputs import compose_outputs_tab
from .tabs.science import compose_science_tab
from .tabs.setup import compose_setup_tab


class BAApp(App[dict[str, object] | None]):
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

    # Default endpoint options (can be overridden via ~/.config/bam/endpoints.yaml)
    DEFAULT_ENDPOINTS = ["Local", "I Drive", "MSD CEPH", "RFS", "HDD1"]
    DEFAULT_ROLES = ["PI", "Students", "Others"]
    DEFAULT_FORMATS = ["tiff", "zarr", "hdf5", "nd2", "czi", "ome-tiff", "other"]

    @classmethod
    def _load_dataset_format_options(cls) -> list[tuple[str, str]]:
        options = []
        for name in cls.DEFAULT_FORMATS:
            if name == "ome-tiff":
                label = "OME-TIFF"
            elif name == "other":
                label = "Other"
            else:
                label = name.upper()
            options.append((label, name))
        return options

    @classmethod
    def _load_endpoint_options(cls) -> list[tuple[str, str]]:
        """Load endpoint options from config file or use defaults."""
        config_path = Path.home() / ".config" / "bam" / "endpoints.yaml"
        endpoints = cls.DEFAULT_ENDPOINTS.copy()

        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict) and "endpoints" in data:
                        endpoints = data["endpoints"]
                    elif isinstance(data, list):
                        endpoints = data
            except Exception:
                pass  # Use defaults on error

        # Convert to tuple format and add "Other" option
        options = [(name, name) for name in endpoints]
        options.append(("Other", "Other"))
        return options

    @classmethod
    def _load_role_options(cls) -> list[tuple[str, str]]:
        """Load collaborator role options from config file or use defaults."""
        config_path = Path.home() / ".config" / "bam" / "roles.yaml"
        roles = cls.DEFAULT_ROLES.copy()

        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict) and "roles" in data:
                        roles = data["roles"]
                    elif isinstance(data, list):
                        roles = data
            except Exception:
                pass

        normalized = set()
        options: list[tuple[str, str]] = []
        for name in roles:
            raw = str(name).strip()
            if not raw:
                continue
            key = raw.lower()
            if key in ("other", "others"):
                key = "other"
                raw = "Other"
            if key in normalized:
                continue
            normalized.add(key)
            options.append((raw, raw))
        if "other" not in normalized:
            options.append(("Other", "Other"))
        return options

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
        if self._defaults.get("collaborators"):
            self._collaborator_rows = [
                {
                    "name": str(item.get("name", "")),
                    "role": str(item.get("role", "")),
                    "email": str(item.get("email", "")),
                    "affiliation": str(item.get("affiliation", "")),
                }
                for item in self._defaults.get("collaborators", [])
            ]
        if self._defaults.get("datasets"):
            self._dataset_rows = [
                {
                    "name": str(item.get("name", "")),
                    "endpoint": str(item.get("endpoint", "")),
                    "source": str(item.get("source", "")),
                    "local": str(item.get("local", "")),
                    "locally_mounted": bool(item.get("locally_mounted", False)),
                    "description": str(item.get("description", "")),
                    "format": str(item.get("format", "")),
                    "raw_size_gb": str(item.get("raw_size_gb", "")),
                    "raw_size_unit": str(item.get("raw_size_unit", "gb")),
                    "compressed": bool(item.get("compressed", False)),
                    "uncompressed_size_gb": str(item.get("uncompressed_size_gb", "")),
                    "uncompressed_size_unit": str(
                        item.get("uncompressed_size_unit", "gb")
                    ),
                }
                for item in self._defaults.get("datasets", [])
            ]
        if self._defaults.get("acquisition_sessions"):
            self._acquisition_rows = [
                {
                    "imaging_date": item.get("imaging_date"),
                    "microscope": str(item.get("microscope", "")),
                    "modality": str(item.get("modality", "")),
                    "objective": str(item.get("objective", "")),
                    "voxel_x": str(item.get("voxel_x", "")),
                    "voxel_y": str(item.get("voxel_y", "")),
                    "voxel_z": str(item.get("voxel_z", "")),
                    "time_interval_s": str(item.get("time_interval_s", "")),
                    "notes": str(item.get("notes", "")),
                    "channels": item.get("channels", []),
                }
                for item in self._defaults.get("acquisition_sessions", [])
            ]
        if self._defaults.get("milestones"):
            self._milestone_rows = [
                {
                    "name": str(item.get("name", "")),
                    "target_date": item.get("target_date"),
                    "actual_date": item.get("actual_date"),
                    "status": str(item.get("status", "pending")),
                    "notes": str(item.get("notes", "")),
                }
                for item in self._defaults.get("milestones", [])
            ]
        if self._defaults.get("hardware_profiles"):
            self._hardware_profiles = [
                {
                    "name": str(item.get("name", "")),
                    "cpu": str(item.get("cpu", "")),
                    "cores": str(item.get("cores", "")),
                    "ram": str(item.get("ram", "")),
                    "gpu": str(item.get("gpu", "")),
                    "notes": str(item.get("notes", "")),
                    "is_cluster": bool(item.get("is_cluster", False)),
                    "partition": str(item.get("partition", "")),
                    "node_type": str(item.get("node_type", "")),
                }
                for item in self._defaults.get("hardware_profiles", [])
            ]
        if self._defaults.get("method_path"):
            self._method_path = str(self._defaults.get("method_path"))

        self._channel_rows: list[dict[str, str]] = []
        if self._defaults.get("channels"):
            self._channel_rows = [
                {
                    "name": str(item.get("name", "")),
                    "fluorophore": str(item.get("fluorophore", "")),
                    "excitation_nm": str(item.get("excitation_nm", "")),
                    "emission_nm": str(item.get("emission_nm", "")),
                }
                for item in self._defaults.get("channels", [])
            ]

        version = "unknown"
        try:
            version = metadata.version("bam")
        except metadata.PackageNotFoundError:
            pass
        self.title = f"BAM - Bioimage Analysis Manager {version}"

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
        self._toggle_data_sections(self._defaults.get("data_enabled", True))

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

    def _get_project_state_key(self) -> str:
        """Return a unique key for this project's UI state."""
        return str(self._project_root.resolve())

    def _apply_ui_state(self) -> None:
        try:
            if not self._ui_state_path.exists():
                return
            with open(self._ui_state_path) as f:
                all_state = yaml.safe_load(f) or {}
        except Exception:
            return

        # Get project-specific state
        project_key = self._get_project_state_key()
        data = all_state.get(project_key, {})
        if not data:
            return

        tab_id = data.get("active_tab")
        focus_id = data.get("focused_id")

        if tab_id:
            try:
                tabbed = self.query_one("#tabs", TabbedContent)
                tabbed.active = str(tab_id)
            except Exception:
                pass

        if focus_id:

            def _focus_later() -> None:
                try:
                    widget = self.query_one(f"#{focus_id}")
                    widget.focus()
                except Exception:
                    pass

            # Use set_timer with small delay to ensure tab content is ready
            self.set_timer(0.1, _focus_later)

    def _store_ui_state(self) -> None:
        try:
            if not self.screen_stack:
                return
        except Exception:
            return
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            active_tab = tabbed.active
        except Exception:
            active_tab = ""

        focused_id = ""
        if self.focused is not None and getattr(self.focused, "id", None):
            focused_id = str(self.focused.id)

        project_key = self._get_project_state_key()
        project_state = {"active_tab": active_tab, "focused_id": focused_id}

        try:
            self._ui_state_path.parent.mkdir(parents=True, exist_ok=True)
            # Load existing state for all projects
            all_state = {}
            if self._ui_state_path.exists():
                with open(self._ui_state_path) as f:
                    all_state = yaml.safe_load(f) or {}
            # Update state for this project
            all_state[project_key] = project_state
            with open(self._ui_state_path, "w") as f:
                yaml.safe_dump(all_state, f, sort_keys=False)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "add_collaborator":
            self.action_add_collaborator_row()
            return
        if button_id == "remove_collaborator":
            self.action_remove_collaborator_row()
            return
        if button_id == "add_dataset":
            self.action_add_dataset()
            return
        if button_id == "remove_dataset":
            self.action_remove_dataset()
            return
        if button_id == "sync_dataset":
            self.action_sync_dataset()
            return
        if button_id == "add_acquisition":
            self.action_add_acquisition()
            return
        if button_id == "remove_acquisition":
            self.action_remove_acquisition()
            return
        if button_id == "add_channel":
            self.action_add_channel_row()
            return
        if button_id == "remove_channel":
            self.action_remove_channel_row()
            return
        if button_id == "add_milestone":
            self.action_add_milestone()
            return
        if button_id == "remove_milestone":
            self.action_remove_milestone()
            return
        if button_id == "browse_method":
            self._open_directory_picker("method_path")
        elif button_id == "method_template":
            self._create_method_template()
        elif button_id == "hardware_add":
            self._add_hardware_profile()
        elif button_id == "hardware_remove":
            self._remove_selected_hardware()
        elif button_id == "hardware_detect":
            self._detect_hardware_profile()
        elif button_id == "languages_add":
            self._add_list_entries("languages_list", "Add Languages")
        elif button_id == "software_add":
            self._add_list_entries("software_list", "Add Software")
        elif button_id == "cluster_packages_add":
            self._add_list_entries("cluster_packages_list", "Add Cluster Packages")
        elif button_id == "idea_cancel":
            self.exit(None)
        elif button_id == "task_add":
            self._add_task()
        elif button_id == "task_checkout":
            self._checkout_task()
        elif button_id == "task_pause":
            self._toggle_pause_task()
        elif button_id == "task_set_status":
            self._set_task_status()
        elif button_id == "artifact_add":
            self._add_artifact()
        elif button_id == "artifact_update":
            self._update_artifact_status()

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

        if event.data_table.id == "collaborators_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._collaborator_rows):
                    row_data = self._collaborator_rows[idx]
                    self.push_screen(
                        CollaboratorModal(self._load_role_options(), row_data),
                        lambda data, i=idx: self._handle_edit_collaborator(i, data),
                    )
            except (ValueError, IndexError):
                pass

        elif event.data_table.id == "channels_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._channel_rows):
                    row_data = self._channel_rows[idx]
                    self.push_screen(
                        ChannelModal(row_data),
                        lambda data, i=idx: self._handle_edit_channel(i, data),
                    )
            except (ValueError, IndexError):
                pass

        elif event.data_table.id == "hardware_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._hardware_profiles):
                    self._selected_hardware_index = idx
                    row_data = self._hardware_profiles[idx]
                    self.push_screen(
                        HardwareModal(row_data),
                        lambda data, i=idx: self._handle_edit_hardware(i, data),
                    )
            except (ValueError, IndexError):
                pass

        elif event.data_table.id == "datasets_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._dataset_rows):
                    row_data = self._dataset_rows[idx]
                    self.push_screen(
                        DatasetModal(
                            self._load_endpoint_options(),
                            self._load_dataset_format_options(),
                            row_data,
                        ),
                        lambda data, i=idx: self._handle_edit_dataset(i, data),
                    )
            except (ValueError, IndexError):
                pass

        elif event.data_table.id == "milestones_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._milestone_rows):
                    row_data = self._milestone_rows[idx]
                    self.push_screen(
                        MilestoneModal(row_data),
                        lambda data, i=idx: self._handle_edit_milestone(i, data),
                    )
            except (ValueError, IndexError):
                pass

        elif event.data_table.id == "acquisition_table":
            try:
                idx = int(row_key)
                if 0 <= idx < len(self._acquisition_rows):
                    if (
                        self._selected_acquisition_index is not None
                        and self._selected_acquisition_index != idx
                    ):
                        self._store_channels_for_session(
                            self._selected_acquisition_index
                        )
                    row_data = self._acquisition_rows[idx]
                    self.push_screen(
                        AcquisitionSessionModal(row_data),
                        lambda data, i=idx: self._handle_edit_acquisition(i, data),
                    )
                self._load_session_channels(idx)
            except (ValueError, IndexError):
                pass

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

    def _handle_edit_collaborator(self, idx: int, data: dict[str, str] | None) -> None:
        """Update collaborator data after modal close."""
        if data and 0 <= idx < len(self._collaborator_rows):
            self._collaborator_rows[idx] = data
            self._populate_collaborators_table()

    def _handle_edit_hardware(
        self, idx: int, data: dict[str, str | bool] | None
    ) -> None:
        if data and 0 <= idx < len(self._hardware_profiles):
            self._hardware_profiles[idx] = data
            self._populate_hardware_table()

    def _populate_hardware_table(self) -> None:
        try:
            table = self.query_one("#hardware_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "CPU", "Cores", "RAM", "GPU")
            for idx, row in enumerate(self._hardware_profiles):
                table.add_row(
                    row.get("name", ""),
                    row.get("cpu", ""),
                    row.get("cores", ""),
                    row.get("ram", ""),
                    row.get("gpu", ""),
                    key=str(idx),
                )
        except Exception:
            pass

    def _add_hardware_profile(self) -> None:
        self.push_screen(HardwareModal(), self._handle_new_hardware)

    def _handle_new_hardware(self, data: dict[str, str | bool] | None) -> None:
        if data:
            self._hardware_profiles.append(data)
            self._populate_hardware_table()

    def _remove_selected_hardware(self) -> None:
        try:
            table = self.query_one("#hardware_table", DataTable)
            idx = table.cursor_row
            if idx is None:
                return
            if 0 <= idx < len(self._hardware_profiles):
                self._hardware_profiles.pop(idx)
            self._populate_hardware_table()
        except Exception:
            pass

    def _detect_hardware_profile(self) -> None:
        try:
            detected = detect_hardware()
            profile = {
                "name": "local",
                "cpu": detected.get("cpu", ""),
                "cores": detected.get("cores", ""),
                "ram": detected.get("ram", ""),
                "gpu": detected.get("gpu", ""),
                "notes": "",
                "is_cluster": False,
                "partition": "",
                "node_type": "",
            }
            self._hardware_profiles.append(profile)
            self._populate_hardware_table()
        except Exception:
            pass

    def _create_method_template(self) -> None:
        try:
            path_input = self.query_one("#method_path", Input)
            method_path = path_input.value.strip() or str(
                self._project_root / "method.md"
            )
            content = (
                "# Methods\n\n"
                "## Overview\n\n"
                "Describe the analysis workflow.\n\n"
                "## Data\n\n"
                "Describe input data and preprocessing.\n\n"
                "## Analysis\n\n"
                "Describe key steps, software, and parameters.\n"
            )
            path = Path(method_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            created = False
            if not path.exists():
                path.write_text(content)
                created = True
            path_input.value = str(path)
            self._method_path = str(path)
            self._method_template_used = "default"
            self._load_method_preview()
            if created:
                self.notify("Method template created", severity="information")
            else:
                self.notify("Method template already exists", severity="warning")
        except Exception as exc:
            self.notify(f"Template creation failed: {exc}", severity="error")

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

    def _load_method_preview(self) -> None:
        try:
            path = self.query_one("#method_path", Input).value.strip()
            if not path:
                return
            method_path = Path(path).expanduser()
            text = method_path.read_text()
            self.query_one("#method_preview", Markdown).update(text)
            self._method_preview_path = str(method_path)
            try:
                self._method_preview_mtime = method_path.stat().st_mtime
            except Exception:
                self._method_preview_mtime = None
        except Exception:
            pass

    def _load_method_preview_if_exists(self, path: str) -> None:
        try:
            method_path = Path(path).expanduser()
            if method_path.is_file():
                text = method_path.read_text()
                self.query_one("#method_preview", Markdown).update(text)
                self._method_preview_path = str(method_path)
                try:
                    self._method_preview_mtime = method_path.stat().st_mtime
                except Exception:
                    self._method_preview_mtime = None
        except Exception:
            pass

    def _poll_method_preview(self) -> None:
        if not self._method_preview_path:
            return
        try:
            method_path = Path(self._method_preview_path)
            if not method_path.exists():
                return
            mtime = method_path.stat().st_mtime
            if self._method_preview_mtime is None or mtime > self._method_preview_mtime:
                self._method_preview_mtime = mtime
                text = method_path.read_text()
                self.query_one("#method_preview", Markdown).update(text)
        except Exception:
            pass

    def _maybe_sync_method_path(self) -> None:
        try:
            current = self.query_one("#method_path", Input).value.strip()
            if current and current != self._method_path:
                self._method_path = current
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

    # Tab navigation actions (F1-F7 in order)
    def action_show_tab_1(self) -> None:
        self._set_tab("setup")

    def action_show_tab_2(self) -> None:
        self._set_tab("science")

    def action_show_tab_3(self) -> None:
        self._set_tab("admin")

    def action_show_tab_4(self) -> None:
        self._set_tab("outputs")

    def action_show_tab_5(self) -> None:
        self._set_tab("hub")

    def action_show_tab_6(self) -> None:
        self._set_tab("log")

    def action_show_tab_7(self) -> None:
        self._set_tab("idea")

    def action_next_tab(self) -> None:
        self._cycle_tab(1)

    def action_prev_tab(self) -> None:
        self._cycle_tab(-1)

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

    def _reload_form_from_manifest(self, manifest: Manifest) -> None:
        """Reload all form fields from manifest data."""
        # Project fields
        try:
            self.query_one("#project_name", Input).value = manifest.project.name
        except Exception:
            pass
        try:
            if manifest.project.status:
                self.query_one(
                    "#project_status", Select
                ).value = manifest.project.status
        except Exception:
            pass

        # People fields
        try:
            if manifest.people:
                self.query_one("#analyst", Input).value = manifest.people.analyst or ""
        except Exception:
            pass

        # Collaborators
        try:
            if manifest.people and manifest.people.collaborators:
                self._collaborator_rows = [
                    {
                        "name": c.name,
                        "role": c.role or "",
                        "email": c.email or "",
                        "affiliation": c.affiliation or "",
                    }
                    for c in manifest.people.collaborators
                ]
            else:
                self._collaborator_rows = []
            self._populate_collaborators_table()
        except Exception:
            pass

        # Tags
        try:
            if manifest.tags:
                self.query_one("#project_tags", Input).value = ", ".join(manifest.tags)
            else:
                self.query_one("#project_tags", Input).value = ""
        except Exception:
            pass

        # Data fields
        try:
            has_datasets = bool(manifest.datasets)
            self.query_one("#data_enabled", Checkbox).value = has_datasets
            self._toggle_data_sections(has_datasets)
            self._dataset_rows = [
                {
                    "name": dataset.name,
                    "endpoint": dataset.endpoint or "",
                    "source": str(dataset.source or ""),
                    "local": str(dataset.local or ""),
                    "locally_mounted": dataset.locally_mounted,
                    "description": dataset.description or "",
                    "format": dataset.format or "",
                    "raw_size_gb": ""
                    if dataset.raw_size_gb is None
                    else str(dataset.raw_size_gb),
                    "raw_size_unit": dataset.raw_size_unit or "gb",
                    "compressed": bool(dataset.compressed)
                    if dataset.compressed is not None
                    else False,
                    "uncompressed_size_gb": ""
                    if dataset.uncompressed_size_gb is None
                    else str(dataset.uncompressed_size_gb),
                    "uncompressed_size_unit": dataset.uncompressed_size_unit or "gb",
                }
                for dataset in manifest.datasets
            ]
            self._populate_datasets_table()
        except Exception:
            pass

        # Billing fields
        try:
            if manifest.billing:
                self.query_one("#fund_code", Input).value = manifest.billing.fund_code
                self.query_one("#hourly_rate", Input).value = (
                    ""
                    if manifest.billing.hourly_rate is None
                    else str(manifest.billing.hourly_rate)
                )
                self.query_one("#budget_hours", Input).value = (
                    ""
                    if manifest.billing.budget_hours is None
                    else str(manifest.billing.budget_hours)
                )
                self.query_one("#spent_hours", Input).value = (
                    ""
                    if manifest.billing.spent_hours is None
                    else str(manifest.billing.spent_hours)
                )
                start_picker = self.query_one("#billing_start_date", DateSelect)
                end_picker = self.query_one("#billing_end_date", DateSelect)
                start_picker.date = self._to_pendulum_date(manifest.billing.start_date)
                end_picker.date = self._to_pendulum_date(manifest.billing.end_date)
                self.query_one("#billing_notes", TextArea).text = (
                    manifest.billing.notes or ""
                )
        except Exception:
            pass

        # Timeline fields
        try:
            if manifest.timeline and manifest.timeline.milestones:
                self._milestone_rows = [
                    {
                        "name": milestone.name,
                        "target_date": milestone.target_date,
                        "actual_date": milestone.actual_date,
                        "status": milestone.status,
                        "notes": milestone.notes,
                    }
                    for milestone in manifest.timeline.milestones
                ]
            else:
                self._milestone_rows = []
            self._populate_milestones_table()
        except Exception:
            pass

        # Acquisition fields
        try:
            if manifest.acquisition:
                sessions = manifest.acquisition.sessions or []
                if not sessions and any(
                    [
                        manifest.acquisition.microscope,
                        manifest.acquisition.modality,
                        manifest.acquisition.objective,
                        manifest.acquisition.voxel_size,
                        manifest.acquisition.time_interval_s,
                        manifest.acquisition.notes,
                    ]
                ):
                    sessions = [
                        {
                            "microscope": manifest.acquisition.microscope,
                            "modality": manifest.acquisition.modality,
                            "objective": manifest.acquisition.objective,
                            "voxel_size": manifest.acquisition.voxel_size,
                            "time_interval_s": manifest.acquisition.time_interval_s,
                            "notes": manifest.acquisition.notes,
                        }
                    ]

                self._acquisition_rows = []
                for session in sessions:
                    voxel = None
                    if isinstance(session, dict):
                        voxel = session.get("voxel_size")
                    else:
                        voxel = getattr(session, "voxel_size", None)
                    self._acquisition_rows.append(
                        {
                            "imaging_date": getattr(session, "imaging_date", None)
                            if not isinstance(session, dict)
                            else session.get("imaging_date", None),
                            "microscope": getattr(session, "microscope", None)
                            if not isinstance(session, dict)
                            else session.get("microscope", ""),
                            "modality": getattr(session, "modality", None)
                            if not isinstance(session, dict)
                            else session.get("modality", ""),
                            "objective": getattr(session, "objective", None)
                            if not isinstance(session, dict)
                            else session.get("objective", ""),
                            "voxel_x": str(voxel.x_um)
                            if voxel and getattr(voxel, "x_um", None) is not None
                            else "",
                            "voxel_y": str(voxel.y_um)
                            if voxel and getattr(voxel, "y_um", None) is not None
                            else "",
                            "voxel_z": str(voxel.z_um)
                            if voxel and getattr(voxel, "z_um", None) is not None
                            else "",
                            "time_interval_s": str(
                                getattr(session, "time_interval_s", None)
                                if not isinstance(session, dict)
                                else session.get("time_interval_s", "")
                            ),
                            "notes": getattr(session, "notes", None)
                            if not isinstance(session, dict)
                            else session.get("notes", ""),
                            "channels": getattr(session, "channels", None)
                            if not isinstance(session, dict)
                            else session.get("channels", []),
                        }
                    )
                self._populate_acquisition_table()
                if self._acquisition_rows:
                    try:
                        table = self.query_one("#acquisition_table", DataTable)
                        table.show_cursor = True
                        table.move_cursor(row=0, column=0)
                        self._load_session_channels(0)
                    except Exception:
                        self._load_session_channels(0)
                else:
                    self._channel_rows = []
                    self._populate_channels_table()
        except Exception:
            pass

        # Tools fields
        try:
            if manifest.tools:
                if manifest.tools.git_remote:
                    self.query_one(
                        "#git_remote", Input
                    ).value = manifest.tools.git_remote
                if manifest.tools.environment:
                    self.query_one(
                        "#environment", Select
                    ).value = manifest.tools.environment
                self.query_one("#env_file", Input).value = manifest.tools.env_file or ""
                if manifest.tools.languages:
                    try:
                        languages_list = self.query_one(
                            "#languages_list", SelectionList
                        )
                        languages_list.deselect_all()
                        for item in languages_list._options:
                            if item.id in manifest.tools.languages:
                                languages_list.select(item.id)
                    except Exception:
                        pass
                if manifest.tools.software:
                    try:
                        software_list = self.query_one("#software_list", SelectionList)
                        software_list.deselect_all()
                        for item in software_list._options:
                            if item.id in manifest.tools.software:
                                software_list.select(item.id)
                    except Exception:
                        pass
                if manifest.tools.languages:
                    try:
                        languages_list = self.query_one(
                            "#languages_list", SelectionList
                        )
                        languages_list.deselect_all()
                        for item in languages_list._options:
                            if item.id in manifest.tools.languages:
                                languages_list.select(item.id)
                    except Exception:
                        pass
                if manifest.tools.cluster_packages:
                    try:
                        cluster_list = self.query_one(
                            "#cluster_packages_list", SelectionList
                        )
                        cluster_list.deselect_all()
                        for item in cluster_list._options:
                            if item.id in manifest.tools.cluster_packages:
                                cluster_list.select(item.id)
                    except Exception:
                        pass
        except Exception:
            pass

        # Method fields
        try:
            if manifest.method:
                if manifest.method.file_path:
                    self.query_one(
                        "#method_path", Input
                    ).value = manifest.method.file_path
                    self._load_method_preview()
                if manifest.method.template_used:
                    self._method_template_used = manifest.method.template_used
        except Exception:
            pass

        # Billing defaults
        try:
            if manifest.billing:
                self._defaults["fund_code"] = manifest.billing.fund_code
                if manifest.billing.hourly_rate is not None:
                    self._defaults["hourly_rate"] = str(manifest.billing.hourly_rate)
                if manifest.billing.budget_hours is not None:
                    self._defaults["budget_hours"] = str(manifest.billing.budget_hours)
                if manifest.billing.spent_hours is not None:
                    self._defaults["spent_hours"] = str(manifest.billing.spent_hours)
                if manifest.billing.start_date:
                    self._defaults["billing_start_date"] = manifest.billing.start_date
                if manifest.billing.end_date:
                    self._defaults["billing_end_date"] = manifest.billing.end_date
                if manifest.billing.notes:
                    self._defaults["billing_notes"] = manifest.billing.notes
        except Exception:
            pass

        # Hardware profiles
        try:
            if manifest.hardware_profiles:
                self._hardware_profiles = [
                    {
                        "name": profile.name,
                        "cpu": profile.cpu,
                        "cores": getattr(profile, "cores", ""),
                        "ram": profile.ram,
                        "gpu": profile.gpu,
                        "notes": profile.notes,
                        "is_cluster": profile.is_cluster,
                        "partition": profile.partition,
                        "node_type": profile.node_type,
                    }
                    for profile in manifest.hardware_profiles
                ]
                self._populate_hardware_table()
        except Exception:
            pass

        # Refresh validation states
        self._refresh_init_validation()

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
                self.notify(f"Could not reset form: {e}", severity="error")
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

    def _save_init(self) -> None:
        """Save form data from all tabs to manifest without exiting."""
        if self._mode not in ("init", "menu", "both"):
            self.notify("Initialization is disabled in this mode", severity="error")
            return

        values = self._collect_values()
        required_fields = ["project_name", "analyst"]
        missing = [
            key for key in required_fields if not str(values.get(key, "")).strip()
        ]
        if missing:
            self.notify(
                "Please fill in required fields (Project Name, Analyst)",
                severity="error",
            )
            return

        try:
            # Load existing manifest or create new one
            manifest_path = self._project_root / "manifest.yaml"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest_data = yaml.safe_load(f) or {}
            else:
                manifest_data = {}

            # Update project section
            if "project" not in manifest_data:
                manifest_data["project"] = {}
            manifest_data["project"]["name"] = str(values["project_name"])

            # Collect additional project fields
            try:
                status_select = self.query_one("#project_status", Select)
                if status_select.value and status_select.value != Select.BLANK:
                    manifest_data["project"]["status"] = str(status_select.value)
            except Exception:
                pass

            try:
                tags_input = self.query_one("#project_tags", Input).value.strip()
                if tags_input:
                    manifest_data["tags"] = [
                        tag.strip() for tag in tags_input.split(",") if tag.strip()
                    ]
            except Exception:
                pass

            # Update people section
            if "people" not in manifest_data:
                manifest_data["people"] = {}
            manifest_data["people"]["analyst"] = str(values["analyst"])

            # Collect collaborators
            try:
                collaborators = self._collect_collaborators()
                if collaborators:
                    manifest_data["people"]["collaborators"] = collaborators
            except Exception:
                pass

            # Update datasets section
            data_enabled = bool(values.get("data_enabled", True))
            if data_enabled and self._dataset_rows:
                manifest_data["datasets"] = self._collect_datasets()
            else:
                manifest_data.pop("datasets", None)

            # Collect billing data
            try:
                billing_data = {}
                fund_code = self.query_one("#fund_code", Input).value.strip()
                if fund_code:
                    billing_data["fund_code"] = fund_code

                hourly_rate = self.query_one("#hourly_rate", Input).value.strip()
                if hourly_rate:
                    billing_data["hourly_rate"] = float(hourly_rate)

                budget_hours = self.query_one("#budget_hours", Input).value.strip()
                if budget_hours:
                    billing_data["budget_hours"] = float(budget_hours)

                spent_hours = self.query_one("#spent_hours", Input).value.strip()
                if spent_hours:
                    billing_data["spent_hours"] = float(spent_hours)

                start_date = self._normalize_date(
                    self.query_one("#billing_start_date", DateSelect).value
                )
                end_date = self._normalize_date(
                    self.query_one("#billing_end_date", DateSelect).value
                )
                if start_date:
                    billing_data["start_date"] = start_date
                if end_date:
                    billing_data["end_date"] = end_date

                notes = self.query_one("#billing_notes", TextArea).text.strip()
                if notes:
                    billing_data["notes"] = notes

                if billing_data:
                    if "billing" not in manifest_data:
                        manifest_data["billing"] = {}
                    manifest_data["billing"].update(billing_data)
            except Exception:
                pass

            # Collect timeline data
            try:
                milestones = self._collect_milestones()
                if milestones:
                    if "timeline" not in manifest_data:
                        manifest_data["timeline"] = {}
                    manifest_data["timeline"]["milestones"] = milestones
                else:
                    if "timeline" in manifest_data:
                        manifest_data["timeline"].pop("milestones", None)
                        if not manifest_data["timeline"]:
                            manifest_data.pop("timeline", None)
                if "timeline" in manifest_data:
                    manifest_data["timeline"].pop("notes", None)
                    if not manifest_data["timeline"]:
                        manifest_data.pop("timeline", None)
            except Exception:
                pass

            self._sanitize_manifest_dates(manifest_data)

            # Collect acquisition data from Science tab
            try:
                acquisition_data = {}
                sessions = self._collect_acquisition_sessions()
                if sessions:
                    acquisition_data["sessions"] = sessions

                if self._acquisition_rows:
                    idx = 0
                    try:
                        table = self.query_one("#acquisition_table", DataTable)
                        if table.cursor_row is not None:
                            idx = table.cursor_row
                    except Exception:
                        idx = 0
                    if 0 <= idx < len(self._acquisition_rows):
                        if isinstance(self._acquisition_rows[idx], dict):
                            self._acquisition_rows[idx]["channels"] = [
                                dict(row) for row in self._channel_rows
                            ]

                if acquisition_data:
                    if "acquisition" not in manifest_data:
                        manifest_data["acquisition"] = {}
                    manifest_data["acquisition"].update(acquisition_data)
                else:
                    manifest_data.pop("acquisition", None)
            except Exception:
                pass  # Skip if Science tab fields not found

            # Collect tools data from Science tab
            try:
                tools_data = {}

                git_remote = self.query_one("#git_remote", Input).value.strip()
                if git_remote:
                    tools_data["git_remote"] = git_remote

                env_select = self.query_one("#environment", Select)
                environment_value = (
                    str(env_select.value)
                    if env_select.value and env_select.value != Select.BLANK
                    else ""
                )
                if environment_value.lower() == "other":
                    custom = self.query_one("#environment_custom", Input).value.strip()
                    if custom:
                        environment_value = custom
                if environment_value:
                    tools_data["environment"] = environment_value

                env_file = self.query_one("#env_file", Input).value.strip()
                if env_file:
                    tools_data["env_file"] = env_file

                try:
                    languages_list = self.query_one("#languages_list", SelectionList)
                    languages = [str(item) for item in languages_list.selected]
                    if languages:
                        tools_data["languages"] = languages
                except Exception:
                    pass

                try:
                    software_list = self.query_one("#software_list", SelectionList)
                    software = [str(item) for item in software_list.selected]
                    if software:
                        tools_data["software"] = software
                except Exception:
                    pass

                try:
                    cluster_list = self.query_one(
                        "#cluster_packages_list", SelectionList
                    )
                    cluster_packages = [str(item) for item in cluster_list.selected]
                    if cluster_packages:
                        tools_data["cluster_packages"] = cluster_packages
                except Exception:
                    pass

                # Only update tools section if we have data to add
                if tools_data:
                    if "tools" not in manifest_data:
                        manifest_data["tools"] = {}
                    manifest_data["tools"].update(tools_data)
            except Exception:
                pass  # Skip if tools fields not found

            # Collect method data
            try:
                method_path = self.query_one("#method_path", Input).value.strip()
                if method_path:
                    manifest_data["method"] = {
                        "file_path": method_path,
                        "template_used": self._method_template_used,
                    }
            except Exception:
                pass

            # Collect hardware profiles
            if self._hardware_profiles:
                manifest_data["hardware_profiles"] = self._hardware_profiles
            else:
                manifest_data.pop("hardware_profiles", None)

            # Save the updated manifest
            ensure_directories(self._project_root)
            ensure_worklog(self._project_root)

            with open(manifest_path, "w") as f:
                yaml.safe_dump(manifest_data, f, sort_keys=False)

            if manifest_data.get("datasets"):
                local_path = manifest_data["datasets"][0].get("local")
                if local_path:
                    ensure_data_symlink(self._project_root, Path(local_path))

            # Reload the manifest to update the internal state
            self._manifest = Manifest.model_validate(manifest_data)

            self.notify("Manifest saved", severity="information")
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def _save_log(self) -> None:
        """Save worklog without exiting."""
        from .models import WorkLog
        from .worklog import save_worklog

        try:
            worklog = WorkLog(entries=self._worklog_entries)
            save_worklog(self._project_root, worklog)
            self.notify("Worklog saved", severity="information")
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

    def _save_manifest(self) -> None:
        """Save manifest tab without exiting."""
        # Reuse the validation logic from _submit_manifest but don't exit
        sections = {}
        errors = {}
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
            area = self.query_one(f"#manifest_{section}_area", TextArea)
            raw_text = area.text.strip()
            try:
                sections[section] = yaml.safe_load(raw_text) if raw_text else None
                area.remove_class("invalid")
                area.add_class("valid")
            except yaml.YAMLError as exc:
                errors[section] = str(exc)
                area.remove_class("valid")
                area.add_class("invalid")

        if errors:
            self.notify("Fix YAML errors before saving", severity="error")
            return

        try:
            manifest = Manifest.model_validate(
                {k: v for k, v in sections.items() if v is not None}
            )
            manifest_path = self._project_root / "manifest.yaml"
            dump_manifest(manifest_path, manifest)
            self.notify("Manifest saved", severity="information")
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error")

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

    def _start_sync(self, dataset: dict[str, object]) -> None:
        if self._syncing:
            return

        # Check if locally mounted
        if not bool(dataset.get("locally_mounted", False)):
            self.notify("Dataset must be locally mounted to sync", severity="warning")
            return

        source = str(dataset.get("source", "")).strip()
        local = str(dataset.get("local", "")).strip()

        if not source:
            self.notify("Source path is empty", severity="error")
            return
        if not local:
            self.notify("Local path is empty", severity="error")
            return

        source_path = Path(source).expanduser().resolve()
        local_path = Path(local).expanduser().resolve()

        # Check if source and local are the same
        if source_path == local_path:
            self.notify(
                "Local cache is same as source, sync not needed", severity="information"
            )
            return

        # Check if local cache is a symlink pointing to source
        if local_path.exists() and local_path.is_symlink():
            try:
                link_target = local_path.resolve()
                if link_target == source_path:
                    self.notify(
                        "Local cache is linked to source, sync not needed",
                        severity="information",
                    )
                    return
            except Exception:
                pass

        if not source_path.exists():
            self.notify(f"Source path does not exist: {source}", severity="error")
            return

        self._syncing = True
        self.run_worker(self._run_rsync(source, local), exclusive=True)

    async def _run_rsync(self, source: str, local: str) -> None:
        progress_bar = self.query_one("#sync_progress", ProgressBar)
        sync_pct = self.query_one("#sync_pct", Static)
        progress_bar.add_class("visible")
        sync_pct.add_class("visible")
        progress_bar.update(progress=0)
        sync_pct.update("0%")

        try:
            # Check if rsync is available
            if not shutil.which("rsync"):
                self.notify("rsync not found in PATH", severity="error")
                return

            # Run rsync with progress
            source_path = source.rstrip("/") + "/"
            proc = await asyncio.create_subprocess_exec(
                "rsync",
                "-a",
                "--info=progress2",
                "--no-inc-recursive",
                source_path,
                local,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            while True:
                if proc.stdout:
                    line = await proc.stdout.readline()
                else:
                    break

                if not line:
                    break

                # Check for None just to be safe for type checker, though readline checks above
                if line is None:
                    break

                text = line.decode().strip()
                # Parse rsync progress output: "1,234,567  45%  1.23MB/s  0:01:23"
                if "%" in text:
                    try:
                        parts = text.split()
                        for part in parts:
                            if part.endswith("%"):
                                pct = int(part.rstrip("%"))
                                progress_bar.update(progress=pct)
                                sync_pct.update(f"{pct}%")
                                break
                    except (ValueError, IndexError):
                        pass

            await proc.wait()

            if proc.returncode == 0:
                progress_bar.update(progress=100)
                sync_pct.update("100%")
                self.notify("Sync completed successfully", severity="information")
            else:
                stderr = b""
                if proc.stderr:
                    stderr = await proc.stderr.read()
                self.notify(f"Sync failed: {stderr.decode().strip()}", severity="error")
        except Exception as e:
            self.notify(f"Sync error: {e}", severity="error")
        finally:
            self._syncing = False
            # Hide progress bar after a short delay
            await asyncio.sleep(1)
            progress_bar.remove_class("visible")
            sync_pct.remove_class("visible")

    def _collect_values(self) -> dict[str, object]:
        data_enabled = self.query_one("#data_enabled", Checkbox)
        modality_custom = ""
        environment_custom = ""
        try:
            modality_custom = self.query_one("#modality_custom", Input).value
        except Exception:
            pass
        try:
            environment_custom = self.query_one("#environment_custom", Input).value
        except Exception:
            pass
        return {
            "project_name": self.query_one("#project_name", Input).value,
            "analyst": self.query_one("#analyst", Input).value,
            "data_enabled": data_enabled.value,
            "datasets": self._dataset_rows,
            "modality_custom": modality_custom,
            "environment_custom": environment_custom,
        }

    def _refresh_init_validation(self) -> None:
        for field_id in ("project_name", "analyst"):
            widget = self.query_one(f"#{field_id}", Input)
            widget.remove_class("valid")
            widget.remove_class("invalid")
            if widget.value.strip():
                widget.add_class("valid")
            else:
                widget.add_class("invalid")

    def _toggle_data_sections(self, enabled: bool) -> None:
        """Show/hide data sections based on enabled state."""
        try:
            data_sections = self.query_one("#data_sections", Vertical)
            if enabled:
                data_sections.remove_class("hidden")
            else:
                data_sections.add_class("hidden")
        except Exception:
            pass

    def _ensure_dataset_rows(self) -> None:
        if self._dataset_rows:
            return
        self._dataset_rows = []

    def _update_method_path_suggestions(
        self, input_id: str, current_value: str
    ) -> None:
        """Update method path suggestions dropdown."""
        try:
            suggestions = self._method_path_suggestions or self.query_one(
                "#method_path_suggestions", OptionList
            )
            suggestions.clear_options()

            if not current_value:
                self._hide_method_path_suggestions()
                return

            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()

            if not search_dir.exists():
                self._hide_method_path_suggestions()
                return

            entries = []
            for entry in search_dir.iterdir():
                name = entry.name
                if prefix and not name.lower().startswith(prefix):
                    continue
                entries.append(str(entry))
            entries = sorted(entries)[:10]

            if entries:
                for entry in entries:
                    suggestions.add_option(Option(entry))
                suggestions.add_class("visible")
                self._method_path_suggestions_visible = True
                self._active_method_input = input_id
            else:
                self._hide_method_path_suggestions()
        except Exception:
            self._hide_method_path_suggestions()

    def _hide_method_path_suggestions(self) -> None:
        """Hide the method path suggestions dropdown."""
        try:
            suggestions = self._method_path_suggestions or self.query_one(
                "#method_path_suggestions", OptionList
            )
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._active_method_input = None
            self._method_path_suggestions_visible = False
        except Exception:
            pass

    def _collect_collaborators(self) -> list[dict[str, str]]:
        collaborators = []
        for row in self._collaborator_rows:
            name = row.get("name", "").strip()
            role = row.get("role", "").strip()
            email = row.get("email", "").strip()
            affiliation = row.get("affiliation", "").strip()
            if not any([name, role, email, affiliation]):
                continue
            collab = {"name": name}
            if role:
                collab["role"] = role
            if email:
                collab["email"] = email
            if affiliation:
                collab["affiliation"] = affiliation
            collaborators.append(collab)
        return collaborators

    def _ensure_collaborator_rows(self) -> None:
        if self._collaborator_rows:
            return
        # Removed the fallback empty row logic
        self._collaborator_rows = []

    def _populate_collaborators_table(self) -> None:
        """Populate the DataTable with collaborator data."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if not table.columns:
                # Add columns with proportional widths
                table.add_column("Name", width=20)
                table.add_column("Role", width=15)
                table.add_column("Email", width=25)
                table.add_column("Affiliation", width=20)
            table.clear()
            for idx, row in enumerate(self._collaborator_rows):
                table.add_row(
                    row.get("name", ""),
                    row.get("role", ""),
                    row.get("email", ""),
                    row.get("affiliation", ""),
                    key=str(idx),
                )
        except Exception:
            pass

    def action_add_collaborator_row(self) -> None:
        """Action to add a new collaborator row (Ctrl+A)."""
        # Always allow adding, even if table not focused (as long as we are in setup tab)
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "setup":
            return

        self.push_screen(
            CollaboratorModal(self._load_role_options()), self._handle_new_collaborator
        )

    def _handle_new_collaborator(self, data: dict[str, str] | None) -> None:
        """Add new collaborator after modal close."""
        if data:
            self._collaborator_rows.append(data)
            self._populate_collaborators_table()

    def action_remove_collaborator_row(self) -> None:
        """Action to remove the selected collaborator row (Ctrl+D)."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            # Only remove if table is focused or active
            if (
                not table.has_focus
                and self.query_one("#tabs", TabbedContent).active != "setup"
            ):
                return

            if table.cursor_row is None:
                return

            idx = table.cursor_row
            if 0 <= idx < len(self._collaborator_rows):
                self._collaborator_rows.pop(idx)

            self._populate_collaborators_table()

            # Adjust cursor position
            if self._collaborator_rows:
                idx = min(idx, len(self._collaborator_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection (Enter key or click) in collaborators table for inline editing."""
        if event.data_table.id != "collaborators_table":
            return
        # Start editing when Enter is pressed or cell is clicked
        self._edit_collaborator_cell()

    def _edit_collaborator_cell(self) -> None:
        """Open an input dialog to edit the current cell."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None or table.cursor_column is None:
                return

            row_idx = table.cursor_row
            col_idx = table.cursor_column

            if row_idx >= len(self._collaborator_rows):
                return

            column_names = ["name", "role", "email", "affiliation"]
            if col_idx >= len(column_names):
                return

            field_name = column_names[col_idx]
            current_value = self._collaborator_rows[row_idx].get(field_name, "")

            # For role column, show select dialog
            if field_name == "role":
                self._edit_role_cell(row_idx, col_idx, current_value)
            else:
                self._edit_text_cell(row_idx, col_idx, field_name, current_value)
        except Exception as e:
            self.notify(f"Error editing cell: {e}", severity="error")

    def _edit_text_cell(
        self, row_idx: int, col_idx: int, field_name: str, current_value: str
    ) -> None:
        """Deprecated: inline cell editor removed."""
        return

    def _edit_role_cell(self, row_idx: int, col_idx: int, current_value: str) -> None:
        """Deprecated: inline cell editor removed."""
        return

    def _update_collaborator_from_inputs(self) -> None:
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            name = self.query_one("#collab_name_input", Input).value.strip()
            role = self.query_one("#collab_role_select", Select).value
            email = self.query_one("#collab_email_input", Input).value.strip()
            affiliation = self.query_one(
                "#collab_affiliation_input", Input
            ).value.strip()
            role_value = "" if role in (None, Select.BLANK) else str(role)
            self._collaborator_rows[idx] = {
                "name": name,
                "role": role_value,
                "email": email,
                "affiliation": affiliation,
            }
            self._populate_collaborators_table()
        except Exception:
            pass

    def _remove_selected_collaborator(self) -> None:
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._collaborator_rows):
                self._collaborator_rows.pop(idx)
            if not self._collaborator_rows:
                self._collaborator_rows = [
                    {"name": "", "role": "", "email": "", "affiliation": ""}
                ]
            self._populate_collaborators_table()
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Channel Table Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _populate_channels_table(self) -> None:
        """Populate the DataTable with channel data."""
        try:
            table = self.query_one("#channels_table", DataTable)
            if not table.columns:
                table.add_column("Name", width=15)
                table.add_column("Fluorophore", width=15)
                table.add_column("Ex (nm)", width=10)
                table.add_column("Em (nm)", width=10)
            table.clear()
            for idx, row in enumerate(self._channel_rows):
                table.add_row(
                    row.get("name", ""),
                    row.get("fluorophore", ""),
                    row.get("excitation_nm", ""),
                    row.get("emission_nm", ""),
                    key=str(idx),
                )
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Acquisition Sessions Table Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _populate_acquisition_table(self) -> None:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            table.clear(columns=True)
            table.add_columns(
                "Date",
                "Microscope",
                "Modality",
                "Objective",
                "Voxel",
                "Time (s)",
                "Notes",
            )
            for idx, row in enumerate(self._acquisition_rows):
                table.add_row(
                    self._format_date_cell(row.get("imaging_date")),
                    str(row.get("microscope", "")),
                    str(row.get("modality", "")),
                    str(row.get("objective", "")),
                    self._format_voxel(row),
                    str(row.get("time_interval_s", "")),
                    self._truncate_text(str(row.get("notes", ""))),
                    key=str(idx),
                )
        except Exception:
            pass

    def _load_session_channels(self, idx: int) -> None:
        try:
            if not (0 <= idx < len(self._acquisition_rows)):
                self._channel_rows = []
                self._populate_channels_table()
                return
            row = self._acquisition_rows[idx]
            self._selected_acquisition_index = idx
            channels = row.get("channels", []) if isinstance(row, dict) else []
            if (
                isinstance(channels, list)
                and channels
                and isinstance(channels[0], dict)
            ):
                self._channel_rows = [
                    {
                        "name": ch.get("name", ""),
                        "fluorophore": ch.get("fluorophore", ""),
                        "excitation_nm": str(ch.get("excitation_nm", "")),
                        "emission_nm": str(ch.get("emission_nm", "")),
                    }
                    for ch in channels
                ]
            else:
                self._channel_rows = []
            self._populate_channels_table()
        except Exception:
            pass

    def _store_channels_for_selected_session(self) -> None:
        try:
            idx = self._get_selected_acquisition_index()
            if idx is None:
                return
            self._store_channels_for_session(idx)
        except Exception:
            pass

    def _store_channels_for_session(self, idx: int) -> None:
        if not (0 <= idx < len(self._acquisition_rows)):
            return
        if isinstance(self._acquisition_rows[idx], dict):
            self._acquisition_rows[idx]["channels"] = [
                dict(row) for row in self._channel_rows
            ]

    def _get_selected_acquisition_index(self) -> Optional[int]:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            idx = table.cursor_row
            if idx is None and self._acquisition_rows:
                idx = 0
            if idx is None or not (0 <= idx < len(self._acquisition_rows)):
                return None
            return idx
        except Exception:
            return None

    def _format_voxel(self, row: dict[str, object]) -> str:
        x = str(row.get("voxel_x", "")).strip()
        y = str(row.get("voxel_y", "")).strip()
        z = str(row.get("voxel_z", "")).strip()
        if not any([x, y, z]):
            return ""
        return f"{x} x {y} x {z}"

    def action_add_acquisition(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "science":
            return
        science_sections = self.query_one("#science_sections", TabbedContent)
        if science_sections.active != "science_acquisition":
            return
        self._store_channels_for_selected_session()
        initial_data = None
        try:
            table = self.query_one("#acquisition_table", DataTable)
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self._acquisition_rows):
                initial_data = dict(self._acquisition_rows[idx])
        except Exception:
            initial_data = None
        self.push_screen(
            AcquisitionSessionModal(initial_data),
            self._handle_new_acquisition,
        )

    def action_remove_acquisition(self) -> None:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            if table.cursor_row is None:
                self.notify("Select a session to remove", severity="warning")
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._acquisition_rows):
                self._acquisition_rows.pop(idx)
            self._populate_acquisition_table()
            if self._acquisition_rows:
                idx = min(idx, len(self._acquisition_rows) - 1)
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            else:
                self._selected_acquisition_index = None
                self._channel_rows = []
                self._populate_channels_table()
        except Exception:
            pass

    def _handle_new_acquisition(self, data: dict[str, object] | None) -> None:
        if data:
            if "channels" not in data:
                data["channels"] = []
            self._acquisition_rows.append(data)
            self._populate_acquisition_table()

            try:
                table = self.query_one("#acquisition_table", DataTable)
                idx = len(self._acquisition_rows) - 1
                table.show_cursor = True
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            except Exception:
                pass

    def _handle_edit_acquisition(
        self, idx: int, data: dict[str, object] | None
    ) -> None:
        if data and 0 <= idx < len(self._acquisition_rows):
            existing = self._acquisition_rows[idx]
            if isinstance(existing, dict) and "channels" in existing:
                data.setdefault("channels", existing.get("channels", []))
            self._acquisition_rows[idx] = data
            self._populate_acquisition_table()
            try:
                table = self.query_one("#acquisition_table", DataTable)
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────────
    # Milestone Table Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _populate_milestones_table(self) -> None:
        try:
            table = self.query_one("#milestones_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "Target", "Actual", "Status", "Notes")
            for idx, row in enumerate(self._milestone_rows):
                table.add_row(
                    str(row.get("name", "")),
                    self._format_date_cell(row.get("target_date")),
                    self._format_date_cell(row.get("actual_date")),
                    str(row.get("status", "pending")),
                    self._truncate_text(str(row.get("notes", ""))),
                    key=str(idx),
                )
        except Exception:
            pass

    def _format_date_cell(self, value: object) -> str:
        if isinstance(value, date):
            return value.isoformat()
        if value:
            return str(value)
        return ""

    def _normalize_date(self, value: object) -> date | None:
        if value is None:
            return None
        # Handle datetime (including pendulum.DateTime) - extract pure Python date
        if isinstance(value, datetime):
            return date(value.year, value.month, value.day)
        # Handle pure date objects (but not datetime subclasses)
        if type(value) is date:
            return value
        # Handle objects with .date() method (e.g., pendulum types)
        date_method = getattr(value, "date", None)
        if callable(date_method):
            try:
                result = date_method()
                # Convert to pure Python date
                if isinstance(result, date):
                    return date(result.year, result.month, result.day)
                return None
            except Exception:
                return None
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _to_pendulum_date(self, value: object) -> pendulum.DateTime | None:
        if value is None:
            return None
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, datetime):
            return pendulum.datetime(value.year, value.month, value.day)
        if type(value) is date:
            return pendulum.datetime(value.year, value.month, value.day)
        date_method = getattr(value, "date", None)
        if callable(date_method):
            try:
                result = date_method()
                if isinstance(result, date):
                    return pendulum.datetime(result.year, result.month, result.day)
            except Exception:
                return None
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                if isinstance(parsed, pendulum.DateTime):
                    return parsed
                return None
            except Exception:
                return None
        return None

    def _sanitize_manifest_dates(self, manifest_data: dict[str, object]) -> None:
        timeline = manifest_data.get("timeline")
        if isinstance(timeline, dict):
            milestones = timeline.get("milestones")
            if isinstance(milestones, list):
                for milestone in milestones:
                    if not isinstance(milestone, dict):
                        continue
                    for field in ("target_date", "actual_date"):
                        milestone[field] = self._normalize_date(milestone.get(field))

        billing = manifest_data.get("billing")
        if isinstance(billing, dict):
            for field in ("start_date", "end_date"):
                billing[field] = self._normalize_date(billing.get(field))

    def _truncate_text(self, value: str, max_len: int = 30) -> str:
        if len(value) <= max_len:
            return value
        return f"{value[: max_len - 3]}..."

    def action_add_milestone(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "admin":
            return
        admin_sections = self.query_one("#admin_sections", TabbedContent)
        if admin_sections.active != "admin_timeline":
            return
        initial_data = None
        try:
            table = self.query_one("#milestones_table", DataTable)
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self._milestone_rows):
                initial_data = dict(self._milestone_rows[idx])
                initial_data["name"] = ""
        except Exception:
            initial_data = None
        self.push_screen(MilestoneModal(initial_data), self._handle_new_milestone)

    def action_remove_milestone(self) -> None:
        try:
            table = self.query_one("#milestones_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._milestone_rows):
                self._milestone_rows.pop(idx)
            self._populate_milestones_table()
            if self._milestone_rows:
                idx = min(idx, len(self._milestone_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _handle_new_milestone(self, data: dict[str, object] | None) -> None:
        if data:
            self._milestone_rows.append(data)
            self._populate_milestones_table()

    def _handle_edit_milestone(self, idx: int, data: dict[str, object] | None) -> None:
        if data and 0 <= idx < len(self._milestone_rows):
            self._milestone_rows[idx] = data
            self._populate_milestones_table()

    # ─────────────────────────────────────────────────────────────────────────
    # Dataset Table Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _populate_datasets_table(self) -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "Endpoint", "Source", "Local", "Format", "Size")
            for idx, row in enumerate(self._dataset_rows):
                table.add_row(
                    str(row.get("name", "")),
                    str(row.get("endpoint", "")),
                    self._truncate_path(str(row.get("source", ""))),
                    self._truncate_path(str(row.get("local", ""))),
                    str(row.get("format", "")),
                    self._format_dataset_size(row),
                    key=str(idx),
                )
        except Exception:
            pass

    def _format_dataset_size(self, row: dict[str, object]) -> str:
        raw_size = str(row.get("raw_size_gb", "")).strip()
        if not raw_size:
            return ""
        unit = str(row.get("raw_size_unit", "gb")).lower()
        suffix = unit.upper() if unit else "GB"
        return f"{raw_size} {suffix}"

    def _truncate_path(self, value: str, max_len: int = 30) -> str:
        if len(value) <= max_len:
            return value
        return f"...{value[-(max_len - 3) :]}"

    def action_add_dataset(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "setup":
            return
        initial_data = None
        try:
            table = self.query_one("#datasets_table", DataTable)
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self._dataset_rows):
                initial_data = dict(self._dataset_rows[idx])
                initial_data["name"] = ""
        except Exception:
            initial_data = None
        self.push_screen(
            DatasetModal(
                self._load_endpoint_options(),
                self._load_dataset_format_options(),
                initial_data,
            ),
            self._handle_new_dataset,
        )

    def action_remove_dataset(self) -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            if table.cursor_row is None:
                self.notify("Select a dataset to remove", severity="warning")
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._dataset_rows):
                self._dataset_rows.pop(idx)
            self._populate_datasets_table()
            if self._dataset_rows:
                idx = min(idx, len(self._dataset_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def action_sync_dataset(self) -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            idx = table.cursor_row
            if idx is None and self._dataset_rows:
                idx = 0
            if idx is None or not (0 <= idx < len(self._dataset_rows)):
                self.notify("Select a dataset to sync", severity="warning")
                return
            row = self._dataset_rows[idx]
            self._start_sync(row)
        except Exception:
            pass

    def _handle_new_dataset(self, data: dict[str, object] | None) -> None:
        if data:
            self._dataset_rows.append(data)
            self._populate_datasets_table()

    def _handle_edit_dataset(self, idx: int, data: dict[str, object] | None) -> None:
        if data and 0 <= idx < len(self._dataset_rows):
            self._dataset_rows[idx] = data
            self._populate_datasets_table()
            try:
                table = self.query_one("#datasets_table", DataTable)
                table.move_cursor(row=idx, column=0)
            except Exception:
                pass

    def action_add_channel_row(self) -> None:
        """Action to add a new channel row."""
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "science":
            return
        if not self._acquisition_rows:
            self.notify("Add an imaging session first", severity="warning")
            return
        self.push_screen(ChannelModal(), self._handle_new_channel)

    def _handle_new_channel(self, data: dict[str, str] | None) -> None:
        """Add new channel after modal close."""
        if data:
            self._channel_rows.append(data)
            self._populate_channels_table()
            self._store_channels_for_selected_session()

    def action_remove_channel_row(self) -> None:
        """Action to remove the selected channel row."""
        try:
            table = self.query_one("#channels_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._channel_rows):
                self._channel_rows.pop(idx)
            self._populate_channels_table()
            self._store_channels_for_selected_session()
            if self._channel_rows:
                idx = min(idx, len(self._channel_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _handle_edit_channel(self, idx: int, data: dict[str, str] | None) -> None:
        """Update channel data after modal close."""
        if data and 0 <= idx < len(self._channel_rows):
            self._channel_rows[idx] = data
            self._populate_channels_table()
            self._store_channels_for_selected_session()

    def _collect_channels(self) -> list[dict[str, object]]:
        """Collect channel data for saving."""
        channels = []
        for row in self._channel_rows:
            name = row.get("name", "").strip()
            if not name:
                continue
            channel: dict[str, object] = {"name": name}
            fluorophore = row.get("fluorophore", "").strip()
            if fluorophore:
                channel["fluorophore"] = fluorophore
            ex_nm = row.get("excitation_nm", "").strip()
            if ex_nm and ex_nm.isdigit():
                channel["excitation_nm"] = int(ex_nm)
            em_nm = row.get("emission_nm", "").strip()
            if em_nm and em_nm.isdigit():
                channel["emission_nm"] = int(em_nm)
            channels.append(channel)
        return channels

    def _collect_datasets(self) -> list[dict[str, object]]:
        datasets: list[dict[str, object]] = []
        for row in self._dataset_rows:
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            dataset: dict[str, object] = {"name": name}
            endpoint = str(row.get("endpoint", "")).strip()
            if endpoint:
                dataset["endpoint"] = endpoint
            source = str(row.get("source", "")).strip()
            if source:
                dataset["source"] = source
            local = str(row.get("local", "")).strip()
            if local:
                dataset["local"] = local
            dataset["locally_mounted"] = bool(row.get("locally_mounted", False))
            description = str(row.get("description", "")).strip()
            if description:
                dataset["description"] = description
            data_format = str(row.get("format", "")).strip()
            if data_format:
                dataset["format"] = data_format
            raw_size = str(row.get("raw_size_gb", "")).strip()
            if raw_size:
                try:
                    dataset["raw_size_gb"] = float(raw_size)
                except ValueError:
                    pass
            raw_unit = str(row.get("raw_size_unit", "")).strip()
            if raw_unit:
                dataset["raw_size_unit"] = raw_unit
            compressed = row.get("compressed")
            if compressed is not None:
                dataset["compressed"] = bool(compressed)
            uncompressed_size = str(row.get("uncompressed_size_gb", "")).strip()
            if uncompressed_size:
                try:
                    dataset["uncompressed_size_gb"] = float(uncompressed_size)
                except ValueError:
                    pass
            uncompressed_unit = str(row.get("uncompressed_size_unit", "")).strip()
            if uncompressed_unit:
                dataset["uncompressed_size_unit"] = uncompressed_unit
            datasets.append(dataset)
        return datasets

    def _collect_milestones(self) -> list[dict[str, object]]:
        milestones: list[dict[str, object]] = []
        for row in self._milestone_rows:
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            milestone: dict[str, object] = {"name": name}
            target = self._normalize_date(row.get("target_date"))
            actual = self._normalize_date(row.get("actual_date"))
            if target:
                milestone["target_date"] = target
            if actual:
                milestone["actual_date"] = actual
            status = str(row.get("status", "")).strip()
            if status:
                milestone["status"] = status
            notes = str(row.get("notes", "")).strip()
            if notes:
                milestone["notes"] = notes
            milestones.append(milestone)
        return milestones

    def _collect_acquisition_sessions(self) -> list[dict[str, object]]:
        sessions: list[dict[str, object]] = []
        for row in self._acquisition_rows:
            session: dict[str, object] = {}
            imaging_date = self._normalize_date(row.get("imaging_date"))
            if imaging_date:
                session["imaging_date"] = imaging_date
            microscope = str(row.get("microscope", "")).strip()
            if microscope:
                session["microscope"] = microscope
            modality = str(row.get("modality", "")).strip()
            if modality:
                session["modality"] = modality
            objective = str(row.get("objective", "")).strip()
            if objective:
                session["objective"] = objective

            voxel_x = str(row.get("voxel_x", "")).strip()
            voxel_y = str(row.get("voxel_y", "")).strip()
            voxel_z = str(row.get("voxel_z", "")).strip()
            if voxel_x or voxel_y or voxel_z:
                session["voxel_size"] = {
                    "x_um": float(voxel_x) if voxel_x else None,
                    "y_um": float(voxel_y) if voxel_y else None,
                    "z_um": float(voxel_z) if voxel_z else None,
                }

            time_interval = str(row.get("time_interval_s", "")).strip()
            if time_interval:
                session["time_interval_s"] = float(time_interval)

            notes = str(row.get("notes", "")).strip()
            if notes:
                session["notes"] = notes

            channels = row.get("channels", []) if isinstance(row, dict) else []
            if isinstance(channels, list) and channels:
                session["channels"] = channels

            if session:
                sessions.append(session)
        return sessions

    def _submit_init(self) -> None:
        if self._mode not in ("init", "menu", "both"):
            if self._init_error is not None:
                self._init_error.update("Initialization is disabled in log-only mode.")
            return
        values = self._collect_values()
        # Check required string fields
        required_fields = ["project_name", "analyst"]
        missing = [
            key for key in required_fields if not str(values.get(key, "")).strip()
        ]
        if missing:
            if self._init_error is not None:
                self._init_error.update(
                    "Please fill in all required fields before saving."
                )
            self.notify("Please fill in required fields", severity="error")
            return
        self.notify("Saving manifest...", severity="information")
        self._store_ui_state()
        self.exit({"action": "init", "data": values})

    def _submit_log(self) -> None:
        if self._mode not in ("log", "menu", "both"):
            if self._log_error is not None:
                self._log_error.update("Logging is disabled in init-only mode.")
            return
        self._store_ui_state()
        self.exit({"action": "log", "entries": self._worklog_entries})

    def _set_tab(self, tab_id: str) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        tabbed.active = tab_id

    def _cycle_tab(self, delta: int) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        tabs = ["setup", "science", "admin", "outputs", "hub", "log", "idea"]
        try:
            current = tabs.index(tabbed.active)
        except ValueError:
            current = 0
        tabbed.active = tabs[(current + delta) % len(tabs)]

    def _format_duration(self, seconds: int) -> str:
        duration = timedelta(seconds=seconds)
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"

    def _apply_entry_status(self, entry: LogEntry, status: TaskStatus) -> LogEntry:
        now = datetime.now()
        previous_status = entry.status
        if status == TaskStatus.paused and entry.status == TaskStatus.active:
            entry.elapsed_seconds += int((now - entry.checkin).total_seconds())
            entry.status = TaskStatus.paused
            entry.checkout = entry.checkin
            return entry
        if status == TaskStatus.active and entry.status == TaskStatus.paused:
            entry.status = TaskStatus.active
            entry.checkin = now
            entry.checkout = None
            return entry
        entry.status = status
        if status == TaskStatus.completed:
            entry.checkout = (
                entry.checkin if previous_status == TaskStatus.paused else now
            )
        return entry

    def _tick_worklog(self) -> None:
        self._refresh_worklog_lists()

    def _refresh_worklog_lists(self) -> None:
        try:
            active_list = self.query_one("#active_tasks", ListView)
            completed_list = self.query_one("#completed_tasks", ListView)
        except Exception:
            return

        active_list.clear()
        completed_list.clear()
        today = date.today()
        for idx, entry in enumerate(self._worklog_entries):
            duration = self._format_duration(entry.duration_seconds())
            label = f"{entry.task} [{entry.status.value}] ({duration})"
            if entry.status in (TaskStatus.active, TaskStatus.paused):
                active_list.append(ListItem(Static(label), id=f"active-{idx}"))
            if entry.status == TaskStatus.completed:
                checkout = entry.checkout or entry.checkin
                if checkout.date() == today:
                    completed_list.append(
                        ListItem(Static(label), id=f"completed-{idx}")
                    )

    def _add_task(self) -> None:
        description = self.query_one("#task_description", Input).value.strip()
        task_type = self.query_one("#task_type", Select).value
        notes = self.query_one("#task_notes", Input).value.strip() or None
        if not description:
            if self._log_error is not None:
                self._log_error.update("Task description is required.")
            return
        entry = LogEntry(
            checkin=datetime.now(),
            task=description,
            type=str(task_type),
            status=TaskStatus.active,
            notes=notes,
        )
        self._worklog_entries.append(entry)
        self.query_one("#task_description", Input).value = ""
        self.query_one("#task_notes", Input).value = ""
        self._refresh_worklog_lists()

    def _checkout_task(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to check out.")
            return
        entry = self._worklog_entries[self._selected_active_index]
        entry = self._apply_entry_status(entry, TaskStatus.completed)
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()

    def _toggle_pause_task(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to pause or resume.")
            return
        entry = self._worklog_entries[self._selected_active_index]
        if entry.status == TaskStatus.active:
            entry = self._apply_entry_status(entry, TaskStatus.paused)
        elif entry.status == TaskStatus.paused:
            entry = self._apply_entry_status(entry, TaskStatus.active)
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()

    def _set_task_status(self) -> None:
        if self._selected_active_index is None:
            if self._log_error is not None:
                self._log_error.update("Select an active task to update status.")
            return
        status_value = self.query_one("#task_status", Select).value
        entry = self._worklog_entries[self._selected_active_index]
        entry = self._apply_entry_status(entry, TaskStatus(str(status_value)))
        self._worklog_entries[self._selected_active_index] = entry
        self._refresh_worklog_lists()

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

    def _refresh_artifact_list(self) -> None:
        try:
            list_view = self.query_one("#artifact_list", ListView)
        except Exception:
            return
        list_view.clear()
        for idx, artifact in enumerate(self._artifact_entries):
            label = f"{artifact.path} [{artifact.status}] ({artifact.type})"
            list_view.append(ListItem(Static(label), id=f"artifact-{idx}"))

    def _add_artifact(self) -> None:
        path = self.query_one("#artifact_path", Input).value.strip()
        artifact_type = (
            self.query_one("#artifact_type", Input).value.strip() or "unknown"
        )
        status = self.query_one("#artifact_status", Select).value or "draft"
        if not path:
            self.notify("Artifact path is required", severity="error")
            return
        artifact = Artifact(path=path, type=artifact_type, status=str(status))
        self._artifact_entries.append(artifact)
        self.query_one("#artifact_path", Input).value = ""
        self.query_one("#artifact_type", Input).value = ""
        self._refresh_artifact_list()

    def _update_artifact_status(self) -> None:
        if self._selected_artifact_index is None:
            self.notify("Select an artifact to update", severity="warning")
            return
        status = self.query_one("#artifact_update_status", Select).value
        artifact = self._artifact_entries[self._selected_artifact_index]
        artifact.status = str(status)
        artifact.updated = date.today()
        self._artifact_entries[self._selected_artifact_index] = artifact
        self._refresh_artifact_list()

    def _submit_artifact(self) -> None:
        self._store_ui_state()
        self.exit(
            {
                "action": "artifact",
                "artifacts": [artifact for artifact in self._artifact_entries],
            }
        )

    def _load_manifest_sections(self) -> None:
        if self._manifest is None:
            return
        manifest_dict = self._manifest.model_dump(mode="json", exclude_none=True)
        for section, value in manifest_dict.items():
            area_id = f"#manifest_{section}_area"
            try:
                area = self.query_one(area_id, TextArea)
            except Exception:
                continue
            text = (
                yaml.safe_dump(value, sort_keys=False).strip()
                if value is not None
                else ""
            )
            area.text = text
            area.remove_class("invalid")
            area.remove_class("valid")
            area.add_class("valid")

    def _submit_manifest(self) -> None:
        sections = {}
        errors = {}
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
            area = self.query_one(f"#manifest_{section}_area", TextArea)
            raw_text = area.text.strip()
            try:
                sections[section] = yaml.safe_load(raw_text) if raw_text else None
                area.remove_class("invalid")
                area.add_class("valid")
            except yaml.YAMLError as exc:
                errors[section] = str(exc)
                area.remove_class("valid")
                area.add_class("invalid")

        if errors:
            if self._manifest_errors is not None:
                self._manifest_errors.update("Fix YAML errors before saving.")
            return

        try:
            manifest = Manifest.model_validate(
                {k: v for k, v in sections.items() if v is not None}
            )
        except Exception as exc:
            if self._manifest_errors is not None:
                self._manifest_errors.update(f"Validation error: {exc}")
            return

        self._store_ui_state()
        self.exit({"action": "manifest", "manifest": manifest})
