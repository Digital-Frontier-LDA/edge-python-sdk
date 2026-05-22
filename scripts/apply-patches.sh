#!/usr/bin/env bash
# apply-patches.sh — build src/edge_python_sdk/_generated/ from pinned upstream + patches/.
#
# Idempotent. Reads the upstream version from pyproject.toml, downloads the
# sdist from PyPI's JSON API, applies patches in numeric order, then rewrites
# `latitudesh_python_sdk` import paths to `edge_python_sdk._generated`.

set -euo pipefail

UPSTREAM_PACKAGE="latitudesh-python-sdk"
UPSTREAM_DIST_NAME="latitudesh_python_sdk"  # PEP 503 normalized name (dashes→underscores) used inside the tarball

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_DIR="${ROOT}/.upstream-cache"
TARGET_PARENT="${ROOT}/src/edge_python_sdk"
TARGET_DIR="${TARGET_PARENT}/_generated"
PATCHES_DIR="${ROOT}/patches"

# Extract pinned upstream version from pyproject.toml: the [tool.edge-python-sdk]
# upstream-version field is the authoritative pin.
UPSTREAM_VERSION="$(
  awk '
    /^\[tool\.edge-python-sdk\]/ { in_section = 1; next }
    /^\[/ { in_section = 0 }
    in_section && /^upstream-version[[:space:]]*=/ {
      gsub(/.*=[[:space:]]*"|"[[:space:]]*$/, "")
      print
      exit
    }
  ' "${ROOT}/pyproject.toml"
)"

if [[ -z "${UPSTREAM_VERSION}" ]]; then
  echo "ERROR: could not read [tool.edge-python-sdk].upstream-version from pyproject.toml" >&2
  exit 1
fi

echo "==> upstream: ${UPSTREAM_PACKAGE}==${UPSTREAM_VERSION}"
echo "==> target:   ${TARGET_DIR}"

mkdir -p "${CACHE_DIR}"
TARBALL="${CACHE_DIR}/${UPSTREAM_DIST_NAME}-${UPSTREAM_VERSION}.tar.gz"

# 1. Resolve sdist URL from PyPI's JSON API (only if not already cached)
if [[ ! -f "${TARBALL}" ]]; then
  echo "==> resolving sdist URL from PyPI..."
  SDIST_URL="$(
    curl -fsSL "https://pypi.org/pypi/${UPSTREAM_PACKAGE}/${UPSTREAM_VERSION}/json" \
      | python3 -c "import json,sys; d=json.load(sys.stdin); [print(u['url']) for u in d['urls'] if u['packagetype']=='sdist']" \
      | head -n1
  )"
  if [[ -z "${SDIST_URL}" ]]; then
    echo "ERROR: no sdist found on PyPI for ${UPSTREAM_PACKAGE}==${UPSTREAM_VERSION}" >&2
    exit 1
  fi
  echo "==> downloading ${SDIST_URL}"
  curl -fsSL "${SDIST_URL}" -o "${TARBALL}"
fi

# 2. Fresh extraction every run. We extract under /tmp (via mktemp) rather
# than under the project tree because the upstream sdist contains its own
# pyproject.toml — leaving it inside our repo confuses uv's workspace
# discovery into trying to build it as a sub-package. The tarball stays
# cached in .upstream-cache/ so repeated runs don't re-download.
EXTRACT_DIR="$(mktemp -d -t edge-python-sdk-extract-XXXXXX)"
trap 'rm -rf "${EXTRACT_DIR}"' EXIT
tar -xzf "${TARBALL}" -C "${EXTRACT_DIR}"

UPSTREAM_TREE="${EXTRACT_DIR}/${UPSTREAM_DIST_NAME}-${UPSTREAM_VERSION}"
if [[ ! -d "${UPSTREAM_TREE}/src/${UPSTREAM_DIST_NAME}" ]]; then
  echo "ERROR: expected ${UPSTREAM_TREE}/src/${UPSTREAM_DIST_NAME} after extraction" >&2
  exit 1
fi

# 3. Apply patches in numeric order. We deliberately use plain `patch -p1`
# instead of `git apply` because `git apply` discovers the parent project's
# .git directory and interprets patch paths relative to that repo root —
# which means patches against our extracted upstream tree silently no-op.
echo "==> applying patches"
shopt -s nullglob
PATCHES=( "${PATCHES_DIR}"/*.patch )
shopt -u nullglob
if [[ ${#PATCHES[@]} -eq 0 ]]; then
  echo "ERROR: no .patch files found in ${PATCHES_DIR}" >&2
  exit 1
fi
for patch in $(printf '%s\n' "${PATCHES[@]}" | sort); do
  echo "    - $(basename "${patch}")"
  ( cd "${UPSTREAM_TREE}" && patch -p1 --silent --no-backup-if-mismatch -i "${patch}" )
done

# 4. Rewrite imports: `latitudesh_python_sdk` → `edge_python_sdk._generated`.
# We rewrite the package name everywhere it appears in source files; that
# covers `from latitudesh_python_sdk...`, `import latitudesh_python_sdk...`,
# and stringified references (e.g. forward-ref annotations).
echo "==> rewriting imports"
PATCHED_SRC="${UPSTREAM_TREE}/src/${UPSTREAM_DIST_NAME}"
find "${PATCHED_SRC}" -type f -name "*.py" -print0 \
  | xargs -0 perl -i -pe 's/\blatitudesh_python_sdk\b/edge_python_sdk._generated/g'

# 5. Move to _generated/. Replace any prior build atomically.
echo "==> installing into ${TARGET_DIR}"
rm -rf "${TARGET_DIR}"
mkdir -p "${TARGET_PARENT}"
mv "${PATCHED_SRC}" "${TARGET_DIR}"

# 6. Record provenance — useful for `python -m edge_python_sdk._generated --version`
# style debugging and for sync-upstream.yml to confirm the build matches the pin.
cat >"${TARGET_DIR}/_provenance.py" <<EOF
"""Build provenance — written by scripts/apply-patches.sh. Do not edit by hand."""

UPSTREAM_PACKAGE = "${UPSTREAM_PACKAGE}"
UPSTREAM_VERSION = "${UPSTREAM_VERSION}"
PATCHES = (
$(for p in "${PATCHES[@]}"; do printf '    "%s",\n' "$(basename "$p")"; done)
)
EOF

echo "==> done. ${TARGET_DIR} ready."
