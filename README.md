# edge-python-sdk

[![CI](https://github.com/Digital-Frontier-LDA/edge-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Digital-Frontier-LDA/edge-python-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/edge-python-sdk.svg)](https://pypi.org/project/edge-python-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/edge-python-sdk.svg)](https://pypi.org/project/edge-python-sdk/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)

> **Status: released — `0.1.1` (alpha).** The wrapper, the three permissive-enum
> patches, and the conformance suite are implemented; the public API is frozen
> per [`SPEC.md`](./SPEC.md). Installable from
> [PyPI](https://pypi.org/project/edge-python-sdk/).

A single Python client for multiple Latitude-shaped compute providers. It wraps the
upstream [`latitudesh-python-sdk`](https://github.com/latitudesh/latitudesh-python-sdk)
(pinned at `3.0.5`), removes client-side strict-enum validation for catalog fields
(sites/plans/operating systems), and selects a backend provider at construction time.

Modeled on LiteLLM's "1 API, N providers" approach — adapted for stateful bare-metal compute.

## Why this exists — and how it relates to upstream

`edge-python-sdk` is **not a fork** of
[`latitudesh-python-sdk`](https://github.com/latitudesh/latitudesh-python-sdk), and
it is **not affiliated with or endorsed by Latitude.sh**. It is a thin wrapper that
depends on the upstream SDK as a pinned dependency, then builds and ships a lightly
*patched* copy of it. It exists to fix one specific limitation:

- **Upstream's catalog enums are closed.** The upstream SDK ships `(str, Enum)`
  classes for site/plan/OS slugs. Any provider whose catalog differs from
  Latitude's — a self-hosted adapter, a regional reseller, a Latitude-shaped
  gateway in front of another backend — gets rejected *at the SDK layer*, before
  the request ever reaches the server.
- **We make those seven enums permissive.** Three patches replace them with type
  aliases, so any string passes through to the API — which is the only authority
  on what's actually valid. Strict validation is still enforced for
  `provider="latitude"`: the real API rejects unknown values anyway, so the SDK
  staying strict there costs nothing.
- **One client, several backends.** `EdgeClient(provider=...)` selects the backend
  at construction time — `latitude` direct, or `digital-frontier` (any
  Latitude-shaped adapter at a URL you supply).

If you only ever talk to the real Latitude.sh API, **use the upstream SDK
directly** — this wrapper adds nothing for that case. Reach for `edge-python-sdk`
when you target a non-Latitude, Latitude-shaped backend, or want to switch between
several without changing call sites.

See **[`docs/comparison-with-upstream.md`](./docs/comparison-with-upstream.md)** for
the full rationale: the exact patches, the upstream-sync strategy, versioning, and
licensing/attribution.

## Installation

```bash
pip install edge-python-sdk
```

## Quickstart

```python
from edge_python_sdk import EdgeClient

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

## Provider behavior differences

`edge-python-sdk` gives you one API across providers — but the providers are not
identical infrastructure. A few response fields keep the same Latitude name and
JSON type, yet carry a value whose **nature differs** by provider. Anything not
listed here behaves identically across providers.

| Field | `provider="latitude"` (bare metal) | `provider="digital-frontier"` (Akash-backed) |
|---|---|---|
| `primary_ipv4` | A literal public IPv4, e.g. `203.0.113.7`. | A provider **gateway hostname**, e.g. `provider.m3a.eu-n-3.example.network` — an Akash deployment is reached through a provider gateway, not a dedicated inbound IP. |
| `primary_port` | The service's own listening port. | A **provider-assigned forwarded port**, e.g. `30713`, mapping to the container's internal port. |

Treat `primary_ipv4:primary_port` as an opaque `host:port` pair — never assume
`primary_ipv4` is an IP literal, or that `primary_port` is the port your service
declared. The `digital-frontier` adapter keeps the Latitude field names for
drop-in compatibility; the authoritative registry of divergences lives in the
adapter repo at
[`docs/provider-behavior.md`](https://github.com/Digital-Frontier-LDA/latitude-api-adapter/blob/main/docs/provider-behavior.md).

## Upstream version

This release wraps **`latitudesh-python-sdk==3.0.5`**. Wrapper versioning is
independent of upstream — see [`SPEC.md` §6](./SPEC.md#6-versioning-policy).

```python
import edge_python_sdk
edge_python_sdk.__version__         # "0.1.1"
edge_python_sdk.upstream_version    # "3.0.5"
```

## Migrating from `latitudesh-python-sdk`

The only API difference is the constructor. See
[`docs/upgrading-from-latitudesh.md`](./docs/upgrading-from-latitudesh.md).

## Development

The patched SDK lives in `src/edge_python_sdk/_generated/` (gitignored, built
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

The wrapper code in this repository is licensed under [Apache-2.0](./LICENSE).

The patched copy of `latitudesh-python-sdk` that ships inside the built wheel
remains under upstream's original **MIT License** (© 2025 Latitude.sh). The two
licenses are compatible; see
[`docs/comparison-with-upstream.md`](./docs/comparison-with-upstream.md#licensing--attribution)
for the attribution details.
