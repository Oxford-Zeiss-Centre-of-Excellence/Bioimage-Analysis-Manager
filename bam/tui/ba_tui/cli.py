from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .io import dump_manifest, load_manifest
from .models import (
    Dataset,
    Manifest,
    ManifestValidationError,
    TaskStatus,
    build_manifest,
)
from .scaffold import (
    create_idea_file,
    ensure_data_symlink,
    ensure_directories,
    ensure_log_types_template,
    ensure_worklog,
    register_artifact,
)
from .tui import BAApp, _serialize_figures
from .worklog import (
    append_worklog_entry,
    checkin_task,
    load_task_types,
    load_worklog,
    read_recent_entries,
    save_worklog,
    update_latest_active_task,
    update_task_status_by_index,
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=True))


def load_prefill(path: str | None) -> dict[str, object]:
    if not path:
        return {}
    prefill_path = Path(path)
    if not prefill_path.exists():
        return {}
    try:
        data = json.loads(prefill_path.read_text())
    except json.JSONDecodeError:
        return {}
    return {
        "project_name": str(data.get("project_name", "")),
        "analyst": str(data.get("analyst", "")),
        "data_enabled": bool(data.get("data_enabled", True)),
        "datasets": data.get("datasets", [])
        if isinstance(data.get("datasets"), list)
        else [],
    }


def run_init(args: argparse.Namespace) -> int:
    project_root = Path(args.path).expanduser().resolve()
    defaults = load_prefill(args.prefill)
    existing_manifest = load_manifest(project_root / "manifest.yaml")
    if existing_manifest:
        defaults["project_name"] = existing_manifest.project.name
        if existing_manifest.people:
            defaults["analyst"] = existing_manifest.people.analyst
        if existing_manifest.datasets:
            defaults["data_enabled"] = True
            defaults["datasets"] = [d.to_dict() for d in existing_manifest.datasets]
        else:
            defaults["data_enabled"] = False
    app = BAApp(
        mode="init",
        recent_entries=[],
        project_root=project_root,
        project_name=str(defaults.get("project_name", "")),
        analyst=str(defaults.get("analyst", "")),
        data_enabled=bool(defaults.get("data_enabled", True)),
        initial_data=defaults,
    )
    result = app.run()
    if result is None or result.get("action") != "init":
        emit({"status": "cancelled"})
        return 1

    try:
        result_data = result.get("data")
        if not isinstance(result_data, dict):
            emit({"status": "error", "message": "Invalid init response."})
            return 1
        manifest = build_manifest(
            project_name=str(result_data.get("project_name", "")),
            analyst=str(result_data.get("analyst", "")),
            datasets=[
                Dataset.from_dict(item)
                for item in result_data.get("datasets", [])
                if isinstance(item, dict)
            ],
        )
    except ManifestValidationError as exc:
        emit({"status": "error", "message": str(exc), "errors": exc.errors})
        return 1

    ensure_directories(project_root)
    ensure_worklog(project_root)
    ensure_log_types_template(project_root)
    manifest_path = project_root / "manifest.yaml"
    dump_manifest(manifest_path, manifest)

    warning = None
    if manifest.datasets:
        first = manifest.datasets[0]
        if first.local:
            warning = ensure_data_symlink(project_root, first.local)

    emit(
        {
            "status": "ok",
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
            "data_link_warning": warning,
        }
    )
    return 0


