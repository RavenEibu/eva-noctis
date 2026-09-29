#!/usr/bin/env bash
# EVA Noctis - installer for the kitty and Ghostty themes.
#
# Run it without arguments for an interactive menu:
#   bash install.sh
#   curl -fsSL https://raw.githubusercontent.com/RavenEibu/eva-noctis/main/terminals/install.sh | bash
#
# Non-interactive flags:
#   --install | --uninstall     what to do (default: --install)
#   --kitty | --ghostty         limit to one terminal (default: both)
#   --apply                     after installing, activate a dark/light pair
#   --dark NAME --light NAME    the pair to activate (default EVA-01 / EVA-00)
#   --list                      list the available themes
set -euo pipefail

REPO_TARBALL="https://github.com/RavenEibu/eva-noctis/archive/refs/heads/main.tar.gz"
EXPLICIT=0; ACTION=""; DO_KITTY=1; DO_GHOSTTY=1; APPLY=0; LIST=0; FLAGS=0
DARK="EVA-01"; LIGHT="EVA-00"

while [ $# -gt 0 ]; do
  FLAGS=1
  case "$1" in
    --install) ACTION=install ;;
    --uninstall) ACTION=uninstall ;;
    --kitty) DO_GHOSTTY=0; EXPLICIT=1 ;;
    --ghostty) DO_KITTY=0; EXPLICIT=1 ;;
    --apply) APPLY=1 ;;
    --dark) DARK="${2:?missing value}"; shift ;;
    --light) LIGHT="${2:?missing value}"; shift ;;
    --list) LIST=1 ;;
    -h|--help) sed -n '2,17p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
  shift
done
DARK="${DARK#Noctis-}"; LIGHT="${LIGHT#Noctis-}"

# --- locate the theme files (local checkout / extension folder, or download) ---
SRC=""
SELF="${BASH_SOURCE[0]:-}"
if [ -n "$SELF" ] && [ -f "$SELF" ]; then
  HERE="$(cd "$(dirname "$SELF")" && pwd)"
  [ -d "$HERE/kitty/themes" ] && SRC="$HERE"
fi
if [ -z "$SRC" ]; then
  command -v curl >/dev/null || { echo "curl is required to download the themes" >&2; exit 1; }
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  echo "Downloading themes..."
  curl -fsSL "$REPO_TARBALL" | tar -xz -C "$TMP"
  SRC="$(echo "$TMP"/eva-noctis-*/terminals)"
fi

if [ "$LIST" = 1 ]; then ls "$SRC/ghostty/themes" | sed 's/^Noctis-//'; exit 0; fi

# --- paths and detection ---
KITTY_DIR="${KITTY_CONFIG_DIRECTORY:-${XDG_CONFIG_HOME:-$HOME/.config}/kitty}"
GHOSTTY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/ghostty"
if [ ! -d "$GHOSTTY_DIR" ] && [ -d "$HOME/Library/Application Support/com.mitchellh.ghostty" ]; then
  GHOSTTY_DIR="$HOME/Library/Application Support/com.mitchellh.ghostty"
fi
has_kitty()    { command -v kitty >/dev/null 2>&1 || [ -d "$KITTY_DIR" ]; }
has_ghostty()  { command -v ghostty >/dev/null 2>&1 || [ -d "$GHOSTTY_DIR" ] || [ -d /Applications/Ghostty.app ]; }
kitty_installed()   { compgen -G "$KITTY_DIR/themes/Noctis-*.conf" >/dev/null; }
ghostty_installed() { compgen -G "$GHOSTTY_DIR/themes/Noctis-*" >/dev/null; }
backup() { if [ -f "$1" ] && [ ! -e "$1.pre-eva-noctis" ]; then cp "$1" "$1.pre-eva-noctis"; fi; }

TTY_OK=0; if (exec </dev/tty) 2>/dev/null; then TTY_OK=1; fi
ask() { local a; read -r -p "$1" a </dev/tty || a=""; printf '%s' "$a"; }

