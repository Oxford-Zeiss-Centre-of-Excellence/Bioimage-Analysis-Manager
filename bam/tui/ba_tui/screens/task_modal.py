"""Task creation/editing modal for worklog."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Static

from ..config import (
    category_has_subcategories,
    load_task_categories,
    load_task_subcategories,
)
from ..models import (
    RunStatus,
    TaskDifficulty,
)
from ..styles import TASK_MODAL_CSS
from .base import FormModal


class TaskModal(FormModal):
    """Modal to create or edit a task."""

    CSS = TASK_MODAL_CSS

    def __init__(
        self,
        initial_data: dict[str, object] | None = None,
        allow_remove: bool = False,
        compute_locations: list[str] | None = None,
        project_root: Path | None = None,
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._initial_category = (
            str(self.initial_data.get("category"))
            if self.initial_data.get("category")
            else None
        )
        self._initial_sub_category = (
            str(self.initial_data.get("sub_category"))
            if self.initial_data.get("sub_category")
            else None
        )
        self._allow_remove = allow_remove
        self.compute_locations = compute_locations or ["Local"]
        self.project_root = project_root

    def compose(self) -> ComposeResult:
        title = "Edit Task" if self.initial_data else "New Task"

        # Category options from config
        category_options = load_task_categories(self.project_root)
        initial_category = self.initial_data.get("category") or ""

        # Only set category value if it exists in the options
        category_value = Select.BLANK
        if initial_category:
            # Check if the value exists in options
            for label, value in category_options:
                if (
                    value == initial_category
                    or value.lower() == str(initial_category).lower()
                ):
                    category_value = value
                    break

        # Sub-category options (dynamic based on category)
        # Use category_value (which has been validated) instead of initial_category
        category_for_subcat = (
            str(category_value) if category_value != Select.BLANK else None
        )
        sub_category_options = load_task_subcategories(
            category_for_subcat, self.project_root
        )
        initial_sub_category = self.initial_data.get("sub_category") or ""

        # Only set subcategory value if it exists in the options
        sub_category_value = Select.BLANK
        if initial_sub_category and sub_category_options:
            # Check if the value exists in options (case-insensitive match)
            for label, value in sub_category_options:
                if (
                    value == initial_sub_category
                    or value.lower() == str(initial_sub_category).lower()
                ):
                    sub_category_value = value
                    break

        show_sub_category = len(sub_category_options) > 0
        show_other_category = (
            str(category_value).lower() == "other"
            if category_value != Select.BLANK
            else False
        )
        show_other_sub_category = (
            str(initial_sub_category).lower() == "other"
            if initial_sub_category
            else False
        )

        # Difficulty options
        difficulty_options = [(diff.value, diff.value) for diff in TaskDifficulty]
        initial_difficulty = self.initial_data.get("difficulty") or ""
        difficulty_value = Select.BLANK
        if initial_difficulty:
            for label, value in difficulty_options:
                if (
                    value == initial_difficulty
                    or value.lower() == str(initial_difficulty).lower()
                ):
                    difficulty_value = value
                    break

        # Execution fields
        show_execution = category_value == "Execution"
        compute_options = [(loc, loc) for loc in self.compute_locations]
        initial_compute = self.initial_data.get("compute") or ""
        compute_value = Select.BLANK
        if initial_compute:
            for label, value in compute_options:
                if value == initial_compute:
                    compute_value = value
                    break

        run_status_options = [(status.value, status.value) for status in RunStatus]
        initial_run_status = self.initial_data.get("run_status") or ""
        run_status_value = Select.BLANK
        if initial_run_status:
            for label, value in run_status_options:
                if (
                    value == initial_run_status
                    or value.lower() == str(initial_run_status).lower()
                ):
                    run_status_value = value
                    break

        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                # Name
                with Horizontal(classes="form-row"):
                    yield Label("Task Name*:")
                    yield Input(
                        str(self.initial_data.get("name") or ""),
                        id="task_name",
                        placeholder="e.g., Train cell segmentation model",
                    )

                # Category
                with Horizontal(classes="form-row"):
                    yield Label("Category*:")
                    yield Select(
                        category_options,
                        value=category_value,
                        id="task_category",
                        allow_blank=False,
                    )

                # Other Category (conditional on "Other" category)
                with Horizontal(classes="form-row", id="other_category_row"):
                    yield Label("Other Category:")
                    yield Input(
                        str(self.initial_data.get("other_category") or ""),
                        id="task_other_category",
                        placeholder="Specify other category type",
                    )
                if not show_other_category:
                    self.set_class(
                        not show_other_category, "other_category_row", "-hidden"
                    )

                # Sub-category (conditional on Development)
                with Horizontal(classes="form-row", id="sub_category_row"):
                    yield Label("Sub-category:")
                    yield Select(
                        sub_category_options,
                        value=sub_category_value,
                        id="task_sub_category",
                        allow_blank=True,
                    )
                if not show_sub_category:
                    self.set_class(not show_sub_category, "sub_category_row", "-hidden")

                # Other Sub-category (conditional on "Other" sub-category)
                with Horizontal(classes="form-row", id="other_sub_category_row"):
                    yield Label("Other Sub-category:")
                    yield Input(
                        str(self.initial_data.get("other_sub_category") or ""),
                        id="task_other_sub_category",
                        placeholder="Specify other sub-category type",
                    )
                if not show_other_sub_category:
                    self.set_class(
                        not show_other_sub_category, "other_sub_category_row", "-hidden"
                    )

                # Difficulty
                with Horizontal(classes="form-row"):
                    yield Label("Difficulty:")
                    yield Select(
                        difficulty_options,
                        value=difficulty_value,
                        id="task_difficulty",
                        allow_blank=True,
                    )

                # Execution-specific fields
                with Horizontal(classes="form-row", id="data_path_row"):
                    yield Label("Data Path:")
                    yield Input(
                        str(self.initial_data.get("data_path") or ""),
                        id="task_data_path",
                        placeholder="/data/experiment1",
                    )
                if not show_execution:
                    self.set_class(not show_execution, "data_path_row", "-hidden")

                with Horizontal(classes="form-row", id="compute_row"):
                    yield Label("Compute:")
                    yield Select(
                        compute_options,
                        value=compute_value,
                        id="task_compute",
                        allow_blank=True,
                    )
                if not show_execution:
                    self.set_class(not show_execution, "compute_row", "-hidden")

                with Horizontal(classes="form-row", id="run_status_row"):
                    yield Label("Run Status:")
                    yield Select(
                        run_status_options,
                        value=run_status_value,
                        id="task_run_status",
                        allow_blank=True,
                    )
                if not show_execution:
                    self.set_class(not show_execution, "run_status_row", "-hidden")

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("Save (Ctrl+A)", id="save", variant="success")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", id="remove", variant="error")
                yield Button("Cancel (Esc)", id="cancel")

    def on_mount(self) -> None:
        """Initialize subcategory options and value after mount."""
        try:
            category_select = self.query_one("#task_category", Select)
            sub_category_select = self.query_one("#task_sub_category", Select)
            sub_category_row = self.query_one("#sub_category_row")
            other_sub_category_row = self.query_one("#other_sub_category_row")

            category_value = (
                str(category_select.value)
                if category_select.value != Select.BLANK
                else None
            )
            sub_category_options = load_task_subcategories(
                category_value, self.project_root
            )
            has_subcats = len(sub_category_options) > 0
            sub_category_select.set_options(sub_category_options)

            if has_subcats:
                sub_category_row.remove_class("-hidden")
            else:
                sub_category_row.add_class("-hidden")
                other_sub_category_row.add_class("-hidden")
                sub_category_select.value = Select.BLANK

            # Restore initial subcategory value from initial_data, not just cached value
            if has_subcats:
                initial_sub_category = self.initial_data.get("sub_category")
                if initial_sub_category:
                    # Find matching value in options (case-insensitive)
                    for label, value in sub_category_options:
                        if (
                            value == initial_sub_category
                            or value.lower() == str(initial_sub_category).lower()
                        ):
                            sub_category_select.value = value
                            break
        except Exception:
            pass

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle category selection to show/hide conditional fields."""
        if event.select.id == "task_category":
            category = str(event.value)

            # Load subcategories for the selected category
            sub_category_options = load_task_subcategories(category, self.project_root)
            has_subcats = len(sub_category_options) > 0

            # Update subcategory select options
            sub_category_select = self.query_one("#task_sub_category", Select)
            sub_category_select.set_options(sub_category_options)

            # Show/hide sub-category row based on whether category has subcategories
            sub_category_row = self.query_one("#sub_category_row")
            if has_subcats:
                sub_category_row.remove_class("-hidden")
                if (
                    self._initial_sub_category
                    and self._initial_category
                    and category.lower() == self._initial_category.lower()
                    and sub_category_select.value == Select.BLANK
                ):
                    for label, value in sub_category_options:
                        if (
                            value == self._initial_sub_category
                            or value.lower() == self._initial_sub_category.lower()
                        ):
                            sub_category_select.value = value
                            # Ensure "Other Sub-category" field visibility matches restored value
                            other_sub_category_row = self.query_one(
                                "#other_sub_category_row"
                            )
                            if value.lower() == "other":
                                other_sub_category_row.remove_class("-hidden")
                            else:
                                other_sub_category_row.add_class("-hidden")
                            break
            else:
                sub_category_row.add_class("-hidden")
                other_sub_category_row = self.query_one("#other_sub_category_row")
                other_sub_category_row.add_class("-hidden")
                sub_category_select.value = Select.BLANK
                other_sub_category_input = self.query_one(
                    "#task_other_sub_category", Input
                )
                other_sub_category_input.value = ""

            # Show/hide "Other Category" field
            is_other = category.lower() == "other"
            other_category_row = self.query_one("#other_category_row")
            if is_other:
                other_category_row.remove_class("-hidden")
            else:
                other_category_row.add_class("-hidden")

            # Show/hide execution fields for Execution
            is_exec = category.lower() == "execution"
            for row_id in ["data_path_row", "compute_row", "run_status_row"]:
                row = self.query_one(f"#{row_id}")
                if is_exec:
                    row.remove_class("-hidden")
                else:
                    row.add_class("-hidden")

            # Ensure layout recalculates after toggling execution rows
            try:
                dialog_scroll = self.query_one("#dialog_scroll")
                dialog_scroll.refresh(layout=True)
            except Exception:
                pass
            self.refresh(layout=True)

        elif event.select.id == "task_sub_category":
            sub_category = str(event.value)

            # Show/hide "Other Sub-category" field
            is_other_sub = sub_category.lower() == "other"
            other_sub_category_row = self.query_one("#other_sub_category_row")
            if is_other_sub:
                other_sub_category_row.remove_class("-hidden")
            else:
                other_sub_category_row.add_class("-hidden")

    def _submit(self) -> None:
        """Collect form values and dismiss."""
        name_input = self.query_one("#task_name", Input)
        name = name_input.value.strip()

        if not name:
            name_input.add_class("error")
            return

        category_select = self.query_one("#task_category", Select)
        category = (
            str(category_select.value)
            if category_select.value != Select.BLANK
            else None
        )

        if not category:
            return

        sub_category_select = self.query_one("#task_sub_category", Select)
        sub_category = (
            str(sub_category_select.value)
            if sub_category_select.value != Select.BLANK
            else None
        )

        # Collect "Other" field values (optional)
        other_category_input = self.query_one("#task_other_category", Input)
        other_category = other_category_input.value.strip() or None

        other_sub_category_input = self.query_one("#task_other_sub_category", Input)
        other_sub_category = other_sub_category_input.value.strip() or None

        # Only keep subcategory if the category has subcategories defined
        if not category_has_subcategories(category, self.project_root):
            sub_category = None
            other_sub_category = None

        difficulty_select = self.query_one("#task_difficulty", Select)
        difficulty = (
            str(difficulty_select.value)
            if difficulty_select.value != Select.BLANK
            else None
        )

        data_path_input = self.query_one("#task_data_path", Input)
        data_path = data_path_input.value.strip() or None

        compute_select = self.query_one("#task_compute", Select)
        compute = (
            str(compute_select.value) if compute_select.value != Select.BLANK else None
        )

        run_status_select = self.query_one("#task_run_status", Select)
        run_status = (
            str(run_status_select.value)
            if run_status_select.value != Select.BLANK
            else None
        )

        result = {
            "name": name,
            "category": category,
            "sub_category": sub_category,
            "other_category": other_category,
            "other_sub_category": other_sub_category,
            "difficulty": difficulty,
            "data_path": data_path,
            "compute": compute,
            "run_status": run_status,
        }

        self.dismiss(result)