def run_log(args: argparse.Namespace) -> int:
    project_root = Path(args.path).expanduser().resolve()
    ensure_log_types_template(project_root)
    if args.message:
        entry = append_worklog_entry(project_root, args.message)
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "entry": entry,
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    if args.new_task:
        entry = checkin_task(project_root, args.new_task, args.task_type or "analysis")
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "entry": entry,
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    if args.checkout:
        if args.index is not None:
            entry = update_task_status_by_index(
                project_root,
                index=args.index,
                status=TaskStatus.completed,
                set_checkout=True,
            )
        else:
            entry = update_latest_active_task(
                project_root, status=TaskStatus.completed, set_checkout=True
            )
        if entry is None:
            emit({"status": "error", "message": "No active task to check out."})
            return 1
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "entry": entry,
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    if args.pause:
        if args.index is not None:
            entry = update_task_status_by_index(
                project_root, index=args.index, status=TaskStatus.paused
            )
        else:
            entry = update_latest_active_task(project_root, status=TaskStatus.paused)
        if entry is None:
            emit({"status": "error", "message": "No active task to pause."})
            return 1
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "entry": entry,
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    if args.status:
        try:
            status = TaskStatus(args.status)
        except ValueError:
            emit({"status": "error", "message": f"Invalid status: {args.status}"})
            return 1
        if args.index is not None:
            entry = update_task_status_by_index(
                project_root, index=args.index, status=status
            )
        else:
            entry = update_latest_active_task(project_root, status=status)
        if entry is None:
            emit({"status": "error", "message": "No task found to update."})
            return 1
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "entry": entry,
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    recent = read_recent_entries(project_root)
    worklog = load_worklog(project_root)
    task_types = load_task_types(project_root)
    app = BAApp(
        mode="log",
        recent_entries=recent,
        worklog_entries=None,  # Legacy parameter, not used anymore
        task_types=task_types,
    )
    result = app.run()
    if result is None or result.get("action") != "log":
        emit({"status": "cancelled"})
        return 1

    # Worklog is auto-saved by worklog operations, no need to save here
    emit(
        {
            "status": "ok",
            "project_root": str(project_root),
            "worklog_path": str(project_root / "log" / "tasks.yaml"),
        }
    )
    return 0


def run_idea(args: argparse.Namespace) -> int:
    project_root = Path(args.path).expanduser().resolve()
    recent = read_recent_entries(project_root)
    app = BAApp(
        mode="idea",
        recent_entries=recent,
        idea_title=args.title or "",
    )
    result = app.run()
    if result is None or result.get("action") != "idea":
        emit({"status": "cancelled"})
        return 1
    data = result.get("data")
    if not isinstance(data, dict):
        emit({"status": "error", "message": "Invalid idea response."})
        return 1
    idea_path = create_idea_file(
        project_root,
        title=data.get("title", ""),
        priority=data.get("priority", "medium"),
        problem=data.get("problem", ""),
        approach=data.get("approach", ""),
    )
    emit(
        {
            "status": "ok",
            "project_root": str(project_root),
            "idea_path": str(idea_path),
        }
    )
    return 0


def run_artifact(args: argparse.Namespace) -> int:
    project_root = Path(args.path).expanduser().resolve()
    manifest_path = project_root / "manifest.yaml"
    manifest = load_manifest(manifest_path)
    if manifest is None:
        emit({"status": "error", "message": "manifest.yaml not found."})
        return 1

    if args.register:
        manifest = register_artifact(
            manifest,
            path=args.register,
            artifact_type=args.artifact_type or "unknown",
            status=args.status or "draft",
        )
        dump_manifest(manifest_path, manifest)
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "manifest_path": str(manifest_path),
            }
        )
        return 0

    recent = read_recent_entries(project_root)
    app = BAApp(
        mode="artifact",
        recent_entries=recent,
        artifacts=manifest.artifacts,
    )
    result = app.run()
    if result is None or result.get("action") != "artifact":
        emit({"status": "cancelled"})
        return 1

    updated = result.get("artifacts", [])
    if isinstance(updated, list):
        manifest.artifacts = updated
        dump_manifest(manifest_path, manifest)
    emit(
        {
            "status": "ok",
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
        }
    )
    return 0


