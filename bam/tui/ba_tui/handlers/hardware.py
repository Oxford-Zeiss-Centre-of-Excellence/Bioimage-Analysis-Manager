from __future__ import annotations

from textual.widgets import DataTable

from ..screens import HardwareModal
from ..utils import detect_hardware


class HardwareMixin:
    """Mixin for hardware profile management."""

    _hardware_profiles: list[dict[str, str | bool]]

    def _handle_edit_hardware(
        self, idx: int, data: dict[str, str | bool] | None
    ) -> None:
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._hardware_profiles):
                self._hardware_profiles.pop(idx)
                self._populate_hardware_table()
            return
        if data and 0 <= idx < len(self._hardware_profiles):
            self._hardware_profiles[idx] = data
            self._populate_hardware_table()

    def _populate_hardware_table(self) -> None:
        try:
            table = self.query_one("#hardware_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "CPU", "Cores", "RAM", "GPU", "GPU Count")
            for idx, row in enumerate(self._hardware_profiles):
                gpu_count = row.get("gpu_count", 0)
                gpu_count_str = str(gpu_count) if gpu_count > 0 else ""
                table.add_row(
                    row.get("name", ""),
                    row.get("cpu", ""),
                    row.get("cores", ""),
                    row.get("ram", ""),
                    row.get("gpu", ""),
                    gpu_count_str,
                    key=str(idx),
                )
        except Exception:
            pass

    def _add_hardware_profile(self) -> None:
        self.push_screen(HardwareModal(), self._handle_new_hardware)

    def _handle_new_hardware(self, data: dict[str, str | bool] | None) -> None:
        if data:
            self._hardware_profiles.append(data)
            self._populate_hardware_table()

    def _remove_selected_hardware(self) -> None:
        try:
            table = self.query_one("#hardware_table", DataTable)
            idx = table.cursor_row
            if idx is None:
                return
            if 0 <= idx < len(self._hardware_profiles):
                self._hardware_profiles.pop(idx)
            self._populate_hardware_table()
        except Exception:
            pass

    def _detect_hardware_profile(self) -> None:
        try:
            detected = detect_hardware()
            profile = {
                "name": "local",
                "cpu": detected.get("cpu", ""),
                "cores": detected.get("cores", ""),
                "ram": detected.get("ram", ""),
                "gpu": detected.get("gpu", ""),
                "notes": "",
                "is_cluster": False,
                "partition": "",
                "node_type": "",
            }
            self._hardware_profiles.append(profile)
            self._populate_hardware_table()
        except Exception:
            pass
