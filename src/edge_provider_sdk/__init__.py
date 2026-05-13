"""edge-provider-sdk — single Python client for Latitude-shaped compute providers.

See SPEC.md for the full design document.
"""

from __future__ import annotations

from importlib import metadata as _metadata

__version__ = "0.1.0"


def _read_upstream_version() -> str:
    """Resolve the installed `latitudesh-python-sdk` version.

    Falls back to the SPEC-pinned value if the upstream package isn't installed
    (e.g. running from a bare source checkout without `uv sync`).
    """
    try:
        return _metadata.version("latitudesh-python-sdk")
    except _metadata.PackageNotFoundError:
        return "3.0.5"


upstream_version: str = _read_upstream_version()

from .client import EdgeClient  # noqa: E402 — re-export below version constants
from .providers import SUPPORTED_PROVIDERS, ProviderName  # noqa: E402

__all__ = [
    "__version__",
    "upstream_version",
    "EdgeClient",
    "ProviderName",
    "SUPPORTED_PROVIDERS",
]
