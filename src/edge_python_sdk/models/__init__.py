"""Public model namespace — re-exports of types from the patched `_generated/` SDK.

`_generated/` is an internal namespace (see SPEC.md §5). This module is the
stable public surface SPEC.md §3 calls for. Lazy `__getattr__` delegates to the
generated module so we preserve its import-on-access behavior for ~700 types,
and so a bare source checkout (where `_generated/` is gitignored until
`scripts/apply-patches.sh` runs) can still import this module successfully.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


def _generated() -> Any:
    return import_module("edge_python_sdk._generated.models")


def __getattr__(name: str) -> Any:
    if name == "__all__":
        all_list = list(_generated().__all__)
        globals()["__all__"] = all_list
        return all_list
    return getattr(_generated(), name)


def __dir__() -> list[str]:
    return sorted(set(__getattr__("__all__")) | set(globals()))
