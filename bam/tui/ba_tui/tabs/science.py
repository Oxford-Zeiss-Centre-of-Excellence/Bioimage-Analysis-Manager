"""Science tab: acquisition, method, tools, hardware."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    Markdown,
    OptionList,
    Select,
    SelectionList,
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
                with VerticalScroll(id="acquisition_form"):
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
                    with Horizontal(
                        classes="form-row"
                        + (
                            ""
                            if app._defaults.get("modality", "").lower() == "other"
                            else " hidden"
                        ),
                        id="modality_other_row",
                    ):
                        yield Label("Custom modality:")
                        yield Input(
                            app._defaults.get("modality_custom", ""),
                            placeholder="Enter modality",
                            id="modality_custom",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Objective:")
                        yield Input(
                            app._defaults.get("objective", ""),
                            placeholder="e.g., 40x/1.3 Oil",
                            id="objective",
                        )

                    yield Static(
                        "Channels (Ctrl+A: add, Ctrl+D: delete, Enter: edit)",
                        classes="section-header",
                    )
                    yield DataTable(id="channels_table", cursor_type="row")

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
            # Method Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Method", id="science_method"):
                with VerticalScroll(id="method_form"):
                    yield Static("Method Documentation", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Method file:")
                        yield Input(
                            app._defaults.get("method_path", ""),
                            placeholder="Path to method.md",
                            id="method_path",
                        )
                        yield Button("Browse", id="browse_method", variant="primary")
                    yield OptionList(id="method_path_suggestions")
                    yield Static("Preview", classes="section-header")
                    yield Markdown(
                        app._defaults.get("method_preview", ""), id="method_preview"
                    )
                    with Horizontal(classes="form-row"):
                        yield Button(
                            "Create Template", id="method_template", variant="success"
                        )

            # ─────────────────────────────────────────────────────────────
            # Tools Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Tools", id="science_tools"):
                with VerticalScroll(id="tools_form"):
                    yield Static("Repository", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Git remote:")
                        yield Input(
                            app._defaults.get("git_remote", ""),
                            placeholder="Auto-detected from .git",
                            id="git_remote",
                        )

                    yield Static("Languages", classes="section-header")
                    yield SelectionList(
                        *[
                            (label, label, label in app._defaults.get("languages", []))
                            for label in (
                                "Python",
                                "R",
                                "C/C++",
                                "Shell scripting",
                                "Java",
                                "LaTeX",
                                "MATLAB",
                                "Julia",
                                "Fiji macro",
                                "JavaScript",
                                "TypeScript",
                                "Go",
                                "Rust",
                            )
                        ],
                        id="languages_list",
                    )
                    with Horizontal(id="languages_actions"):
                        yield Button(
                            "Add Languages",
                            id="languages_add",
                            variant="primary",
                        )

                    yield Static("Software", classes="section-header")
                    yield SelectionList(
                        *[
                            (label, label, label in app._defaults.get("software", []))
                            for label in (
                                "Fiji/ImageJ",
                                "napari",
                                "QuPath",
                                "Imaris",
                                "Arivis",
                                "ZEN",
                                "CellProfiler",
                                "ilastik",
                                "Icy",
                                "OMERO",
                                "Huygens",
                                "Prism",
                                "SPSS",
                                "R Studio",
                                "JupyterLab",
                                "Google Colab",
                                "AWS SageMaker",
                                "Azure ML",
                                "Kaggle Notebooks",
                            )
                        ],
                        id="software_list",
                    )
                    with Horizontal(id="software_actions"):
                        yield Button(
                            "Add Software",
                            id="software_add",
                            variant="primary",
                        )

                    yield Static("Environment (optional)", classes="section-header")
                    with Horizontal(classes="form-row"):
                        yield Label("Type:")
                        yield Select(
                            [
                                ("Conda", "conda"),
                                ("Pixi", "pixi"),
                                ("Venv", "venv"),
                                ("UV", "uv"),
                                ("Poetry", "poetry"),
                                ("Docker", "docker"),
                                ("Devcontainer", "devcontainer"),
                                ("renv", "renv"),
                                ("Nix", "nix"),
                                ("C/C++", "c-cpp"),
                                ("JS/TS", "js-ts"),
                                ("Other", "other"),
                                ("None", ""),
                            ],
                            value=app._defaults.get("environment", Select.BLANK),
                            allow_blank=True,
                            id="environment",
                        )
                    with Horizontal(
                        classes="form-row"
                        + (
                            ""
                            if app._defaults.get("environment", "").lower() == "other"
                            else " hidden"
                        ),
                        id="environment_other_row",
                    ):
                        yield Label("Other env:")
                        yield Input(
                            app._defaults.get("environment_custom", ""),
                            placeholder="Enter environment",
                            id="environment_custom",
                        )
                    with Horizontal(classes="form-row"):
                        yield Label("Env file:")
                        yield Input(
                            app._defaults.get("env_file", ""),
                            placeholder="e.g., environment.yaml, requirements.txt",
                            id="env_file",
                        )

                    yield Static("Cluster Packages", classes="section-header")
                    yield SelectionList(
                        *[
                            (
                                label,
                                label,
                                label in app._defaults.get("cluster_packages", []),
                            )
                            for label in (
                                "SLURM",
                                "UGE",
                                "PBS",
                                "LSF",
                                "Snakemake",
                                "Nextflow",
                                "Cromwell",
                                "WDL",
                                "CWL",
                                "Singularity/Apptainer",
                            )
                        ],
                        id="cluster_packages_list",
                    )
                    with Horizontal(id="cluster_packages_actions"):
                        yield Button(
                            "Add Cluster Packages",
                            id="cluster_packages_add",
                            variant="primary",
                        )

            # ─────────────────────────────────────────────────────────────
            # Hardware Section
            # ─────────────────────────────────────────────────────────────
            with TabPane("Hardware", id="science_hardware"):
                with VerticalScroll(id="hardware_form"):
                    yield Static("Hardware Profiles", classes="section-header")
                    yield DataTable(id="hardware_table", cursor_type="row")
                    with Horizontal(classes="form-row", id="hardware_actions"):
                        yield Button("Add", id="hardware_add", variant="success")
                        yield Button("Remove", id="hardware_remove", variant="error")
                        yield Button(
                            "Detect Hardware", id="hardware_detect", variant="primary"
                        )
