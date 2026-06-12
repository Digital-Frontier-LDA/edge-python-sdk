"""Module-level smoke tests for `edge_python_sdk` packaging.

Construction + behavior tests live in `test_client_construction.py`.
"""

from __future__ import annotations

from importlib import metadata

import edge_python_sdk


def test_version_is_exported() -> None:
    # __version__ is sourced from installed package metadata so it can't drift
    # from pyproject.toml. Asserting equality with metadata locks in that
    # contract without hardcoding a specific version string.
    assert edge_python_sdk.__version__ == metadata.version("edge-python-sdk")


def test_upstream_version_is_exported() -> None:
    assert edge_python_sdk.upstream_version == "3.0.5"


def test_top_level_exports() -> None:
    assert hasattr(edge_python_sdk, "EdgeClient")
    assert edge_python_sdk.SUPPORTED_PROVIDERS == ("latitude", "digital-frontier")


def test_models_namespace_reexports_errors() -> None:
    # Regression for the 0.1.0 bug where edge_python_sdk.models was an empty
    # placeholder. SPEC.md §3 designates this module as the stable public
    # surface for the patched _generated/ SDK; vanilla-shaped consumers expect
    # the standard error classes to import from here.
    from edge_python_sdk.models import (
        APIError,
        LatitudeshError,
        ResponseValidationError,
    )

    assert APIError.__name__ == "APIError"
    assert ResponseValidationError.__name__ == "ResponseValidationError"
    assert LatitudeshError.__name__ == "LatitudeshError"


def test_models_namespace_publishes_all() -> None:
    from edge_python_sdk import models

    assert "APIError" in models.__all__
    assert "ResponseValidationError" in models.__all__
    assert "LatitudeshError" in models.__all__
