#!/usr/bin/env bash
# The VSIX that scripts/package.py builds must contain the same files as the official `vsce package` would
# (so publishing with either tool ships the same payload). Needs node/npx.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 scripts/package.py >/dev/null
version="$(python3 -c 'import json; print(json.load(open("package.json"))["version"])')"
ours="$(unzip -Z1 "eva-noctis-$version.vsix" | sed -n 's#^extension/##p' | tr 'A-Z' 'a-z' | sort)"
theirs="$(npx --yes @vscode/vsce@3 ls --no-dependencies | grep -v '^$' | tr 'A-Z' 'a-z' | sort)"
if [ "$ours" != "$theirs" ]; then
  echo "package.py and vsce ship different files:" >&2
  diff <(echo "$ours") <(echo "$theirs") >&2 || true
  exit 1
fi
echo "vsce payload matches package.py ($(echo "$ours" | wc -l) files)"
