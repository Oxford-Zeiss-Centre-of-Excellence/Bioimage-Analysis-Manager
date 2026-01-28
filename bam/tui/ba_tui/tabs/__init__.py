"""Tab composition helpers."""
from .admin import compose_admin_tab
from .hub import compose_hub_tab
from .idea import compose_idea_tab
from .log import compose_log_tab
from .outputs import compose_outputs_tab
from .science import compose_science_tab
from .setup import compose_setup_tab

# Legacy exports for backward compatibility
from .artifact import compose_artifact_tab
from .init import compose_init_tab
from .manifest import compose_manifest_tab

__all__ = [
    # New tabs
    "compose_setup_tab",
    "compose_science_tab",
    "compose_admin_tab",
    "compose_outputs_tab",
    "compose_hub_tab",
    "compose_log_tab",
    "compose_idea_tab",
    # Legacy tabs
    "compose_init_tab",
    "compose_artifact_tab",
    "compose_manifest_tab",
]
