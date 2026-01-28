"""Science tab: acquisition, tools."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)


def compose_science_tab(app: object) -> ComposeResult:
    """Compose the Science tab with acquisition and tools sections."""
    with TabPane("Science (F2)", id="science"):
        with TabbedContent(id="science_sections"):
            # ─────────────────────────────────────────────────────────────
            # Acquisition Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Acquisition", id="science_acquisition"):
                with Vertical(id="acquisition_form"):
                    yield Static("Imaging Parameters", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Microscope:")
                        yield Input(
                            app._defaults.get("microscope", ""),
                            placeholder="Microscope model/name",
                            id="microscope",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Modality:")
                        yield Select(
                            [
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
                            ],
                            value=app._defaults.get("modality", Select.BLANK),
                            allow_blank=True,
                            id="modality",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Objective:")
                        yield Input(
                            app._defaults.get("objective", ""),
                            placeholder="e.g., 40x/1.3 Oil",
                            id="objective",
                        )

                    yield Static(
                        "Channels (one per line: name | fluorophore | excitation_nm | emission_nm)"
                    )
                    yield TextArea(
                        app._defaults.get("channels_text", ""),
                        id="channels_text",
                    )
                    yield Static(
                        "Example: DAPI | DAPI | 405 | 461",
                        classes="form-hint",
                    )

                    yield Static("Voxel Size", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("X (µm):")
                        yield Input(
                            app._defaults.get("voxel_x", ""),
                            placeholder="X dimension",
                            id="voxel_x",
                        )
                        yield Label("Y (µm):")
                        yield Input(
                            app._defaults.get("voxel_y", ""),
                            placeholder="Y dimension",
                            id="voxel_y",
                        )
                        yield Label("Z (µm):")
                        yield Input(
                            app._defaults.get("voxel_z", ""),
                            placeholder="Z dimension",
                            id="voxel_z",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Time interval (s):")
                        yield Input(
                            app._defaults.get("time_interval", ""),
                            placeholder="For timelapse imaging",
                            id="time_interval",
                        )

                    yield Static("Acquisition Notes")
                    yield TextArea(
                        app._defaults.get("acquisition_notes", ""),
                        id="acquisition_notes",
                    )

            # ─────────────────────────────────────────────────────────────
            # Tools Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Tools", id="science_tools"):
                with Vertical(id="tools_form"):
                    yield Static("Environment", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Type:")
                        yield Select(
                            [
                                ("Conda", "conda"),
                                ("Pixi", "pixi"),
                                ("Venv", "venv"),
                                ("Docker", "docker"),
                                ("None", ""),
                            ],
                            value=app._defaults.get("environment", Select.BLANK),
                            allow_blank=True,
                            id="environment",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Env file:")
                        yield Input(
                            app._defaults.get("env_file", ""),
                            placeholder="Path to environment.yaml or requirements.txt",
                            id="env_file",
                        )

                    yield Static("Languages (comma-separated)")
                    with Horizontal(classes="form-row"):
                        yield Label("Languages:")
                        yield Input(
                            app._defaults.get("languages", "python"),
                            placeholder="e.g., python, R, fiji-macro",
                            id="languages",
                        )

                    yield Static("Key Packages (one per line: name | version)")
                    yield TextArea(
                        app._defaults.get("packages_text", ""),
                        id="packages_text",
                    )
                    yield Static(
                        "Example: napari | 0.4.18",
                        classes="form-hint",
                    )

                    yield Static("Paths", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Scripts dir:")
                        yield Input(
                            app._defaults.get("scripts_dir", ""),
                            placeholder="Path to analysis scripts",
                            id="scripts_dir",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Notebooks dir:")
                        yield Input(
                            app._defaults.get("notebooks_dir", ""),
                            placeholder="Path to Jupyter notebooks",
                            id="notebooks_dir",
                        )
