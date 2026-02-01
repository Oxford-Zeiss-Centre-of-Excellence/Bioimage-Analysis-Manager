from __future__ import annotations

from typing import Optional

from textual.widgets import DataTable, TabbedContent

from ..screens import AcquisitionSessionModal, ChannelModal


class AcquisitionMixin:
    """Mixin for acquisition sessions and channel management."""

    _acquisition_rows: list[dict[str, object]]
    _channel_rows: list[dict[str, str]]
    _selected_acquisition_index: Optional[int]

    def _populate_channels_table(self) -> None:
        """Populate the DataTable with channel data."""
        try:
            table = self.query_one("#channels_table", DataTable)
            if not table.columns:
                table.add_column("Name", width=15)
                table.add_column("Fluorophore", width=15)
                table.add_column("Ex (nm)", width=10)
                table.add_column("Em (nm)", width=10)
            table.clear()
            for idx, row in enumerate(self._channel_rows):
                table.add_row(
                    row.get("name", ""),
                    row.get("fluorophore", ""),
                    row.get("excitation_nm", ""),
                    row.get("emission_nm", ""),
                    key=str(idx),
                )
        except Exception:
            pass

    def _populate_acquisition_table(self) -> None:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            table.clear(columns=True)
            table.add_columns(
                "Date",
                "Microscope",
                "Modality",
                "Objective",
                "Voxel",
                "Time (s)",
                "Notes",
            )
            for idx, row in enumerate(self._acquisition_rows):
                table.add_row(
                    self._format_date_cell(row.get("imaging_date")),
                    str(row.get("microscope", "")),
                    str(row.get("modality", "")),
                    str(row.get("objective", "")),
                    self._format_voxel(row),
                    str(row.get("time_interval_s", "")),
                    self._truncate_text(str(row.get("notes", ""))),
                    key=str(idx),
                )
        except Exception:
            pass

    def _load_session_channels(self, idx: int) -> None:
        try:
            if not (0 <= idx < len(self._acquisition_rows)):
                self._channel_rows = []
                self._populate_channels_table()
                return
            row = self._acquisition_rows[idx]
            self._selected_acquisition_index = idx
            channels = row.get("channels", []) if isinstance(row, dict) else []
            if (
                isinstance(channels, list)
                and channels
                and isinstance(channels[0], dict)
            ):
                self._channel_rows = [
                    {
                        "name": ch.get("name", ""),
                        "fluorophore": ch.get("fluorophore", ""),
                        "excitation_nm": str(ch.get("excitation_nm", "")),
                        "emission_nm": str(ch.get("emission_nm", "")),
                    }
                    for ch in channels
                ]
            else:
                self._channel_rows = []
            self._populate_channels_table()
        except Exception:
            pass

    def _store_channels_for_selected_session(self) -> None:
        try:
            idx = self._get_selected_acquisition_index()
            if idx is None:
                return
            self._store_channels_for_session(idx)
        except Exception:
            pass

    def _store_channels_for_session(self, idx: int) -> None:
        if not (0 <= idx < len(self._acquisition_rows)):
            return
        if isinstance(self._acquisition_rows[idx], dict):
            self._acquisition_rows[idx]["channels"] = [
                dict(row) for row in self._channel_rows
            ]

    def _get_selected_acquisition_index(self) -> Optional[int]:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            idx = table.cursor_row
            if idx is None and self._acquisition_rows:
                idx = 0
            if idx is None or not (0 <= idx < len(self._acquisition_rows)):
                return None
            return idx
        except Exception:
            return None

    def _format_voxel(self, row: dict[str, object]) -> str:
        x = str(row.get("voxel_x", "")).strip()
        y = str(row.get("voxel_y", "")).strip()
        z = str(row.get("voxel_z", "")).strip()
        if not any([x, y, z]):
            return ""
        return f"{x} x {y} x {z}"

    def action_add_acquisition(self) -> None:
        if self.query_one("#tabs", TabbedContent).active != "science":
            return
        if (
            self.query_one("#science_sections", TabbedContent).active
            != "science_acquisition"
        ):
            return
        self._store_channels_for_selected_session()
        # Always use None for new acquisition (no pre-filled data)
        self.push_screen(
            AcquisitionSessionModal(None),
            self._handle_new_acquisition,
        )

    def action_remove_acquisition(self) -> None:
        try:
            table = self.query_one("#acquisition_table", DataTable)
            if table.cursor_row is None:
                self.notify("Select a session to remove", severity="warning")
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._acquisition_rows):
                self._acquisition_rows.pop(idx)
            self._populate_acquisition_table()
            if self._acquisition_rows:
                idx = min(idx, len(self._acquisition_rows) - 1)
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            else:
                self._selected_acquisition_index = None
                self._channel_rows = []
                self._populate_channels_table()
        except Exception:
            pass

    def _handle_new_acquisition(self, data: dict[str, object] | None) -> None:
        if data:
            if "channels" not in data:
                data["channels"] = []
            self._acquisition_rows.append(data)
            self._populate_acquisition_table()

            try:
                table = self.query_one("#acquisition_table", DataTable)
                idx = len(self._acquisition_rows) - 1
                table.show_cursor = True
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            except Exception:
                pass

    def _handle_edit_acquisition(
        self, idx: int, data: dict[str, object] | None
    ) -> None:
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._acquisition_rows):
                self._acquisition_rows.pop(idx)
                self._populate_acquisition_table()
                try:
                    table = self.query_one("#acquisition_table", DataTable)
                    if self._acquisition_rows:
                        idx = min(idx, len(self._acquisition_rows) - 1)
                        table.move_cursor(row=idx, column=0)
                        self._load_session_channels(idx)
                    else:
                        self._selected_acquisition_index = None
                        self._channel_rows = []
                        self._populate_channels_table()
                except Exception:
                    pass
            return
        if data and 0 <= idx < len(self._acquisition_rows):
            existing = self._acquisition_rows[idx]
            if isinstance(existing, dict) and "channels" in existing:
                data.setdefault("channels", existing.get("channels", []))
            self._acquisition_rows[idx] = data
            self._populate_acquisition_table()
            try:
                table = self.query_one("#acquisition_table", DataTable)
                table.move_cursor(row=idx, column=0)
                self._load_session_channels(idx)
            except Exception:
                pass

    def action_add_channel_row(self) -> None:
        """Action to add a new channel row."""
        if self.query_one("#tabs", TabbedContent).active != "science":
            return
        if not self._acquisition_rows:
            self.notify("Add an imaging session first", severity="warning")
            return
        self.push_screen(ChannelModal(), self._handle_new_channel)

    def _handle_new_channel(self, data: dict[str, str] | None) -> None:
        """Add new channel after modal close."""
        if data:
            self._channel_rows.append(data)
            self._populate_channels_table()
            self._store_channels_for_selected_session()

    def action_remove_channel_row(self) -> None:
        """Action to remove the selected channel row."""
        try:
            table = self.query_one("#channels_table", DataTable)
            if table.cursor_row is None:
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._channel_rows):
                self._channel_rows.pop(idx)
            self._populate_channels_table()
            self._store_channels_for_selected_session()
            if self._channel_rows:
                idx = min(idx, len(self._channel_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def _handle_edit_channel(self, idx: int, data: dict[str, str] | None) -> None:
        """Update channel data after modal close."""
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._channel_rows):
                self._channel_rows.pop(idx)
                self._populate_channels_table()
                self._store_channels_for_selected_session()
            return
        if data and 0 <= idx < len(self._channel_rows):
            self._channel_rows[idx] = data
            self._populate_channels_table()
            self._store_channels_for_selected_session()

    def _collect_channels(self) -> list[dict[str, object]]:
        """Collect channel data for saving."""
        channels = []
        for row in self._channel_rows:
            name = row.get("name", "").strip()
            if not name:
                continue
            channel: dict[str, object] = {"name": name}
            fluorophore = row.get("fluorophore", "").strip()
            if fluorophore:
                channel["fluorophore"] = fluorophore
            ex_nm = row.get("excitation_nm", "").strip()
            if ex_nm and ex_nm.isdigit():
                channel["excitation_nm"] = int(ex_nm)
            em_nm = row.get("emission_nm", "").strip()
            if em_nm and em_nm.isdigit():
                channel["emission_nm"] = int(em_nm)
            channels.append(channel)
        return channels

    def _collect_acquisition_sessions(self) -> list[dict[str, object]]:
        sessions: list[dict[str, object]] = []
        for row in self._acquisition_rows:
            session: dict[str, object] = {}
            imaging_date = self._normalize_date(row.get("imaging_date"))
            if imaging_date:
                session["imaging_date"] = imaging_date
            microscope = str(row.get("microscope", "")).strip()
            if microscope:
                session["microscope"] = microscope
            modality = str(row.get("modality", "")).strip()
            if modality:
                session["modality"] = modality
            objective = str(row.get("objective", "")).strip()
            if objective:
                session["objective"] = objective

            voxel_x = str(row.get("voxel_x", "")).strip()
            voxel_y = str(row.get("voxel_y", "")).strip()
            voxel_z = str(row.get("voxel_z", "")).strip()
            if voxel_x or voxel_y or voxel_z:
                session["voxel_size"] = {
                    "x_um": float(voxel_x) if voxel_x else None,
                    "y_um": float(voxel_y) if voxel_y else None,
                    "z_um": float(voxel_z) if voxel_z else None,
                }

            time_interval = str(row.get("time_interval_s", "")).strip()
            if time_interval:
                session["time_interval_s"] = float(time_interval)

            notes = str(row.get("notes", "")).strip()
            if notes:
                session["notes"] = notes

            channels = row.get("channels", []) if isinstance(row, dict) else []
            if isinstance(channels, list) and channels:
                session["channels"] = channels

            if session:
                sessions.append(session)
        return sessions
