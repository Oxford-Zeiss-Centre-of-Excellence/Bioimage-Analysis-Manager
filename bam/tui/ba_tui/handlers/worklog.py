"""Worklog handlers for task-based time tracking."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from textual.widgets import Button, Static, Tree
from textual.widgets.tree import TreeNode

from ..models import (
    LogTaskStatus,
    RunStatus,
    Task,
    TaskCategory,
    TaskDifficulty,
    TaskSubCategory,
    WorkLog,
)
from ..screens.edit_session_modal import EditSessionModal
from ..screens.session_note_modal import SessionNoteModal
from ..screens.task_modal import TaskModal
from ..worklog import (
    add_session_note,
    complete_task,
    create_task,
    edit_session,
    incomplete_task,
    load_worklog,
    punch_in,
    punch_out,
    validate_sessions,
)


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


class WorklogMixin:
    """Mixin for worklog task management in TUI."""

    _project_root: Path
    _worklog: WorkLog
    _selected_task_id: str | None
    _selected_session_index: int | None
    _show_history: bool
    _last_working_task_id: str | None

    def _init_worklog(self) -> None:
        """Initialize worklog state."""
        self._worklog = WorkLog()
        self._selected_task_id = None
        self._selected_session_index = None
        self._show_history = False
        self._last_working_task_id = None

    def _load_worklog_data(self) -> None:
        """Load worklog from disk."""
        self._worklog = load_worklog(self._project_root)
        self._check_problematic_sessions()
        self._refresh_task_tree()
        self._update_dashboard()
        self._update_action_buttons()

    def _get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        for task in self._worklog.tasks:
            if task.id == task_id:
                return task
        return None

    def _check_problematic_sessions(self) -> None:
        """Check for problematic sessions and show toast warning."""
        count, problems = validate_sessions(self._project_root)
        if count > 0:
            message = f"{count} session{'s' if count > 1 else ''} need attention. Check highlighted entries in the log."
            self.notify(message, severity="warning", timeout=5)

    def _select_task_in_tree(self, task_id: str) -> None:
        """Select a task in the tree by its ID."""
        try:
            tree = self.query_one("#task_tree", Tree)
        except Exception:
            return

        # Find the node with matching task ID
        for node in tree.root.children:
            if (
                node.data
                and node.data.get("type") == "task"
                and node.data.get("id") == task_id
            ):
                tree.select_node(node)
                tree.move_cursor(node)
                break

    def _refresh_task_tree(self) -> None:
        """Refresh the task tree display."""
        try:
            tree = self.query_one("#task_tree", Tree)
        except Exception:
            return

        tree.clear()
        tree.root.expand()

        # Show all tasks
        tasks_to_show = self._worklog.tasks

        # Add tasks to tree
        for task in tasks_to_show:
            task_label = self._format_task_label(task)
            task_node = tree.root.add(task_label, data={"type": "task", "id": task.id})

            # Add sessions as children
            for idx, session in enumerate(task.sessions):
                session_label = self._format_session_label(session, idx)
                session_node = task_node.add(
                    session_label,
                    data={"type": "session", "task_id": task.id, "session_index": idx},
                )
                # Note: TreeNode doesn't support CSS classes, colors are in the label text via format_session_label

    def _format_task_label(self, task: Task) -> str:
        """Format task as tree label."""
        total_duration = format_duration(task.total_duration_seconds())

        # Status indicator with blinking for active tasks
        status_icon = ""
        if task.is_active():
            # Blink between green and black for active sessions
            import time
            blink_on = int(time.time()) % 2 == 0
            status_icon = "🟢" if blink_on else "⚫"
        elif task.status == LogTaskStatus.completed:
            status_icon = "✅"
        elif task.status == LogTaskStatus.archived:
            status_icon = "📦"

        tag = self._task_category_tag(task)

        # Last working indicator
        last_working_indicator = ""
        if task.id == self._last_working_task_id:
            last_working_indicator = " (last working)"

        label = f"[{tag}] {task.name} {total_duration} {status_icon}{last_working_indicator}"

        return label

    def _task_category_tag(self, task: Task) -> str:
        """Short tag for task category (used in tree/cards)."""
        tag_map = {
            TaskCategory.development: "🛠  Dev",
            TaskCategory.data_copying: "📁 Data",
            TaskCategory.execution: "⚙  Exec",
            TaskCategory.documentation: "📝 Docs",
            TaskCategory.meeting: "📅 Meet",
            TaskCategory.admin: "🗂  Admin",
            TaskCategory.learning: "📚 Learn",
            TaskCategory.support: "🧰 Support",
            TaskCategory.other: "•  Other",
        }
        base = tag_map.get(task.category, task.category.value)
        if task.sub_category:
            return f"{base}: {task.sub_category.value}"
        return base

    def _format_session_label(self, session, index: int) -> str:
        """Format session as tree label."""
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

    def _get_session_color_class(self, session) -> str:
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

    def _update_dashboard(self) -> None:
        """Update dashboard display with all active sessions."""
        from textual.containers import Horizontal, Vertical
        from textual.widgets import Button, Static

        try:
            container = self.query_one("#dashboard_sessions_container", Vertical)
        except Exception:
            return

        # Clear existing content - use await remove so it completes before mounting new widgets
        if container._nodes:
            for child in list(container._nodes):
                child.remove()

        # Find all active tasks
        active_tasks = self._worklog.active_tasks()

        if not active_tasks:
            # No active sessions
            no_sessions = Static("No active sessions", classes="muted-text")
            container.mount(no_sessions)
            return

        # Clear existing content
        container.remove_children()

        # Find all active tasks
        active_tasks = self._worklog.active_tasks()

        if not active_tasks:
            # No active sessions
            no_sessions = Static(
                "No active sessions", id="no_sessions_message", classes="muted-text"
            )
            container.mount(no_sessions)
            return

        # Add blinking indicator calculation
        import time

        blink_on = int(time.time()) % 2 == 0
        indicator = "🟢" if blink_on else "⚫"

        # Create a session widget for each active task
        for task in active_tasks:
            active_session = task.active_session()
            if not active_session:
                continue

            # Calculate elapsed time
            elapsed = active_session.duration_seconds()
            total = task.total_duration_seconds()

            tag = self._task_category_tag(task)

            # Create session box container and mount it first
            session_box = Vertical(classes="session-box")
            container.mount(session_box)

            # Session header with task info
            header = Static(
                f"{indicator} [{tag}] {task.name}", classes="session-header"
            )

            # Session details
            details = Static(
                f"⏱ Session: {format_duration(elapsed)}  │  📊 Task total: {format_duration(total)}",
                classes="session-details",
            )

            # Build session box with all components
            session_box.mount(header)
            session_box.mount(details)

            # Create buttons container and mount it
            buttons_container = Horizontal(classes="session-buttons")
            session_box.mount(buttons_container)

            # Now mount buttons to the attached container
            check_out_btn = Button(
                "Check Out (O)",
                id=f"session_check_out_{task.id}",
                variant="primary",
                classes="session-btn",
            )
            add_note_btn = Button(
                "Add Note (N)",
                id=f"session_add_note_{task.id}",
                variant="default",
                classes="session-btn",
            )

            buttons_container.mount(check_out_btn)
            buttons_container.mount(add_note_btn)

    def _on_tree_node_selected(self, node: TreeNode) -> None:
        """Handle tree node selection."""
        # Safety check - make sure we have a proper TreeNode
        if not hasattr(node, "data"):
            return

        if not node.data:
            self._selected_task_id = None
            self._selected_session_index = None
            return

        node_data = node.data
        if not isinstance(node_data, dict):
            return

        if node_data.get("type") == "task":
            self._selected_task_id = node_data.get("id")
            self._selected_session_index = None
        elif node_data.get("type") == "session":
            self._selected_task_id = node_data.get("task_id")
            self._selected_session_index = node_data.get("session_index")

        self._update_action_buttons()

    def _update_action_buttons(self) -> None:
        """Enable/disable action buttons based on selection."""
        try:
            check_in_btn = self.query_one("#check_in_btn", Button)
            edit_btn = self.query_one("#edit_btn", Button)
            complete_btn = self.query_one("#complete_btn", Button)
            delete_btn = self.query_one("#delete_btn", Button)
        except Exception:
            return

        if self._selected_task_id:
            task = self._get_task(self._selected_task_id)
            has_active_session = bool(task and task.active_session())
            is_completed = bool(task and task.status == LogTaskStatus.completed)

            # Toggle check in/out button label and state
            if has_active_session:
                check_in_btn.label = "Check Out (I)"
                check_in_btn.disabled = False
            else:
                check_in_btn.label = "Check In (I)"
                # Disable if task is completed
                check_in_btn.disabled = is_completed

            edit_btn.disabled = False
            delete_btn.disabled = False
            if task and task.status == LogTaskStatus.completed:
                complete_btn.label = "Incomplete (C)"
            else:
                complete_btn.label = "Complete (C)"
            complete_btn.disabled = False
        else:
            check_in_btn.disabled = True
            edit_btn.disabled = True
            complete_btn.disabled = True
            delete_btn.disabled = True

    async def _handle_new_task(self) -> None:
        """Handle creating a new task."""
        # Pre-populate with data from selected task if available
        initial_data: dict[str, object] | None = None
        if self._selected_task_id:
            task = self._get_task(self._selected_task_id)
            if task and task.data_path:
                initial_data = {
                    "data_path": task.data_path,
                }

        result = await self.push_screen_wait(
            TaskModal(
                compute_locations=["Local", "HPC-GPU", "HPC-CPU", "Workstation"],
                initial_data=initial_data,
                project_root=self._project_root,
            )
        )

        if not result or isinstance(result, dict) and result.get("__delete__"):
            return

        # Create task
        new_task = create_task(
            self._project_root,
            name=result["name"],
            category=TaskCategory(result["category"]),
            sub_category=TaskSubCategory(result["sub_category"])
            if result.get("sub_category")
            else None,
            difficulty=TaskDifficulty(result["difficulty"])
            if result.get("difficulty")
            else None,
            data_path=result.get("data_path"),
            compute=result.get("compute"),
            run_status=RunStatus(result["run_status"])
            if result.get("run_status")
            else None,
        )

        # Select the newly created task
        self._selected_task_id = new_task.id
        self._load_worklog_data()
        self._select_task_in_tree(new_task.id)

    async def _handle_check_in(self) -> None:
        """Handle toggling check in/out for selected task."""
        if not self._selected_task_id:
            return

        task = self._get_task(self._selected_task_id)
        if not task:
            return

        # If task has active session, check out instead
        if task.active_session():
            await self._handle_check_out()
            return

        # Check if task is completed
        if task.status == LogTaskStatus.completed:
            # Task is completed, warn user and mark incomplete
            self.notify(
                "⚠️ Task was completed. Marking as incomplete to check in.",
                severity="warning",
                timeout=5
            )
            # Mark task as incomplete
            incomplete_task(self._project_root, self._selected_task_id)
            # Reload to update the status
            self._load_worklog_data()

        punch_in(self._project_root, self._selected_task_id)
        self._load_worklog_data()

    async def _handle_check_out(self) -> None:
        """Handle checking out of active task."""
        task = None
        if self._selected_task_id:
            task = self._get_task(self._selected_task_id)
        if not task:
            active_tasks = self._worklog.active_tasks()
            if len(active_tasks) == 1:
                task = active_tasks[0]
            else:
                return

        active_session = task.active_session()
        if not active_session:
            return

        if active_session:
            # Check if session > 8h
            duration_hours = active_session.duration_seconds() / 3600
            if duration_hours > 8:
                # Show warning (simplified - in real app, use a confirmation dialog)
                self.notify(
                    f"You've been checked in for {int(duration_hours)}h. Checking out...",
                    severity="warning",
                )

        # Track as last working task
        self._last_working_task_id = task.id

        punch_out(self._project_root, task.id)
        self._load_worklog_data()

    async def _handle_session_check_out(self, task_id: str) -> None:
        """Handle checking out of specific task session."""
        task = self._get_task(task_id)
        if not task:
            return

        active_session = task.active_session()
        if active_session:
            # Check if session > 8h
            duration_hours = active_session.duration_seconds() / 3600
            if duration_hours > 8:
                self.notify(
                    f"You've been checked in for {int(duration_hours)}h. Checking out...",
                    severity="warning",
                )

        # Track as last working task
        self._last_working_task_id = task_id

        punch_out(self._project_root, task_id)
        self._load_worklog_data()

    async def _handle_session_add_note(self, task_id: str) -> None:
        """Handle adding note to specific task's active session."""
        task = self._get_task(task_id)
        if not task:
            return

        active_session = task.active_session()
        if not active_session:
            return

        result = await self.push_screen_wait(SessionNoteModal())
        if result and result.get("note"):
            # Find session index
            session_idx = len(task.sessions) - 1
            for idx, sess in enumerate(task.sessions):
                if sess == active_session:
                    session_idx = idx
                    break

            add_session_note(
                self._project_root,
                task_id,
                session_idx,
                result["note"],
            )
            self._load_worklog_data()

    async def _handle_add_note(self) -> None:
        """Handle adding note to active session."""
        task = None
        if self._selected_task_id:
            task = self._get_task(self._selected_task_id)
        if not task:
            active_tasks = self._worklog.active_tasks()
            if len(active_tasks) == 1:
                task = active_tasks[0]
            else:
                return

        active_session = task.active_session()
        if not active_session:
            return

        result = await self.push_screen_wait(SessionNoteModal())
        if result and result.get("note"):
            # Find session index
            session_idx = len(task.sessions) - 1
            for idx, sess in enumerate(task.sessions):
                if sess == active_session:
                    session_idx = idx
                    break

            from ..worklog import add_session_note

            add_session_note(self._project_root, task.id, session_idx, result["note"])
            self._load_worklog_data()

    async def _handle_edit(self) -> None:
        """Handle editing selected task or session."""
        if not self._selected_task_id:
            return

        task = self._worklog.get_task_by_id(self._selected_task_id)
        if not task:
            return

        if self._selected_session_index is not None:
            # Edit session
            session = task.sessions[self._selected_session_index]
            result = await self.push_screen_wait(
                EditSessionModal(
                    task_name=task.name,
                    initial_punch_in=session.punch_in,
                    initial_punch_out=session.punch_out,
                    initial_note=session.note,
                )
            )

            if result and not result.get("__delete__"):
                edit_session(
                    self._project_root,
                    task.id,
                    self._selected_session_index,
                    result["punch_in"],
                    result["punch_out"],
                    result["note"],
                )
                self._load_worklog_data()
                # Keep the session selected after edit
                self._select_task_in_tree(task.id)
        else:
            # Edit task
            initial_data = {
                "name": task.name,
                "category": task.category.value,
                "sub_category": task.sub_category.value if task.sub_category else None,
                "difficulty": task.difficulty.value if task.difficulty else None,
                "data_path": task.data_path,
                "compute": task.compute,
                "run_status": task.run_status.value if task.run_status else None,
            }

            result = await self.push_screen_wait(
                TaskModal(
                    initial_data=initial_data,
                    allow_remove=True,
                    project_root=self._project_root,
                )
            )

            if result:
                if result.get("__delete__"):
                    from ..worklog import delete_task

                    delete_task(self._project_root, task.id)
                else:
                    from ..worklog import edit_task

                    edit_task(
                        self._project_root,
                        task.id,
                        name=result.get("name"),
                        category=TaskCategory(result["category"])
                        if result.get("category")
                        else None,
                        sub_category=TaskSubCategory(result["sub_category"])
                        if result.get("sub_category")
                        else None,
                        difficulty=TaskDifficulty(result["difficulty"])
                        if result.get("difficulty")
                        else None,
                        data_path=result.get("data_path"),
                        compute=result.get("compute"),
                        run_status=RunStatus(result["run_status"])
                        if result.get("run_status")
                        else None,
                    )

                self._load_worklog_data()
                # Keep the task selected after edit (unless deleted)
                if not result.get("__delete__"):
                    self._select_task_in_tree(task.id)

    async def _handle_complete(self) -> None:
        """Handle completing/uncompleting selected task."""
        if not self._selected_task_id:
            return

        task = self._get_task(self._selected_task_id)
        if task:
            if task.status == LogTaskStatus.completed:
                # Uncomplete the task
                incomplete_task(self._project_root, self._selected_task_id)
            else:
                # Complete the task
                complete_task(self._project_root, self._selected_task_id)

        self._load_worklog_data()

    async def _handle_delete(self) -> None:
        """Handle deleting selected task or session."""
        if not self._selected_task_id:
            return

        if self._selected_session_index is not None:
            # Delete session
            from ..worklog import delete_session

            task = self._get_task(self._selected_task_id)
            if task:
                delete_session(
                    self._project_root,
                    self._selected_task_id,
                    self._selected_session_index,
                )
        else:
            # Delete task
            from ..worklog import delete_task

            delete_task(self._project_root, self._selected_task_id)

        self._load_worklog_data()

    def _tick_worklog(self) -> None:
        """Periodic update for dashboard and tree (called every second)."""
        # Update dashboard to refresh elapsed time for active session
        self._update_dashboard()

        # Refresh tree to update blinking indicators for active tasks
        if self._worklog.active_tasks():
            # Save current selection
            current_selection = self._selected_task_id
            self._refresh_task_tree()
            # Restore selection
            if current_selection:
                self._select_task_in_tree(current_selection)
