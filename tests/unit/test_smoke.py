"""Module-level smoke tests for `edge_provider_sdk` packaging.

Construction + behavior tests live in `test_client_construction.py`.
"""

from __future__ import annotations

from importlib import metadata

import edge_provider_sdk


def test_version_is_exported() -> None:
    # __version__ is sourced from installed package metadata so it can't drift
    # from pyproject.toml. Asserting equality with metadata locks in that
    # contract without hardcoding a specific version string.
    assert edge_provider_sdk.__version__ == metadata.version("edge-provider-sdk")


def test_upstream_version_is_exported() -> None:
    assert edge_provider_sdk.upstream_version == "3.0.5"


def test_top_level_exports() -> None:
    assert hasattr(edge_provider_sdk, "EdgeClient")
    assert edge_provider_sdk.SUPPORTED_PROVIDERS == ("latitude", "digital-frontier")
