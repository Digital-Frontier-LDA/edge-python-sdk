# edge-provider-sdk — v0.1 Specification

> Status: **DRAFT**. Living design document. Sign-off triggers v0.1 scaffolding.
> Inspiration: LiteLLM (1 API, N providers) adapted for stateful bare-metal compute.

---

## 1. Purpose & scope

`edge-provider-sdk` is a public PyPI package providing a single Python client for
multiple Latitude-shaped compute providers. It wraps the upstream
`latitudesh-python-sdk` (a Speakeasy-generated SDK by latitudeshdev), removes
client-side strict-enum validation for catalog fields, and selects a backend
provider at construction time.

### In scope for v0.1
- Two providers: `latitude` (direct, `https://api.latitude.sh`) and `digital-frontier`
  (Latitude-shaped adapter at any user-supplied URL).
- Permissive enums for: site (3 enum classes), plan (1), operating system (3).
- A small `catalog` accessor that returns the provider's known site/plan/OS values.
- Conformance test suite both providers pass.
- Public PyPI release with semver, OIDC trusted-publishing, and a documented
  upgrade path from upstream `latitudesh-python-sdk`.

### Explicitly out of scope for v0.1
- Cross-provider routing (`routing="cheapest"`, fallback chains).
- Persistence of `(provider, server_id)` mappings — consumers track this.
- Cost tracking / price normalization.
- Direct-to-Akash provider (still goes through the DF adapter for now).
- Provider plugin extension points for third-party providers.

These belong in v0.2+ once v0.1 is stable on PyPI.

---

## 2. Public API surface

### 2.1 Constructor

```python
from edge_provider_sdk import EdgeClient

# Latitude direct (strict enums enforced where upstream enforces them)
client = EdgeClient(provider="latitude", bearer="lt_...")

# Digital Frontier adapter
client = EdgeClient(
    provider="digital-frontier",
    base_url="https://df.example.com/api/v1",
    bearer="df_...",
)
```

**Constructor parameters:**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `provider` | `Literal["latitude", "digital-frontier"]` | yes | More providers in v0.2+ |
| `bearer` | `str \| Callable[[], str]` | yes | Pass-through to upstream SDK |
| `base_url` | `str \| None` | required when `provider="digital-frontier"`; ignored otherwise | Adapter's `/api/v1` root |
| `client` / `async_client` | `httpx.Client \| AsyncClient` | optional | Pass-through |
| `retry_config` / `timeout_ms` / `debug_logger` | … | optional | Pass-through |

Anything else upstream accepts is also accepted via `**kwargs` and forwarded.

### 2.2 Operations — identical to upstream

`client.servers`, `client.projects`, `client.ssh_keys`, `client.plans`, `client.regions`,
`client.operating_systems` etc. behave **exactly** like upstream `latitudesh-python-sdk`
on the chosen `server_url`. We do not re-document operations here — see upstream docs.

The wrapper does not intercept, transform, or proxy these calls beyond `server_url`
selection and enum permissiveness.

### 2.3 Catalog accessor — new in this package

```python
client.catalog.sites()      # list[str]  — known site codes for this provider
client.catalog.plans()      # list[str]  — known plan slugs
client.catalog.os()         # list[str]  — known OS slugs
client.catalog.refresh()    # fetch fresh values from the provider's discovery endpoints
```

| Provider | `sites()` source | `plans()` source | `os()` source |
|---|---|---|---|
| `latitude` | Hardcoded list mirroring the upstream enum (18 values) | Calls `GET /plans` | Calls `GET /operating_systems` |
| `digital-frontier` | Calls `GET /regions` on the adapter | Calls `GET /plans` | Calls `GET /operating_systems` |

