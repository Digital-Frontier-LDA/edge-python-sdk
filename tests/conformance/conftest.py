"""Fixtures shared across the conformance suite (SPEC §9.2).

Tests are parametrized over both providers via the `client` fixture. Each
provider uses a distinct base URL so respx mocks can be unambiguous.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
import respx

from edge_provider_sdk import EdgeClient

LATITUDE_BASE_URL = "https://api.latitude.sh"
DF_BASE_URL = "https://df.test/api/v1"


@pytest.fixture
def respx_mock() -> Iterator[respx.MockRouter]:
    """Per-test respx router scoped to *both* provider hostnames.

    `assert_all_called=False` because not every test exercises every endpoint
    on the router; individual tests assert their own routes were hit.
    """
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as router:
        yield router


@pytest.fixture(params=["latitude", "digital-frontier"])
def provider(request: pytest.FixtureRequest) -> str:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture
def base_url(provider: str) -> str:
    return LATITUDE_BASE_URL if provider == "latitude" else DF_BASE_URL


@pytest.fixture
def client(provider: str, base_url: str) -> EdgeClient:
    """An `EdgeClient` configured for whichever provider this parametrization picked."""
    kwargs: dict[str, object] = {"provider": provider, "bearer": "fake-token"}
    if provider == "digital-frontier":
        kwargs["base_url"] = base_url
    return EdgeClient(**kwargs)  # type: ignore[arg-type]
