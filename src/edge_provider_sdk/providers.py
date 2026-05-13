"""Provider registry — maps `provider=` strings to provider configurations.

See SPEC.md §3 (Provider contract).
"""

from __future__ import annotations

from typing import Final, Literal

ProviderName = Literal["latitude", "digital-frontier"]

SUPPORTED_PROVIDERS: Final[tuple[ProviderName, ...]] = ("latitude", "digital-frontier")

# Default base URL per provider. `None` means the caller must supply one.
PROVIDER_DEFAULT_BASE_URL: Final[dict[ProviderName, str | None]] = {
    "latitude": "https://api.latitude.sh",
    "digital-frontier": None,
}


def resolve_base_url(provider: ProviderName, base_url: str | None) -> str:
    """Pick the effective `server_url` for the chosen provider.

    - `provider="latitude"`: `base_url` is ignored; we always point at the real
      Latitude API. (SPEC §3.)
    - `provider="digital-frontier"`: `base_url` is required from the caller.
    """
    if provider == "latitude":
        return PROVIDER_DEFAULT_BASE_URL["latitude"]  # type: ignore[return-value]
    if base_url is None or not base_url.strip():
        raise ValueError(
            "provider='digital-frontier' requires a `base_url` "
            "(no default — adapters can live anywhere)."
        )
    return base_url
