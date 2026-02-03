"""Task-based worklog with YAML storage."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from .io import dump_manifest, load_manifest
from .models import (
    LogTaskStatus,
    RunStatus,
    Session,
    Task,
    TaskCategory,
    TaskDifficulty,
    TaskSubCategory,
    WorkLog,
    WorklogManifest,
)

# Sentinel value to distinguish "not provided" from "set to None"
_UNSET = object()


# =============================================================================
# Path helpers
# =============================================================================


def get_worklog_path(project_root: Path) -> Path:
    """Get worklog file path from manifest, or use default."""
    try:
        manifest_path = project_root / "manifest.yaml"
        manifest = load_manifest(manifest_path)
        if manifest and manifest.worklog and manifest.worklog.file_path:
            return project_root / manifest.worklog.file_path
    except Exception:
        pass

    # Default path
    return project_root / "log" / "tasks.yaml"


def _worklog_csv_path(project_root: Path) -> Path:
    """Legacy CSV worklog path (for migration)."""
    return project_root / "log" / "worklog.csv"


# =============================================================================
# Manifest integration
# =============================================================================


def init_worklog_manifest_section(project_root: Path) -> None:
    """Initialize worklog section in manifest if missing."""
    try:
        manifest_path = project_root / "manifest.yaml"
        manifest = load_manifest(manifest_path)
        if manifest and manifest.worklog is None:
            manifest.worklog = WorklogManifest(
                file_path="log/tasks.yaml",
                version=2,
                created=date.today(),
                last_updated=date.today(),
            )
            dump_manifest(manifest_path, manifest)
    except Exception:
        pass


def update_worklog_timestamp(project_root: Path) -> None:
    """Update last_updated timestamp in manifest."""
    try:
        manifest_path = project_root / "manifest.yaml"
        manifest = load_manifest(manifest_path)
        if manifest and manifest.worklog:
            manifest.worklog.last_updated = date.today()
            dump_manifest(manifest_path, manifest)
    except Exception:
        pass


# =============================================================================
# YAML storage
# =============================================================================


def load_worklog(project_root: Path) -> WorkLog:
    """Load worklog from YAML file."""
    worklog_path = get_worklog_path(project_root)

    if not worklog_path.exists():
        return WorkLog()

    try:
        with open(worklog_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        worklog = WorkLog.model_validate(data)

        # Clean up invalid subcategories (data migration)
        needs_save = False
        for task in worklog.tasks:
            if task.sub_category:
                # Import here to avoid circular dependency
                from .config import category_has_subcategories, load_task_subcategories

                # Check if category supports subcategories
                if not category_has_subcategories(task.category.value, project_root):
                    # Category doesn't support subcategories, clear it
                    task.sub_category = None
                    needs_save = True
                else:
                    # Check if subcategory is valid for this category
                    valid_subcats = load_task_subcategories(
                        task.category.value, project_root
                    )
                    valid_values = [value for label, value in valid_subcats]

                    if task.sub_category.value not in valid_values:
                        # Invalid subcategory for this category, clear it
                        task.sub_category = None
                        needs_save = True

        # Save if we cleaned up any data
        if needs_save:
            save_worklog(project_root, worklog)

        return worklog
    except Exception:
        return WorkLog()


def save_worklog(project_root: Path, worklog: WorkLog) -> None:
    """Save worklog to YAML file."""
    worklog_path = get_worklog_path(project_root)
    worklog_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for YAML serialization
    data = worklog.model_dump(mode="json", exclude_none=False)

    with open(worklog_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

    # Update manifest timestamp
    update_worklog_timestamp(project_root)


# =============================================================================
# Migration from CSV
# =============================================================================


def migrate_csv_to_yaml(project_root: Path) -> bool:
    """Migrate old CSV worklog to new YAML format.

    Returns:
        True if migration was performed, False if not needed.
    """
    csv_path = _worklog_csv_path(project_root)

    if not csv_path.exists():
        return False

    # Check if already migrated
    yaml_path = get_worklog_path(project_root)
    if yaml_path.exists():
        return False

    # Create a "Legacy" task with all CSV entries as sessions
    try:
        import csv as csv_module

        sessions = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv_module.DictReader(f)
            for row in reader:
                try:
                    checkin_str = row.get("checkin", "")
                    checkout_str = row.get("checkout", "")

                    if not checkin_str:
                        continue

                    punch_in = datetime.fromisoformat(checkin_str)
                    punch_out = (
                        datetime.fromisoformat(checkout_str) if checkout_str else None
                    )
                    note = row.get("notes") or row.get("task", "")

                    session = Session(
                        punch_in=punch_in,
                        punch_out=punch_out,
                        note=note,
                    )
                    sessions.append(session)
                except Exception:
                    continue

        if sessions:
            # Create Legacy task
            legacy_task = Task(
                id=str(uuid.uuid4()),
                name="Legacy Worklog (Migrated)",
                category=TaskCategory.other,
                status=LogTaskStatus.archived,
                sessions=sessions,
                created=datetime.now(),
            )

            worklog = WorkLog(tasks=[legacy_task])
            save_worklog(project_root, worklog)

            # Initialize manifest section
            init_worklog_manifest_section(project_root)

            # Backup CSV
            backup_path = csv_path.with_suffix(".csv.backup")
            csv_path.rename(backup_path)

            return True
    except Exception:
        pass

    return False


# =============================================================================
# Task operations
# =============================================================================


def create_task(
    project_root: Path,
    name: str,
    category: TaskCategory,
    sub_category: Optional[TaskSubCategory] = None,
    difficulty: Optional[TaskDifficulty] = None,
    data_path: Optional[str] = None,
    compute: Optional[str] = None,
    run_status: Optional[RunStatus] = None,
) -> Task:
    """Create a new task and add it to the worklog."""
    worklog = load_worklog(project_root)

    task = Task(
        id=str(uuid.uuid4()),
        name=name,
        category=category,
        sub_category=sub_category,
        difficulty=difficulty,
        status=LogTaskStatus.active,
        data_path=data_path,
        compute=compute,
        run_status=run_status,
        sessions=[],
        created=datetime.now(),
    )

    worklog.tasks.append(task)
    save_worklog(project_root, worklog)

    return task


def punch_in(project_root: Path, task_id: str) -> Optional[Session]:
    """Punch in to a task (create new session)."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return None

    # Check if already has an active session
    if task.active_session() is not None:
        return None

    session = Session(
        punch_in=datetime.now(),
        punch_out=None,
        note=None,
    )

    task.sessions.append(session)
    save_worklog(project_root, worklog)

    return session


