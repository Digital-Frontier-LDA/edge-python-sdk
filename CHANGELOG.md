# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Wrapper versions are independent of upstream `latitudesh-python-sdk` versions —
see [`SPEC.md` §6](./SPEC.md#6-versioning-policy).

## [Unreleased]

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
