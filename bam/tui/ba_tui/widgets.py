from __future__ import annotations

from textual_datepicker import DateSelect as _DateSelect
from textual_datepicker import DatePicker


class DateSelect(_DateSelect):
    def _show_date_picker(self) -> None:
        super()._show_date_picker()
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

    def watch_dialog_display(self) -> None:
        """Watch for dialog display changes to collapse when closed."""
        if self.dialog and not self.dialog.display:
            self._toggle_mount_expanded(False)

    def on_descendant_blur(self, event) -> None:
        """Collapse mount when focus leaves the date picker area."""
        # Check if dialog is now hidden
        self.call_later(self._check_dialog_closed)

    def _check_dialog_closed(self) -> None:
        """Check if dialog closed and collapse mount."""
        if self.dialog and not self.dialog.display:
            self._toggle_mount_expanded(False)

    def _toggle_mount_expanded(self, expand: bool) -> None:
        """Toggle the expanded class on the picker mount point."""
        try:
            mount_selector = self.picker_mount
            if mount_selector and self.app:
                mount = self.app.query_one(mount_selector)
                if expand:
                    mount.add_class("expanded")
                else:
                    mount.remove_class("expanded")
        except Exception:
            pass
