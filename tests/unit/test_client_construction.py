"""Construction-time behavior of `EdgeClient` — no network calls.

These tests instantiate the client against fake bearers and assert routing,
parameter validation, catalog wiring, and operation-accessor passthrough.
"""

from __future__ import annotations

import pytest

from edge_python_sdk import EdgeClient


def test_latitude_construction() -> None:
    client = EdgeClient(provider="latitude", bearer="lt_fake")

    assert client.provider == "latitude"
    # Latitude uses the unpatched upstream SDK so consumers see strict enums.
    assert type(client._sdk).__module__.startswith("latitudesh_python_sdk")
    # Operation accessors are forwarded via __getattr__.
    assert client.servers is client._sdk.servers
    assert client.projects is client._sdk.projects


def test_digital_frontier_construction() -> None:
    client = EdgeClient(
        provider="digital-frontier",
        bearer="df_fake",
        base_url="https://df.example.com/api/v1",
    )

    assert client.provider == "digital-frontier"
    # DF uses the patched _generated/ tree so all 7 enums are permissive.
    assert type(client._sdk).__module__.startswith("edge_python_sdk._generated")
    assert client.servers is client._sdk.servers


def test_digital_frontier_requires_base_url() -> None:
    with pytest.raises(ValueError, match="base_url"):
        EdgeClient(provider="digital-frontier", bearer="df_fake")


def test_digital_frontier_rejects_blank_base_url() -> None:
    with pytest.raises(ValueError, match="base_url"):
        EdgeClient(provider="digital-frontier", bearer="df_fake", base_url="   ")


def test_unknown_provider_rejected() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        EdgeClient(provider="bogus", bearer="x")  # type: ignore[arg-type]


def test_latitude_ignores_user_supplied_base_url() -> None:
    # SPEC §3 / §2.1: base_url is ignored for Latitude.
    client = EdgeClient(
        provider="latitude", bearer="lt_fake", base_url="https://will-be-ignored"
    )
    sdk_config = client._sdk.sdk_configuration
    assert "api.latitude.sh" in sdk_config.get_server_details()[0]


def test_catalog_sites_static_for_latitude() -> None:
    client = EdgeClient(provider="latitude", bearer="lt_fake")
    sites = client.catalog.sites()

    # 18 canonical Latitude sites from the original enum (SPEC §3, §4).
    assert len(sites) == 18
    assert "ASH" in sites
    assert "TYO2" in sites

    # Second call hits the cache and returns an equal list (defensive copy).
    again = client.catalog.sites()
    assert again == sites
    assert again is not sites  # defensive copy, not the cached reference


def test_catalog_static_sites_do_not_drift_between_sdks() -> None:
    """The patched `_ORIGINAL_SITES` must match the unpatched enum.

    If upstream adds/removes a site, our patch must be re-generated. This
    test catches that drift early instead of silently shipping a stale list.
    """
    from latitudesh_python_sdk.models.create_serverop import (
        CreateServerServersSite as UpstreamSiteEnum,
    )

    from edge_python_sdk._generated.models.create_serverop import _ORIGINAL_SITES

    upstream_values = tuple(m.value for m in UpstreamSiteEnum)
    assert tuple(_ORIGINAL_SITES) == upstream_values
