from __future__ import annotations

from textual.css.query import NoMatches

from textual_datepicker import DateSelect as _DateSelect
from textual_datepicker import DatePicker
from textual_datepicker._date_select import DatePickerDialog


class DateSelect(_DateSelect):
    _dialog_was_visible = False

    def on_mount(self) -> None:
        """Override to query within screen context instead of app."""
        if self.dialog is None:
            self.dialog = DatePickerDialog()
            self.dialog.target = self
            # Use screen.query_one instead of app.query_one for modal support
            self.screen.query_one(self.picker_mount).mount(self.dialog)
        # Start polling for dialog state changes
        self.set_interval(0.2, self._poll_dialog_state)

    def _poll_dialog_state(self) -> None:
        """Periodically check if dialog was closed and collapse mount."""
        if not self.dialog:
            return

        is_visible = self.dialog.display

        # Only collapse on transition from visible to hidden
        if self._dialog_was_visible and not is_visible:
            self._toggle_mount_expanded(False)

        self._dialog_was_visible = is_visible

    def _show_date_picker(self) -> None:
        """Override to use screen.query_one instead of app.query_one."""
        mnt_widget = self.screen.query_one(self.picker_mount)
        self.dialog.display = True

        # calculate offset of DateSelect and apply it to DatePickerDialog
        self.dialog.offset = self.region.offset - mnt_widget.content_region.offset

        # move down 3 (height of input)
        self.dialog.offset = (self.dialog.offset.x, self.dialog.offset.y + 3)

        if self.date is not None:
            self.dialog.date_picker.date = self.date
            for day in self.dialog.query("DayLabel.--day"):
                if day.day == self.date.day:
                    day.focus()
                    break
        else:
            try:
                self.dialog.query_one("DayLabel.--today").focus()
            except NoMatches:
                self.dialog.query("DayLabel.--day").first().focus()

        # Additional fixes for date picker display
        try:
            date_picker = self.dialog.date_picker
            date_picker._update_month_label()
            date_picker._update_day_widgets()
            date_picker.refresh(layout=True)
        except Exception:
            pass
        # Expand the mount point
        self._toggle_mount_expanded(True)

    def on_date_picker_selected(self, event: DatePicker.Selected) -> None:
        """Handle date selection - collapse mount after date is picked."""
        super().on_date_picker_selected(event)
        # Collapse after selection
        self._toggle_mount_expanded(False)

    def on_blur(self) -> None:
        """Collapse mount when DateSelect itself loses focus."""
        self.set_timer(0.1, self._check_and_collapse)

    def on_descendant_blur(self, event) -> None:
        """Collapse mount when focus leaves the date picker area."""
        self.set_timer(0.1, self._check_and_collapse)

    def _check_and_collapse(self) -> None:
        """Check if dialog should be collapsed after focus change."""
        if not self.dialog:
            return

        # If dialog is already hidden, just collapse the mount
        if not self.dialog.display:
            self._toggle_mount_expanded(False)
            return

        # Check if focus is still within the date picker area
        try:
            focused = self.screen.focused
        except Exception:
            focused = None

        # If focus is on the DateSelect itself, keep open
        if focused is self:
            return

        # If focus is on the dialog or its children, keep open
        if focused is self.dialog:
            return
        if self.dialog.date_picker and focused is self.dialog.date_picker:
            return

        try:
            if focused and focused in self.dialog.query("*"):
                return
        except Exception:
            pass

        # Focus is elsewhere - close the dialog and collapse
        self.dialog.display = False
        self._toggle_mount_expanded(False)

    def _toggle_mount_expanded(self, expand: bool) -> None:
        """Toggle the expanded class on the picker mount point."""
        try:
            mount_selector = self.picker_mount
            if mount_selector and self.screen:
                mount = self.screen.query_one(mount_selector)
                if expand:
                    mount.add_class("expanded")
                else:
                    mount.remove_class("expanded")
        except Exception:
            pass