def run_manifest(args: argparse.Namespace) -> int:
    project_root = Path(args.path).expanduser().resolve()
    manifest_path = project_root / "manifest.yaml"
    manifest = load_manifest(manifest_path)
    if manifest is None:
        emit({"status": "error", "message": "manifest.yaml not found."})
        return 1
    recent = read_recent_entries(project_root)
    app = BAApp(
        mode="manifest",
        recent_entries=recent,
        manifest=manifest,
    )
    result = app.run()
    if result is None or result.get("action") != "manifest":
        emit({"status": "cancelled"})
        return 1
    manifest = result.get("manifest")
    if not isinstance(manifest, Manifest):
        emit({"status": "error", "message": "Invalid manifest response."})
        return 1
    dump_manifest(manifest_path, manifest)
    emit(
        {
            "status": "ok",
            "project_root": str(project_root),
            "manifest_path": str(manifest_path),
        }
    )
    return 0


def run_menu(args: argparse.Namespace) -> int:
    """Launch main menu TUI when no subcommand given."""
    project_root = Path(".").resolve()
    recent = read_recent_entries(project_root)
    manifest = load_manifest(project_root / "manifest.yaml")

    defaults = {}
    if manifest:
        defaults = {
            "project_name": manifest.project.name,
            "project_status": manifest.project.status
            if manifest.project and hasattr(manifest.project, "status")
            else "active",
            "analyst": manifest.people.analyst if manifest.people else "",
            "data_enabled": bool(manifest.datasets),
            "datasets": [d.to_dict() for d in manifest.datasets],
        }
        # Add tags
        if manifest.tags:
            defaults["tags"] = ", ".join(manifest.tags)

        # Add collaborators
        if manifest.people and manifest.people.collaborators:
            defaults["collaborators"] = [
                {
                    "name": c.name,
                    "role": c.role,
                    "email": c.email,
                    "affiliation": c.affiliation,
                }
                for c in manifest.people.collaborators
            ]

        # Add acquisition sessions
        if manifest.acquisition and manifest.acquisition.sessions:
            defaults["acquisition_sessions"] = [
                {
                    "imaging_date": session.imaging_date,
                    "microscope": session.microscope,
                    "modality": session.modality,
                    "objective": session.objective,
                    "voxel_x": str(session.voxel_size.x_um)
                    if session.voxel_size and session.voxel_size.x_um
                    else "",
                    "voxel_y": str(session.voxel_size.y_um)
                    if session.voxel_size and session.voxel_size.y_um
                    else "",
                    "voxel_z": str(session.voxel_size.z_um)
                    if session.voxel_size and session.voxel_size.z_um
                    else "",
                    "time_interval_s": str(session.time_interval_s)
                    if session.time_interval_s
                    else "",
                    "notes": session.notes,
                    "channels": [
                        {
                            "name": ch.name,
                            "fluorophore": ch.fluorophore or "",
                            "excitation_nm": str(ch.excitation_nm)
                            if ch.excitation_nm
                            else "",
                            "emission_nm": str(ch.emission_nm)
                            if ch.emission_nm
                            else "",
                        }
                        for ch in session.channels
                    ],
                }
                for session in manifest.acquisition.sessions
            ]

        # Add tools fields
        if manifest.tools:
            if manifest.tools.environment:
                env_value = manifest.tools.environment
                known_env = {
                    "conda",
                    "pixi",
                    "venv",
                    "docker",
                    "devcontainer",
                    "renv",
                    "nix",
                    "c-cpp",
                    "js-ts",
                    "other",
                }
                if env_value in known_env:
                    defaults["environment"] = env_value
                else:
                    defaults["environment"] = "other"
                    defaults["environment_custom"] = env_value
            if manifest.tools.env_file:
                defaults["env_file"] = manifest.tools.env_file
            if manifest.tools.git_remote:
                defaults["git_remote"] = manifest.tools.git_remote
            if manifest.tools.languages:
                defaults["languages"] = manifest.tools.languages
            if manifest.tools.software:
                defaults["software"] = manifest.tools.software
            if manifest.tools.cluster_packages:
                defaults["cluster_packages"] = manifest.tools.cluster_packages
        # Add method fields
        if manifest.method:
            if manifest.method.file_path:
                defaults["method_path"] = manifest.method.file_path
        # Add hardware profiles
        if manifest.hardware_profiles:
            defaults["hardware_profiles"] = [
                {
                    "name": profile.name,
                    "cpu": profile.cpu,
                    "ram": profile.ram,
                    "gpu": profile.gpu,
                    "notes": profile.notes,
                    "is_cluster": profile.is_cluster,
                    "partition": profile.partition,
                    "node_type": profile.node_type,
                }
                for profile in manifest.hardware_profiles
            ]
        # Add billing fields
        if manifest.billing:
            if manifest.billing.fund_code:
                defaults["fund_code"] = manifest.billing.fund_code
            if manifest.billing.hourly_rate is not None:
                defaults["hourly_rate"] = str(manifest.billing.hourly_rate)
            if manifest.billing.budget_hours is not None:
                defaults["budget_hours"] = str(manifest.billing.budget_hours)
            if manifest.billing.spent_hours is not None:
                defaults["spent_hours"] = str(manifest.billing.spent_hours)
            if manifest.billing.start_date:
                defaults["billing_start_date"] = manifest.billing.start_date
            if manifest.billing.end_date:
                defaults["billing_end_date"] = manifest.billing.end_date
            if manifest.billing.notes:
                defaults["billing_notes"] = manifest.billing.notes
        # Add timeline/milestones
        if manifest.timeline and manifest.timeline.milestones:
            defaults["milestones"] = [
                {
                    "name": m.name,
                    "target_date": m.target_date,
                    "actual_date": m.actual_date,
                    "status": m.status,
                    "notes": getattr(m, "notes", ""),
                }
                for m in manifest.timeline.milestones
            ]
        # Add outputs defaults
        if manifest.publication:
            defaults["publication"] = {
                "pub_status": manifest.publication.status,
                "target_journal": manifest.publication.target_journal,
                "manuscript_path": manifest.publication.manuscript_path,
                "preprint_doi": manifest.publication.preprint_doi,
                "published_doi": manifest.publication.published_doi,
                "github_repo": manifest.publication.github_repo,
                "zenodo_doi": manifest.publication.zenodo_doi,
                "pub_notes": manifest.publication.notes,
            }
            defaults["figures"] = _serialize_figures(manifest.publication.figures)
        if manifest.archive:
            defaults["archive"] = {
                "archive_status": manifest.archive.status,
                "archive_date": manifest.archive.archive_date,
                "archive_location": manifest.archive.archive_location,
                "archive_endpoint": manifest.archive.endpoint or "",
                "retention_years": manifest.archive.retention_years,
                "backup_verified": manifest.archive.backup_verified,
                "archive_notes": manifest.archive.notes,
            }
        if manifest.artifacts:
            defaults["artifacts"] = [
                artifact.model_dump() for artifact in manifest.artifacts
            ]
    app = BAApp(
        mode="menu",
        recent_entries=recent,
        project_root=project_root,
        manifest=manifest,
        project_name=str(defaults.get("project_name", "")),
        analyst=str(defaults.get("analyst", "")),
        data_enabled=bool(defaults.get("data_enabled", True)),
        initial_data=defaults,
    )
    result = app.run()

    if result is None:
        emit({"status": "cancelled"})
        return 1

    # Handle init action directly (TUI already collected data)
    if result.get("action") == "init":
        try:
            result_data = result.get("data")
            if not isinstance(result_data, dict):
                emit({"status": "error", "message": "Invalid init response."})
                return 1
            manifest = build_manifest(
                project_name=str(result_data.get("project_name", "")),
                analyst=str(result_data.get("analyst", "")),
                datasets=[
                    Dataset.from_dict(item)
                    for item in result_data.get("datasets", [])
                    if isinstance(item, dict)
                ],
            )
        except ManifestValidationError as exc:
            emit({"status": "error", "message": str(exc), "errors": exc.errors})
            return 1

        ensure_directories(project_root)
        ensure_worklog(project_root)
        manifest_path = project_root / "manifest.yaml"
        dump_manifest(manifest_path, manifest)
        warning = None
        if manifest.datasets:
            first = manifest.datasets[0]
            if first.local:
                warning = ensure_data_symlink(project_root, first.local)

        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "manifest_path": str(manifest_path),
                "data_link_warning": warning,
            }
        )
        return 0

    # Handle log action directly
    elif result.get("action") == "log":
        # Worklog is auto-saved by worklog operations, no need to save here
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "worklog_path": str(project_root / "log" / "tasks.yaml"),
            }
        )
        return 0

    elif result.get("action") == "idea":
        data = result.get("data")
        if not isinstance(data, dict):
            emit({"status": "error", "message": "Invalid idea response."})
            return 1
        idea_path = create_idea_file(
            project_root,
            title=data.get("title", ""),
            priority=data.get("priority", "medium"),
            problem=data.get("problem", ""),
            approach=data.get("approach", ""),
        )
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "idea_path": str(idea_path),
            }
        )
        return 0

    elif result.get("action") == "artifact":
        if manifest is None:
            emit({"status": "error", "message": "manifest.yaml not found."})
            return 1
        updated = result.get("artifacts", [])
        if isinstance(updated, list):
            manifest.artifacts = updated
            dump_manifest(project_root / "manifest.yaml", manifest)
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "manifest_path": str(project_root / "manifest.yaml"),
            }
        )
        return 0

    elif result.get("action") == "manifest":
        if manifest is None:
            emit({"status": "error", "message": "manifest.yaml not found."})
            return 1
        updated_manifest = result.get("manifest")
        if not isinstance(updated_manifest, Manifest):
            emit({"status": "error", "message": "Invalid manifest response."})
            return 1
        dump_manifest(project_root / "manifest.yaml", updated_manifest)
        emit(
            {
                "status": "ok",
                "project_root": str(project_root),
                "manifest_path": str(project_root / "manifest.yaml"),
            }
        )
        return 0

    else:
        emit({"status": "cancelled"})
        return 1


