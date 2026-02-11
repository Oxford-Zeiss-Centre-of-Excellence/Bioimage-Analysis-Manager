"""Centralized path resolution for BAM TUI outputs.

All TUI-managed directories live under .bam/ in new projects,
with fallback to root-level directories for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

# Standard output directories managed by BAM TUI
OUTPUT_DIRS = ["log", "ideas", "doc", "artifact", "templates"]

# Container directory for all outputs
BAM_DIR = ".bam"


def resolve_output_dir(project_root: Path, dirname: str) -> Path:
    """Resolve output directory path with auto-detect fallback.

    Checks .bam/{dirname} first (new structure), then {dirname} at root
    (old structure) for backward compatibility.

    Args:
        project_root: Project root directory
        dirname: Output directory name (e.g., "log", "ideas")

    Returns:
        Path to the output directory. If neither exists, returns the
        new structure path (.bam/{dirname}) for future writes.

    Example:
        >>> resolve_output_dir(Path("/project"), "log")
        Path("/project/.bam/log")  # if exists, or for new writes
        Path("/project/log")       # if only old structure exists
    """
    # Check new structure first
    new_path = project_root / BAM_DIR / dirname
    if new_path.exists():
        return new_path

    # Fallback to old structure for existing projects
    old_path = project_root / dirname
    if old_path.exists():
        return old_path

    # Neither exists - return new structure path for future writes
    return new_path


def resolve_output_file(project_root: Path, dirname: str, filename: str) -> Path:
    """Resolve output file path with auto-detect fallback.

    Similar to resolve_output_dir but for specific files within output directories.

    Args:
        project_root: Project root directory
        dirname: Output directory name (e.g., "log", "ideas")
        filename: File name within the directory (e.g., "tasks.yaml")

    Returns:
        Path to the file. Checks both new and old structure.

    Example:
        >>> resolve_output_file(Path("/project"), "log", "tasks.yaml")
        Path("/project/.bam/log/tasks.yaml")  # if exists
        Path("/project/log/tasks.yaml")       # if only old exists
    """
    # Check new structure first
    new_path = project_root / BAM_DIR / dirname / filename
    if new_path.exists():
        return new_path

    # Fallback to old structure
    old_path = project_root / dirname / filename
    if old_path.exists():
        return old_path

    # Neither exists - return new structure path for future writes
    return new_path


def get_bam_root(project_root: Path) -> Path:
    """Get the .bam directory path.

    Args:
        project_root: Project root directory

    Returns:
        Path to .bam directory
    """
    return project_root / BAM_DIR


def ensure_bam_dir(project_root: Path) -> Path:
    """Ensure .bam directory exists.

    Args:
        project_root: Project root directory

    Returns:
        Path to .bam directory (created if needed)
    """
    bam_dir = get_bam_root(project_root)
    bam_dir.mkdir(parents=True, exist_ok=True)
    return bam_dir
