from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional

import yaml

from .models import LogEntry, TaskStatus, WorkLog
from .scaffold import ensure_log_types_template, ensure_worklog, templates_root


# =============================================================================
# Path helpers
# =============================================================================


def _worklog_csv_path(project_root: Path) -> Path:
    return project_root / "log" / "worklog.csv"


def _worklog_yaml_path(project_root: Path) -> Path:
    return project_root / "log" / "worklog.yaml"


# =============================================================================
# CSV Format (primary)
# =============================================================================

CSV_COLUMNS = ["checkin", "checkout", "task", "type", "status", "notes", "elapsed_seconds"]


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse ISO datetime string."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat() if dt else ""


def load_worklog_csv(project_root: Path) -> WorkLog:
    """Load worklog from CSV file."""
    csv_path = _worklog_csv_path(project_root)
    if not csv_path.exists():
        return WorkLog()

    entries = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                checkin = _parse_datetime(row.get("checkin", ""))
                if not checkin:
                    continue  # Skip invalid rows

                entry = LogEntry(
                    checkin=checkin,
                    checkout=_parse_datetime(row.get("checkout", "")),
                    task=row.get("task", ""),
                    type=row.get("type", "analysis"),
                    status=TaskStatus(row.get("status", "active")),
                    notes=row.get("notes") or None,
                    elapsed_seconds=int(row.get("elapsed_seconds", 0) or 0),
                )
                entries.append(entry)
    except Exception:
        return WorkLog()

    return WorkLog(entries=entries)


def save_worklog_csv(project_root: Path, worklog: WorkLog) -> None:
    """Save worklog to CSV file."""
    csv_path = _worklog_csv_path(project_root)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for entry in worklog.entries:
            writer.writerow({
                "checkin": _format_datetime(entry.checkin),
                "checkout": _format_datetime(entry.checkout),
                "task": entry.task,
                "type": entry.type,
                "status": entry.status.value,
                "notes": entry.notes or "",
                "elapsed_seconds": entry.elapsed_seconds,
            })


# =============================================================================
# YAML Format (legacy, for backward compatibility)
# =============================================================================


def load_worklog_yaml(project_root: Path) -> WorkLog:
    """Load worklog from YAML file (legacy format)."""
    yaml_path = _worklog_yaml_path(project_root)
    if not yaml_path.exists():
        return WorkLog()
    data = yaml.safe_load(yaml_path.read_text()) or {}
    try:
        return WorkLog.model_validate(data)
    except Exception:
        return WorkLog()


def save_worklog_yaml(project_root: Path, worklog: WorkLog) -> None:
    """Save worklog to YAML file (legacy format)."""
    yaml_path = _worklog_yaml_path(project_root)
    payload = worklog.model_dump(mode="json", exclude_none=True)
    yaml.safe_dump(payload, yaml_path.open("w"), sort_keys=False)


# =============================================================================
# Migration
# =============================================================================


def migrate_yaml_to_csv(project_root: Path) -> bool:
    """Migrate worklog from YAML to CSV format.

    Returns True if migration was performed, False if not needed.
    """
    yaml_path = _worklog_yaml_path(project_root)
    csv_path = _worklog_csv_path(project_root)

    if not yaml_path.exists():
        return False

    if csv_path.exists():
        return False  # Already migrated

    # Load from YAML
    worklog = load_worklog_yaml(project_root)

    # Save to CSV
    save_worklog_csv(project_root, worklog)

    # Backup YAML file
    backup_path = yaml_path.with_suffix(".yaml.bak")
    yaml_path.rename(backup_path)

    return True


def needs_migration(project_root: Path) -> bool:
    """Check if YAML to CSV migration is needed."""
    yaml_path = _worklog_yaml_path(project_root)
    csv_path = _worklog_csv_path(project_root)
    return yaml_path.exists() and not csv_path.exists()


# =============================================================================
# Unified API (uses CSV, falls back to YAML)
# =============================================================================


def load_worklog(project_root: Path) -> WorkLog:
    """Load worklog, preferring CSV format."""
    csv_path = _worklog_csv_path(project_root)
    yaml_path = _worklog_yaml_path(project_root)

    if csv_path.exists():
        return load_worklog_csv(project_root)
    elif yaml_path.exists():
        return load_worklog_yaml(project_root)
    else:
        return WorkLog()