def punch_out(project_root: Path, task_id: str) -> Optional[Session]:
    """Punch out of a task (close active session)."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return None

    active = task.active_session()
    if active is None:
        return None

    active.punch_out = datetime.now()
    save_worklog(project_root, worklog)

    return active


def add_session_note(
    project_root: Path,
    task_id: str,
    session_index: int,
    note: str,
) -> bool:
    """Add a note to a specific session."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None or session_index < 0 or session_index >= len(task.sessions):
        return False

    task.sessions[session_index].note = note
    save_worklog(project_root, worklog)

    return True


def edit_session(
    project_root: Path,
    task_id: str,
    session_index: int,
    punch_in: datetime,
    punch_out: Optional[datetime],
    note: Optional[str],
) -> bool:
    """Edit a session's times and note."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None or session_index < 0 or session_index >= len(task.sessions):
        return False

    session = task.sessions[session_index]
    session.punch_in = punch_in
    session.punch_out = punch_out
    session.note = note

    save_worklog(project_root, worklog)

    return True


def complete_task(project_root: Path, task_id: str) -> bool:
    """Mark a task as completed."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return False

    # Punch out any active session
    if task.active_session() is not None:
        punch_out(project_root, task_id)
        # Reload worklog after punch_out
        worklog = load_worklog(project_root)
        task = worklog.get_task_by_id(task_id)
        if task is None:
            return False

    task.status = LogTaskStatus.completed
    save_worklog(project_root, worklog)

    return True


