"""Log tab: Task-based time tracking with punch-in/punch-out."""

from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, TabPane, Tree
from textual.widgets.tree import TreeNode

from ..models import LogTaskStatus, Task, WorkLog


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def format_session_line(session, index: int) -> str:
    """Format a session as a tree line."""
    punch_in_str = session.punch_in.strftime("%Y-%m-%d %H:%M")
    punch_out_str = (
        session.punch_out.strftime("%H:%M") if session.punch_out else "?????"
    )

    duration_str = ""
    if session.punch_out:
        duration = session.duration_seconds()
        duration_str = f" ({format_duration(duration)})"

    note_str = f' "{session.note}"' if session.note else ""

    # Check if problematic
    is_prob, reason = session.is_problematic()
    warning = ""
    if is_prob:
        if reason == "invalid_times":
            warning = " ⚠️ INVALID"
        elif reason == "no_punch_out_24h":
            warning = " ⚠️ >24h ACTIVE"
        elif reason == "duration_24h":
            warning = " ⚠️ >24h"

    return f"{punch_in_str}-{punch_out_str}{duration_str}{note_str}{warning}"


def get_session_color_class(session) -> str:
    """Get color class for session based on status."""
    is_prob, reason = session.is_problematic()

    if is_prob:
        return "session-problem"  # Red

    if session.punch_out is None:
        return "session-active"  # Blue

    duration_hours = session.duration_seconds() / 3600
    if duration_hours >= 8:
        return "session-long"  # Yellow/Orange

    return "session-normal"  # Green


def compose_log_tab(app: object) -> ComposeResult:
    """Compose the Log tab for task-based time tracking."""
    with TabPane("Log (F6)", id="log"):
        with VerticalScroll():
            yield Static("Tasks", classes="section-header")

            # Task tree and active sessions side by side (like figure tree)
            with Horizontal(id="log_tree_container"):
                yield Tree("Active Tasks", id="task_tree")
                with VerticalScroll(id="log_dashboard"):
                    yield Static("Active Sessions", classes="section-header")
                    # Sessions container - dynamically populated
                    with Vertical(id="dashboard_sessions_container"):
                        yield Static(
                            "No active sessions",
                            classes="muted-text",
                        )

            # Action buttons (centered, like publication actions)
            with Horizontal(id="log_actions"):
                yield Button("New Task (A)", id="new_task_btn", variant="success")
                yield Button(
                    "Check In (I)",
                    id="check_in_btn",
                    variant="primary",
                    disabled=True,
                )
                yield Button(
                    "Edit (Enter)", id="edit_btn", variant="default", disabled=True
                )
                yield Button(
                    "Complete (C)",
                    id="complete_btn",
                    variant="default",
                    disabled=True,
                )
                yield Button(
                    "Remove (D)", id="delete_btn", variant="error", disabled=True
                )

            # Hint text
            yield Static(
                "💡 Tasks are for personal progress tracking and time logging (not shared in reports)",
                classes="hint-text",
            )

            # Error/status messages
            yield Static("", id="log_status_message", classes="status-message")
