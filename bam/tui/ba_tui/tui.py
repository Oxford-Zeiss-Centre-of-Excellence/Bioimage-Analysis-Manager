from __future__ import annotations

from datetime import date, datetime, timedelta
from importlib import metadata
from pathlib import Path
from typing import Callable, Optional, cast

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
    Tree,
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
from .models import Artifact, FigureElement, FigureNode, Manifest
from .screens import (
    AcquisitionSessionModal,
    ArtifactModal,
    ChannelModal,
    CollaboratorModal,
    CustomInputModal,
    DatasetModal,
    DeleteConfirmModal,
    DirectoryPickerScreen,
    EditSessionModal,
    ExitConfirmScreen,
    FigureElementModal,
    FigureNodeModal,
    HardwareModal,
    MilestoneModal,
    NewManifestConfirmScreen,
    ResetConfirmScreen,
    SessionNoteModal,
    TaskModal,
)
from .styles import APP_CSS, LOG_TAB_CSS
from .widgets import DateSelect
from .utils import detect_git_remote
from .tabs.admin import compose_admin_tab
from .tabs.hub import compose_hub_tab
from .tabs.idea import compose_idea_tab
from .tabs.log import compose_log_tab
from .tabs.outputs import compose_outputs_tab
from .tabs.science import compose_science_tab
from .tabs.setup import compose_setup_tab


def _serialize_figures(figures) -> list[dict[str, object]]:
    def serialize_node(node) -> dict[str, object]:
        if isinstance(node, FigureElement):
            return {
                "type": "element",
                "id": node.id,
                "output_path": node.output_path,
                "source_type": node.source_type.value
                if hasattr(node.source_type, "value")
                else str(node.source_type),
                "source_ref": node.source_ref,
                "input_files": list(node.input_files),
                "parameters": node.parameters or "",
                "status": node.status.value
                if hasattr(node.status, "value")
                else str(node.status),
                "description": node.description or "",
            }
        return {
            "type": "node",
            "id": node.id,
            "title": node.title,
            "description": node.description or "",
            "children": [serialize_node(child) for child in node.children],
        }

    return [serialize_node(node) for node in figures]


