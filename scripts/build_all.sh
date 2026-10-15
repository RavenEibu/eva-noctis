#!/usr/bin/env bash
# Regenerate every theme from the shared palettes, then validate and package.
#   bash scripts/build_all.sh            # themes + terminals + tests + VSIX
#   bash scripts/build_all.sh --check    # same, and fail if generated files differ from what is committed
# The Noctis base themes are cloned into .cache/noctis (pinned commit) unless NOCTIS_SRC points at a checkout.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

NOCTIS_REV="4a82370b2c064e36726c23e94f27ed3782bd6ecd"
NOCTIS_SRC="${NOCTIS_SRC:-.cache/noctis}"

if [ ! -d "$NOCTIS_SRC/themes" ]; then
  echo "Cloning Noctis ($NOCTIS_REV) into $NOCTIS_SRC..."
  git clone -q https://github.com/liviuschera/noctis.git "$NOCTIS_SRC"
  git -C "$NOCTIS_SRC" checkout -q "$NOCTIS_REV"
fi

python3 scripts/build.py "$NOCTIS_SRC/themes" >/dev/null
python3 scripts/terminals.py "$NOCTIS_SRC/themes" >/dev/null
python3 -m unittest discover -s tests
python3 scripts/package.py

if [ "${1:-}" = "--check" ]; then
  if ! git diff --exit-code --stat -- themes terminals; then
    echo "Generated files differ from the committed ones: edit scripts/build.py or scripts/terminals.py, regenerate and commit." >&2
    exit 1
  fi
  if [ -n "$(git ls-files --others --exclude-standard -- themes terminals)" ]; then
    echo "Untracked generated files:" >&2; git ls-files --others --exclude-standard -- themes terminals >&2; exit 1
  fi
fi
