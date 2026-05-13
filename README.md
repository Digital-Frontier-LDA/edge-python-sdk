# edge-provider-sdk

> **Status: pre-release scaffolding (v0.1.0 in progress).** API surface is frozen
> per [`SPEC.md`](./SPEC.md); patches and wrapper not yet implemented.

A single Python client for multiple Latitude-shaped compute providers. Wraps the
upstream [`latitudesh-python-sdk`](https://pypi.org/project/latitudesh-python-sdk/)
(v3.0.5), removes client-side strict-enum validation for catalog fields
(sites/plans/operating systems), and selects a backend provider at construction time.

Modeled on LiteLLM's "1 API, N providers" approach — adapted for stateful bare-metal compute.

## Why this exists

- The upstream SDK ships with `(str, Enum)` classes for site/plan/OS slugs. Any
  provider whose catalog differs from Latitude's (a self-hosted adapter, a
  fork, a regional reseller) gets rejected at the SDK layer before the request
  reaches the server.
- We patch those seven enums to be permissive type aliases — any string passes
  through to the API, which is the only authority on what's actually valid.
- Strict validation is preserved for `provider="latitude"` via runtime
  validation against the original enum values.

## Installation

```bash
pip install edge-provider-sdk
```

## Quickstart

```python
from edge_provider_sdk import EdgeClient

# Latitude direct (strict enums enforced where upstream enforces them)
client = EdgeClient(provider="latitude", bearer="lt_...")

# Digital Frontier adapter (Latitude-shaped, any URL)
client = EdgeClient(
    provider="digital-frontier",
    base_url="https://df.example.com/api/v1",
    bearer="df_...",
)

# Operations are identical to upstream latitudesh-python-sdk
server = client.servers.create(...)

# Catalog accessor — new in this package
client.catalog.sites()   # list[str]
client.catalog.plans()   # list[str]
client.catalog.os()      # list[str]
```

See [`docs/quickstart.md`](./docs/quickstart.md) for a full walkthrough.

## Upstream version

This release wraps **`latitudesh-python-sdk==3.0.5`**. Wrapper versioning is
independent of upstream — see [`SPEC.md` §6](./SPEC.md#6-versioning-policy).

```python
import edge_provider_sdk
edge_provider_sdk.__version__         # "0.1.0"
edge_provider_sdk.upstream_version    # "3.0.5"
```

## Migrating from `latitudesh-python-sdk`

The only API difference is the constructor. See
[`docs/upgrading-from-latitudesh.md`](./docs/upgrading-from-latitudesh.md).

## Development

The patched SDK lives in `src/edge_provider_sdk/_generated/` (gitignored, built
from `patches/` against the pinned upstream tarball).

```bash
# One-time: build the patched _generated/ tree
./scripts/apply-patches.sh

# Standard workflow
uv sync
uv run pytest
uv run ruff check
uv run mypy src
```

See [`SPEC.md`](./SPEC.md) for the full design document.

## License

Apache-2.0 — matches upstream.