def save_worklog(project_root: Path, worklog: WorkLog) -> None:
    """Save worklog in CSV format."""
    save_worklog_csv(project_root, worklog)


# =============================================================================
# Task type loading
# =============================================================================


def load_task_types(project_root: Path) -> list[dict[str, str]]:
    """Load task types from project or global template."""
    project_template = ensure_log_types_template(project_root)
    if project_template.exists():
        data = yaml.safe_load(project_template.read_text()) or {}
    else:
        fallback = templates_root() / "log-types.yaml"
        data = yaml.safe_load(fallback.read_text()) if fallback.exists() else {}
    task_types = data.get("task_types", [])
    return [entry for entry in task_types if isinstance(entry, dict)]


# =============================================================================
# Worklog operations
# =============================================================================


def append_worklog_entry(project_root: Path, message: str) -> dict[str, str]:
    """Append a completed entry to the worklog."""
    ensure_worklog(project_root)
    worklog = load_worklog(project_root)
    entry = LogEntry(
        checkin=datetime.now(),
        checkout=datetime.now(),
        task=message.strip(),
        status=TaskStatus.completed,
    )
    worklog.entries.append(entry)
    save_worklog(project_root, worklog)
    return entry.model_dump(mode="json", exclude_none=True)


def checkin_task(project_root: Path, task: str, task_type: str) -> dict[str, str]:
    """Check in a new task."""
    ensure_worklog(project_root)
    worklog = load_worklog(project_root)
    entry = LogEntry(
        checkin=datetime.now(),
        task=task.strip(),
        type=task_type.strip() or "analysis",
        status=TaskStatus.active,
    )
    worklog.entries.append(entry)
    save_worklog(project_root, worklog)
    return entry.model_dump(mode="json", exclude_none=True)


def _apply_status_transition(entry: LogEntry, status: TaskStatus, set_checkout: bool) -> LogEntry:
    """Apply a status transition to a log entry."""
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
    if set_checkout or status == TaskStatus.completed:
        if entry.status == TaskStatus.completed:
            if entry.checkout is None:
                entry.checkout = entry.checkin if previous_status == TaskStatus.paused else now
        else:
            entry.checkout = now
    return entry


def update_latest_active_task(
    project_root: Path,
    *,
    status: TaskStatus,
    set_checkout: bool = False,
) -> dict[str, str] | None:
    """Update the latest active task's status."""
    worklog = load_worklog(project_root)
    active_indices = [idx for idx, entry in enumerate(worklog.entries) if entry.status == TaskStatus.active]
    if not active_indices and status == TaskStatus.active:
        active_indices = [idx for idx, entry in enumerate(worklog.entries) if entry.status == TaskStatus.paused]
    if not active_indices:
        return None
    idx = active_indices[-1]
    entry = worklog.entries[idx]
    entry = _apply_status_transition(entry, status, set_checkout)
    worklog.entries[idx] = entry
    save_worklog(project_root, worklog)
    return entry.model_dump(mode="json", exclude_none=True)


def update_task_status_by_index(
    project_root: Path,
    *,
    index: int,
    status: TaskStatus,
    set_checkout: bool = False,
) -> dict[str, str] | None:
    """Update a task's status by its index."""
    worklog = load_worklog(project_root)
    if index < 0 or index >= len(worklog.entries):
        return None
    entry = worklog.entries[index]
    entry = _apply_status_transition(entry, status, set_checkout)
    worklog.entries[index] = entry
    save_worklog(project_root, worklog)
    return entry.model_dump(mode="json", exclude_none=True)


def read_recent_entries(project_root: Path, limit: int = 10) -> list[str]:
    """Read recent worklog entries as formatted strings."""
    worklog = load_worklog(project_root)
    entries = worklog.entries[-limit:]
    output = []
    for entry in entries:
        timestamp = entry.checkin.strftime("%Y-%m-%d %H:%M")
        output.append(f"{timestamp} | {entry.task}")
    return output