def _deserialize_figures(data: list[dict[str, object]]) -> list[FigureNode]:
    def build_node(payload: dict[str, object]):
        node_type = payload.get("type", "node")
        if node_type == "element":
            input_files = payload.get("input_files", [])
            input_list = (
                [str(item) for item in input_files]
                if isinstance(input_files, list)
                else []
            )
            return FigureElement.model_validate(
                {
                    "id": str(payload.get("id", "")),
                    "output_path": str(payload.get("output_path", "")),
                    "source_type": str(payload.get("source_type", "script")),
                    "source_ref": str(payload.get("source_ref", "")),
                    "input_files": input_list,
                    "parameters": str(payload.get("parameters", "")) or None,
                    "status": str(payload.get("status", "draft")),
                    "description": str(payload.get("description", "")) or None,
                }
            )
        children = payload.get("children", [])
        return FigureNode(
            id=str(payload.get("id", "")),
            title=str(payload.get("title", "")),
            description=str(payload.get("description", "")) or None,
            children=[
                build_node(child)
                for child in (children if isinstance(children, list) else [])
                if isinstance(child, dict)
            ],
        )

    nodes = [build_node(item) for item in data if isinstance(item, dict)]
    return [node for node in nodes if isinstance(node, FigureNode)]


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
    CSS = APP_CSS + LOG_TAB_CSS

    BINDINGS = [
        Binding("ctrl+n", "new_manifest", "New", show=True, priority=True),
        Binding("ctrl+s", "save_current", "Save", show=True, priority=True),
        Binding("ctrl+r", "reset_manifest", "Reset", show=True, priority=True),
        Binding("ctrl+x", "exit_app", "Exit", show=True, priority=True),
        Binding("ctrl+left", "prev_main_tab", "◀Tab", show=True, priority=True),
        Binding("ctrl+right", "next_main_tab", "Tab▶", show=True, priority=True),
        Binding("alt+left", "prev_sub_tab", "◀Sub-tab", show=True, priority=True),
        Binding("alt+right", "next_sub_tab", "Sub-tab▶", show=True, priority=True),
        Binding("f1", "show_tab_1", "", show=False),
        Binding("f2", "show_tab_2", "", show=False),
        Binding("f3", "show_tab_3", "", show=False),
        Binding("f4", "show_tab_4", "", show=False),
        Binding("f5", "show_tab_5", "", show=False),
        Binding("f6", "show_tab_6", "", show=False),
        Binding("f7", "show_tab_7", "", show=False),
        Binding("a", "worklog_new_task", "", show=False),
        Binding("i", "worklog_check_in", "", show=False),
        Binding("o", "worklog_check_out", "", show=False),
        Binding("n", "worklog_add_note", "", show=False),
        Binding("c", "worklog_complete", "", show=False),
        Binding("d", "worklog_delete", "", show=False),
        Binding("enter", "worklog_edit", "", show=False),
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
        worklog_entries: Optional[list] = None,  # Legacy, not used anymore
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
        self._worklog_entries: list = worklog_entries or []  # Legacy, not used anymore
        self._task_types = task_types or []
        self._last_click_time: float = 0.0
        self._last_click_row: tuple[str, object] | None = None
        self._idea_title = idea_title
        self._artifact_entries: list[Artifact] = artifacts or []
        self._manifest = manifest
        self._selected_active_index: Optional[int] = None
        self._selected_artifact_index: Optional[int] = None
        self._figure_tree_data: list[dict[str, object]] = []
        self._figure_expanded_ids: set[str] = set()
        self._figure_selected_id: str | None = None
        self._artifact_rows: list[dict[str, object]] = []
        self._archive_defaults: dict[str, object] = {}
        self._publication_defaults: dict[str, object] = {}
        self._archive_path_suggestions_visible = False
        self._archive_path_suggestions = None
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
        self._init_outputs_rows()

    def _init_outputs_rows(self) -> None:
        figures = self._defaults.get("figures")
        if isinstance(figures, list):
            self._figure_tree_data = [dict(item) for item in figures]
        artifacts = self._defaults.get("artifacts")
        if isinstance(artifacts, list):
            self._artifact_rows = [dict(item) for item in artifacts]
        elif self._artifact_entries:
            self._artifact_rows = [
                artifact.model_dump() for artifact in self._artifact_entries
            ]
        publication = self._defaults.get("publication")
        if isinstance(publication, dict):
            self._publication_defaults = dict(publication)
            self._defaults.update(self._publication_defaults)
        archive = self._defaults.get("archive")
        if isinstance(archive, dict):
            self._archive_defaults = dict(archive)
            self._defaults.update(self._archive_defaults)

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
                "image_quality": str(item.get("image_quality", ""))
                if isinstance(item, dict)
                else "",
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
            yield from compose_outputs_tab(cast(object, self))
            yield from compose_hub_tab(self)
            yield from compose_log_tab(self)
            yield from compose_idea_tab(self)
        yield Footer()

    def on_mount(self) -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if self._mode in ("log", "idea", "outputs", "hub"):
            tabbed.active = self._mode
        elif self._mode == "artifact":
            tabbed.active = "outputs"
        else:
            tabbed.active = "setup"
            # Only restore saved UI state for menu mode
            if self._mode == "menu":
                self._apply_ui_state()

        self._refresh_init_validation()

        # Initialize new task-based worklog system
        self._init_worklog()

        # Migrate from old CSV if needed
        from .worklog import migrate_csv_to_yaml, init_worklog_manifest_section

        migrated = migrate_csv_to_yaml(self._project_root)
        if migrated:
            self.notify(
                "Worklog migrated from CSV to new task-based format",
                severity="information",
            )

        # Initialize manifest section
        init_worklog_manifest_section(self._project_root)

        # Load worklog data
        self._load_worklog_data()

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
            self._populate_figure_tree()
        except Exception:
            pass

        try:
            self._populate_artifacts_table()
        except Exception:
            pass

        if self._mode == "artifact":
            try:
                outputs_sections = self.query_one("#outputs_sections", TabbedContent)
                outputs_sections.active = "outputs_artifacts"
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
            "archive_browse": lambda: self._open_directory_picker("archive_location"),
            "idea_cancel": lambda: self.exit(None),
            # Old log tab buttons removed - using new task-based system
            "fig_add_root": self._handle_fig_add_root,
            "fig_add_child": self._handle_fig_add_child,
            "fig_add_element": self._handle_fig_add_element,
            "fig_edit": self._handle_fig_edit,
            "fig_delete": self._handle_fig_delete,
            "artifact_add": self.action_add_artifact,
            "artifact_edit": self._edit_selected_artifact,
            "artifact_remove": self.action_remove_artifact,
            "edit_acquisition": self._edit_selected_acquisition,
            "edit_collaborator": self._edit_selected_collaborator,
            "edit_dataset": self._edit_selected_dataset,
            "edit_milestone": self._edit_selected_milestone,
            "edit_channel": self._edit_selected_channel,
            "hardware_edit": self._edit_selected_hardware,
            # New task-based worklog handlers (non-async wrapper)
            "new_task_btn": lambda: self.run_worker(self._handle_new_task()),
            "check_in_btn": lambda: self.run_worker(self._handle_check_in()),
            "check_out_btn": lambda: self.run_worker(self._handle_check_out()),
            "add_note_btn": lambda: self.run_worker(self._handle_add_note()),
            "edit_btn": lambda: self.run_worker(self._handle_edit()),
            "complete_btn": lambda: self.run_worker(self._handle_complete()),
            "delete_btn": lambda: self.run_worker(self._handle_delete()),
        }
        # Check for dynamic session buttons
        if button_id.startswith("session_check_out_"):
            task_id = button_id.replace("session_check_out_", "")
            self.run_worker(self._handle_session_check_out(task_id))
        elif button_id.startswith("session_add_note_"):
            task_id = button_id.replace("session_add_note_", "")
            self.run_worker(self._handle_session_add_note(task_id))
        else:
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
        elif event.input.id == "archive_location":
            try:
                focused = self.focused
                locally_mounted = self.query_one("#archive_locally_mounted", Checkbox)
                if not locally_mounted.value:
                    self._hide_archive_path_suggestions()
                    return
                if focused is event.input:
                    self._update_archive_path_suggestions(event.value)
                else:
                    self._hide_archive_path_suggestions()
            except Exception:
                pass

    def on_input_focused(self, event) -> None:
        input_id = getattr(event.input, "id", "")
        if input_id == "method_path":
            try:
                self._update_method_path_suggestions(input_id, event.input.value)
            except Exception:
                pass
        elif input_id == "archive_location":
            try:
                locally_mounted = self.query_one("#archive_locally_mounted", Checkbox)
                if locally_mounted.value:
                    self._update_archive_path_suggestions(event.input.value)
            except Exception:
                pass

    def on_option_list_blurred(self, event) -> None:
        if event.option_list.id == "archive_location_suggestions":
            focused = self.focused
            if focused and getattr(focused, "id", "") == "archive_location":
                return
            self._hide_archive_path_suggestions()

    def _handle_fig_add_root(self) -> None:
        self.push_screen(FigureNodeModal(), self._handle_new_figure_root)

    def _handle_fig_add_child(self) -> None:
        _, payload = self._get_selected_tree_payload()
        if not payload or payload.get("type") == "element":
            self.notify("Select a figure or panel", severity="warning")
            return
        self.push_screen(
            FigureNodeModal(),
            lambda data: self._handle_new_figure_child(payload, data),
        )

    def _handle_fig_add_element(self) -> None:
        _, payload = self._get_selected_tree_payload()
        if not payload or payload.get("type") != "node":
            self.notify("Select a figure or panel", severity="warning")
            return
        self.push_screen(
            FigureElementModal(),
            lambda data: self._handle_new_figure_element(payload, data),
        )

    def _handle_fig_edit(self) -> None:
        _, payload = self._get_selected_tree_payload()
        if not payload:
            self.notify("Select a figure item", severity="warning")
            return
        if payload.get("type") == "element":
            self.push_screen(
                FigureElementModal(payload),
                lambda data: self._handle_edit_figure(payload, data),
            )
        else:
            self.push_screen(
                FigureNodeModal(payload),
                lambda data: self._handle_edit_figure(payload, data),
            )

    def _handle_fig_delete(self) -> None:
        _, payload = self._get_selected_tree_payload()
        if not payload:
            self.notify("Select a figure item", severity="warning")
            return
        label = payload.get("id", "item")
        self.push_screen(
            DeleteConfirmModal(str(label)),
            lambda result: self._handle_delete_figure(payload, result),
        )

    def _handle_new_figure_root(self, data: dict[str, object] | None) -> None:
        if not data:
            return
        new_id = str(data.get("id", ""))
        node_data = {
            "type": "node",
            "id": new_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "children": [],
        }
        self._figure_tree_data.append(node_data)
        self._populate_figure_tree(expand_to_id=new_id)

    def _handle_new_figure_child(
        self, parent: dict[str, object], data: dict[str, object] | None
    ) -> None:
        if not data:
            return
        new_id = str(data.get("id", ""))
        node_data = {
            "type": "node",
            "id": new_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "children": [],
        }
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        children.append(node_data)
        self._populate_figure_tree(expand_to_id=new_id)

    def _handle_new_figure_element(
        self, parent: dict[str, object], data: dict[str, object] | None
    ) -> None:
        if not data:
            return
        new_id = str(data.get("id", ""))
        element_data = {
            "type": "element",
            "id": new_id,
            "locally_mounted": data.get("locally_mounted", True),
            "output_path": data.get("output_path", ""),
            "source_type": data.get("source_type", ""),
            "source_ref": data.get("source_ref", ""),
            "input_files": data.get("input_files", []),
            "parameters": data.get("parameters", ""),
            "status": data.get("status", ""),
            "expected_delivery_date": data.get("expected_delivery_date"),
            "description": data.get("description", ""),
        }
        children = parent.get("children")
        if not isinstance(children, list):
            children = []
            parent["children"] = children
        children.append(element_data)
        self._populate_figure_tree(expand_to_id=new_id)

    def _handle_edit_figure(
        self, payload: dict[str, object], data: dict[str, object] | None
    ) -> None:
        if data and data.get("__delete__"):
            parent_payload = self._find_parent_payload(payload)
            parent_id = str(parent_payload.get("id", "")) if parent_payload else None
            parent_list = self._find_parent_list(payload)
            if parent_list is None:
                return
            try:
                parent_list.remove(payload)
            except ValueError:
                return
            self._populate_figure_tree(expand_to_id=parent_id)
            return
        if not data:
            return
        edited_id = str(data.get("id", ""))
        if payload.get("type") == "element":
            payload.update(
                {
                    "type": "element",
                    "id": edited_id,
                    "locally_mounted": data.get("locally_mounted", True),
                    "output_path": data.get("output_path", ""),
                    "source_type": data.get("source_type", ""),
                    "source_ref": data.get("source_ref", ""),
                    "input_files": data.get("input_files", []),
                    "parameters": data.get("parameters", ""),
                    "status": data.get("status", ""),
                    "expected_delivery_date": data.get("expected_delivery_date"),
                    "description": data.get("description", ""),
                }
            )
        else:
            payload.update(
                {
                    "type": "node",
                    "id": edited_id,
                    "title": data.get("title", ""),
                    "description": data.get("description", ""),
                    "children": payload.get("children", []),
                }
            )
        self._populate_figure_tree(expand_to_id=edited_id)

    def _handle_delete_figure(
        self, payload: dict[str, object], result: str | None
    ) -> None:
        if result != "confirm":
            return
        parent_payload = self._find_parent_payload(payload)
        parent_id = str(parent_payload.get("id", "")) if parent_payload else None
        parent_list = self._find_parent_list(payload)
        if parent_list is None:
            return
        try:
            parent_list.remove(payload)
        except ValueError:
            return
        self._populate_figure_tree(expand_to_id=parent_id)

    def _update_figure_info_box(self, node) -> None:
        """Update the figure info box with details of the selected node."""
        try:
            info_content = self.query_one("#figure_info_content", Static)

            if not node or not node.data:
                info_content.update("Select a figure item to view details")
                return

            data = node.data
            node_type = data.get("type", "")

            # Build hierarchy path
            path_parts = []
            current = node
            while current and current.data:
                node_id = current.data.get("id", "")
                if node_id:
                    path_parts.insert(0, node_id)
                current = current.parent

            # Remove "Figures" root from path
            if path_parts and path_parts[0] == "Figures":
                path_parts = path_parts[1:]

            hierarchy_path = " / ".join(path_parts) if path_parts else "N/A"

            if node_type == "element":
                # Format element info
                title_section = f"[b cyan]Element: {data.get('id', 'N/A')}[/b cyan]\n[dim]{hierarchy_path}[/dim]"
                lines = []
                lines.append(f"[center]{title_section}[/center]\n")
                lines.append(f"Type:\n  Element (leaf node)\n")
                lines.append(f"Output path:\n  {data.get('output_path', 'N/A')}\n")
                lines.append(f"Source type:\n  {data.get('source_type', 'N/A')}\n")
                lines.append(f"Source ref:\n  {data.get('source_ref', 'N/A')}\n")

                input_files = data.get("input_files", [])
                if input_files:
                    files_str = ", ".join(str(f) for f in input_files)
                    lines.append(f"Input files:\n  {files_str}\n")
                else:
                    lines.append("Input files:\n  None\n")

                lines.append(f"Parameters:\n  {data.get('parameters', 'N/A')}\n")
                lines.append(f"Status:\n  {data.get('status', 'N/A')}\n")

                delivery_date = data.get("expected_delivery_date")
                if delivery_date:
                    lines.append(f"Expected delivery:\n  {delivery_date}\n")
                else:
                    lines.append("Expected delivery:\n  Not set\n")

                description = data.get("description", "")
                if description:
                    lines.append(f"Description:\n  {description}")

                info_content.update("".join(lines))
            else:
                # Format node (figure/panel) info
                title_section = f"[b green]Figure/Panel: {data.get('id', 'N/A')}[/b green]\n[dim]{hierarchy_path}[/dim]"
                lines = []
                lines.append(f"[center]{title_section}[/center]\n")
                lines.append(f"Type:\n  Container node\n")
                lines.append(f"Title:\n  {data.get('title', 'N/A')}\n")

                description = data.get("description", "")
                if description:
                    lines.append(f"Description:\n  {description}\n")

                children = data.get("children", [])
                if children:
                    lines.append(f"Children:\n  {len(children)}")

                info_content.update("".join(lines))
        except Exception:
            pass

    def _serialize_figures(self, figures) -> list[dict[str, object]]:
        return _serialize_figures(figures)

    def _deserialize_figures(self) -> list[FigureNode]:
        return _deserialize_figures(self._figure_tree_data)

    def _load_publication_defaults(self, manifest) -> None:
        if not getattr(manifest, "publication", None):
            return
        pub = manifest.publication
        self._publication_defaults = {
            "pub_status": pub.status,
            "target_journal": pub.target_journal,
            "manuscript_path": pub.manuscript_path,
            "preprint_doi": pub.preprint_doi,
            "published_doi": pub.published_doi,
            "github_repo": pub.github_repo,
            "zenodo_doi": pub.zenodo_doi,
            "pub_notes": pub.notes,
        }
        self._defaults.update(self._publication_defaults)

    def _load_archive_defaults(self, manifest) -> None:
        if not getattr(manifest, "archive", None):
            return
        archive = manifest.archive
        self._archive_defaults = {
            "archive_status": archive.status,
            "archive_date": archive.archive_date,
            "archive_location": archive.archive_location,
            "archive_endpoint": archive.endpoint or "",
            "retention_years": archive.retention_years,
            "backup_verified": archive.backup_verified,
            "archive_notes": archive.notes,
        }
        self._defaults.update(self._archive_defaults)

    def _get_selected_tree_payload(
        self,
    ) -> tuple[object | None, dict[str, object] | None]:
        try:
            tree = self.query_one("#figure_tree", Tree)
        except Exception:
            return None, None
        node = tree.cursor_node
        if not node:
            return None, None
        payload = node.data if isinstance(node.data, dict) else None
        return node, payload

    def _find_parent_list(
        self, target: dict[str, object]
    ) -> list[dict[str, object]] | None:
        def walk(items: list[dict[str, object]]) -> list[dict[str, object]] | None:
            for item in items:
                if item is target:
                    return items
                children = item.get("children")
                if isinstance(children, list):
                    result = walk(children)
                    if result is not None:
                        return result
            return None

        return walk(self._figure_tree_data)

    def _find_parent_payload(
        self, target: dict[str, object]
    ) -> dict[str, object] | None:
        """Find the parent node payload for a given target."""

        def walk(
            items: list[dict[str, object]], parent: dict[str, object] | None
        ) -> dict[str, object] | None:
            for item in items:
                if item is target:
                    return parent
                children = item.get("children")
                if isinstance(children, list):
                    result = walk(children, item)
                    if result is not None:
                        return result
            return None

        return walk(self._figure_tree_data, None)

    def _populate_figure_tree(self, expand_to_id: str | None = None) -> None:
        try:
            tree = self.query_one("#figure_tree", Tree)
        except Exception:
            return

        # Check if this is initial load (tree has no children yet)
        is_initial_load = len(list(tree.root.children)) == 0

        # Collect currently expanded node IDs before clearing
        expanded_ids: set[str] = set()

        def collect_expanded(node) -> None:
            if node.is_expanded and node.data:
                node_id = node.data.get("id")
                if node_id:
                    expanded_ids.add(str(node_id))
            for child in node.children:
                collect_expanded(child)

        try:
            collect_expanded(tree.root)
        except Exception:
            pass

        # On initial load, use saved state from UI state file
        if is_initial_load and self._figure_expanded_ids:
            expanded_ids = self._figure_expanded_ids.copy()

        try:
            tree.clear()
        except Exception:
            pass
        tree.root.label = "Figures"

        # Map node IDs to tree nodes for expansion restoration
        id_to_node: dict[str, object] = {}

        def add_node(parent, payload: dict[str, object]) -> None:
            node_type = payload.get("type", "node")
            node_id = str(payload.get("id", ""))
            if node_type == "element":
                label = f"{node_id}: {payload.get('output_path', '')}"
                new_node = parent.add(label, data=payload)
                if node_id:
                    id_to_node[node_id] = new_node
                return
            label = node_id
            title = str(payload.get("title", ""))
            if title:
                label = f"{label} - {title}"
            branch = parent.add(label, data=payload)
            if node_id:
                id_to_node[node_id] = branch
            children = payload.get("children", [])
            child_items: list[dict[str, object]] = []
            if isinstance(children, list):
                child_items = [item for item in children if isinstance(item, dict)]
            for child in child_items:
                add_node(branch, child)

        for item in self._figure_tree_data:
            if isinstance(item, dict):
                add_node(tree.root, item)

        # Restore expansion state for previously expanded nodes
        try:
            tree.root.expand()
            for node_id, node in id_to_node.items():
                if node_id in expanded_ids:
                    node.expand()
        except Exception:
            pass

        # Determine which node to select
        select_id = expand_to_id
        if not select_id and is_initial_load and self._figure_selected_id:
            select_id = self._figure_selected_id

        # If select_id specified, expand path to that node and select it
        if select_id and select_id in id_to_node:
            try:
                target_node = id_to_node[select_id]
                # Expand all ancestors to make the target visible
                parent = target_node.parent
                while parent is not None:
                    parent.expand()
                    parent = parent.parent
                # Expand the target node if it's not an element
                if target_node.data and target_node.data.get("type") != "element":
                    target_node.expand()
                # Select and move cursor to the target node
                tree.select_node(target_node)
                tree.move_cursor(target_node)
                # Trigger the info box update by posting highlighted event
                self._update_figure_info_box(target_node)
            except Exception:
                pass

    def _populate_artifacts_table(self) -> None:
        try:
            table = self.query_one("#artifacts_table", DataTable)
        except Exception:
            return
        table.clear(columns=True)
        table.add_columns("Path", "Type", "Status", "Description")
        for idx, row in enumerate(self._artifact_rows):
            table.add_row(
                str(row.get("path", "")),
                str(row.get("type", "")),
                str(row.get("status", "")),
                self._truncate_text(str(row.get("description", "")), 40),
                key=str(idx),
            )

    def _truncate_text(self, value: str, max_len: int = 40) -> str:
        if len(value) <= max_len:
            return value
        return f"{value[: max_len - 3]}..."

    def action_add_artifact(self) -> None:
        try:
            table = self.query_one("#artifacts_table", DataTable)
            idx = table.cursor_row
            initial_data = None
            if idx is not None and 0 <= idx < len(self._artifact_rows):
                initial_data = dict(self._artifact_rows[idx])
                initial_data["path"] = ""
        except Exception:
            initial_data = None
        self.push_screen(
            ArtifactModal(load_endpoint_options(), initial_data),
            self._handle_new_artifact,
        )

    def _submit_artifact(self) -> None:
        self._store_ui_state()
        self.exit({"action": "artifact", "artifacts": self._collect_artifacts()})

    def action_remove_artifact(self) -> None:
        try:
            table = self.query_one("#artifacts_table", DataTable)
            if table.cursor_row is None:
                self.notify("Select an artifact to remove", severity="warning")
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._artifact_rows):
                self._artifact_rows.pop(idx)
            self._populate_artifacts_table()
            if self._artifact_rows:
                idx = min(idx, len(self._artifact_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _handle_new_artifact(self, data: dict[str, object] | None) -> None:
        if not data:
            return
        self._artifact_rows.append(data)
        self._populate_artifacts_table()

    def _handle_edit_artifact(self, idx: int, data: dict[str, object] | None) -> None:
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._artifact_rows):
                self._artifact_rows.pop(idx)
                self._populate_artifacts_table()
            return
        if data and 0 <= idx < len(self._artifact_rows):
            self._artifact_rows[idx] = data
            self._populate_artifacts_table()

    def _handle_artifact_row_selected(self, idx: int) -> None:
        if not (0 <= idx < len(self._artifact_rows)):
            return
        row_data = self._artifact_rows[idx]
        self.push_screen(
            ArtifactModal(load_endpoint_options(), row_data, allow_remove=True),
            lambda data, i=idx: self._handle_edit_artifact(i, data),
        )

    def _collect_archive(self) -> dict[str, object]:
        data: dict[str, object] = {}
        status = self.query_one("#archive_status", Select).value
        if status and status != Select.BLANK:
            data["status"] = str(status)
        date_value = self.query_one("#archive_date", DateSelect).value
        if date_value:
            # Normalize to date only (remove time portion)
            if hasattr(date_value, "date"):
                data["archive_date"] = date_value.date()
            else:
                data["archive_date"] = date_value
        endpoint_value = self.query_one("#archive_endpoint", Select).value
        endpoint_custom = self.query_one(
            "#archive_endpoint_custom", Input
        ).value.strip()
        endpoint = ""
        if endpoint_value and endpoint_value != Select.BLANK:
            endpoint = str(endpoint_value)
        if endpoint.lower() == "other" and endpoint_custom:
            endpoint = endpoint_custom
        elif not endpoint and endpoint_custom:
            endpoint = endpoint_custom
        if endpoint:
            data["endpoint"] = endpoint
        data["archive_location"] = self.query_one(
            "#archive_location", Input
        ).value.strip()
        retention = self.query_one("#retention_years", Input).value.strip()
        if retention:
            try:
                data["retention_years"] = int(retention)
            except ValueError:
                pass
        data["backup_verified"] = bool(
            self.query_one("#backup_verified", Checkbox).value
        )
        data["notes"] = self.query_one("#archive_notes", TextArea).text.strip()
        return data

    def _collect_publication(self) -> dict[str, object]:
        data: dict[str, object] = {}
        status = self.query_one("#pub_status", Select).value
        if status and status != Select.BLANK:
            data["status"] = str(status)
        data["target_journal"] = self.query_one("#target_journal", Input).value.strip()
        data["manuscript_path"] = self.query_one(
            "#manuscript_path", Input
        ).value.strip()
        data["preprint_doi"] = self.query_one("#preprint_doi", Input).value.strip()
        data["published_doi"] = self.query_one("#published_doi", Input).value.strip()
        data["github_repo"] = self.query_one("#github_repo", Input).value.strip()
        data["zenodo_doi"] = self.query_one("#zenodo_doi", Input).value.strip()
        data["notes"] = self.query_one("#pub_notes", TextArea).text.strip()
        if self._figure_tree_data:
            data["figures"] = self._figure_tree_data
        return data

    def _collect_artifacts(self) -> list[Artifact]:
        artifacts: list[Artifact] = []
        for row in self._artifact_rows:
            path = str(row.get("path", "")).strip()
            if not path:
                continue
            artifacts.append(
                Artifact(
                    path=path,
                    endpoint=str(row.get("endpoint", "")) or None,
                    type=str(row.get("type", "")) or "unknown",
                    status=str(row.get("status", "")) or "draft",
                    description=str(row.get("description", "")) or None,
                )
            )
        return artifacts

    def _coerce_date(self, value: object):
        return _coerce_date(value)

    def _load_endpoint_options(self) -> list[tuple[str, str]]:
        return load_endpoint_options()

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
        elif input_id == "archive_location":
            focused = self.focused
            if focused and getattr(focused, "id", "") == "archive_location_suggestions":
                return
            self._hide_archive_path_suggestions()

    def _update_archive_path_suggestions(self, current_value: str) -> None:
        try:
            suggestions = self.query_one("#archive_location_suggestions", OptionList)
            suggestions.clear_options()
            if not current_value:
                suggestions.remove_class("visible")
                self._archive_path_suggestions_visible = False
                return
            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()
            if not search_dir.exists():
                suggestions.remove_class("visible")
                self._archive_path_suggestions_visible = False
                return
            entries: list[tuple[str, str]] = []
            try:
                # Collect both directories and files
                for entry in sorted(search_dir.iterdir()):
                    name = entry.name
                    if not prefix or name.lower().startswith(prefix):
                        if entry.is_dir():
                            entries.append((str(entry), f"📁 {name}/"))
                        else:
                            entries.append((str(entry), f"📄 {name}"))
                        if len(entries) >= 20:
                            break
            except PermissionError:
                pass
            if entries:
                from textual.widgets.option_list import Option

                for entry_path, display_name in entries:
                    suggestions.add_option(Option(display_name, id=entry_path))
                suggestions.add_class("visible")
                self._archive_path_suggestions_visible = True
            else:
                suggestions.remove_class("visible")
                self._archive_path_suggestions_visible = False
        except Exception:
            self._archive_path_suggestions_visible = False

    def _hide_archive_path_suggestions(self) -> None:
        try:
            suggestions = self.query_one("#archive_location_suggestions", OptionList)
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._archive_path_suggestions_visible = False
        except Exception:
            pass

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
        elif event.select.id == "archive_endpoint":
            try:
                row = self.query_one("#archive_endpoint_custom_row", Horizontal)
                if event.value and str(event.value).lower() == "other":
                    row.remove_class("hidden")
                else:
                    row.add_class("hidden")
            except Exception:
                pass
            try:
                checkbox = self.query_one("#archive_locally_mounted", Checkbox)
                is_local = event.value and str(event.value).lower() == "local"
                if is_local:
                    checkbox.value = True
                    checkbox.disabled = True
                else:
                    checkbox.disabled = False
                self._set_archive_browse_enabled(checkbox.value)
            except Exception:
                pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "data_enabled":
            self._toggle_data_sections(event.value)
            if not event.value:
                self._dataset_rows = []
                self._populate_datasets_table()
        elif event.checkbox.id == "archive_locally_mounted":
            self._set_archive_browse_enabled(event.value)
            if not event.value:
                self._hide_archive_path_suggestions()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in tables - double-click opens edit modal."""
        import time

        row_key = event.row_key.value
        if row_key is None:
            return
        table_id = event.data_table.id
        if not table_id:
            return

        # Detect double-click (within 500ms)
        current_time = time.time()
        click_key = (table_id, row_key)

        if (
            self._last_click_row == click_key
            and (current_time - self._last_click_time) < 0.5
        ):
            # Double-click detected - open edit modal
            handlers: dict[str, Callable[[int], None]] = {
                "collaborators_table": self._handle_collaborator_row_selected,
                "channels_table": self._handle_channel_row_selected,
                "hardware_table": self._handle_hardware_row_selected,
                "datasets_table": self._handle_dataset_row_selected,
                "milestones_table": self._handle_milestone_row_selected,
                "acquisition_table": self._handle_acquisition_row_selected,
                "artifacts_table": self._handle_artifact_row_selected,
            }
            handler = handlers.get(table_id)
            if handler:
                try:
                    idx = int(row_key)
                    handler(idx)
                except (ValueError, TypeError):
                    pass
            # Reset after double-click
            self._last_click_time = 0.0
            self._last_click_row = None
        else:
            # Single-click - just update tracking
            self._last_click_time = current_time
            self._last_click_row = click_key

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
                    # Use the option id which contains the full path
                    selected = (
                        str(event.option.id)
                        if event.option.id
                        else str(event.option.prompt)
                    )
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
        elif event.option_list.id == "archive_location_suggestions":
            try:
                input_widget = self.query_one("#archive_location", Input)
                # Use the option id which contains the full path
                selected = (
                    str(event.option.id)
                    if event.option.id
                    else str(event.option.prompt)
                )
                input_widget.value = selected
                self._hide_archive_path_suggestions()
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
            except Exception:
                pass

    def on_key(self, event) -> None:
        # Don't handle context shortcuts if a modal screen is active
        if self.screen_stack and len(self.screen_stack) > 1:
            # Modal is open, let it handle the keys
            return

        if event.key in ("a", "p", "e", "r", "d", "enter"):
            try:
                if isinstance(self.focused, Tree):
                    tabbed = self.query_one("#tabs", TabbedContent)
                    if tabbed.active == "outputs":
                        outputs_sections = self.query_one(
                            "#outputs_sections", TabbedContent
                        )
                        if outputs_sections.active == "outputs_publication":
                            if event.key == "a":
                                self._handle_fig_add_root()
                            elif event.key == "p":
                                self._handle_fig_add_child()
                            elif event.key == "e":
                                self._handle_fig_add_element()
                            elif event.key in ("r", "enter"):
                                self._handle_fig_edit()
                            elif event.key == "d":
                                self._handle_fig_delete()
                            event.prevent_default()
                            event.stop()
                            return
            except Exception:
                pass

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

        if event.key in ("a", "d", "enter"):
            try:
                is_add = event.key == "a"
                is_remove = event.key == "d"
                is_edit = event.key == "enter"
                tabbed = self.query_one("#tabs", TabbedContent)
                # Handle collaborators table in setup tab
                if tabbed.active == "setup":
                    table = self.query_one("#datasets_table", DataTable)
                    if table.has_focus:
                        if is_add:
                            self.action_add_dataset()
                        elif is_remove:
                            self.action_remove_dataset()
                        elif is_edit and table.cursor_row is not None:
                            self._handle_dataset_row_selected(table.cursor_row)
                        event.prevent_default()
                        event.stop()
                        return
                    table = self.query_one("#collaborators_table", DataTable)
                    if table.has_focus:
                        if is_add:
                            self.action_add_collaborator_row()
                        elif is_remove:
                            self.action_remove_collaborator_row()
                        elif is_edit and table.cursor_row is not None:
                            self._handle_collaborator_row_selected(table.cursor_row)
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
                            if is_add:
                                self.action_add_acquisition()
                            elif is_remove:
                                self.action_remove_acquisition()
                            elif is_edit and table.cursor_row is not None:
                                self._handle_acquisition_row_selected(table.cursor_row)
                            event.prevent_default()
                            event.stop()
                            return
                    table = self.query_one("#channels_table", DataTable)
                    if table.has_focus:
                        if is_add:
                            self.action_add_channel_row()
                        elif is_remove:
                            self.action_remove_channel_row()
                        elif is_edit and table.cursor_row is not None:
                            self._handle_channel_row_selected(table.cursor_row)
                        event.prevent_default()
                        event.stop()
                        return
                    hardware_table = self.query_one("#hardware_table", DataTable)
                    if hardware_table.has_focus:
                        if is_add:
                            self._add_hardware_profile()
                        elif is_remove:
                            self._remove_selected_hardware()
                        elif is_edit and hardware_table.cursor_row is not None:
                            self._handle_hardware_row_selected(
                                hardware_table.cursor_row
                            )
                        event.prevent_default()
                        event.stop()
                        return
                elif tabbed.active == "admin":
                    admin_sections = self.query_one("#admin_sections", TabbedContent)
                    if admin_sections.active == "admin_timeline":
                        table = self.query_one("#milestones_table", DataTable)
                        if table.has_focus:
                            if is_add:
                                self.action_add_milestone()
                            elif is_remove:
                                self.action_remove_milestone()
                            elif is_edit and table.cursor_row is not None:
                                self._handle_milestone_row_selected(table.cursor_row)
                            event.prevent_default()
                            event.stop()
                            return
                elif tabbed.active == "outputs":
                    outputs_sections = self.query_one(
                        "#outputs_sections", TabbedContent
                    )
                    if outputs_sections.active == "outputs_artifacts":
                        table = self.query_one("#artifacts_table", DataTable)
                        if table.has_focus:
                            if is_add:
                                self.action_add_artifact()
                            elif is_remove:
                                self.action_remove_artifact()
                            elif is_edit and table.cursor_row is not None:
                                self._handle_artifact_row_selected(table.cursor_row)
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

        try:
            if self._archive_path_suggestions_visible:
                suggestions = self.query_one(
                    "#archive_location_suggestions", OptionList
                )
                if suggestions.has_class("visible"):
                    if event.key == "escape":
                        input_widget = self.query_one("#archive_location", Input)
                        self._hide_archive_path_suggestions()
                        input_widget.focus()
                        event.prevent_default()
                        event.stop()
                    elif event.key == "down":
                        focused = self.focused
                        if focused and focused.id == "archive_location":
                            suggestions.focus()
                            if suggestions.option_count > 0:
                                suggestions.highlighted = 0
                            event.prevent_default()
                            event.stop()
                    elif event.key == "up":
                        if self.focused == suggestions and suggestions.highlighted == 0:
                            input_widget = self.query_one("#archive_location", Input)
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
        if self._mode == "artifact":
            self._submit_artifact()
            return
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active == "init":
            self._save_init()
        elif tabbed.active == "log":
            self._save_log()
        elif tabbed.active == "idea":
            self._submit_idea()
        elif tabbed.active == "manifest":
            self._save_manifest()
        elif tabbed.active in ("setup", "science", "admin", "outputs", "hub"):
            # For manifest editing tabs, save the manifest
            self._save_init()
        else:
            self.notify("Save not available for this tab", severity="warning")

    def action_exit_app(self) -> None:
        self.push_screen(ExitConfirmScreen(), self._handle_exit_confirm)

    def action_prev_main_tab(self) -> None:
        """Navigate to previous main tab."""
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            tabs = ["setup", "science", "admin", "outputs", "hub", "log", "idea"]
            current_idx = tabs.index(tabbed.active) if tabbed.active in tabs else 0
            prev_idx = (current_idx - 1) % len(tabs)
            tabbed.active = tabs[prev_idx]
        except Exception:
            pass

    def action_next_main_tab(self) -> None:
        """Navigate to next main tab."""
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            tabs = ["setup", "science", "admin", "outputs", "hub", "log", "idea"]
            current_idx = tabs.index(tabbed.active) if tabbed.active in tabs else 0
            next_idx = (current_idx + 1) % len(tabs)
            tabbed.active = tabs[next_idx]
        except Exception:
            pass

    def action_prev_sub_tab(self) -> None:
        """Navigate to previous sub-tab in current section."""
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            sub_tab_map = {
                "setup": "#setup_sections",
                "science": "#science_sections",
                "admin": "#admin_sections",
                "outputs": "#outputs_sections",
                "hub": "#hub_sections",
            }
            if tabbed.active in sub_tab_map:
                sub_tabbed = self.query_one(sub_tab_map[tabbed.active], TabbedContent)
                tabs = [str(tab.id) for tab in sub_tabbed.query("TabPane")]
                current_idx = (
                    tabs.index(sub_tabbed.active) if sub_tabbed.active in tabs else 0
                )
                prev_idx = (current_idx - 1) % len(tabs)
                sub_tabbed.active = tabs[prev_idx]
        except Exception:
            pass

    def action_next_sub_tab(self) -> None:
        """Navigate to next sub-tab in current section."""
        try:
            tabbed = self.query_one("#tabs", TabbedContent)
            sub_tab_map = {
                "setup": "#setup_sections",
                "science": "#science_sections",
                "admin": "#admin_sections",
                "outputs": "#outputs_sections",
                "hub": "#hub_sections",
            }
            if tabbed.active in sub_tab_map:
                sub_tabbed = self.query_one(sub_tab_map[tabbed.active], TabbedContent)
                tabs = [str(tab.id) for tab in sub_tabbed.query("TabPane")]
                current_idx = (
                    tabs.index(sub_tabbed.active) if sub_tabbed.active in tabs else 0
                )
                next_idx = (current_idx + 1) % len(tabs)
                sub_tabbed.active = tabs[next_idx]
        except Exception:
            pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "active_tasks":
            if event.item and event.item.id:
                _, idx = event.item.id.split("-", 1)
                self._selected_active_index = int(idx)

    def _handle_exit_confirm(self, result: str | None) -> None:
        if result == "save":
            # Save UI state before exiting
            self._store_ui_state()
            if self._mode == "artifact":
                self._submit_artifact()
                return
            tabbed = self.query_one("#tabs", TabbedContent)
            if tabbed.active == "init":
                self._submit_init()
            elif tabbed.active == "log":
                self._submit_log()
            elif tabbed.active == "idea":
                self._submit_idea()
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

        # Check if input has a current value and use it as starting path
        try:
            input_widget = self.query_one(f"#{target_input_id}", Input)
            current_value = input_widget.value.strip()
            if current_value:
                current_path = Path(current_value).expanduser().resolve()
                if current_path.exists():
                    # If it's a file, start from parent directory
                    if current_path.is_file():
                        start = current_path.parent
                    # If it's a directory, start from that directory
                    elif current_path.is_dir():
                        start = current_path
        except Exception:
            pass

        self.push_screen(DirectoryPickerScreen(start), self._handle_directory_pick)

    def _set_archive_browse_enabled(self, enabled: bool) -> None:
        try:
            button = self.query_one("#archive_browse", Button)
            button.disabled = not enabled
        except Exception:
            pass

    def _edit_selected_artifact(self) -> None:
        """Edit the selected artifact in the table."""
        try:
            table = self.query_one("#artifacts_table", DataTable)
            if table.cursor_row is not None:
                self._handle_artifact_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_acquisition(self) -> None:
        """Edit the selected acquisition session in the table."""
        try:
            table = self.query_one("#acquisition_table", DataTable)
            if table.cursor_row is not None:
                self._handle_acquisition_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_collaborator(self) -> None:
        """Edit the selected collaborator in the table."""
        try:
            table = self.query_one("#collaborators_table", DataTable)
            if table.cursor_row is not None:
                self._handle_collaborator_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_dataset(self) -> None:
        """Edit the selected dataset in the table."""
        try:
            table = self.query_one("#datasets_table", DataTable)
            if table.cursor_row is not None:
                self._handle_dataset_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_milestone(self) -> None:
        """Edit the selected milestone in the table."""
        try:
            table = self.query_one("#milestones_table", DataTable)
            if table.cursor_row is not None:
                self._handle_milestone_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_channel(self) -> None:
        """Edit the selected channel in the table."""
        try:
            table = self.query_one("#channels_table", DataTable)
            if table.cursor_row is not None:
                self._handle_channel_row_selected(table.cursor_row)
        except Exception:
            pass

    def _edit_selected_hardware(self) -> None:
        """Edit the selected hardware profile in the table."""
        try:
            table = self.query_one("#hardware_table", DataTable)
            if table.cursor_row is not None:
                self._handle_hardware_row_selected(table.cursor_row)
        except Exception:
            pass

    def _handle_directory_pick(self, path: str | None) -> None:
        if not path or not self._browse_target:
            self._browse_target = None
            return
        try:
            if self._browse_target == "archive_location":
                input_widget = self.query_one(f"#{self._browse_target}", Input)
                input_widget.value = path
            else:
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

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node highlighting (cursor movement)."""
        try:
            tree = event.control
            if hasattr(tree, "id") and tree.id == "figure_tree":
                self._update_figure_info_box(event.node)
            elif hasattr(tree, "id") and tree.id == "task_tree":
                # Handle task tree keyboard navigation
                if hasattr(event.node, "data"):
                    self._on_tree_node_selected(event.node)
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection for task worklog."""
        try:
            tree = event.control  # Use control instead of tree
            if hasattr(tree, "id") and tree.id == "task_tree":
                # Debug: print type of event.node
                actual_node = event.node
                # Make sure we have the actual TreeNode, not the event
                if hasattr(actual_node, "data"):
                    self._on_tree_node_selected(actual_node)
        except Exception as e:
            # Silently ignore - not all trees are task trees
            pass

    def action_worklog_new_task(self) -> None:
        """Keyboard shortcut for new task (A key)."""
        self.run_worker(self._handle_new_task())

    def action_worklog_check_in(self) -> None:
        """Keyboard shortcut for check in (I key)."""
        self.run_worker(self._handle_check_in())

    def action_worklog_check_out(self) -> None:
        """Keyboard shortcut for check out (O key)."""
        self.run_worker(self._handle_check_out())

    def action_worklog_add_note(self) -> None:
        """Keyboard shortcut for add note (N key)."""
        self.run_worker(self._handle_add_note())

    def action_worklog_complete(self) -> None:
        """Keyboard shortcut for complete task (C key)."""
        self.run_worker(self._handle_complete())

    def action_worklog_delete(self) -> None:
        """Keyboard shortcut for delete task/session (D key)."""
        self.run_worker(self._handle_delete())

    def action_worklog_edit(self) -> None:
        """Keyboard shortcut for edit task/session (Enter key)."""
        self.run_worker(self._handle_edit())
