from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


# =============================================================================
# Enums
# =============================================================================


class TaskStatus(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    blocked = "blocked"
    interrupted = "interrupted"


class FigureStatus(str, Enum):
    draft = "draft"
    ready = "ready"
    submitted = "submitted"
    published = "published"


class SourceType(str, Enum):
    script = "script"
    software = "software"
    manual = "manual"
    raw = "raw"


# =============================================================================
# Figure Tree Models (for publication tracking)
# =============================================================================


class FigureElement(BaseModel):
    """Leaf node: actual generated output with full lineage tracking.

    Examples:
        # Script-generated plot
        FigureElement(
            id="boxplot",
            output_path="figures/fig1/1a-boxplot.pdf",
            source_type="script",
            source_ref="scripts/plot_results.py",
            input_files=["data/results.csv"],
            parameters="--style publication --dpi 300",
            status="ready",
        )

        # Software-generated (e.g., Prism, SPSS)
        FigureElement(
            id="bar-chart",
            output_path="figures/fig2/2b-bar.pdf",
            source_type="software",
            source_ref="GraphPad Prism 9",
            input_files=["data/measurements.pzfx"],
            parameters="Bar graph, mean +/- SEM, unpaired t-test",
            status="draft",
        )

        # Manual editing (e.g., Illustrator)
        FigureElement(
            id="composite",
            output_path="figures/fig1/fig1-final.ai",
            source_type="manual",
            source_ref="Adobe Illustrator 2024",
            input_files=["figures/fig1/1a.pdf", "figures/fig1/1b.pdf"],
            status="ready",
        )

        # Raw image
        FigureElement(
            id="micrograph",
            output_path="figures/fig3/3a-confocal.tif",
            source_type="raw",
            source_ref="Zeiss LSM 880",
            input_files=["raw/sample1_z01.czi"],
            parameters="40x objective, 488nm excitation",
            status="ready",
        )
    """

    id: str
    output_path: str
    source_type: SourceType = SourceType.script
    source_ref: str = ""  # script path OR software name
    input_files: list[str] = Field(default_factory=list)
    parameters: Optional[str] = None  # freeform settings/commands
    status: FigureStatus = FigureStatus.draft
    version: int = 1
    description: Optional[str] = None
    created: date = Field(default_factory=date.today)
    updated: Optional[date] = None


class FigureNode(BaseModel):
    """Container node for figure hierarchy (Figure, Panel, Subfigure, etc.).

    Can contain other FigureNodes or FigureElements as children.
    Status is derived from children (worst status wins).

    Examples:
        # Top-level figure
        FigureNode(
            id="fig1",
            title="Experimental Setup",
            children=[
                FigureNode(id="1a", title="Sample Preparation", children=[...]),
                FigureNode(id="1b", title="Microscopy Setup", children=[...]),
            ]
        )

        # Panel with elements
        FigureNode(
            id="1a",
            title="Sample Preparation",
            children=[
                FigureElement(id="photo", output_path="...", ...),
                FigureElement(id="schematic", output_path="...", ...),
            ]
        )
    """

    id: str
    title: str = ""
    description: Optional[str] = None
    children: list[Union["FigureNode", FigureElement]] = Field(default_factory=list)

    @property
    def status(self) -> FigureStatus:
        """Derived from children: worst status wins (draft < ready < submitted < published)."""
        if not self.children:
            return FigureStatus.draft

        priority = [
            FigureStatus.draft,
            FigureStatus.ready,
            FigureStatus.submitted,
            FigureStatus.published,
        ]
        worst_idx = len(priority) - 1

        for child in self.children:
            if isinstance(child, FigureElement):
                child_status = child.status
            else:
                child_status = child.status

            try:
                idx = priority.index(child_status)
                worst_idx = min(worst_idx, idx)
            except ValueError:
                worst_idx = 0

        return priority[worst_idx]

    def is_leaf(self) -> bool:
        """Check if all children are FigureElements (no nested containers)."""
        return all(isinstance(c, FigureElement) for c in self.children)


# Enable forward reference for recursive type
FigureNode.model_rebuild()


# =============================================================================
# Project Models
# =============================================================================


class Project(BaseModel):
    name: str
    created: date = Field(default_factory=date.today)
    status: str = "active"


class Collaborator(BaseModel):
    """A project collaborator.

    Text format (pipe-separated): name | role | email | affiliation
    Example: John Doe | PI | john@uni.edu | University X
    """

    name: str
    role: str = ""  # PI | collaborator | consultant | student
    email: str = ""
    affiliation: str = ""

    @classmethod
    def from_pipe_string(cls, line: str) -> "Collaborator":
        """Parse from pipe-separated string."""
        parts = [p.strip() for p in line.split("|")]
        return cls(
            name=parts[0] if len(parts) > 0 else "",
            role=parts[1] if len(parts) > 1 else "",
            email=parts[2] if len(parts) > 2 else "",
            affiliation=parts[3] if len(parts) > 3 else "",
        )

    def to_pipe_string(self) -> str:
        """Convert to pipe-separated string."""
        return f"{self.name} | {self.role} | {self.email} | {self.affiliation}"


class People(BaseModel):
    analyst: str = ""
    collaborators: list[Collaborator] = Field(default_factory=list)

    @classmethod
    def parse_collaborators_text(cls, text: str) -> list[Collaborator]:
        """Parse collaborators from multiline text (one per line, pipe-separated)."""
        collaborators = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                collaborators.append(Collaborator.from_pipe_string(line))
        return collaborators

    def collaborators_to_text(self) -> str:
        """Convert collaborators to multiline text."""
        return "\n".join(c.to_pipe_string() for c in self.collaborators)


class Dataset(BaseModel):
    name: str
    endpoint: Optional[str] = None
    source: Optional[Path] = None
    local: Optional[Path] = None
    locally_mounted: bool = False
    description: Optional[str] = None
    format: Optional[str] = None
    image_quality: Optional[str] = None
    raw_size_gb: Optional[float] = None
    raw_size_unit: Optional[str] = None
    compressed: Optional[bool] = None
    uncompressed_size_gb: Optional[float] = None
    uncompressed_size_unit: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dataset":
        raw_size = data.get("raw_size_gb")
        if raw_size in (None, ""):
            raw_size_value = None
        else:
            raw_size_value = float(raw_size)
        uncompressed_size = data.get("uncompressed_size_gb")
        if uncompressed_size in (None, ""):
            uncompressed_value = None
        else:
            uncompressed_value = float(uncompressed_size)
        return cls(
            name=str(data.get("name", "")).strip(),
            endpoint=str(data.get("endpoint", "")).strip() or None,
            source=Path(data["source"]) if data.get("source") else None,
            local=Path(data["local"]) if data.get("local") else None,
            locally_mounted=bool(data.get("locally_mounted", False)),
            description=str(data.get("description", "")).strip() or None,
            format=str(data.get("format", "")).strip() or None,
            image_quality=str(data.get("image_quality", "")).strip() or None,
            raw_size_gb=raw_size_value,
            raw_size_unit=str(data.get("raw_size_unit", "")).strip() or None,
            compressed=bool(data.get("compressed"))
            if data.get("compressed") is not None
            else None,
            uncompressed_size_gb=uncompressed_value,
            uncompressed_size_unit=str(data.get("uncompressed_size_unit", "")).strip()
            or None,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "locally_mounted": self.locally_mounted,
        }
        if self.endpoint:
            payload["endpoint"] = self.endpoint
        if self.source:
            payload["source"] = str(self.source)
        if self.local:
            payload["local"] = str(self.local)
        if self.description:
            payload["description"] = self.description
        if self.format:
            payload["format"] = self.format
        if self.image_quality:
            payload["image_quality"] = self.image_quality
        if self.raw_size_gb is not None:
            payload["raw_size_gb"] = self.raw_size_gb
        if self.raw_size_unit:
            payload["raw_size_unit"] = self.raw_size_unit
        if self.compressed is not None:
            payload["compressed"] = self.compressed
        if self.uncompressed_size_gb is not None:
            payload["uncompressed_size_gb"] = self.uncompressed_size_gb
        if self.uncompressed_size_unit:
            payload["uncompressed_size_unit"] = self.uncompressed_size_unit
        return payload


class Artifact(BaseModel):
    """A project deliverable/output tracked in the manifest registry."""

    endpoint: Optional[str] = None
    path: str
    type: str = "unknown"  # figure | table | dataset | model | report | script
    status: str = "draft"  # draft | ready | delivered | published
    created: date = Field(default_factory=date.today)
    updated: Optional[date] = None
    description: Optional[str] = None


# =============================================================================
# Acquisition Models
# =============================================================================


class Channel(BaseModel):
    """Imaging channel configuration.

    Text format (pipe-separated): name | fluorophore | excitation_nm | emission_nm
    Example: DAPI | DAPI | 405 | 461
    """

    name: str
    fluorophore: str = ""
    excitation_nm: Optional[int] = None
    emission_nm: Optional[int] = None

    @field_validator("excitation_nm", "emission_nm", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for optional int fields."""
        if v == "" or v == "None":
            return None
        return v

    @classmethod
    def from_pipe_string(cls, line: str) -> "Channel":
        """Parse from pipe-separated string."""
        parts = [p.strip() for p in line.split("|")]
        return cls(
            name=parts[0] if len(parts) > 0 else "",
            fluorophore=parts[1] if len(parts) > 1 else "",
            excitation_nm=int(parts[2])
            if len(parts) > 2 and parts[2].isdigit()
            else None,
            emission_nm=int(parts[3])
            if len(parts) > 3 and parts[3].isdigit()
            else None,
        )

    def to_pipe_string(self) -> str:
        """Convert to pipe-separated string."""
        ex = str(self.excitation_nm) if self.excitation_nm else ""
        em = str(self.emission_nm) if self.emission_nm else ""
        return f"{self.name} | {self.fluorophore} | {ex} | {em}"


class VoxelSize(BaseModel):
    """Voxel dimensions in micrometers."""

    x_um: Optional[float] = None
    y_um: Optional[float] = None
    z_um: Optional[float] = None

    @field_validator("x_um", "y_um", "z_um", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for optional float fields."""
        if v == "" or v == "None":
            return None
        return v


class AcquisitionSession(BaseModel):
    """Single imaging session parameters."""

    imaging_date: Optional[date] = None
    microscope: str = ""
    modality: str = ""  # confocal | widefield | lightsheet | EM | etc.
    objective: str = ""  # e.g., "40x/1.3 Oil"
    voxel_size: Optional[VoxelSize] = None
    time_interval_s: Optional[float] = None
    notes: str = ""
    channels: list[Channel] = Field(default_factory=list)

    @field_validator("time_interval_s", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for optional float fields."""
        if v == "" or v == "None":
            return None
        return v


class Acquisition(BaseModel):
    """Imaging parameters and metadata."""

    sessions: list[AcquisitionSession] = Field(default_factory=list)

    # Legacy single-session fields (deprecated)
    microscope: str = ""
    modality: str = ""  # confocal | widefield | lightsheet | EM | etc.
    objective: str = ""  # e.g., "40x/1.3 Oil"
    voxel_size: Optional[VoxelSize] = None
    time_interval_s: Optional[float] = None
    notes: str = ""

    @field_validator("time_interval_s", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for optional float fields."""
        if v == "" or v == "None":
            return None
        return v

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_session(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("sessions"):
            return data

        has_legacy = any(
            data.get(field)
            for field in (
                "imaging_date",
                "microscope",
                "modality",
                "objective",
                "voxel_size",
                "time_interval_s",
                "notes",
            )
        )
        if has_legacy:
            data["sessions"] = [
                {
                    "imaging_date": data.get("imaging_date"),
                    "microscope": data.get("microscope", ""),
                    "modality": data.get("modality", ""),
                    "objective": data.get("objective", ""),
                    "voxel_size": data.get("voxel_size"),
                    "time_interval_s": data.get("time_interval_s"),
                    "notes": data.get("notes", ""),
                    "channels": data.get("channels", []),
                }
            ]
        return data

    @classmethod
    def parse_channels_text(cls, text: str) -> list[Channel]:
        """Parse channels from multiline text."""
        channels = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                channels.append(Channel.from_pipe_string(line))
        return channels

    def channels_to_text(self) -> str:
        """Convert channels to multiline text."""
        return "\n".join(c.to_pipe_string() for c in self.channels)


class HardwareProfile(BaseModel):
    """Hardware profile for a compute environment."""

    name: str
    cpu: str = ""
    ram: str = ""
    gpu: str = ""
    notes: str = ""
    is_cluster: bool = False
    partition: str = ""
    node_type: str = ""


class Method(BaseModel):
    """Method documentation reference."""

    file_path: str = ""
    template_used: str = ""


# =============================================================================
# Tools Models
# =============================================================================


class Tools(BaseModel):
    """Software and analysis environment."""

    environment: str = ""  # conda | pixi | venv | docker
    env_file: str = ""  # Path to environment.yaml or requirements.txt
    languages: list[str] = Field(default_factory=list)  # python, R, fiji-macro
    software: list[str] = Field(default_factory=list)
    git_remote: str = ""
    cluster_packages: list[str] = Field(default_factory=list)


# =============================================================================
# Billing Models
# =============================================================================


class Billing(BaseModel):
    """Project funding and time tracking."""

    fund_code: str = ""
    hourly_rate: Optional[float] = None
    budget_hours: Optional[float] = None
    spent_hours: Optional[float] = None  # Auto-calculated from worklog
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: str = ""


# =============================================================================
# Publication Models
# =============================================================================


class Publication(BaseModel):
    """Publication and sharing information."""

    status: str = "none"  # none | in-prep | submitted | revision | accepted | published
    target_journal: str = ""
    manuscript_path: str = ""
    figures: list[FigureNode] = Field(default_factory=list)  # Hierarchical figure tree
    preprint_doi: str = ""
    published_doi: str = ""
    github_repo: str = ""
    zenodo_doi: str = ""
    notes: str = ""


# =============================================================================
# Archive Models
# =============================================================================


class Archive(BaseModel):
    """Long-term storage and preservation."""

    status: str = "active"  # active | pending-archive | archived
    endpoint: Optional[str] = None
    archive_date: Optional[date] = None
    archive_location: str = ""
    retention_years: Optional[int] = None
    backup_verified: bool = False
    notes: str = ""


# =============================================================================
# Timeline Models
# =============================================================================


class Milestone(BaseModel):
    """A project milestone.

    Text format (pipe-separated): name | target_date | actual_date | status | notes
    Example: Data acquisition | 2024-03-01 | 2024-03-05 | completed | Initial run
    """

    name: str
    target_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: str = "pending"  # pending | in-progress | completed | delayed | cancelled
    notes: str = ""

    @classmethod
    def from_pipe_string(cls, line: str) -> "Milestone":
        """Parse from pipe-separated string."""
        parts = [p.strip() for p in line.split("|")]
        target = None
        actual = None
        if len(parts) > 1 and parts[1]:
            try:
                target = date.fromisoformat(parts[1])
            except ValueError:
                pass
        if len(parts) > 2 and parts[2]:
            try:
                actual = date.fromisoformat(parts[2])
            except ValueError:
                pass
        return cls(
            name=parts[0] if len(parts) > 0 else "",
            target_date=target,
            actual_date=actual,
            status=parts[3] if len(parts) > 3 else "pending",
            notes=parts[4] if len(parts) > 4 else "",
        )

    def to_pipe_string(self) -> str:
        """Convert to pipe-separated string."""
        t = self.target_date.isoformat() if self.target_date else ""
        a = self.actual_date.isoformat() if self.actual_date else ""
        return f"{self.name} | {t} | {a} | {self.status} | {self.notes}"


class Timeline(BaseModel):
    """Project milestones and deadlines."""

    milestones: list[Milestone] = Field(default_factory=list)


# =============================================================================
# Hub Models
# =============================================================================


class Hub(BaseModel):
    """Cross-project registry settings."""

    registered: bool = False
    registered_date: Optional[date] = None
    last_sync: Optional[datetime] = None


# =============================================================================
# Worklog Models
# =============================================================================


class LogEntry(BaseModel):
    checkin: datetime
    checkout: Optional[datetime] = None
    task: str
    type: str = "analysis"
    status: TaskStatus = TaskStatus.active
    notes: Optional[str] = None
    elapsed_seconds: int = 0

    def duration_seconds(self) -> int:
        if self.status == TaskStatus.paused:
            return self.elapsed_seconds
        if self.status == TaskStatus.completed and self.checkout is not None:
            delta = self.checkout - self.checkin
            return int(delta.total_seconds()) + self.elapsed_seconds
        delta = datetime.now() - self.checkin
        return int(delta.total_seconds()) + self.elapsed_seconds


class WorkLog(BaseModel):
    entries: list[LogEntry] = Field(default_factory=list)

    def active_tasks(self) -> list[LogEntry]:
        return [entry for entry in self.entries if entry.status == TaskStatus.active]

    def today_completed(self) -> list[LogEntry]:
        today = date.today()
        return [
            entry
            for entry in self.entries
            if entry.status == TaskStatus.completed
            and entry.checkout is not None
            and entry.checkout.date() == today
        ]


class Manifest(BaseModel):
    """Main manifest model containing all project metadata."""

    project: Project
    people: Optional[People] = None
    datasets: list[Dataset] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    acquisition: Optional[Acquisition] = None
    tools: Optional[Tools] = None
    hardware_profiles: list[HardwareProfile] = Field(default_factory=list)
    method: Optional[Method] = None
    billing: Optional[Billing] = None
    publication: Optional[Publication] = None
    archive: Optional[Archive] = None
    timeline: Optional[Timeline] = None
    artifacts: list[Artifact] = Field(default_factory=list)
    hub: Optional[Hub] = None

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_dicts(cls, data: Any) -> Any:
        """Convert legacy dict[str, Any] fields to proper models for backward compatibility."""
        if not isinstance(data, dict):
            return data

        # Handle legacy collaborators format (list of dicts instead of Collaborator)
        if "people" in data and isinstance(data["people"], dict):
            collabs = data["people"].get("collaborators", [])
            if collabs and isinstance(collabs[0], dict) and "name" in collabs[0]:
                # Already in correct format, pydantic will handle it
                pass

        if "data" in data and "datasets" not in data:
            legacy = data.get("data")
            datasets: list[dict[str, Any]] = []
            if isinstance(legacy, dict):
                enabled = bool(legacy.get("enabled", True))
                if enabled:
                    has_fields = any(
                        legacy.get(key)
                        for key in (
                            "endpoint",
                            "source",
                            "local",
                            "description",
                            "format",
                            "raw_size_gb",
                            "raw_size_unit",
                            "compressed",
                            "uncompressed_size_gb",
                            "uncompressed_size_unit",
                        )
                    )
                    if has_fields:
                        dataset = {
                            "name": "dataset-1",
                            "endpoint": legacy.get("endpoint"),
                            "source": legacy.get("source"),
                            "local": legacy.get("local"),
                            "locally_mounted": legacy.get("locally_mounted", False),
                            "description": legacy.get("description"),
                            "format": legacy.get("format"),
                            "raw_size_gb": legacy.get("raw_size_gb"),
                            "raw_size_unit": legacy.get("raw_size_unit"),
                            "compressed": legacy.get("compressed"),
                            "uncompressed_size_gb": legacy.get("uncompressed_size_gb"),
                            "uncompressed_size_unit": legacy.get(
                                "uncompressed_size_unit"
                            ),
                        }
                        datasets.append(dataset)
            data["datasets"] = datasets
            data.pop("data", None)

        timeline = data.get("timeline")
        if isinstance(timeline, dict):
            timeline.pop("notes", None)
            milestones = timeline.get("milestones")
            if isinstance(milestones, list):
                for milestone in milestones:
                    if not isinstance(milestone, dict):
                        continue
                    for field in ("target_date", "actual_date"):
                        value = milestone.get(field)
                        if value is None:
                            continue
                        if isinstance(value, date):
                            continue
                        date_method = getattr(value, "date", None)
                        if callable(date_method):
                            try:
                                coerced = date_method()
                                if isinstance(coerced, date):
                                    milestone[field] = coerced
                                else:
                                    milestone[field] = None
                            except Exception:
                                milestone[field] = None

        return data


def build_manifest(
    *,
    project_name: str,
    analyst: str,
    datasets: Optional[list[Dataset]] = None,
    data_enabled: bool = True,
    data_endpoint: str = "",
    data_source: str = "",
    data_local: str = "",
    data_format: str = "",
    locally_mounted: bool = False,
) -> Manifest:
    final_datasets: list[Dataset] = []
    if datasets is not None:
        final_datasets = datasets
    elif data_enabled and any([data_endpoint, data_source, data_local, data_format]):
        final_datasets = [
            Dataset(
                name="dataset-1",
                endpoint=data_endpoint.strip() if data_endpoint else None,
                source=Path(data_source) if data_source else None,
                local=Path(data_local) if data_local else None,
                format=data_format.strip() if data_format else None,
                locally_mounted=locally_mounted,
            )
        ]

    return Manifest(
        project=Project(name=project_name.strip()),
        people=People(analyst=analyst.strip()),
        datasets=final_datasets,
    )


class ManifestValidationError(RuntimeError):
    def __init__(
        self, message: str, errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message)
        self.errors = errors or []


def raise_validation_error(error: ValidationError) -> None:
    details = []
    for entry in error.errors():
        loc = ".".join(str(item) for item in entry.get("loc", []))
        details.append({"field": loc, "error": entry.get("msg", "Invalid value")})
    raise ManifestValidationError("Manifest validation failed", details)
