from __future__ import annotations

from datetime import date

import pendulum
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Input, Label, Select, Static

from ..styles import SESSION_MODAL_CSS
from ..widgets import DateSelect
from .base import FormModal


class AcquisitionSessionModal(FormModal):
    """Modal to add or edit an acquisition session."""

    CSS = SESSION_MODAL_CSS

    MODALITY_OPTIONS = [
        ("Confocal", "confocal"),
        ("Widefield", "widefield"),
        ("Light-sheet", "light-sheet"),
        ("Two-photon", "two-photon"),
        ("Super-resolution", "super-resolution"),
        ("EM", "em"),
        ("Brightfield", "brightfield"),
        ("Phase contrast", "phase-contrast"),
        ("DIC", "dic"),
        ("Other", "other"),
    ]

    def __init__(
        self, initial_data: dict[str, object] | None = None, allow_remove: bool = False
    ) -> None:
        super().__init__()
        self.initial_data = initial_data or {}
        self._allow_remove = allow_remove

    def compose(self) -> ComposeResult:
        title = "Edit Imaging Session" if self.initial_data else "Add Imaging Session"
        with Vertical(id="dialog"):
            yield Static(title, classes="header")
            with VerticalScroll(id="dialog_scroll"):
                imaging_date = self._coerce_date(self.initial_data.get("imaging_date"))
                with Horizontal(classes="form-row"):
                    yield Label("Imaging date:")
                    yield DateSelect(
                        "#session_datepicker_mount",
                        date=imaging_date,
                        id="session_imaging_date",
                    )
                yield Static("", id="session_datepicker_mount")
                with Horizontal(classes="form-row"):
                    yield Label("Microscope:")
                    yield Input(
                        str(self.initial_data.get("microscope", "")),
                        id="session_microscope",
                        placeholder="Microscope model/name",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Modality:")
                    modality_value = self.initial_data.get("modality")
                    yield Select(
                        self.MODALITY_OPTIONS,
                        value=modality_value if modality_value else Select.BLANK,
                        allow_blank=True,
                        id="session_modality",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Objective:")
                    yield Input(
                        str(self.initial_data.get("objective", "")),
                        id="session_objective",
                        placeholder="e.g., 40x/1.3 Oil",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel X (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_x", "")),
                        id="session_voxel_x",
                        placeholder="X dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel Y (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_y", "")),
                        id="session_voxel_y",
                        placeholder="Y dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Voxel Z (µm):")
                    yield Input(
                        str(self.initial_data.get("voxel_z", "")),
                        id="session_voxel_z",
                        placeholder="Z dimension",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Time interval (s):")
                    yield Input(
                        str(self.initial_data.get("time_interval_s", "")),
                        id="session_time_interval",
                        placeholder="For timelapse imaging",
                    )

                with Horizontal(classes="form-row"):
                    yield Label("Notes:")
                    yield Input(
                        str(self.initial_data.get("notes", "")),
                        id="session_notes",
                        placeholder="Optional",
                    )

            from textual.widgets import Button

            with Horizontal(id="buttons"):
                yield Button("Save (Ctrl+A)", variant="success", id="save")
                if self._allow_remove:
                    yield Button("Remove (Ctrl+D)", variant="error", id="remove")
                yield Button("Cancel (Esc)", variant="default", id="cancel")

    def _submit(self) -> None:
        microscope = self.query_one("#session_microscope", Input).value.strip()
        modality = self.query_one("#session_modality", Select).value
        modality_value = "" if modality in (None, Select.BLANK) else str(modality)

        # Get date and normalize to date only (remove time)
        imaging_date_value = self.query_one("#session_imaging_date", DateSelect).value
        if imaging_date_value and hasattr(imaging_date_value, "date"):
            imaging_date_value = imaging_date_value.date()

        data: dict[str, object] = {
            "imaging_date": imaging_date_value,
            "microscope": microscope,
            "modality": modality_value,
            "objective": self.query_one("#session_objective", Input).value.strip(),
            "voxel_x": self.query_one("#session_voxel_x", Input).value.strip(),
            "voxel_y": self.query_one("#session_voxel_y", Input).value.strip(),
            "voxel_z": self.query_one("#session_voxel_z", Input).value.strip(),
            "time_interval_s": self.query_one(
                "#session_time_interval", Input
            ).value.strip(),
            "notes": self.query_one("#session_notes", Input).value.strip(),
        }
        self.dismiss(data)

    @staticmethod
    def _coerce_date(value: object) -> pendulum.DateTime | None:
        if isinstance(value, pendulum.DateTime):
            return value
        if isinstance(value, date):
            return pendulum.datetime(value.year, value.month, value.day)
        if isinstance(value, str) and value:
            try:
                parsed = pendulum.parse(value)
                if isinstance(parsed, pendulum.DateTime):
                    return parsed
                return None
            except Exception:
                return None
        return None
