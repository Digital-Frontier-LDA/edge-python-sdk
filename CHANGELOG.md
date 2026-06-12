# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Wrapper versions are independent of upstream `latitudesh-python-sdk` versions —
see [`SPEC.md` §6](./SPEC.md#6-versioning-policy).

## [Unreleased]

## [0.1.2] — 2026-06-12

First release of the renamed `edge-python-sdk` package on PyPI. The legacy
`edge-provider-sdk` 0.1.1 release remains orphaned upstream (PyPI does not
support project renames); consumers must switch to `pip install edge-python-sdk`
and `import edge_python_sdk`.

### Changed
- **BREAKING (distribution rename).** `edge-provider-sdk` → `edge-python-sdk`,
  and the import path `edge_provider_sdk` → `edge_python_sdk`. Repository,
  package directory, distribution name, scripts, CI, and docs all renamed
  together.

### Added
- `src/edge_python_sdk/py.typed` — PEP 561 marker so downstream `mypy` treats
  the wrapper package as typed. The pre-existing marker under `_generated/`
  is upstream's and didn't cover the top-level package.
- Secret scanning in CI via gitleaks (`secrets-gitleaks` job + `.gitleaks.toml`,
  binary pinned to 8.30.1 with checksum-verified install; default ruleset +
  allowlists for SHA-pinned actions and release-asset checksums).
- `SECURITY.md` routing disclosure through GitHub Security Advisories.
- `CONTRIBUTING.md` covering dev setup, the patch workflow, and PR expectations.
- Issue and PR templates; blank issues disabled; security and upstream-bug
  reports routed via contact links.
- `.github/dependabot.yml` for weekly grouped `pip` updates (dev / runtime) and
  GitHub Actions updates. `latitudesh-python-sdk` is excluded because
  `sync-upstream.yml` already owns its lifecycle.
- README badges: CI status, PyPI version, supported Python versions, license.

### Fixed
- **Upstream MIT-attribution compliance.** `scripts/apply-patches.sh` now copies
  upstream's `LICENSE` into
  `src/edge_python_sdk/_generated/THIRD-PARTY-LICENSES/latitudesh-python-sdk-LICENSE`,
  and the wheel ships it alongside the vendored patched code. Previously the
  wheel shipped patched MIT-licensed code with no attribution notice — closes
  the open compliance item that
  [`docs/comparison-with-upstream.md`](./docs/comparison-with-upstream.md#licensing--attribution)
  had previously flagged.

## [0.1.2a1] — 2026-06-12

First TestPyPI pre-release of the renamed `edge-python-sdk` package. Same code
as the forthcoming `0.1.2`; only the version string differs. Validates the
fresh trusted-publisher configuration on TestPyPI under the new distribution
name before burning the `0.1.2` slot on real PyPI.

## [0.1.1] — 2026-05-14

### Fixed
- `edge_python_sdk.models` now actually re-exports the model namespace from
  the patched `_generated/` SDK. In `0.1.0` the module was a placeholder
  docstring, so `from edge_python_sdk.models import APIError,
  ResponseValidationError` (or any other model class) raised `AttributeError`.
  Re-exports are lazy — the wrapper delegates `__getattr__` to
  `_generated.models`, so startup cost is unchanged.

## [0.1.0a2] — 2026-05-13

Second TestPyPI pre-release. The `0.1.0a1` install surfaced a hardcoded
`__version__` in `edge_python_sdk/__init__.py` that would drift from
`pyproject.toml` on every bump. Re-validates the release pipeline with that
fixed before promoting to PyPI as `0.1.0`.

### Fixed
- `edge_python_sdk.__version__` now reads from `importlib.metadata` so it
  always matches the installed package's `pyproject.toml` version (was
  hardcoded to `"0.1.0"`).

## [0.1.0a1] — 2026-05-13

First TestPyPI pre-release — dry-runs the release pipeline end-to-end against
the test index before burning the `0.1.0` slot on PyPI. Same code as the
forthcoming `0.1.0`; only the version string differs.

### Added
- Initial repository scaffolding from `SPEC.md` §8.
- `pyproject.toml` pinning upstream `latitudesh-python-sdk==3.0.5` and declaring
  wrapper version `0.1.0a1`.
- Apache-2.0 license matching upstream.

## [0.1.0] — 2026-05-13

First public release. Wraps `latitudesh-python-sdk==3.0.5`. Released via the
TestPyPI dry-run pipeline validated by `0.1.0a1` and `0.1.0a2`.

### Added
- `EdgeClient(provider=...)` constructor supporting `provider="latitude"` and
  `provider="digital-frontier"`.
- Three permissive-enum patches against upstream (sites, plans, operating systems).
- `client.catalog.sites() / plans() / os() / refresh()` accessor.
- Conformance test suite parameterised over both providers.
- `edge_python_sdk.__version__` sourced from installed package metadata so
  it cannot drift from `pyproject.toml`.

[Unreleased]: https://github.com/Digital-Frontier-LDA/edge-python-sdk/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Digital-Frontier-LDA/edge-python-sdk/releases/tag/v0.1.1
[0.1.0]: https://github.com/Digital-Frontier-LDA/edge-python-sdk/releases/tag/v0.1.0
[0.1.0a2]: https://github.com/Digital-Frontier-LDA/edge-python-sdk/releases/tag/v0.1.0-alpha.2
[0.1.0a1]: https://github.com/Digital-Frontier-LDA/edge-python-sdk/releases/tag/v0.1.0-alpha.1