def run_validate(args: argparse.Namespace) -> int:
    """Validate manifest.yaml schema."""
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
    else:
        manifest_path = Path(".").resolve() / "manifest.yaml"

    if not manifest_path.exists():
        if not args.quiet:
            emit({"status": "error", "message": f"Manifest not found: {manifest_path}"})
        return 1

    try:
        manifest = load_manifest(manifest_path)
        if manifest is None:
            if not args.quiet:
                emit(
                    {"status": "error", "message": "Manifest is empty or invalid YAML"}
                )
            return 1

        if not args.quiet:
            emit(
                {
                    "status": "ok",
                    "message": "Manifest validation passed",
                    "manifest_path": str(manifest_path),
                }
            )
        return 0

    except ManifestValidationError as exc:
        if not args.quiet:
            emit(
                {
                    "status": "error",
                    "message": "Manifest validation failed",
                    "manifest_path": str(manifest_path),
                    "errors": exc.errors,
                }
            )
        return 1
    except Exception as exc:
        if not args.quiet:
            emit(
                {
                    "status": "error",
                    "message": f"Validation error: {str(exc)}",
                    "manifest_path": str(manifest_path),
                }
            )
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bam",
        description="BAM (Bioimage Analysis Manager) - TUI for project management, work logging, and artifact tracking.",
        epilog="""
Examples:
  bam                          Open main menu
  bam init                     Initialize project in current directory
  bam init --path /data/proj   Initialize project at specific path
  bam log                      Open TUI to add worklog entry
  bam log --message "Done"     Add entry directly (no TUI)

Output:
  All commands output JSON to stdout for easy parsing by scripts and agents.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.set_defaults(func=run_menu)
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a BA project",
        description="Create project structure with manifest, directories, and data symlink.",
        epilog="""
