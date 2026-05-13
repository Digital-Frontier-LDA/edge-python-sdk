"""Catalog cache + refresh behavior (SPEC §2.3).

These tests exercise `Catalog` directly with a fake SDK stub so they can
assert *exactly* how many times the underlying SDK is called. No HTTP, no
respx — that's covered by the conformance suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from edge_provider_sdk.catalog import Catalog


@dataclass
class _Attrs:
    slug: str | None = None


@dataclass
class _RegionsItem:
    attributes: _Attrs


@dataclass
class _RegionsPage:
    data: list[_RegionsItem]


@dataclass
class _RegionsResponse:
    result: _RegionsPage


@dataclass
class _PlanItem:
    attributes: _Attrs


@dataclass
class _PlansResponse:
    data: list[_PlanItem]


@dataclass
class _OsItem:
    attributes: _Attrs


@dataclass
class _OsInnerPage:
    data: list[_OsItem]


@dataclass
class _OsOuterPage:
    data: list[_OsInnerPage]


@dataclass
class _OsResponse:
    result: _OsOuterPage


@dataclass
class _AccessorStub:
    name: str
    payload: Any
    call_count: int = 0

    def list(self, **_kwargs: Any) -> Any:
        self.call_count += 1
        return self.payload


@dataclass
class _SdkStub:
    regions: _AccessorStub = field(
        default_factory=lambda: _AccessorStub(
            "regions",
            _RegionsResponse(_RegionsPage([_RegionsItem(_Attrs("alpha")), _RegionsItem(_Attrs("beta"))])),
        )
    )
    plans: _AccessorStub = field(
        default_factory=lambda: _AccessorStub(
            "plans",
            _PlansResponse([_PlanItem(_Attrs("plan-a")), _PlanItem(_Attrs("plan-b"))]),
        )
    )
    operating_systems: _AccessorStub = field(
        default_factory=lambda: _AccessorStub(
            "operating_systems",
            _OsResponse(
                _OsOuterPage(
                    [_OsInnerPage([_OsItem(_Attrs("os-a")), _OsItem(_Attrs("os-b"))])]
                )
            ),
        )
    )


STATIC_LATITUDE_SITES = ("ASH", "BUE", "CHI")


def test_latitude_sites_are_static_and_do_not_call_sdk() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="latitude", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)

    assert cat.sites() == ["ASH", "BUE", "CHI"]
    assert sdk.regions.call_count == 0  # static list — no network

    # Second call still no network.
    cat.sites()
    assert sdk.regions.call_count == 0


def test_latitude_refresh_does_not_invalidate_static_sites() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="latitude", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)
    _ = cat.sites()

    cat.refresh()
    # sites() must still be static after refresh per SPEC §2.3.
    assert cat.sites() == ["ASH", "BUE", "CHI"]
    assert sdk.regions.call_count == 0


def test_latitude_plans_and_os_are_cached() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="latitude", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)

    assert cat.plans() == ["plan-a", "plan-b"]
    assert cat.plans() == ["plan-a", "plan-b"]
    assert sdk.plans.call_count == 1  # cached after first call

    assert cat.os() == ["os-a", "os-b"]
    assert cat.os() == ["os-a", "os-b"]
    assert sdk.operating_systems.call_count == 1


def test_latitude_refresh_invalidates_plans_and_os() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="latitude", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)
    _ = cat.plans()
    _ = cat.os()

    cat.refresh()
    _ = cat.plans()
    _ = cat.os()
    assert sdk.plans.call_count == 2
    assert sdk.operating_systems.call_count == 2


def test_digital_frontier_sites_call_regions() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="digital-frontier", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)

    assert cat.sites() == ["alpha", "beta"]
    assert sdk.regions.call_count == 1

    # Cached.
    cat.sites()
    assert sdk.regions.call_count == 1


def test_digital_frontier_refresh_invalidates_everything() -> None:
    sdk = _SdkStub()
    cat = Catalog(provider="digital-frontier", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)
    _ = cat.sites()
    _ = cat.plans()
    _ = cat.os()

    cat.refresh()
    _ = cat.sites()
    _ = cat.plans()
    _ = cat.os()
    assert sdk.regions.call_count == 2
    assert sdk.plans.call_count == 2
    assert sdk.operating_systems.call_count == 2


def test_returned_lists_are_defensive_copies() -> None:
    """Mutating a returned list must not corrupt the cache."""
    sdk = _SdkStub()
    cat = Catalog(provider="digital-frontier", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)

    first = cat.plans()
    first.clear()  # caller-side mutation

    second = cat.plans()
    assert second == ["plan-a", "plan-b"]
    assert sdk.plans.call_count == 1  # still cached


def test_handles_empty_responses() -> None:
    """A provider with an empty catalog returns []."""
    sdk = _SdkStub(
        regions=_AccessorStub("regions", _RegionsResponse(_RegionsPage([]))),
        plans=_AccessorStub("plans", _PlansResponse([])),
        operating_systems=_AccessorStub(
            "operating_systems", _OsResponse(_OsOuterPage([_OsInnerPage([])]))
        ),
    )
    cat = Catalog(provider="digital-frontier", sdk=sdk, static_sites=STATIC_LATITUDE_SITES)
    assert cat.sites() == []
    assert cat.plans() == []
    assert cat.os() == []


@pytest.mark.parametrize("provider", ["latitude", "digital-frontier"])
def test_handles_none_response(provider: str) -> None:
    """An SDK returning None (e.g. 204) must not blow up — empty list instead."""
    sdk = _SdkStub(
        regions=_AccessorStub("regions", None),
        plans=_AccessorStub("plans", None),
        operating_systems=_AccessorStub("operating_systems", None),
    )
    cat = Catalog(provider=provider, sdk=sdk, static_sites=STATIC_LATITUDE_SITES)  # type: ignore[arg-type]

    if provider == "latitude":
        assert cat.sites() == list(STATIC_LATITUDE_SITES)
    else:
        assert cat.sites() == []
    assert cat.plans() == []
    assert cat.os() == []
