# `edge-python-sdk` vs. `latitudesh-python-sdk`

This document explains **why `edge-python-sdk` exists as a separate project**,
how it relates to the upstream Latitude.sh SDK, and when you should use one over
the other.

- **Upstream:** [`latitudesh/latitudesh-python-sdk`](https://github.com/latitudesh/latitudesh-python-sdk)
  ([PyPI](https://pypi.org/project/latitudesh-python-sdk/)) — the official
  Latitude.sh Python SDK.
- **This project:** [`Digital-Frontier-LDA/edge-python-sdk`](https://github.com/Digital-Frontier-LDA/edge-python-sdk)
  ([PyPI](https://pypi.org/project/edge-python-sdk/)) — a community wrapper.

## TL;DR

`edge-python-sdk` is a **thin wrapper** around the upstream SDK. It is **not a
fork**, and it is **not affiliated with or endorsed by Latitude.sh**. It depends
on `latitudesh-python-sdk` as a pinned dependency, ships a lightly patched copy
of it, and adds a provider-selecting constructor.

It exists to solve one problem: the upstream SDK validates site/plan/OS slugs
against **closed enums**, which rejects any Latitude-*shaped* backend whose
catalog differs from Latitude.sh's own — before the request ever leaves the
client. If you only ever call the real Latitude.sh API, you do not need this
wrapper; use the upstream SDK directly.

## The two projects at a glance

|  | `latitudesh-python-sdk` (upstream) | `edge-python-sdk` (this project) |
|---|---|---|
| Maintainer | Latitude.sh (official) | Digital-Frontier-LDA (community) |
| Repository | [latitudesh/latitudesh-python-sdk](https://github.com/latitudesh/latitudesh-python-sdk) | [Digital-Frontier-LDA/edge-python-sdk](https://github.com/Digital-Frontier-LDA/edge-python-sdk) |
| Origin | Speakeasy-generated from Latitude's OpenAPI spec | Hand-written wrapper + 3 patches over upstream |
| License | MIT (© 2025 Latitude.sh) | Apache-2.0 (wrapper) — bundles MIT upstream |
| Backends | Latitude.sh only | `latitude` + `digital-frontier` (any Latitude-shaped URL) |
| Catalog enums | Strict `(str, Enum)` for site/plan/OS | Permissive for non-Latitude; strict kept for `latitude` |
| API surface | `servers`, `projects`, `ssh_keys`, … | **Identical** — forwarded verbatim, plus a `catalog` accessor |
| Versioning | Tracks Latitude's API / Speakeasy cadence | Independent wrapper semver (see [SPEC §6](../SPEC.md#6-versioning-policy)) |

## What `edge-python-sdk` is — and is not

**It is:**

- A wrapper that re-exports the upstream SDK's behavior unchanged, with a
  different constructor (`EdgeClient(provider=...)`).
- A build recipe: `patches/` + `scripts/apply-patches.sh` produce a patched copy
  of upstream pinned at a known version.

**It is not:**

- **Not a fork.** There is no divergent copy of upstream's source in version
  control. `_generated/` is built on demand from the pinned upstream release and
  is `.gitignore`d. Upstream remains a normal pinned dependency in
  `pyproject.toml`.
- **Not official.** It is community-maintained and has no affiliation with
  Latitude.sh (see [Affiliation](#affiliation)).
- **Not a re-implementation.** Operations (`servers`, `projects`, `ssh_keys`, …)
  are not intercepted, transformed, or proxied — attribute access is forwarded
  straight to the underlying SDK. The wrapper only chooses the `server_url` and
  the enum-strictness mode.

## The problem: closed catalog enums

The upstream SDK is generated from Latitude.sh's OpenAPI spec. The spec enumerates
the valid site, plan, and operating-system slugs, so Speakeasy emits them as
`(str, Enum)` classes — for example:

```python
# upstream: latitudesh_python_sdk/models/create_serverop.py
class CreateServerServersSite(str, Enum):
    ASH = "ASH"
    BUE = "BUE"
    # ... 16 more
```

That is correct and useful for Latitude.sh itself. But it means the **client**
becomes a second authority on what catalog values exist. Any backend that speaks
the Latitude API shape but exposes a *different* catalog — a self-hosted adapter,
a regional reseller, a Latitude-shaped gateway in front of another compute
backend — has its requests rejected inside the SDK, before they reach the server
that actually knows whether the value is valid.

`edge-python-sdk` removes the client from that decision for non-Latitude
backends. Seven enum classes are converted to permissive type aliases:

```python
# patched: any string is accepted; the API is the sole validator
CreateServerServersSite = str
```

| Patch | Concern | Enum classes converted |
|---|---|---|
| `0001-site-enum-permissive.patch` | site slugs | `CreateServerServersSite`, `PostVpnSessionVpnSessionsSite`, `CreateVirtualNetworkPrivateNetworksSite` |
| `0002-plan-enum-permissive.patch` | plan slugs | `CreateServerServersPlan` |
| `0003-os-enum-permissive.patch` | OS slugs | `CreateServerServersOperatingSystem`, `CreateServerReinstallServersOperatingSystem`, `UpdateServerDeployConfigServersOperatingSystem` |

The original enum members are preserved as `_ORIGINAL_SITES` / `_ORIGINAL_PLANS`
/ `_ORIGINAL_OS` constants, so the `latitude` provider can still validate
strictly. See [SPEC §4](../SPEC.md#4-patches-against-upstream) for the full patch
contract.

## What the wrapper adds

1. **Provider selection at construction.** `EdgeClient(provider="latitude")`
   instantiates the unpatched upstream SDK against `https://api.latitude.sh`.
   `EdgeClient(provider="digital-frontier", base_url=...)` instantiates the
   patched SDK against any URL you supply.
2. **Per-provider enum behavior.** `latitude` keeps upstream's strict enums —
   loosening them there would only swap a fast client-side error for a slower
   network round-trip with no benefit. `digital-frontier` gets the permissive
   patches.
3. **A `catalog` accessor.** `client.catalog.sites() / plans() / os() /
   refresh()` returns the active provider's known catalog values — a static
   mirror of the upstream enum for `latitude`, live discovery calls for
   `digital-frontier`. This has no upstream equivalent.

Everything else is upstream, verbatim.

## Which one should you use?

| Your situation | Use |
|---|---|
| You only ever call the real `api.latitude.sh` | **`latitudesh-python-sdk`** directly — the wrapper adds nothing |
| You target a non-Latitude, Latitude-shaped backend | **`edge-python-sdk`** (`provider="digital-frontier"`) |
| You switch between Latitude and other backends in one codebase | **`edge-python-sdk`** — one client, swap `provider=` |
| You need the official, Latitude-supported package | **`latitudesh-python-sdk`** |

Migration is cheap either way — the only API difference is the constructor. See
[`upgrading-from-latitudesh.md`](./upgrading-from-latitudesh.md).

## How the patches track upstream

The upstream version is **pinned** in `pyproject.toml`:

```toml
[tool.edge-python-sdk]
upstream-package = "latitudesh-python-sdk"
upstream-version = "3.0.5"
```

`scripts/apply-patches.sh` downloads exactly that release, applies the three
patches in order, rewrites the `latitudesh_python_sdk` import path to
`edge_python_sdk._generated` (so both packages can coexist in one
environment), and installs the result into the `.gitignore`d `_generated/` tree.

A scheduled `sync-upstream.yml` workflow checks daily for a newer upstream
release. If one exists and the patches still apply cleanly with conformance
passing, it opens a `sync: bump upstream to <version>` PR; if a patch conflicts,
it opens a PR carrying the failed hunks for manual rebase. See
[SPEC §5](../SPEC.md#5-build-flow) and [§7](../SPEC.md#7-ci--release-automation).

## Versioning relationship

Wrapper versions are **independent of upstream**. `edge-python-sdk` follows its
own semver (`0.1.0`, `0.1.1`, …); the wrapped upstream version is recorded in
package metadata, not in the version string. At runtime:

```python
import edge_python_sdk
edge_python_sdk.__version__         # the wrapper version, e.g. "0.1.1"
edge_python_sdk.upstream_version    # the wrapped upstream version, e.g. "3.0.5"
```

A new upstream release does not force a wrapper release, and vice versa. The
rationale — and the version schemes that were considered and rejected — is in
[SPEC §6](../SPEC.md#6-versioning-policy).

## Licensing & attribution

Two licenses are in play, and they are compatible:

- **This wrapper** — everything authored in this repository (`EdgeClient`, the
  provider registry, the catalog accessor, the patches, the build scripts) — is
  licensed under **Apache-2.0** ([`LICENSE`](../LICENSE)).
- **Upstream `latitudesh-python-sdk`** is licensed under the **MIT License**,
  Copyright (c) 2025 Latitude.sh.

> ⚠️ Earlier revisions of the README and `SPEC.md` described this project's
> license as "Apache-2.0 — matches upstream." That was incorrect: **upstream is
> MIT, not Apache-2.0.** The README has been corrected; `SPEC.md` §8 and §11
> still carry the old wording and should be fixed.

### What this means for distribution

The **sdist** ships only the *recipe* — `patches/` plus
`scripts/apply-patches.sh`. It contains no upstream code; a build from sdist
re-downloads the pinned upstream release and patches it locally.

The **wheel** is different: it bundles the fully patched `_generated/` tree,
which is substantially upstream's MIT-licensed source. The MIT License requires
that "the above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software."

**How this is satisfied.** `scripts/apply-patches.sh` copies upstream's
`LICENSE` into `src/edge_python_sdk/_generated/THIRD-PARTY-LICENSES/latitudesh-python-sdk-LICENSE`
during the build. The wheel includes the `_generated/` tree as a hatch artifact,
so the file ships with every wheel. The sdist ships only the recipe — but
because a build from sdist re-runs `apply-patches.sh`, downstream consumers
end up with the same notice in their installed package.

## Affiliation

`edge-python-sdk` is an independent, community-maintained project. It is **not
affiliated with, endorsed by, or sponsored by Latitude.sh**. "Latitude.sh" and
related names are used here only to describe interoperability and the wrapped
upstream dependency; all such marks belong to their respective owner.
