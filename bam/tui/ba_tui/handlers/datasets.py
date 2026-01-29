from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import DataTable, TabbedContent

from typing import TYPE_CHECKING

from ..config import load_dataset_format_options, load_endpoint_options
from ..screens import DatasetModal

if TYPE_CHECKING:
    from ..tui import BAApp


class DatasetsMixin:
    """Mixin for dataset table management."""

    _dataset_rows: list[dict[str, object]]

    def _toggle_data_sections(self: "BAApp", enabled: bool) -> None:
        """Show/hide data sections based on enabled state."""
        try:
            data_sections = self.query_one("#data_sections", Vertical)
            if enabled:
                data_sections.remove_class("hidden")
            else:
                data_sections.add_class("hidden")
        except Exception:
            pass

    def _ensure_dataset_rows(self: "BAApp") -> None:
        if self._dataset_rows:
            return
        self._dataset_rows = []

    def _populate_datasets_table(self: "BAApp") -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            table.clear(columns=True)
            table.add_columns("Name", "Endpoint", "Source", "Local", "Format", "Size")
            for idx, row in enumerate(self._dataset_rows):
                table.add_row(
                    str(row.get("name", "")),
                    str(row.get("endpoint", "")),
                    self._truncate_path(str(row.get("source", ""))),
                    self._truncate_path(str(row.get("local", ""))),
                    str(row.get("format", "")),
                    self._format_dataset_size(row),
                    key=str(idx),
                )
        except Exception:
            pass

    def _format_dataset_size(self: "BAApp", row: dict[str, object]) -> str:
        raw_size = str(row.get("raw_size_gb", "")).strip()
        if not raw_size:
            return ""
        unit = str(row.get("raw_size_unit", "gb")).lower()
        suffix = unit.upper() if unit else "GB"
        return f"{raw_size} {suffix}"

    def _truncate_path(self: "BAApp", value: str, max_len: int = 30) -> str:
        if len(value) <= max_len:
            return value
        return f"...{value[-(max_len - 3) :]}"

    def action_add_dataset(self: "BAApp") -> None:
        tabbed = self.query_one("#tabs", TabbedContent)
        if tabbed.active != "setup":
            return
        initial_data = None
        try:
            table = self.query_one("#datasets_table", DataTable)
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self._dataset_rows):
                initial_data = dict(self._dataset_rows[idx])
                initial_data["name"] = ""
        except Exception:
            initial_data = None
        self.push_screen(
            DatasetModal(
                load_endpoint_options(),
                load_dataset_format_options(),
                initial_data,
            ),
            self._handle_new_dataset,
        )

    def action_remove_dataset(self: "BAApp") -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            if table.cursor_row is None:
                self.notify("Select a dataset to remove", severity="warning")
                return
            idx = table.cursor_row
            if 0 <= idx < len(self._dataset_rows):
                self._dataset_rows.pop(idx)
            self._populate_datasets_table()
            if self._dataset_rows:
                idx = min(idx, len(self._dataset_rows) - 1)
                table.move_cursor(row=idx, column=0)
        except Exception:
            pass

    def action_sync_dataset(self: "BAApp") -> None:
        try:
            table = self.query_one("#datasets_table", DataTable)
            idx = table.cursor_row
            if idx is None and self._dataset_rows:
                idx = 0
            if idx is None or not (0 <= idx < len(self._dataset_rows)):
                self.notify("Select a dataset to sync", severity="warning")
                return
            row = self._dataset_rows[idx]
            self._start_sync(row)
        except Exception:
            pass

    def _handle_new_dataset(self: "BAApp", data: dict[str, object] | None) -> None:
        if data:
            self._dataset_rows.append(data)
            self._populate_datasets_table()

    def _handle_edit_dataset(
        self: "BAApp", idx: int, data: dict[str, object] | None
    ) -> None:
        if data and data.get("__delete__"):
            if 0 <= idx < len(self._dataset_rows):
                self._dataset_rows.pop(idx)
                self._populate_datasets_table()
                try:
                    table = self.query_one("#datasets_table", DataTable)
                    if self._dataset_rows:
                        idx = min(idx, len(self._dataset_rows) - 1)
                        table.move_cursor(row=idx, column=0)
                except Exception:
                    pass
            return
        if data and 0 <= idx < len(self._dataset_rows):
            self._dataset_rows[idx] = data
            self._populate_datasets_table()
            try:
                table = self.query_one("#datasets_table", DataTable)
                table.move_cursor(row=idx, column=0)
            except Exception:
                pass

    def _collect_datasets(self: "BAApp") -> list[dict[str, object]]:
        datasets: list[dict[str, object]] = []
        for row in self._dataset_rows:
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            dataset: dict[str, object] = {"name": name}
            endpoint = str(row.get("endpoint", "")).strip()
            if endpoint:
                dataset["endpoint"] = endpoint
            source = str(row.get("source", "")).strip()
            if source:
                dataset["source"] = source
            local = str(row.get("local", "")).strip()
            if local:
                dataset["local"] = local
            dataset["locally_mounted"] = bool(row.get("locally_mounted", False))
            description = str(row.get("description", "")).strip()
            if description:
                dataset["description"] = description
            data_format = str(row.get("format", "")).strip()
            if data_format:
                dataset["format"] = data_format
            raw_size = str(row.get("raw_size_gb", "")).strip()
            if raw_size:
                try:
                    dataset["raw_size_gb"] = float(raw_size)
                except ValueError:
                    pass
            raw_unit = str(row.get("raw_size_unit", "")).strip()
            if raw_unit:
                dataset["raw_size_unit"] = raw_unit
            compressed = row.get("compressed")
            if compressed is not None:
                dataset["compressed"] = bool(compressed)
            uncompressed_size = str(row.get("uncompressed_size_gb", "")).strip()
            if uncompressed_size:
                try:
                    dataset["uncompressed_size_gb"] = float(uncompressed_size)
                except ValueError:
                    pass
            uncompressed_unit = str(row.get("uncompressed_size_unit", "")).strip()
            if uncompressed_unit:
                dataset["uncompressed_size_unit"] = uncompressed_unit
            datasets.append(dataset)
        return datasets