def incomplete_task(project_root: Path, task_id: str) -> bool:
    """Mark a task as active (uncomplete it)."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return False

    task.status = LogTaskStatus.active
    save_worklog(project_root, worklog)

    return True


def delete_task(project_root: Path, task_id: str) -> bool:
    """Delete a task from the worklog."""
    worklog = load_worklog(project_root)

    worklog.tasks = [t for t in worklog.tasks if t.id != task_id]
    save_worklog(project_root, worklog)

    return True


def delete_session(project_root: Path, task_id: str, session_index: int) -> bool:
    """Delete a session from a task."""
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return False

    if 0 <= session_index < len(task.sessions):
        task.sessions.pop(session_index)
        save_worklog(project_root, worklog)
        return True

    return False


def edit_task(
    project_root: Path,
    task_id: str,
    name: Any = _UNSET,
    category: Any = _UNSET,
    sub_category: Any = _UNSET,
    difficulty: Any = _UNSET,
    data_path: Any = _UNSET,
    compute: Any = _UNSET,
    run_status: Any = _UNSET,
) -> bool:
    """Edit task properties.

    Uses sentinel value _UNSET to distinguish between "not provided" and "set to None".
    This allows explicitly clearing fields by passing None.
    """
    worklog = load_worklog(project_root)
    task = worklog.get_task_by_id(task_id)

    if task is None:
        return False

    if name is not _UNSET:
        task.name = name
    if category is not _UNSET:
        task.category = category
    if sub_category is not _UNSET:
        task.sub_category = sub_category
    if difficulty is not _UNSET:
        task.difficulty = difficulty
    if data_path is not _UNSET:
        task.data_path = data_path
    if compute is not _UNSET:
        task.compute = compute
    if run_status is not _UNSET:
        task.run_status = run_status

    save_worklog(project_root, worklog)

    return True


# =============================================================================
# Validation helpers
# =============================================================================


def validate_sessions(project_root: Path) -> tuple[int, list[tuple[str, int, str]]]:
    """Validate all sessions and return problematic ones.

    Returns:
        (total_count, [(task_id, session_index, reason), ...])
    """
    worklog = load_worklog(project_root)
    problems = []

    for task in worklog.tasks:
        for idx, session in enumerate(task.sessions):
            is_prob, reason = session.is_problematic()
            if is_prob:
                problems.append((task.id, idx, reason))

    return (len(problems), problems)


# =============================================================================
# Backward compatibility functions (for CLI)
# =============================================================================


def append_worklog_entry(project_root: Path, message: str) -> dict[str, str]:
    """Legacy function for CLI compatibility.

    Creates a simple task with one completed session.
    """
    from datetime import datetime

    task = create_task(
        project_root,
        name=message,
        category=TaskCategory.other,
    )

    # Create a completed session
    session = Session(
        punch_in=datetime.now(),
        punch_out=datetime.now(),
        note=None,
    )
    task.sessions.append(session)

    worklog = load_worklog(project_root)
    save_worklog(project_root, worklog)

    return {"task": task.name, "status": "completed"}


def checkin_task(project_root: Path, task: str, task_type: str) -> dict[str, str]:
    """Legacy function for CLI compatibility.

    Creates a new task and punches in.
    """
    # Map old task_type to new categories
    category_map = {
        "analysis": TaskCategory.other,
        "development": TaskCategory.development,
        "data_copying": TaskCategory.data_copying,
        "data copying": TaskCategory.data_copying,
        "execution": TaskCategory.execution,
        "documentation": TaskCategory.documentation,
        "meeting": TaskCategory.meeting,
        "admin": TaskCategory.admin,
    }

    category = category_map.get(task_type.lower(), TaskCategory.other)

    new_task = create_task(
        project_root,
        name=task,
        category=category,
    )

    punch_in(project_root, new_task.id)

    return {"task_id": new_task.id, "status": "active"}


def load_task_types(project_root: Path) -> list[dict[str, str]]:
    """Legacy function for CLI compatibility.

    Returns basic task types for backward compatibility.
    """
    return [
        {"id": "development", "label": "Development"},
        {"id": "data_copying", "label": "Data Copying"},
        {"id": "execution", "label": "Execution"},
        {"id": "documentation", "label": "Documentation"},
        {"id": "meeting", "label": "Meeting"},
        {"id": "admin", "label": "Admin"},
        {"id": "other", "label": "Other"},
    ]


def read_recent_entries(project_root: Path, limit: int = 10) -> list[str]:
    """Legacy function for CLI compatibility.

    Returns recent sessions formatted as strings.
    """
    worklog = load_worklog(project_root)
    entries = []

    # Collect all sessions from all tasks
    all_sessions = []
    for task in worklog.tasks:
        for session in task.sessions:
            all_sessions.append((task.name, session))

    # Sort by punch_in time (most recent first)
    all_sessions.sort(key=lambda x: x[1].punch_in, reverse=True)

    # Format and return
    for task_name, session in all_sessions[:limit]:
        timestamp = session.punch_in.strftime("%Y-%m-%d %H:%M")
        entries.append(f"{timestamp} | {task_name}")

    return entries


def update_latest_active_task(
    project_root: Path,
    *,
    status: str,
    set_checkout: bool = False,
) -> dict[str, str] | None:
    """Legacy function for CLI compatibility.

    Updates the latest active task status.
    """
    worklog = load_worklog(project_root)
    active_tasks = worklog.active_tasks()

    if not active_tasks:
        return None

    task = active_tasks[-1]  # Get latest active

    if status == "completed":
        punch_out(project_root, task.id)
        complete_task(project_root, task.id)

    return {"task_id": task.id, "status": status}


def update_task_status_by_index(
    project_root: Path,
    *,
    index: int,
    status: str,
    set_checkout: bool = False,
) -> dict[str, str] | None:
    """Legacy function for CLI compatibility.

    Updates a task's status by index.
    """
    worklog = load_worklog(project_root)

    if index < 0 or index >= len(worklog.tasks):
        return None

    task = worklog.tasks[index]

    if status == "completed":
        complete_task(project_root, task.id)

    return {"task_id": task.id, "status": status}