Examples:
  bam init                          Interactive TUI in current directory
  bam init --path /data/my-project  Initialize at specific path
  bam init --prefill defaults.json  Pre-fill form with JSON data
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    init_parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Project root directory (default: current directory)",
    )
    init_parser.add_argument(
        "--prefill",
        metavar="FILE",
        help="JSON file with prefill data (project_name, analyst, datasets)",
    )
    init_parser.set_defaults(func=run_init)

    # log subcommand
    log_parser = subparsers.add_parser(
        "log",
        help="Append a worklog entry",
        description="Add structured entry to .bam/log/tasks.yaml with time tracking.",
        epilog="""
Examples:
  bam log                                    Open TUI to write entry
  bam log --message "Ran segmentation"       Add entry directly
  bam log --path /data/proj --message "Done" Add to specific project
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    log_parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Project root directory (default: current directory)",
    )
    log_parser.add_argument(
        "--message",
        "-m",
        metavar="TEXT",
        help="Log entry message (skips TUI if provided)",
    )
    log_parser.add_argument(
        "-n",
        "--new-task",
        metavar="TEXT",
        help="Quick check-in for a new task (creates active entry)",
    )
    log_parser.add_argument(
        "--type", dest="task_type", metavar="TYPE", help="Task type for quick check-in"
    )
    log_parser.add_argument(
        "-o",
        "--checkout",
        action="store_true",
        help="Quick check-out of latest active task",
    )
    log_parser.add_argument(
        "-p", "--pause", action="store_true", help="Pause latest active task"
    )
    log_parser.add_argument(
        "-s", "--status", metavar="STATUS", help="Change status of latest active task"
    )
    log_parser.add_argument(
        "--index", type=int, help="Entry index to target for quick actions"
    )
    log_parser.set_defaults(func=run_log)

    # idea subcommand
    idea_parser = subparsers.add_parser(
        "idea",
        help="Create a new idea entry",
        description="Create an idea markdown file from template.",
        epilog="""
Examples:
  bam idea
  bam idea --title "GPU acceleration"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    idea_parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Project root directory (default: current directory)",
    )
    idea_parser.add_argument("--title", metavar="TEXT", help="Prefill idea title")
    idea_parser.set_defaults(func=run_idea)

    # artifact subcommand
    artifact_parser = subparsers.add_parser(
        "artifact",
        help="Register or update artifacts",
        description="Register artifacts and update status in manifest.yaml.",
        epilog="""
Examples:
  bam artifact
  bam artifact --register .bam/artifact/figure1.png --type figure
  bam artifact --status delivered
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    artifact_parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Project root directory (default: current directory)",
    )
    artifact_parser.add_argument(
        "--register",
        metavar="PATH",
        help="Register an artifact path immediately (skips TUI)",
    )
    artifact_parser.add_argument(
        "--type",
        dest="artifact_type",
        metavar="TYPE",
        help="Artifact type (figure, table, report, etc.)",
    )
    artifact_parser.add_argument(
        "--status",
        metavar="STATUS",
        help="Artifact status (draft, ready, delivered, archived)",
    )
    artifact_parser.set_defaults(func=run_artifact)

    # manifest subcommand
    manifest_parser = subparsers.add_parser(
        "manifest",
        help="Edit manifest sections",
        description="Open TUI to edit the full manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    manifest_parser.add_argument(
        "--path",
        default=".",
        metavar="DIR",
        help="Project root directory (default: current directory)",
    )
    manifest_parser.set_defaults(func=run_manifest)

    # validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate manifest.yaml schema",
        description="Check if manifest.yaml conforms to the expected schema.",
        epilog="""
Examples:
  bam validate                       Validate manifest.yaml in current directory
  bam validate --manifest path.yaml  Validate specific manifest file
  bam validate --quiet               Quiet mode for CI (no output, only exit code)
  
Exit codes:
  0 - Validation passed
  1 - Validation failed
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    validate_parser.add_argument(
        "--manifest",
        metavar="FILE",
        help="Path to manifest file (default: manifest.yaml in current directory)",
    )
    validate_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode - suppress output (useful for CI/CD)",
    )
    validate_parser.set_defaults(func=run_validate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        exit_code = args.func(args)
    except KeyboardInterrupt:
        emit({"status": "cancelled"})
        exit_code = 1
    except Exception as exc:  # pragma: no cover - safeguard for CLI
        emit({"status": "error", "message": str(exc)})
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
