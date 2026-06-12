# Contributing to edge-python-sdk

Thanks for your interest. This project wraps
[`latitudesh-python-sdk`](https://github.com/latitudesh/latitudesh-python-sdk)
with permissive catalog enums to support multi-provider deployments. See
[`SPEC.md`](./SPEC.md) for the design rationale.

## Reporting issues

- **Bugs in our wrapper** — open an issue here with a minimal repro.
- **Bugs in the underlying SDK** (anything under `_generated/` that exists
  unchanged in upstream) — file at
  [latitudesh/latitudesh-python-sdk](https://github.com/latitudesh/latitudesh-python-sdk/issues).
- **Security issues** — see [`SECURITY.md`](./SECURITY.md). Do not open a
  public issue.

## Development setup

Requires Python ≥ 3.10 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Digital-Frontier-LDA/edge-python-sdk
cd edge-python-sdk

# One-time: build the patched _generated/ tree from upstream + patches/
./scripts/apply-patches.sh

# Sync dependencies + dev tools
uv sync --all-extras

# Run the full suite
uv run pytest -q
uv run ruff check .
uv run mypy src
```

## Making changes

1. **Branch off `main`** with a descriptive prefix: `fix/`, `feat/`, `docs/`,
   `chore/`.
2. **Keep PRs focused.** One concern per PR; smaller is better.
3. **Add tests.** Every behavior change needs a test. The wire-format tests in
   `tests/conformance/` are the regression net against upstream schemas.
4. **Run the full suite locally** before pushing. CI runs ruff, mypy, and
   pytest across Python 3.10 – 3.13.
5. **Update [`CHANGELOG.md`](./CHANGELOG.md)** under the `## Unreleased`
   section. One bullet per user-visible change.

## Modifying patches

Patches in `patches/` apply against upstream `latitudesh-python-sdk` during
`apply-patches.sh`. To add or modify a patch:

1. Extract the pinned upstream sdist locally (the script does this under
   `/tmp` — copy that tree somewhere durable to work in).
2. Edit and regenerate the patch with `git format-patch` or `diff -u`.
3. Number it sequentially: `patches/000N-short-description.patch`.
4. Re-run `./scripts/apply-patches.sh` and the test suite.

See [`SPEC.md`](./SPEC.md) §3 – §4 for the design constraints patches must
respect (in particular, what stays strict for `provider="latitude"`).

## Releases

Maintainers only — see [`docs/release.md`](./docs/release.md).
