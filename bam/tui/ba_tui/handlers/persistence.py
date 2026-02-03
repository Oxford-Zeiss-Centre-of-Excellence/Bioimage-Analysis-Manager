from __future__ import annotations
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from textual.widgets import (
    Checkbox,
    DataTable,
    Input,
    SelectionList,
    Select,
    Static,
    TextArea,
)

from ..io import dump_manifest
from ..models import (
    Manifest,
    Manifest as ManifestModel,
    ManifestValidationError,
    raise_validation_error,
)
from ..scaffold import ensure_data_symlink, ensure_directories, ensure_worklog
from ..widgets import DateSelect


def validate_manifest_data(
    data: dict[str, Any],
) -> tuple[bool, str, ManifestModel | None]:
    """Validate manifest data dictionary.

    Returns:
        (is_valid, error_message, manifest_object)
    """
    try:
        manifest = Manifest.model_validate(data)
        return (True, "", manifest)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            loc = ".".join(str(item) for item in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            error_details.append(f"  • {loc}: {msg}")
        error_message = "Manifest validation failed:\n" + "\n".join(error_details)
        return (False, error_message, None)
    except Exception as e:
        return (False, f"Validation error: {str(e)}", None)


def create_manifest_backup(manifest_path: Path) -> Path | None:
    """Create a timestamped backup of the manifest file.

    Returns:
        Path to backup file, or None if backup failed
    """
    if not manifest_path.exists():
        return None

    try:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        backup_path = manifest_path.with_suffix(f".{timestamp}.bak.yaml")

        # Copy the file
        import shutil

        shutil.copy2(manifest_path, backup_path)

        return backup_path
    except Exception:
        return None


class PersistenceMixin:
    """Mixin for saving/loading manifest and form state."""

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)

    _project_root: Path
    _defaults: dict[str, object]
    _dataset_rows: list[dict[str, object]]
    _collaborator_rows: list[dict[str, str]]
    _milestone_rows: list[dict[str, object]]
    _acquisition_rows: list[dict[str, object]]
    _channel_rows: list[dict[str, str]]
    _hardware_profiles: list[dict[str, str | bool]]
    _figure_tree_data: list[dict[str, object]]
    _artifact_rows: list[dict[str, object]]
    _manifest: ManifestModel | None
    _init_error: Static | None
    _log_error: Static | None
    _manifest_errors: Static | None
    _method_template_used: str
    query_one: Any
    notify: Any
    exit: Any
    run_worker: Any
    push_screen: Any
    _populate_collaborators_table: Any
    _toggle_data_sections: Any
    _populate_datasets_table: Any
    _to_pendulum_date: Any
    _populate_milestones_table: Any
    _populate_acquisition_table: Any
    _load_session_channels: Any
    _populate_channels_table: Any
    _load_method_preview: Any
    _refresh_init_validation: Any
    _collect_collaborators: Any
    _collect_datasets: Any
    _normalize_date: Any
    _collect_milestones: Any
    _sanitize_manifest_dates: Any
    _collect_acquisition_sessions: Any
    _store_ui_state: Any
    _populate_figure_tree: Any
    _populate_artifacts_table: Any
    _load_archive_defaults: Any
    _load_publication_defaults: Any
    _collect_publication: Any
    _collect_archive: Any
    _collect_artifacts: Any

    def _reload_form_from_manifest(self, manifest: ManifestModel) -> None:
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
                    "image_quality": dataset.image_quality or "",
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

        # Outputs defaults
        try:
            self._load_publication_defaults(manifest)
        except Exception:
            pass

        try:
            self._load_archive_defaults(manifest)
        except Exception:
            pass

        try:
            self._figure_tree_data = self._serialize_figures(
                manifest.publication.figures if manifest.publication else []
            )
            self._populate_figure_tree()
        except Exception:
            pass

        try:
            self._artifact_rows = [
                artifact.model_dump() for artifact in manifest.artifacts
            ]
            self._populate_artifacts_table()
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

            # Collect outputs data
            try:
                publication = self._collect_publication()
                if publication:
                    manifest_data["publication"] = publication
                else:
                    manifest_data.pop("publication", None)
            except Exception:
                pass

            try:
                archive = self._collect_archive()
                if archive:
                    manifest_data["archive"] = archive
                else:
                    manifest_data.pop("archive", None)
            except Exception:
                pass

            try:
                artifacts = self._collect_artifacts()
                if artifacts:
                    manifest_data["artifacts"] = [
                        artifact.model_dump() for artifact in artifacts
                    ]
                else:
                    manifest_data.pop("artifacts", None)
            except Exception:
                pass

            # Collect hardware profiles
            if self._hardware_profiles:
                manifest_data["hardware_profiles"] = self._hardware_profiles
            else:
                manifest_data.pop("hardware_profiles", None)

            # Validate manifest data before saving
            is_valid, error_msg, validated_manifest = validate_manifest_data(
                manifest_data
            )
            if not is_valid:
                # Create backup of corrupted data before rejecting
                backup_path = create_manifest_backup(manifest_path)
                if backup_path:
                    self.notify(
                        f"Backup created: {backup_path.name}",
                        severity="information",
                        timeout=3,
                    )

                self.notify(
                    "Validation failed. Please fix errors before saving.",
                    severity="error",
                )
                self.notify(error_msg, severity="warning", timeout=10)
                return

            # Save the validated manifest
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
            self.notify(f"Save failed: {e}", severity="error", markup=False)

    def _save_log(self) -> None:
        """Save manifest (not tasks.yaml which is auto-saved on changes)."""
        # Note: Worklog is auto-saved by worklog operations
        # Ctrl+S should save the manifest, not the tasks
        self._save_init()

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
            manifest_data = {k: v for k, v in sections.items() if v is not None}

            # Validate before saving
            is_valid, error_msg, manifest = validate_manifest_data(manifest_data)
            manifest_path = self._project_root / "manifest.yaml"

            if not is_valid:
                # Create backup of corrupted existing manifest before rejecting save
                backup_path = create_manifest_backup(manifest_path)
                if backup_path:
                    self.notify(
                        f"Backup created: {backup_path.name}",
                        severity="information",
                        timeout=3,
                    )

                self.notify("Validation failed. Please fix errors.", severity="error")
                self.notify(error_msg, severity="warning", timeout=10)
                return

            # Save the validated manifest (no backup needed - data is valid)
            assert (
                manifest is not None
            )  # Type guard: manifest is always non-None when is_valid=True
            dump_manifest(manifest_path, manifest)
            self.notify("Manifest saved", severity="information")
        except Exception as e:
            self.notify(f"Save failed: {e}", severity="error", markup=False)

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
