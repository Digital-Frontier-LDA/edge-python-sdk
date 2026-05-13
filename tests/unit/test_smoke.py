"""Module-level smoke tests for `edge_provider_sdk` packaging.

Construction + behavior tests live in `test_client_construction.py`.
"""

from __future__ import annotations

import edge_provider_sdk


def test_version_is_exported() -> None:
    assert edge_provider_sdk.__version__ == "0.1.0"


def test_upstream_version_is_exported() -> None:
    assert edge_provider_sdk.upstream_version == "3.0.5"


def test_top_level_exports() -> None:
    assert hasattr(edge_provider_sdk, "EdgeClient")
    assert edge_provider_sdk.SUPPORTED_PROVIDERS == ("latitude", "digital-frontier")
