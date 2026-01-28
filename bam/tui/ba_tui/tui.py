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
    OptionList,
    ProgressBar,
    Select,
    Static,
    TabbedContent,
    TextArea,
)
from textual.widgets.option_list import Option

from .io import dump_manifest
from .models import Artifact, LogEntry, Manifest, TaskStatus, build_manifest
from .scaffold import ensure_data_symlink, ensure_directories, ensure_worklog
from .screens import (
    CollaboratorModal,
    DirectoryPickerScreen,
    ExitConfirmScreen,
    NewManifestConfirmScreen,
)
from .styles import APP_CSS
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
            "data_endpoint": data_endpoint,
            "data_source": data_source,
            "data_local": data_local,
            "locally_mounted": locally_mounted,
        }
        if initial_data:
            self._defaults.update(initial_data)
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
        self._active_path_input: Optional[str] = None
        self._collaborator_rows: list[dict[str, str]] = []
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

        self._refresh_init_validation()
        self._refresh_sync_button_state()
        self._refresh_worklog_lists()
        self._refresh_artifact_list()
        self._load_manifest_sections()
        self.set_interval(1, self._tick_worklog)

        # Auto-check locally mounted if endpoint is Local
        try:
            endpoint_select = self.query_one("#data_endpoint", Select)
            if endpoint_select.value == "Local":
                checkbox = self.query_one("#locally_mounted", Checkbox)
                checkbox.value = True
        except Exception:
            pass

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
            self._ensure_collaborator_rows()
            self._populate_collaborators_table()
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "sync_btn":
            if not self._is_sync_disabled():
                self._start_sync()
        elif button_id == "browse_source":
            # Only allow browse if locally mounted
            try:
                checkbox = self.query_one("#locally_mounted", Checkbox)
                if checkbox.value:
                    self._open_directory_picker("data_source")
                else:
                    self.notify(
                        "Enable 'Locally Mounted' to browse source", severity="warning"
                    )
            except Exception:
                self._open_directory_picker("data_source")
        elif button_id == "browse_local":
            self._open_directory_picker("data_local")
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
        elif event.input.id in ("project_name", "analyst", "data_source", "data_local"):
            self._refresh_init_validation()
            self._hide_path_suggestions()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in ("project_name", "analyst", "data_source", "data_local"):
            self._refresh_init_validation()
            self._refresh_sync_button_state()
        # Show path suggestions for path fields when locally mounted
        if event.input.id in ("data_source", "data_local"):
            try:
                checkbox = self.query_one("#locally_mounted", Checkbox)
                if checkbox.value:
                    self._update_path_suggestions(event.input.id, event.value)
                else:
                    self._hide_path_suggestions()
            except Exception:
                pass

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "data_endpoint":
            # Auto-check locally mounted when "Local" is selected
            try:
                checkbox = self.query_one("#locally_mounted", Checkbox)
                if event.value == "Local":
                    checkbox.value = True
                self._refresh_sync_button_state()
            except Exception:
                pass
        elif event.select.id == "collab_role_select":
            pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "locally_mounted":
            self._refresh_sync_button_state()
            if not event.value:
                self._hide_path_suggestions()
        elif event.checkbox.id == "data_enabled":
            self._toggle_data_sections(event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in collaborators table."""
        if event.data_table.id != "collaborators_table":
            return

        row_key = event.row_key.value
        if row_key is None:
            return

        try:
            idx = int(row_key)
            if 0 <= idx < len(self._collaborator_rows):
                row_data = self._collaborator_rows[idx]
                self.push_screen(
                    CollaboratorModal(self._load_role_options(), row_data),
                    lambda data: self._handle_edit_collaborator(idx, data),
                )
        except (ValueError, IndexError):
            pass

    def _handle_edit_collaborator(self, idx: int, data: dict[str, str] | None) -> None:
        """Update collaborator data after modal close."""
        if data and 0 <= idx < len(self._collaborator_rows):
            self._collaborator_rows[idx] = data
            self._populate_collaborators_table()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "path_suggestions":
            # Apply selected path to the active input
            if self._active_path_input:
                try:
                    input_widget = self.query_one(f"#{self._active_path_input}", Input)
                    input_widget.value = str(event.option.prompt)
                    self._hide_path_suggestions()
                    self._refresh_init_validation()
                    self._refresh_sync_button_state()
                    # Return focus to input for continued typing
                    input_widget.focus()
                except Exception:
                    pass

    def on_key(self, event) -> None:
        if event.key in ("ctrl+a", "ctrl+d"):
            try:
                tabbed = self.query_one("#tabs", TabbedContent)
                table = self.query_one("#collaborators_table", DataTable)
                if tabbed.active == "setup" and table.has_focus:
                    if event.key == "ctrl+a":
                        self.action_add_collaborator_row()
                    else:
                        self.action_remove_collaborator_row()
                    event.prevent_default()
                    event.stop()
                    return
            except Exception:
                pass

        # Handle path suggestions keyboard navigation
        try:
            suggestions = self.query_one("#path_suggestions", OptionList)
            if suggestions.has_class("visible"):
                # Escape: hide suggestions and return focus to input
                if event.key == "escape":
                    if self._active_path_input:
                        input_widget = self.query_one(
                            f"#{self._active_path_input}", Input
                        )
                        self._hide_path_suggestions()
                        input_widget.focus()
                        event.prevent_default()
                        event.stop()
                # Down arrow from input: focus suggestions
                elif event.key == "down" and self._active_path_input:
                    focused = self.focused
                    if focused and focused.id == self._active_path_input:
                        suggestions.focus()
                        if suggestions.option_count > 0:
                            suggestions.highlighted = 0
                        event.prevent_default()
                        event.stop()
                # Up arrow from first suggestion: return to input
                elif event.key == "up":
                    if self.focused == suggestions and suggestions.highlighted == 0:
                        if self._active_path_input:
                            input_widget = self.query_one(
                                f"#{self._active_path_input}", Input
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

    def _handle_new_manifest_confirm(self, result: str | None) -> None:
        """Handle the confirmation result from NewManifestConfirmScreen."""
        if result == "discard":
            # Clear all form fields
            try:
                self.query_one("#project_name", Input).value = ""
                self.query_one("#analyst", Input).value = ""
                self.query_one("#data_source", Input).value = ""
                self.query_one("#data_local", Input).value = ""
                self.query_one("#data_enabled", Checkbox).value = True
                self.query_one("#locally_mounted", Checkbox).value = False
                self._collaborator_rows = [
                    {"name": "", "role": "", "email": "", "affiliation": ""}
                ]
                self._populate_collaborators_table()
                self._set_tab("init")
                self._refresh_init_validation()
                self._refresh_sync_button_state()
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

            # Update data section
            if "data" not in manifest_data:
                manifest_data["data"] = {}
            manifest_data["data"]["enabled"] = bool(values.get("data_enabled", True))

            endpoint = str(values.get("data_endpoint", "")).strip()
            if endpoint:
                manifest_data["data"]["endpoint"] = endpoint

            source = str(values.get("data_source", "")).strip()
            if source:
                manifest_data["data"]["source"] = source

            local = str(values.get("data_local", "")).strip()
            if local:
                manifest_data["data"]["local"] = local

            manifest_data["data"]["locally_mounted"] = bool(
                values.get("locally_mounted", False)
            )

            data_format = str(values.get("data_format", "")).strip()
            if data_format:
                manifest_data["data"]["format"] = data_format

            # Collect acquisition data from Science tab
            try:
                acquisition_data = {}

                microscope = self.query_one("#microscope", Input).value.strip()
                if microscope:
                    acquisition_data["microscope"] = microscope

                modality_select = self.query_one("#modality", Select)
                if modality_select.value and modality_select.value != Select.BLANK:
                    acquisition_data["modality"] = str(modality_select.value)

                objective = self.query_one("#objective", Input).value.strip()
                if objective:
                    acquisition_data["objective"] = objective

                channels = self.query_one("#channels_text", TextArea).text.strip()
                if channels:
                    acquisition_data["channels"] = [
                        ch.strip() for ch in channels.split("\n") if ch.strip()
                    ]

                voxel_x = self.query_one("#voxel_x", Input).value.strip()
                voxel_y = self.query_one("#voxel_y", Input).value.strip()
                voxel_z = self.query_one("#voxel_z", Input).value.strip()
                if voxel_x or voxel_y or voxel_z:
                    acquisition_data["voxel_size"] = {
                        "x_um": float(voxel_x) if voxel_x else None,
                        "y_um": float(voxel_y) if voxel_y else None,
                        "z_um": float(voxel_z) if voxel_z else None,
                    }

                time_interval = self.query_one("#time_interval", Input).value.strip()
                if time_interval:
                    acquisition_data["time_interval_s"] = float(time_interval)

                acq_notes = self.query_one("#acquisition_notes", TextArea).text.strip()
                if acq_notes:
                    acquisition_data["notes"] = acq_notes

                # Only update acquisition section if we have data to add
                if acquisition_data:
                    if "acquisition" not in manifest_data:
                        manifest_data["acquisition"] = {}
                    manifest_data["acquisition"].update(acquisition_data)
            except Exception:
                pass  # Skip if Science tab fields not found

            # Collect tools data from Science tab
            try:
                tools_data = {}

                env_select = self.query_one("#environment", Select)
                if env_select.value and env_select.value != Select.BLANK:
                    tools_data["environment"] = str(env_select.value)

                env_file = self.query_one("#env_file", Input).value.strip()
                if env_file:
                    tools_data["env_file"] = env_file

                languages = self.query_one("#languages", Input).value.strip()
                if languages:
                    tools_data["languages"] = [
                        lang.strip() for lang in languages.split(",") if lang.strip()
                    ]

                packages = self.query_one("#packages_text", TextArea).text.strip()
                if packages:
                    # Store as list of package objects with just names
                    tools_data["key_packages"] = [
                        {"name": pkg.strip()}
                        for pkg in packages.split("\n")
                        if pkg.strip()
                    ]

                scripts_dir = self.query_one("#scripts_dir", Input).value.strip()
                if scripts_dir:
                    tools_data["scripts_dir"] = scripts_dir

                # Only update tools section if we have data to add
                if tools_data:
                    if "tools" not in manifest_data:
                        manifest_data["tools"] = {}
                    manifest_data["tools"].update(tools_data)
            except Exception:
                pass  # Skip if tools fields not found

            # Save the updated manifest
            ensure_directories(self._project_root)
            ensure_worklog(self._project_root)

            with open(manifest_path, "w") as f:
                yaml.safe_dump(manifest_data, f, sort_keys=False)

            if manifest_data.get("data", {}).get("enabled") and manifest_data.get(
                "data", {}
            ).get("local"):
                ensure_data_symlink(self._project_root, manifest_data["data"]["local"])

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
            self._refresh_sync_button_state()
        except Exception:
            pass
        self._browse_target = None

    def _start_sync(self) -> None:
        if self._syncing:
            return

        # Check if locally mounted
        try:
            checkbox = self.query_one("#locally_mounted", Checkbox)
            if not checkbox.value:
                self.notify("Enable 'Locally Mounted' to sync", severity="warning")
                return
        except Exception:
            pass

        source = self.query_one("#data_source", Input).value.strip()
        local = self.query_one("#data_local", Input).value.strip()

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
        endpoint_select = self.query_one("#data_endpoint", Select)
        locally_mounted = self.query_one("#locally_mounted", Checkbox)
        format_select = self.query_one("#data_format", Select)
        return {
            "project_name": self.query_one("#project_name", Input).value,
            "analyst": self.query_one("#analyst", Input).value,
            "data_enabled": data_enabled.value,
            "data_endpoint": str(endpoint_select.value)
            if endpoint_select.value
            else "",
            "data_source": self.query_one("#data_source", Input).value,
            "data_local": self.query_one("#data_local", Input).value,
            "data_format": str(format_select.value)
            if format_select.value is not Select.BLANK
            else "",
            "locally_mounted": locally_mounted.value,
        }

    def _refresh_init_validation(self) -> None:
        for field_id in ("project_name", "analyst", "data_source", "data_local"):
            widget = self.query_one(f"#{field_id}", Input)
            widget.remove_class("valid")
            widget.remove_class("invalid")
            if widget.value.strip():
                widget.add_class("valid")
            else:
                widget.add_class("invalid")

    def _is_sync_disabled(self) -> bool:
        """Check if sync should be disabled."""
        try:
            checkbox = self.query_one("#locally_mounted", Checkbox)
            if not checkbox.value:
                return True

            source = self.query_one("#data_source", Input).value.strip()
            local = self.query_one("#data_local", Input).value.strip()

            if not source or not local:
                return True

            # Check if source and local are the same
            source_path = Path(source).expanduser().resolve()
            local_path = Path(local).expanduser().resolve()

            if source_path == local_path:
                return True

            # Check if local cache is a symlink pointing to source
            if local_path.is_symlink():
                try:
                    link_target = local_path.resolve()
                    if link_target == source_path:
                        return True
                except Exception:
                    pass

            return False
        except Exception:
            return True

    def _refresh_sync_button_state(self) -> None:
        """Update sync button appearance based on state."""
        try:
            sync_btn = self.query_one("#sync_btn", Button)
            if self._is_sync_disabled():
                sync_btn.add_class("disabled")
                sync_btn.variant = "default"
            else:
                sync_btn.remove_class("disabled")
                sync_btn.variant = "primary"
        except Exception:
            pass

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

    def _update_path_suggestions(self, input_id: str, current_value: str) -> None:
        """Update path suggestions dropdown based on current input."""
        try:
            suggestions = self.query_one("#path_suggestions", OptionList)
            suggestions.clear_options()

            if not current_value:
                self._hide_path_suggestions()
                return

            # Expand user path and get parent directory
            path = Path(current_value).expanduser()

            # Determine directory to list and prefix to match
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()

            if not search_dir.exists():
                self._hide_path_suggestions()
                return

            # Get matching entries
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
                self._active_path_input = input_id
                # Don't auto-focus - user presses Down arrow to navigate to suggestions
            else:
                self._hide_path_suggestions()
        except Exception:
            self._hide_path_suggestions()

    def _hide_path_suggestions(self) -> None:
        """Hide the path suggestions dropdown."""
        try:
            suggestions = self.query_one("#path_suggestions", OptionList)
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._active_path_input = None
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
        self.exit({"action": "init", "data": values})

    def _submit_log(self) -> None:
        if self._mode not in ("log", "menu", "both"):
            if self._log_error is not None:
                self._log_error.update("Logging is disabled in init-only mode.")
            return
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

        self.exit({"action": "manifest", "manifest": manifest})
