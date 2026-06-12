# Security policy

## Supported versions

`edge-python-sdk` is in active early development (0.1.x). Only the latest
released minor version receives security fixes.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a vulnerability

**Please do not file a public GitHub issue for security vulnerabilities.**

Report security issues privately via
[GitHub Security Advisories](https://github.com/Digital-Frontier-LDA/edge-python-sdk/security/advisories/new)
(Repository → Security → Report a vulnerability). The advisory flow keeps the
report private until a coordinated fix is ready.

You should expect an initial acknowledgement within **3 business days**. We aim
to release a fix within **90 days** of a confirmed report, coordinated with the
reporter for disclosure timing.

## Scope

**In scope:**
- Code under `src/edge_python_sdk/` (excluding `_generated/`)
- The release pipeline (`.github/workflows/release.yml`) and trusted-publisher
  configuration on PyPI
- The patch-application machinery (`scripts/`, `patches/`)

**Out of scope — please report upstream:**
- Vulnerabilities present in unpatched `latitudesh-python-sdk` code (anything
  under `_generated/` that exists identically in
  [latitudesh/latitudesh-python-sdk](https://github.com/latitudesh/latitudesh-python-sdk)).
