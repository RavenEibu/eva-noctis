#!/usr/bin/env bash
# Load every generated terminal theme with the real application when it is installed. Missing tools are skipped.
#   bash scripts/smoke_terminals.sh
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
note() { printf '%-10s %s\n' "$1" "$2"; }

if command -v tmux >/dev/null; then
  bad=0
  for f in terminals/tmux/themes/*.conf; do
    out="$(tmux -L evasmoke -f /dev/null start-server \; source-file "$f" \; show -g status-style 2>&1)" || bad=1
    echo "$out" | grep -qiE 'unknown|invalid|error' && bad=1
    tmux -L evasmoke kill-server 2>/dev/null
  done
  note tmux "$([ $bad = 0 ] && echo ok || echo FAILED)"; fail=$((fail + bad))
else note tmux skipped; fi

if command -v zellij >/dev/null; then
  bad=0
  for f in terminals/zellij/themes/*.kdl; do
    rm -rf "$tmp/zj"; mkdir -p "$tmp/zj/themes"; cp "$f" "$tmp/zj/themes/"
    n="$(grep -o '^    [a-z0-9-]* {' "$f" | tr -d ' {')"; printf 'theme "%s"\n' "$n" > "$tmp/zj/config.kdl"
    out="$(zellij --config-dir "$tmp/zj" --config "$tmp/zj/config.kdl" setup --check 2>&1)"
    echo "$out" | grep -q 'Well defined' && ! echo "$out" | grep -q '╭─' || bad=1
  done
  note zellij "$([ $bad = 0 ] && echo ok || echo FAILED)"; fail=$((fail + bad))
else note zellij skipped; fi

if command -v xrdb >/dev/null; then
  bad=0
  for f in terminals/xresources/themes/Noctis-*; do
    [ "$(xrdb -n -merge "$f" 2>&1 | grep -c '^\*\.color')" = 16 ] || bad=1
  done
  note xrdb "$([ $bad = 0 ] && echo ok || echo FAILED)"; fail=$((fail + bad))
else note xrdb skipped; fi

if command -v ghostty >/dev/null; then
  bad=0
  for f in terminals/ghostty/themes/*; do
    printf 'theme = %s\n' "$PWD/$f" > "$tmp/g.cfg"; ghostty +validate-config --config-file="$tmp/g.cfg" >/dev/null 2>&1 || bad=1
  done
  note ghostty "$([ $bad = 0 ] && echo ok || echo FAILED)"; fail=$((fail + bad))
else note ghostty skipped; fi

if command -v foot >/dev/null; then
  bad=0
  for f in terminals/foot/themes/*.ini; do
    printf 'include=%s\n' "$PWD/$f" > "$tmp/foot.ini"
    out="$(foot --check-config -c "$tmp/foot.ini" 2>&1)" || bad=1
    echo "$out" | grep -qiE 'warn|err|invalid|deprecat' && bad=1
  done
  note foot "$([ $bad = 0 ] && echo ok || echo FAILED)"; fail=$((fail + bad))
else note foot skipped; fi

if command -v kitty >/dev/null; then
  cat > "$tmp/kc.py" <<'PY'
import sys
from kitty.config import load_config
bad = 0
for f in sys.argv[1:]:
    errs = []
    load_config(f, accumulate_bad_lines=errs)
    bad += bool(errs)
print("kitty-bad", bad)
PY
  out="$(kitty +runpy "import sys; sys.argv=['x']+sys.argv[1:]; exec(open('$tmp/kc.py').read())" terminals/kitty/themes/*.conf 2>&1 | tail -1)"
  [ "$out" = "kitty-bad 0" ] && note kitty ok || { note kitty "FAILED ($out)"; fail=$((fail + 1)); }
else note kitty skipped; fi

exit "$fail"
