# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Wrapper versions are independent of upstream `latitudesh-python-sdk` versions —
see [`SPEC.md` §6](./SPEC.md#6-versioning-policy).

## [Unreleased]

## [0.1.0a1] — 2026-05-13

First TestPyPI pre-release — dry-runs the release pipeline end-to-end against
the test index before burning the `0.1.0` slot on PyPI. Same code as the
forthcoming `0.1.0`; only the version string differs.

### Added
- Initial repository scaffolding from `SPEC.md` §8.
- `pyproject.toml` pinning upstream `latitudesh-python-sdk==3.0.5` and declaring
  wrapper version `0.1.0a1`.
- Apache-2.0 license matching upstream.

## [0.1.0] — TBD

Wraps `latitudesh-python-sdk==3.0.5`.

### Added
- `EdgeClient(provider=...)` constructor supporting `provider="latitude"` and
  `provider="digital-frontier"`.
- Three permissive-enum patches against upstream (sites, plans, operating systems).
- `client.catalog.sites() / plans() / os() / refresh()` accessor.
- Conformance test suite parameterised over both providers.

[Unreleased]: https://github.com/Digital-Frontier-LDA/edge-provider-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Digital-Frontier-LDA/edge-provider-sdk/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/Digital-Frontier-LDA/edge-provider-sdk/releases/tag/v0.1.0-alpha.1
