"""Catalog accessor — returns the active provider's known site/plan/OS values.

See SPEC.md §2.3.

Caches are scoped to the `Catalog` instance (which is owned by `EdgeClient`).
There is no TTL; call `refresh()` to invalidate. For `provider="latitude"`,
`sites()` is a static mirror of the upstream enum and `refresh()` does not
re-fetch it (per SPEC §2.3).
"""

from __future__ import annotations

from typing import Any

from .providers import ProviderName


class Catalog:
    """Provider-aware accessor for site/plan/OS catalog values."""

    def __init__(
        self,
        provider: ProviderName,
        sdk: Any,
        static_sites: tuple[str, ...],
    ) -> None:
        self._provider: ProviderName = provider
        self._sdk = sdk
        self._static_sites: tuple[str, ...] = static_sites
        self._sites_cache: list[str] | None = None
        self._plans_cache: list[str] | None = None
        self._os_cache: list[str] | None = None

    def sites(self) -> list[str]:
        if self._sites_cache is not None:
            return list(self._sites_cache)
        if self._provider == "latitude":
            sites = list(self._static_sites)
        else:
            response = self._sdk.regions.list(page_size=100)
            sites = _extract_slugs_from_regions(response)
        self._sites_cache = sites
        return list(sites)

    def plans(self) -> list[str]:
        if self._plans_cache is not None:
            return list(self._plans_cache)
        response = self._sdk.plans.list()
        plans = _extract_slugs_from_plans(response)
        self._plans_cache = plans
        return list(plans)

    def os(self) -> list[str]:
        if self._os_cache is not None:
            return list(self._os_cache)
        response = self._sdk.operating_systems.list(page_size=100)
        oses = _extract_slugs_from_operating_systems(response)
        self._os_cache = oses
        return list(oses)

    def refresh(self) -> None:
        """Re-read catalog values from the network on the next access.

        For `provider="latitude"`, `sites()` is a static mirror and stays
        cached — the rest of the catalog is invalidated.
        """
        if self._provider != "latitude":
            self._sites_cache = None
        self._plans_cache = None
        self._os_cache = None


def _extract_slugs_from_regions(response: Any) -> list[str]:
    if response is None or response.result is None or response.result.data is None:
        return []
    return [r.attributes.slug for r in response.result.data if r.attributes and r.attributes.slug]


def _extract_slugs_from_plans(response: Any) -> list[str]:
    if response is None or response.data is None:
        return []
    return [p.attributes.slug for p in response.data if p.attributes and p.attributes.slug]


def _extract_slugs_from_operating_systems(response: Any) -> list[str]:
    if response is None or response.result is None or response.result.data is None:
        return []
    slugs: list[str] = []
    for page in response.result.data:
        if page.data is None:
            continue
        for entry in page.data:
            if entry.attributes and entry.attributes.slug:
                slugs.append(entry.attributes.slug)
    return slugs
