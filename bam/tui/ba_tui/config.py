from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_ENDPOINTS = ["Local", "I Drive", "MSD CEPH", "RFS", "HDD1"]
DEFAULT_ROLES = ["PI", "Students", "Others"]
DEFAULT_FORMATS = ["tiff", "zarr", "hdf5", "nd2", "czi", "ome-tiff", "other"]


def load_dataset_format_options() -> list[tuple[str, str]]:
    options = []
    for name in DEFAULT_FORMATS:
        if name == "ome-tiff":
            label = "OME-TIFF"
        elif name == "other":
            label = "Other"
        else:
            label = name.upper()
        options.append((label, name))
    return options


def load_endpoint_options() -> list[tuple[str, str]]:
    """Load endpoint options from config file or use defaults."""
    config_path = Path.home() / ".config" / "bam" / "endpoints.yaml"
    endpoints = DEFAULT_ENDPOINTS.copy()

    if config_path.exists():
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "endpoints" in data:
                    endpoints = data["endpoints"]
                elif isinstance(data, list):
                    endpoints = data
        except Exception:
            pass  # Use defaults on error

    # Convert to tuple format and add "Other" option
    options = [(name, name) for name in endpoints]
    options.append(("Other", "Other"))
    return options


def load_role_options() -> list[tuple[str, str]]:
    """Load collaborator role options from config file or use defaults."""
    config_path = Path.home() / ".config" / "bam" / "roles.yaml"
    roles = DEFAULT_ROLES.copy()

    if config_path.exists():
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "roles" in data:
                    roles = data["roles"]
                elif isinstance(data, list):
                    roles = data
        except Exception:
            pass

    normalized = set()
    options: list[tuple[str, str]] = []
    for name in roles:
        raw = str(name).strip()
        if not raw:
            continue
        key = raw.lower()
        if key in ("other", "others"):
            key = "other"
            raw = "Other"
        if key in normalized:
            continue
        normalized.add(key)
        options.append((raw, raw))
    if "other" not in normalized:
        options.append(("Other", "Other"))
    return options
