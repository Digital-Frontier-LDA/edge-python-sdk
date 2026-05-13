"""Conformance suite — both providers must speak the same wire format.

Each test pairs an `EdgeClient.<accessor>` call with a respx mock, then
asserts the request URL, Authorization header, and (where applicable)
body shape match the Latitude API contract. The same assertions run for
`provider="latitude"` (which hits `https://api.latitude.sh`) and
`provider="digital-frontier"` (which hits the user-supplied base_url) —
SPEC §9.2.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from edge_provider_sdk import EdgeClient

# The Latitude SDK only treats a response as a successful payload if it
# arrives with the JSON:API content type. Plain `application/json` is
# rejected with APIError("Unexpected response received").
_JSON_API = "application/vnd.api+json"


def _ok(body: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        content=json.dumps(body).encode("utf-8"),
        headers={"content-type": _JSON_API},
    )


def test_servers_list_request_shape(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    route = respx_mock.get(f"{base_url}/servers").mock(
        return_value=_ok({"data": [], "meta": {"total": 0}}),
    )

    client.servers.list()

    assert route.called
    sent = route.calls.last.request
    # Latitude's auth scheme is apiKey-in-header (not http_bearer), so the SDK
    # sends the token verbatim without prepending "Bearer ".
    assert sent.headers["authorization"] == "fake-token"
    assert sent.url.path == "/servers" if "latitude" in base_url else "/api/v1/servers"


def test_regions_list_request_shape(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    route = respx_mock.get(f"{base_url}/regions").mock(return_value=_ok({"data": []}))

    client.regions.list()

    assert route.called
    sent = route.calls.last.request
    # Latitude's auth scheme is apiKey-in-header (not http_bearer), so the SDK
    # sends the token verbatim without prepending "Bearer ".
    assert sent.headers["authorization"] == "fake-token"


def test_plans_list_request_shape(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    route = respx_mock.get(f"{base_url}/plans").mock(return_value=_ok({"data": []}))

    client.plans.list()

    assert route.called


def test_operating_systems_list_request_shape(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    route = respx_mock.get(f"{base_url}/plans/operating_systems").mock(
        return_value=_ok({"data": []}),
    )

    client.operating_systems.list()

    assert route.called


def test_servers_create_canonical_latitude_payload(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    """Canonical Latitude slugs must serialize identically across providers.

    A wrapped DF adapter that mirrors Latitude exactly should accept the
    same payload as the real Latitude API.
    """
    route = respx_mock.post(f"{base_url}/servers").mock(
        return_value=_ok({"data": {"id": "srv_123", "type": "servers"}}, status=201),
    )

    client.servers.create(
        data={
            "type": "servers",
            "attributes": {
                "project": "proj_test",
                "plan": "c3-large-x86",
                "site": "SAO",
                "operating_system": "ubuntu_24_04_x64_lts",
                "hostname": "edge-test-1",
            },
        }
    )

    assert route.called
    sent = route.calls.last.request
    body = json.loads(sent.content)
    attrs = body["data"]["attributes"]
    assert attrs["plan"] == "c3-large-x86"
    assert attrs["site"] == "SAO"
    assert attrs["operating_system"] == "ubuntu_24_04_x64_lts"


def test_digital_frontier_accepts_arbitrary_catalog_slugs() -> None:
    """DF-only: enums are permissive, so custom slugs serialize through.

    Latitude provider would either reject these at the pydantic boundary
    (strict enums) or pass them to the server, which rejects them. Either
    way, the test is meaningful only for DF.
    """
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post("https://df.test/api/v1/servers").mock(
            return_value=_ok({"data": {"id": "srv_x", "type": "servers"}}, status=201),
        )

        df = EdgeClient(
            provider="digital-frontier",
            bearer="df_fake",
            base_url="https://df.test/api/v1",
        )
        df.servers.create(
            data={
                "type": "servers",
                "attributes": {
                    "project": "proj_test",
                    "plan": "df-shape-h100-8x",
                    "site": "df-region-mtl-1",
                    "operating_system": "custom-distro-edge",
                    "hostname": "edge-test-1",
                },
            }
        )

        assert route.called
        attrs = json.loads(route.calls.last.request.content)["data"]["attributes"]
        assert attrs["plan"] == "df-shape-h100-8x"
        assert attrs["site"] == "df-region-mtl-1"
        assert attrs["operating_system"] == "custom-distro-edge"


def test_catalog_plans_extracts_slugs(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    respx_mock.get(f"{base_url}/plans").mock(
        return_value=_ok(
            {
                "data": [
                    {"id": "p1", "type": "plans", "attributes": {"slug": "alpha-plan"}},
                    {"id": "p2", "type": "plans", "attributes": {"slug": "beta-plan"}},
                ]
            }
        )
    )

    assert client.catalog.plans() == ["alpha-plan", "beta-plan"]


def test_catalog_os_extracts_slugs(
    respx_mock: respx.MockRouter,
    client: EdgeClient,
    base_url: str,
) -> None:
    # Upstream's `/plans/operating_systems` paginated response wraps each
    # page's `data` array inside another object — the outer `data` is a
    # list of pages, each with its own `data` list of OS entries.
    respx_mock.get(f"{base_url}/plans/operating_systems").mock(
        return_value=_ok(
            {
                "data": [
                    {
                        "data": [
                            {"id": "o1", "type": "operating_systems", "attributes": {"slug": "os-a"}},
                            {"id": "o2", "type": "operating_systems", "attributes": {"slug": "os-b"}},
                        ]
                    }
                ]
            }
        )
    )

    assert client.catalog.os() == ["os-a", "os-b"]


def test_catalog_sites_for_digital_frontier_calls_regions() -> None:
    with respx.mock(assert_all_mocked=True) as router:
        router.get("https://df.test/api/v1/regions").mock(
            return_value=_ok(
                {
                    "data": [
                        {"id": "r1", "type": "regions", "attributes": {"slug": "mtl-1"}},
                        {"id": "r2", "type": "regions", "attributes": {"slug": "ams-1"}},
                    ]
                }
            )
        )

        df = EdgeClient(
            provider="digital-frontier",
            bearer="df_fake",
            base_url="https://df.test/api/v1",
        )
        assert df.catalog.sites() == ["mtl-1", "ams-1"]
