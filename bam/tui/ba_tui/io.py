from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import Manifest, ManifestValidationError, raise_validation_error


def load_manifest(path: Path) -> Manifest | None:
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    if not data:
        return None
    try:
        return Manifest.model_validate(data)
    except ValidationError as exc:
        raise_validation_error(exc)


def dump_manifest(path: Path, manifest: Manifest) -> None:
    payload: dict[str, Any] = manifest.model_dump(mode="json", exclude_none=True)
    yaml.safe_dump(payload, path.open("w"), sort_keys=False)
