"""Public model namespace — re-exports of types from the patched `_generated/` SDK.

`_generated/` is an internal namespace (see SPEC.md §5). This module is the
stable public surface SPEC.md §3 calls for. Lazy `__getattr__` delegates to the
generated module so we preserve its import-on-access behavior for ~700 types.
"""

from __future__ import annotations

from typing import Any

from edge_provider_sdk._generated import models as _generated_models

__all__ = list(_generated_models.__all__)


def __getattr__(name: str) -> Any:
    return getattr(_generated_models, name)


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
