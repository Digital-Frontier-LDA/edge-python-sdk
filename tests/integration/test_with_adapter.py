"""End-to-end integration against a real Latitude-shaped adapter (SPEC §9.3).

Gated by `EDGE_PROVIDER_INTEGRATION=1` because it requires a running
`latitude-api-adapter` instance (typically via docker-compose: CockroachDB +
Redis + the adapter image). Casual contributors and CI by default skip
this module so they don't need Docker.

To run locally:

    docker compose -f tests/integration/docker-compose.yml up -d
    export EDGE_PROVIDER_INTEGRATION=1
    export EDGE_PROVIDER_ADAPTER_URL=http://localhost:3000/api/v1
    export EDGE_PROVIDER_ADAPTER_BEARER=df_test_xxx
    uv run pytest tests/integration/ -v

The compose file isn't shipped yet — that lands in step 6 of SPEC.md §13
alongside the sync-upstream and release workflows. For now this file
documents the contract and skips cleanly.
"""

from __future__ import annotations

import os
import uuid

import pytest

from edge_python_sdk import EdgeClient

INTEGRATION_GATE = os.environ.get("EDGE_PROVIDER_INTEGRATION") == "1"
ADAPTER_URL = os.environ.get("EDGE_PROVIDER_ADAPTER_URL", "")
ADAPTER_BEARER = os.environ.get("EDGE_PROVIDER_ADAPTER_BEARER", "")


pytestmark = pytest.mark.skipif(
    not INTEGRATION_GATE,
    reason="EDGE_PROVIDER_INTEGRATION=1 not set — see test_with_adapter.py docstring",
)


@pytest.fixture
def df_client() -> EdgeClient:
    if not ADAPTER_URL or not ADAPTER_BEARER:
        pytest.fail(
            "EDGE_PROVIDER_INTEGRATION=1 requires EDGE_PROVIDER_ADAPTER_URL "
            "and EDGE_PROVIDER_ADAPTER_BEARER to be set."
        )
    return EdgeClient(
        provider="digital-frontier",
        base_url=ADAPTER_URL,
        bearer=ADAPTER_BEARER,
    )


def test_catalog_returns_non_empty_lists(df_client: EdgeClient) -> None:
    """A freshly-booted adapter must populate its catalog endpoints."""
    sites = df_client.catalog.sites()
    plans = df_client.catalog.plans()
    oses = df_client.catalog.os()
    assert sites, "adapter returned no /regions — seed data missing?"
    assert plans, "adapter returned no /plans"
    assert oses, "adapter returned no /plans/operating_systems"


def test_create_then_delete_server(df_client: EdgeClient) -> None:
    """Smoke-test the create/destroy cycle against a live adapter."""
    sites = df_client.catalog.sites()
    plans = df_client.catalog.plans()
    oses = df_client.catalog.os()

    # Use the first available value from each catalog. The adapter is
    # expected to accept its own slugs even if they don't match Latitude's.
    hostname = f"edge-it-{uuid.uuid4().hex[:8]}"
    created = df_client.servers.create(
        data={
            "type": "servers",
            "attributes": {
                "project": os.environ.get("EDGE_PROVIDER_PROJECT", "default"),
                "plan": plans[0],
                "site": sites[0],
                "operating_system": oses[0],
                "hostname": hostname,
            },
        }
    )
    server_id = created.data.id  # type: ignore[union-attr]
    try:
        assert server_id
    finally:
        df_client.servers.destroy(server_id=server_id)
