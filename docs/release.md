# Release runbook

Two-stage release process matching [`SPEC.md` §13 steps 8–9](../SPEC.md#13-sign-off):

1. **Alpha → TestPyPI**: cut `vX.Y.Z-alpha.N` and mark as pre-release. The
   `Release` workflow publishes to [test.pypi.org](https://test.pypi.org).
2. **Real release → PyPI**: cut `vX.Y.Z`, no pre-release flag. The workflow
   publishes to [pypi.org](https://pypi.org).

## One-time setup (must happen before first release)

Both indices use **OIDC trusted publishing** — no API tokens, no secrets in
GitHub. Each one needs a pending publisher registered:

### TestPyPI

1. Log in to <https://test.pypi.org> with the account that should own the project.
2. Go to **Account settings → Publishing**.
3. Add a new **pending publisher** with:
   - PyPI Project Name: `edge-provider-sdk`
   - Owner: `Digital-Frontier-LDA`
   - Repository name: `edge-provider-sdk`
   - Workflow name: `release.yml`
   - Environment name: `testpypi`

### PyPI (production)

Repeat the same registration on <https://pypi.org>, with environment name
`pypi`.

### GitHub Environments

In the repo's **Settings → Environments**, create two environments named
`testpypi` and `pypi`. They don't need protection rules for v0.1; the OIDC
exchange is gated by the workflow's `if:` conditions.

## Cutting a release

### Alpha (TestPyPI dry-run)

```bash
# 1. Bump pyproject.toml + CHANGELOG to 0.1.0a1 (PEP 440 prerelease form —
#    `0.1.0-alpha.1` is not PEP 440-valid in pyproject.toml).
# 2. Commit on a release-prep branch, open a PR, merge.

git checkout main
git pull
# Either tag style works — release.yml compares via packaging.version.Version,
# which normalises both forms. Pick whichever you prefer to read.
git tag v0.1.0a1                # or: git tag v0.1.0-alpha.1
git push origin v0.1.0a1

# 3. On GitHub, click "Draft a new release", pick the tag, check
#    "Set as a pre-release", publish.
# 4. Watch the Release workflow run. `publish-testpypi` should succeed;
#    `publish-pypi` is skipped.
# 5. Sanity-install (TestPyPI doesn't host runtime deps, so use --extra-index-url
#    to pull `latitudesh-python-sdk` and the rest from real PyPI):
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            edge-provider-sdk==0.1.0a1
python -c "import edge_provider_sdk; print(edge_provider_sdk.__version__)"
```

### Real release (PyPI)

```bash
# 1. Make sure pyproject.toml + CHANGELOG say 0.1.0 (no suffix).
git checkout main
git pull
git tag v0.1.0
git push origin v0.1.0

# 2. On GitHub, "Draft a new release", pick v0.1.0, leave pre-release
#    unchecked, publish. The `publish-pypi` job runs.
# 3. Verify:
pip install edge-provider-sdk==0.1.0
```

## What the workflow guards against

`release.yml` will refuse to publish if any of these is true:

- The tag doesn't match `pyproject.toml`'s `version` field
  (e.g. `v0.2.0` tag with `version = "0.1.0"` in pyproject).
- `scripts/apply-patches.sh` fails (upstream changed and patches no longer apply).
- The built wheel contains fewer than 100 `_generated/` files
  (the wheel is supposed to ship the fully-patched SDK).
- `twine check` rejects the artifact metadata.

## Yanking

If a release ships broken: use the PyPI/TestPyPI web UI to yank the version.
PyPI doesn't allow re-uploading the same version after yank, so always
bump-and-re-release rather than overwrite.
