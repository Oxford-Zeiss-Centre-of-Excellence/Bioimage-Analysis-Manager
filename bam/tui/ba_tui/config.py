from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Cache for loaded configuration
_config_cache: dict[str, Any] | None = None


def load_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load configuration from defaults, system config, and project config.

    Priority (highest to lowest):
    1. Project-level: <project>/.bam/config.yaml
    2. System-wide: ~/.bam/config.yaml
    3. Defaults: config_defaults.yaml
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None:
        return _config_cache

    # Load defaults from package
    defaults_path = Path(__file__).parent / "config_defaults.yaml"
    config = {}

    if defaults_path.exists():
        try:
            with open(defaults_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Load system-wide config (~/.bam/config.yaml)
    system_config_path = Path.home() / ".bam" / "config.yaml"
    if system_config_path.exists():
        try:
            with open(system_config_path) as f:
                system_config = yaml.safe_load(f) or {}
                config.update(system_config)
        except Exception:
            pass

    # Load project-level config (<project>/.bam/config.yaml)
    if project_root:
        project_config_path = project_root / ".bam" / "config.yaml"
        if project_config_path.exists():
            try:
                with open(project_config_path) as f:
                    project_config = yaml.safe_load(f) or {}
                    config.update(project_config)
            except Exception:
                pass

    _config_cache = config
    return config


def get_config_list(key: str, project_root: Path | None = None) -> list[Any]:
    """Get a configuration list by key."""
    config = load_config(project_root)
    return config.get(key, [])


def get_config_options(
    key: str, project_root: Path | None = None, add_other: bool = False
) -> list[tuple[str, str]]:
    """Convert config list to select options format.

    Handles both simple lists (strings) and dict format with label/value.
    """
    items = get_config_list(key, project_root)
    options = []

    for item in items:
        if isinstance(item, dict):
            label = item.get("label", "")
            value = item.get("value", label)
            options.append((label, value))
        elif isinstance(item, str):
            options.append((item, item))

    if add_other and not any(v.lower() == "other" for _, v in options):
        options.append(("Other", "Other"))

    return options


# Convenience functions for specific configs
def load_clusters(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Load cluster options."""
    return get_config_options("clusters", project_root, add_other=True)


def load_compute_locations(project_root: Path | None = None) -> list[str]:
    """Load compute location options."""
    return get_config_list("compute_locations", project_root)


def load_endpoint_options(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Load endpoint options."""
    return get_config_options("endpoints", project_root, add_other=True)


def load_dataset_format_options(
    project_root: Path | None = None,
) -> list[tuple[str, str]]:
    """Load data format options."""
    items = get_config_list("data_formats", project_root)
    options = []
    for name in items:
        if name == "ome-tiff":
            label = "OME-TIFF"
        elif name == "other":
            label = "Other"
        else:
            label = name.upper()
        options.append((label, name))
    return options


def load_role_options(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Load collaborator role options."""
    return get_config_options("collaborator_roles", project_root, add_other=True)


def load_task_categories(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Load task category options."""
    return get_config_options("task_categories", project_root)


def load_task_subcategories(
    category: str | None = None, project_root: Path | None = None
) -> list[tuple[str, str]]:
    """Load task subcategory options for a specific category.

    Args:
        category: The category value to get subcategories for (e.g., 'Development', 'Execution')
        project_root: Optional project root path for config loading

    Returns:
        List of (label, value) tuples for subcategories, or empty list if category has no subcategories
    """
    if not category:
        return []

    categories = get_config_list("task_categories", project_root)

    for cat in categories:
        if isinstance(cat, dict):
            cat_value = cat.get("value", "")
            # Match on value (exact match first, then case-insensitive)
            if cat_value == category or cat_value.lower() == category.lower():
                subcats = cat.get("subcategories", [])
                if subcats:
                    options = []
                    for subcat in subcats:
                        if isinstance(subcat, dict):
                            label = subcat.get("label", "")
                            value = subcat.get("value", label)
                            options.append((label, value))
                    return options
                return []

    return []


def category_has_subcategories(
    category: str | None = None, project_root: Path | None = None
) -> bool:
    """Check if a category has subcategories defined.

    Args:
        category: The category value to check
        project_root: Optional project root path for config loading

    Returns:
        True if the category has subcategories, False otherwise
    """
    if not category:
        return False

    subcats = load_task_subcategories(category, project_root)
    return len(subcats) > 0