# --- actions ---
install_kitty() {
  mkdir -p "$KITTY_DIR/themes"
  cp "$SRC"/kitty/themes/*.conf "$KITTY_DIR/themes/"
  echo "kitty: installed $(ls "$SRC"/kitty/themes | wc -l | tr -d ' ') themes in $KITTY_DIR/themes"
}
apply_kitty() {
  for f in "$DARK" "$LIGHT"; do
    [ -f "$SRC/kitty/themes/Noctis-$f.conf" ] || { echo "kitty: unknown theme '$f' (see --list)" >&2; return 1; }
  done
  backup "$KITTY_DIR/dark-theme.auto.conf"; backup "$KITTY_DIR/light-theme.auto.conf"
  cp "$SRC/kitty/themes/Noctis-$DARK.conf"  "$KITTY_DIR/dark-theme.auto.conf"
  cp "$SRC/kitty/themes/Noctis-$LIGHT.conf" "$KITTY_DIR/light-theme.auto.conf"
  echo "kitty: dark=$DARK light=$LIGHT (follows the system appearance). Reload with Ctrl+Shift+F5."
}
uninstall_kitty() {
  # undo an applied pair: restore the backup, or remove the file if it is a plain Noctis copy
  for m in dark light; do
    f="$KITTY_DIR/$m-theme.auto.conf"
    [ -f "$f" ] || continue
    for t in "$KITTY_DIR"/themes/Noctis-*.conf; do
      [ -f "$t" ] && cmp -s "$f" "$t" || continue
      if [ -f "$f.pre-eva-noctis" ]; then mv "$f.pre-eva-noctis" "$f"; echo "kitty: restored $f from backup"
      else rm -f "$f"; echo "kitty: removed $f"; fi
      break
    done
  done
  rm -f "$KITTY_DIR"/themes/Noctis-*.conf
  echo "kitty: removed the Noctis themes from $KITTY_DIR/themes"
}
install_ghostty() {
  mkdir -p "$GHOSTTY_DIR/themes"
  cp "$SRC"/ghostty/themes/* "$GHOSTTY_DIR/themes/"
  echo "Ghostty: installed $(ls "$SRC"/ghostty/themes | wc -l | tr -d ' ') themes in $GHOSTTY_DIR/themes"
}
apply_ghostty() {
  for f in "$DARK" "$LIGHT"; do
    [ -f "$SRC/ghostty/themes/Noctis-$f" ] || { echo "Ghostty: unknown theme '$f' (see --list)" >&2; return 1; }
  done
  CFG="$GHOSTTY_DIR/config"; touch "$CFG"; backup "$CFG"
  { grep -v '^[[:space:]]*theme[[:space:]]*=' "$CFG" || true; } > "$CFG.tmp"
  printf 'theme = light:Noctis-%s,dark:Noctis-%s\n' "$LIGHT" "$DARK" >> "$CFG.tmp"
  mv "$CFG.tmp" "$CFG"
  echo "Ghostty: theme = light:Noctis-$LIGHT,dark:Noctis-$DARK. Reload with Ctrl+Shift+,"
}
uninstall_ghostty() {
  CFG="$GHOSTTY_DIR/config"
  if [ -f "$CFG" ] && grep -q '^[[:space:]]*theme[[:space:]]*=.*Noctis-' "$CFG"; then
    grep -v '^[[:space:]]*theme[[:space:]]*=.*Noctis-' "$CFG" > "$CFG.tmp" || true
    # bring back the theme line you had before, if the backup has one
    if [ -f "$CFG.pre-eva-noctis" ]; then grep '^[[:space:]]*theme[[:space:]]*=' "$CFG.pre-eva-noctis" | grep -v 'Noctis-' >> "$CFG.tmp" || true; fi
    mv "$CFG.tmp" "$CFG"
    echo "Ghostty: removed the Noctis 'theme =' line from $CFG"
  fi
  rm -f "$GHOSTTY_DIR"/themes/Noctis-*
  echo "Ghostty: removed the Noctis themes from $GHOSTTY_DIR/themes"
}

run() { # run <install|uninstall> <kitty|ghostty>
  local act="$1" term="$2"
  if [ "$act" = install ]; then
    "install_$term"; [ "$APPLY" = 1 ] && "apply_$term" || true
  else
    "uninstall_$term"
  fi
}

choose_pair() {
  echo; echo "Available themes:"; ls "$SRC/ghostty/themes" | sed 's/^Noctis-//' | column -c 100 2>/dev/null || ls "$SRC/ghostty/themes" | sed 's/^Noctis-//'
  local d l
  d="$(ask "Dark theme  [$DARK]: ")"; [ -n "$d" ] && DARK="${d#Noctis-}"
  l="$(ask "Light theme [$LIGHT]: ")"; [ -n "$l" ] && LIGHT="${l#Noctis-}"
}

interactive() {
  local kmark="not detected" gmark="not detected" opts=() labels=() n
  has_kitty   && kmark="detected";  kitty_installed   && kmark="Noctis themes installed"
  has_ghostty && gmark="detected";  ghostty_installed && gmark="Noctis themes installed"
  echo
  echo "EVA Noctis - terminal themes"
  echo "  kitty:   $kmark"
  echo "  Ghostty: $gmark"
  echo
  n=0
  add() { n=$((n+1)); opts[$n]="$1"; labels[$n]="$2"; echo "  $n) $2"; }
  add "install kitty"       "Install / update for kitty"
  add "install ghostty"     "Install / update for Ghostty"
  add "install both"        "Install / update for both"
  kitty_installed   && add "uninstall kitty"   "Uninstall from kitty"
  ghostty_installed && add "uninstall ghostty" "Uninstall from Ghostty"
  if kitty_installed && ghostty_installed; then add "uninstall both" "Uninstall from both"; fi
  add "quit" "Quit"
  echo
  local c; c="$(ask "Choose [1-$n]: ")"
  [[ "$c" =~ ^[0-9]+$ ]] && [ "$c" -ge 1 ] && [ "$c" -le "$n" ] || { echo "Nothing selected."; exit 1; }
  read -r ACTION WHICH <<< "${opts[$c]}"
  [ "$ACTION" = quit ] && exit 0
  case "$WHICH" in kitty) DO_GHOSTTY=0; EXPLICIT=1 ;; ghostty) DO_KITTY=0; EXPLICIT=1 ;; esac
  if [ "$ACTION" = install ]; then
    local a; a="$(ask "Activate a dark/light pair now? (dark $DARK / light $LIGHT) [Y/n/c=choose]: ")"
    case "$a" in n|N) APPLY=0 ;; c|C) APPLY=1; choose_pair ;; *) APPLY=1 ;; esac
  else
    local a; a="$(ask "Really uninstall? [y/N]: ")"; [[ "$a" =~ ^[yY] ]] || { echo "Cancelled."; exit 0; }
  fi
  echo
}

if [ "$FLAGS" = 0 ] && [ -z "$ACTION" ]; then
  if [ "$TTY_OK" = 1 ]; then interactive
  else ACTION=install; echo "No terminal available for prompts: installing for every detected terminal (use --help for options)."; fi
fi
[ -z "$ACTION" ] && ACTION=install

for term in kitty ghostty; do
  case "$term" in kitty) [ "$DO_KITTY" = 1 ] || continue ;; ghostty) [ "$DO_GHOSTTY" = 1 ] || continue ;; esac
  if [ "$ACTION" = uninstall ]; then
    if "${term}_installed"; then run uninstall "$term"; else echo "$term: nothing to uninstall"; fi
  else
    # a terminal that was not asked for explicitly is skipped when it is not present
    if [ "$EXPLICIT" = 1 ] || "has_$term"; then run install "$term"
    else echo "$term: not found, skipping"; fi
  fi
done
