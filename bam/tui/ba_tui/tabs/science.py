"""Science tab: acquisition, method, tools, hardware."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Horizontal, VerticalScroll
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
                    yield Static(
                        "Imaging Sessions",
                        classes="section-header",
                    )
                    with Center():
                        yield DataTable(id="acquisition_table", cursor_type="row")
                    with Horizontal(id="acquisition_actions"):
                        yield Button(
                            "Add (A)",
                            id="add_acquisition",
                            variant="success",
                        )
                        yield Button(
                            "Edit (Enter)",
                            id="edit_acquisition",
                            variant="default",
                        )
                        yield Button(
                            "Remove (D)",
                            id="remove_acquisition",
                            variant="error",
                        )

                    yield Static(
                        "Channels",
                        classes="section-header",
                    )
                    with Center():
                        yield DataTable(id="channels_table", cursor_type="row")
                    with Horizontal(id="channel_actions"):
                        yield Button(
                            "Add (A)",
                            id="add_channel",
                            variant="success",
                        )
                        yield Button(
                            "Edit (Enter)",
                            id="edit_channel",
                            variant="default",
                        )
                        yield Button(
                            "Remove (D)",
                            id="remove_channel",
                            variant="error",
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
                                "Shell scripting (Bash, Zsh, etc.)",
                                "MATLAB",
                                "Fiji macro",
                                "LaTeX",
                                "Java",
                                "R",
                                "C/C++",
                                "Julia",
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
                    with Center():
                        yield DataTable(id="hardware_table", cursor_type="row")
                    with Horizontal(classes="form-row", id="hardware_actions"):
                        yield Button("Add (A)", id="hardware_add", variant="success")
                        yield Button(
                            "Edit (Enter)", id="hardware_edit", variant="default"
                        )
                        yield Button(
                            "Remove (D)", id="hardware_remove", variant="error"
                        )
                        yield Button(
                            "Detect Hardware", id="hardware_detect", variant="primary"
                        )
