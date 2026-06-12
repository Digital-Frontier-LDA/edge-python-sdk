"""EdgeClient — wrapper around the patched latitudesh-python-sdk.

See SPEC.md §2 (Public API surface) and §3 (Provider contract).

For `provider="latitude"`, EdgeClient instantiates the unpatched upstream
`latitudesh_python_sdk.Latitudesh` directly — strict enums and faithful
upstream behavior. For `provider="digital-frontier"`, it instantiates the
patched `edge_python_sdk._generated.Latitudesh` so any region/plan/OS
string passes through. The two SDKs coexist because they live under
different module names (see `scripts/apply-patches.sh`).

`EdgeClient` does not proxy individual operations: attribute access is
forwarded to the underlying SDK via `__getattr__`, so `client.servers`,
`client.projects`, `client.ssh_keys`, etc. behave exactly as upstream
documents them.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .catalog import Catalog
from .providers import SUPPORTED_PROVIDERS, ProviderName, resolve_base_url


class EdgeClient:
    """Single client for multiple Latitude-shaped compute providers."""

    def __init__(
        self,
        *,
        provider: ProviderName,
        bearer: str | Callable[[], str | None] | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"unknown provider {provider!r}; supported: {SUPPORTED_PROVIDERS}"
            )

        server_url = resolve_base_url(provider, base_url)

        sdk_cls, original_sites = _load_provider_backend(provider)
        self._sdk: Any = sdk_cls(bearer=bearer, server_url=server_url, **kwargs)
        self._provider: ProviderName = provider
        self._catalog = Catalog(
            provider=provider,
            sdk=self._sdk,
            static_sites=original_sites,
        )

    @property
    def provider(self) -> ProviderName:
        return self._provider

    @property
    def catalog(self) -> Catalog:
        return self._catalog

    def __getattr__(self, name: str) -> Any:
        # Called only when the attribute isn't on the EdgeClient itself —
        # forwards operation accessors (servers, projects, ssh_keys, …) to
        # the underlying SDK. The leading-underscore guard prevents infinite
        # recursion if `_sdk` is touched before __init__ completes.
        if name.startswith("_"):
            raise AttributeError(name)
        sdk = self.__dict__.get("_sdk")
        if sdk is None:
            raise AttributeError(name)
        return getattr(sdk, name)


def _load_provider_backend(provider: ProviderName) -> tuple[type, tuple[str, ...]]:
    """Resolve `(SDK class, canonical Latitude site list)` for a provider.

    Imports are lazy so a user who only ever uses `provider="latitude"` doesn't
    pay the cost of loading the patched `_generated/` tree, and vice versa.
    """
    if provider == "latitude":
        from latitudesh_python_sdk import Latitudesh as _UpstreamSdk
        from latitudesh_python_sdk.models.create_serverop import (
            CreateServerServersSite as _OriginalSiteEnum,
        )

        return _UpstreamSdk, tuple(m.value for m in _OriginalSiteEnum)

    if provider == "digital-frontier":
        from edge_python_sdk._generated import Latitudesh as _PatchedSdk
        from edge_python_sdk._generated.models.create_serverop import (
            _ORIGINAL_SITES,
        )

        return _PatchedSdk, tuple(_ORIGINAL_SITES)

    raise ValueError(f"unknown provider {provider!r}")