`refresh()` re-reads from the network (no-op for Latitude `sites()` since it's static).
Results are cached for the lifetime of the `EdgeClient` instance — no TTL in v0.1.

---

## 3. Provider contract

A provider is identified by a string registered in `edge_provider_sdk.providers`.
v0.1 ships two:

| `provider=` | Default `base_url` | Enum behavior | Catalog source for sites |
|---|---|---|---|
| `latitude` | `https://api.latitude.sh` | Upstream enums **still validate** (we don't loosen Latitude itself) | Static enum mirror |
| `digital-frontier` | None (required from caller) | All 7 enums **permissive** (accept any string) | `GET /regions` |

**Why Latitude stays strict:** the real Latitude API rejects unknown values
server-side anyway. Loosening the SDK there would only delay the error from
client to network round-trip with no benefit. We keep upstream behavior to be a
faithful passthrough.

**Permissive vs strict implementation:** the patched SDK lives in
`src/edge_provider_sdk/_generated/` (gitignored, built from `patches/`). Permissive
versions replace the seven `(str, Enum)` classes with type aliases:

```python
# Before (upstream)
class CreateServerServersSite(str, Enum):
    ASH = "ASH"
    BUE = "BUE"
    # ... 16 more

# After (patched)
CreateServerServersSite = str  # any string accepted; runtime validation by API
```

At runtime, the active provider is enforced via construction-time selection — when
`provider="latitude"`, the wrapper validates inputs against the original enum values
before passing them to the patched SDK; when `provider="digital-frontier"`, no
client-side validation runs.

---

## 4. Patches against upstream

Pinned upstream: **`latitudesh-python-sdk==3.0.5`**.

Three patch files, each targeting one logical concern:

| Patch | Files modified | Enum classes converted |
|---|---|---|
| `patches/0001-site-enum-permissive.patch` | `models/create_serverop.py`, `models/post_vpn_sessionop.py`, `models/create_virtual_networkop.py` | `CreateServerServersSite`, `PostVpnSessionVpnSessionsSite`, `CreateVirtualNetworkPrivateNetworksSite` |
| `patches/0002-plan-enum-permissive.patch` | `models/create_serverop.py` | `CreateServerServersPlan` |
| `patches/0003-os-enum-permissive.patch` | `models/create_serverop.py`, `models/create_server_reinstallop.py`, `models/update_server_deploy_configop.py` | `CreateServerServersOperatingSystem`, `CreateServerReinstallServersOperatingSystem`, `UpdateServerDeployConfigServersOperatingSystem` |

**Patch format:** `git format-patch` output, applied with `git apply` against an
unpacked upstream tarball.

**Original enum value preservation:** the patched SDK exports `_ORIGINAL_SITES`,
`_ORIGINAL_PLANS`, `_ORIGINAL_OS` constants holding the original enum members, so
the Latitude provider can still do strict validation.

---

## 5. Build flow

```
upstream tarball (pip download)
        │
        ▼
 scripts/apply-patches.sh
        │  (extract, apply 3 patches, rewrite import path)
        ▼
 src/edge_provider_sdk/_generated/   (gitignored)
        │
        ▼  imported by
 src/edge_provider_sdk/client.py     (EdgeClient wrapper)
```

**Why rewrite the import path:** to avoid collision when both `latitudesh-python-sdk`
and `edge-provider-sdk` are installed in the same environment, the patched module
is namespaced as `edge_provider_sdk._generated` internally, and re-exported only
through `EdgeClient` and `edge_provider_sdk.models`.

**Build script:** `scripts/apply-patches.sh` is idempotent. It pins the upstream
version, downloads via `pip download --no-deps --no-binary=:all:`, applies the
patches, and rewrites imports. CI runs it on every push.

---

## 6. Versioning policy

**Decided 2026-05-13 by quorum (codex-1, gemini-1 unanimous; see
`.planning/quorum/debates/2026-05-13-edge-provider-sdk-version-scheme.md`).**

- Public API follows **independent wrapper semver** — fully decoupled from
  upstream cadence.
- Wrapper version: `0.1.0`, `0.2.0`, `1.0.0`, … on `pyproject.toml`.
- Upstream version recorded in package metadata, **not** in the version string:
  ```toml
  [project]
  name = "edge-provider-sdk"
  version = "0.1.0"

  [tool.edge-provider-sdk]
  upstream-package = "latitudesh-python-sdk"
  upstream-version = "3.0.5"
  ```
- Runtime accessors:
  ```python
  edge_provider_sdk.__version__         # "0.1.0"
  edge_provider_sdk.upstream_version    # "3.0.5"
  ```
- README states the wrapped upstream version prominently.
- **Breaking changes** to `EdgeClient` trigger wrapper major bumps (`1.0.0` → `2.0.0`),
  independent of upstream major bumps.
- v0.1 ships as **`0.1.0`** (wrapper) wrapping upstream `3.0.5`.

### Alternatives considered and rejected

| Alternative | Reason rejected |
|---|---|
| `3.0.5+ep1` (PEP 440 local version) | PyPI Warehouse rejects local-version segments on public uploads (PEP 440). Dead on arrival. |
| `3.0.5.post1` (PEP 440 post-release) | Misuses `.postN` — PEP 440 reserves it for trivial post-release corrections, not feature-additive wrapper iterations. Misrepresents the wrapper as a post-release of upstream Latitude. |
| `edge-provider-sdk-3` v `0.1.0` (hybrid name) | Package-name churn per upstream major hurts `pip install edge-provider-sdk` discoverability. Only pays off if simultaneous parallel installs across upstream majors become a real requirement — not for v0.1. |

This pattern matches `mypy-extensions` (wraps mypy), `pytest-asyncio` (wraps pytest), and the broader wrapper-library ecosystem on PyPI.

---

## 7. CI / release automation

Three GitHub Actions workflows:

### `.github/workflows/ci.yml`
- Triggers: push, pull_request
- Matrix: Python 3.10, 3.11, 3.12, 3.13
- Steps: `apply-patches.sh` → `uv sync` → `ruff check` → `mypy` → `pytest tests/`
- Conformance tests run against:
  - `provider="latitude"`: mocked HTTP via `respx`
  - `provider="digital-frontier"`: a local `latitude-api-adapter` instance spun up via
    docker-compose (CockroachDB + Redis + adapter image)

### `.github/workflows/sync-upstream.yml`
- Trigger: daily cron + manual dispatch
- Steps:
  1. Read pinned upstream version from `pyproject.toml`
  2. `pip index versions latitudesh-python-sdk` → detect latest
  3. If newer: bump pin, run `apply-patches.sh`, run conformance
  4. If patches still apply cleanly and tests pass: open a PR titled
     `sync: bump upstream to <version>`
  5. If patches conflict: open a PR with the failed patch hunks for manual rebase

### `.github/workflows/release.yml`
- Trigger: GitHub release published from a `v*` tag
- Steps: build wheel + sdist → publish to PyPI via OIDC trusted publishing
- PyPI project: `edge-provider-sdk` — Trusted Publisher configured to this repo

---

## 8. Repository layout

```
edge-provider-sdk/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── sync-upstream.yml
│       └── release.yml
├── docs/
│   ├── quickstart.md
│   ├── providers.md
│   └── upgrading-from-latitudesh.md
├── patches/
│   ├── 0001-site-enum-permissive.patch
│   ├── 0002-plan-enum-permissive.patch
│   └── 0003-os-enum-permissive.patch
├── scripts/
│   ├── apply-patches.sh
│   └── refresh-upstream.sh
├── src/
│   └── edge_provider_sdk/
│       ├── __init__.py
│       ├── client.py
│       ├── providers.py
│       ├── catalog.py
│       ├── _generated/         # gitignored; built from patches
│       └── models/             # re-exports of permissive types
├── tests/
│   ├── conformance/
│   │   ├── test_servers.py
│   │   ├── test_projects.py
│   │   ├── test_ssh_keys.py
│   │   └── test_catalog.py
│   ├── unit/
│   │   ├── test_client_construction.py
│   │   └── test_enum_permissiveness.py
│   └── integration/
│       └── test_with_adapter.py    # spins up latitude-api-adapter
├── pyproject.toml
├── README.md
├── SPEC.md                          # this file
├── CHANGELOG.md
├── LICENSE                          # Apache-2.0 (matches upstream)
└── .gitignore
```

---

## 9. Testing strategy

### 9.1 Unit tests
- Construction validation (`provider` accepted, required `base_url`, etc.)
- Permissive-enum behavior: arbitrary strings pass through to the SDK
- Catalog cache behavior
- Pass-through of `**kwargs` to upstream `Latitudesh`

### 9.2 Conformance tests
- A **single suite** parameterized over both providers
- Each test exercises a Latitude SDK operation and asserts the request is well-formed
- Latitude: assertions match upstream wire format exactly
- DF: assertions match adapter's accepted shape (which is also Latitude shape)
- Tests use `respx` for HTTP mocking (Latitude) or a real adapter instance (DF)

### 9.3 Integration tests
- Boot a local `latitude-api-adapter` instance against CockroachDB + Redis
- Run end-to-end: create project → create ssh_key → create server → poll status → delete
- Gated by `EDGE_PROVIDER_INTEGRATION=1` env var so casual contributors don't need Docker

---

## 10. Documentation

`docs/` ships with:
- **`quickstart.md`** — install, instantiate both providers, do one create-server flow
- **`providers.md`** — provider matrix: which catalog entries each supports, validation behavior, link to upstream SDK docs
- **`upgrading-from-latitudesh.md`** — 1:1 migration guide. The constructor is the
  only API difference; everything else is identical.

README points at all three.

---

## 11. Open questions

These need answers **before** v0.1 ships, but **not** before scaffolding starts:

1. **~~PEP 440 version scheme.~~** ✅ RESOLVED 2026-05-13 — wrapper semver `0.1.0`
   (independent of upstream), upstream version in `[tool.edge-provider-sdk]`
   metadata. See §6 and quorum debate
   `.planning/quorum/debates/2026-05-13-edge-provider-sdk-version-scheme.md`.

2. **License.** Apache-2.0 matches upstream, but does upstream's NOTICE need
   attribution? Need to audit upstream license headers.

3. **Catalog discovery for `latitude` provider.** Static list (hardcoded mirror
   of upstream enums) vs live fetch from `GET /plans`. Live fetch is more correct
   but adds a network call on first `catalog.plans()`. **Likely answer:** static
   for sites (rarely changes), live for plans/OS (changes more often).

4. **Type stubs for patched SDK.** Pydantic models still type as `BaseModel`, but
   patched enum-replacement types lose IDE autocomplete for known values. Do we
   ship `.pyi` stubs that re-add the `Literal[...]` union of known values for
   IDE hints while keeping runtime permissive?

5. **Async support.** Upstream ships sync + async. Our wrapper must too. Confirmed
   in §2.1 (`async_client` param), but conformance tests should cover both.

6. **Test infrastructure cost.** Conformance against a real DF adapter means CI
   spins up CRDB + Redis + adapter container on every PR. Acceptable for an OSS
   project but slow. Alternative: a `provider="mock"` that records expected
   wire format and runs in-process. **Likely answer:** keep the real adapter for
   integration tests (gated), use `respx` mocks for conformance.

7. **Provider plugin extension API.** Should v0.1 expose any extension point
   (entry-points group, registration function)? Risk: locks the API for v0.2
   third-party providers before we know what they need. **Likely answer:** No
   extension API in v0.1; document explicitly that adding providers requires
   forking until v0.2.

---

## 12. v0.2+ roadmap (informational)

Not in scope for v0.1, but framing the design:

- **Direct-to-Akash provider** (`provider="akash"`): client-side translation of
  Latitude shape → Akash console API, no adapter middleman
- **Routing layer** (`EdgeRouter` separate from `EdgeClient`): fallback chains,
  cost-based dispatch, capability matrix
- **Persistence helper**: optional sqlite-backed mapping of `external_id → (provider, native_id)`
- **Cost normalization**: per-provider price model, unified `$/hour` view
- **Provider plugin entry points**: third parties ship their own providers via
  `pip install` and a `pyproject.toml` entry point group

---

## 13. Sign-off

When this document is approved, the next steps are (in order):

1. Scaffold the repository structure (§8)
2. Generate the three patch files against pinned upstream (§4)
3. Write `apply-patches.sh` and verify it produces a working SDK
4. Implement `EdgeClient`, `providers.py`, `catalog.py` (§2, §3)
5. Write conformance + unit tests (§9)
6. Write CI workflows (§7)
7. Initial commit + push to `main`
8. Tag `v0.1.0-alpha.1`, dry-run PyPI publish via TestPyPI
9. Tag `v0.1.0`, publish to PyPI
