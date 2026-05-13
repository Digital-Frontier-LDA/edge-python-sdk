#!/usr/bin/env bash
# refresh-upstream.sh — check PyPI for a newer latitudesh-python-sdk release.
#
# - Reads the pinned version from `[tool.edge-provider-sdk].upstream-version`
#   in pyproject.toml.
# - Queries PyPI's JSON API for the latest released version.
# - Prints the latest version on stdout when it differs from the pin.
# - Prints nothing and exits 0 when already up to date.
# - Exits 1 on any error (PyPI unreachable, pyproject malformed, etc.).
#
# The companion workflow `.github/workflows/sync-upstream.yml` reads the
# stdout to decide whether to bump and open a PR.

set -euo pipefail

UPSTREAM_PACKAGE="latitudesh-python-sdk"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CURRENT_PIN="$(
  awk '
    /^\[tool\.edge-provider-sdk\]/ { in_section = 1; next }
    /^\[/ { in_section = 0 }
    in_section && /^upstream-version[[:space:]]*=/ {
      gsub(/.*=[[:space:]]*"|"[[:space:]]*$/, "")
      print
      exit
    }
  ' "${ROOT}/pyproject.toml"
)"

if [[ -z "${CURRENT_PIN}" ]]; then
  echo "ERROR: could not read [tool.edge-provider-sdk].upstream-version from pyproject.toml" >&2
  exit 1
fi

LATEST="$(
  curl -fsSL "https://pypi.org/pypi/${UPSTREAM_PACKAGE}/json" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
)"

if [[ -z "${LATEST}" ]]; then
  echo "ERROR: could not resolve latest version of ${UPSTREAM_PACKAGE} from PyPI" >&2
  exit 1
fi

# Emit summary to stderr (visible in CI logs) and the new-version-or-nothing
# signal to stdout (consumed by the workflow).
echo "pinned: ${CURRENT_PIN}" >&2
echo "latest: ${LATEST}" >&2

if [[ "${CURRENT_PIN}" != "${LATEST}" ]]; then
  echo "${LATEST}"
fi
