#!/usr/bin/env bash
# EVA Noctis - installer for the kitty and Ghostty themes.
#
# Usage:
#   ./install.sh                         install every theme for kitty and Ghostty (if found)
#   ./install.sh --apply                 also activate EVA-01 (dark) / EVA-00 (light)
#   ./install.sh --apply --dark EVA-13 --light EVA-01-Light
#   ./install.sh --kitty | --ghostty     only one terminal
#   ./install.sh --list                  list the available themes
#   ./install.sh --uninstall             remove the Noctis-* themes
#
# Without a local copy of the themes (e.g. on a fresh machine) it downloads them:
#   curl -fsSL https://raw.githubusercontent.com/RavenEibu/eva-noctis/main/terminals/install.sh | bash -s -- --apply
set -euo pipefail

REPO_TARBALL="https://github.com/RavenEibu/eva-noctis/archive/refs/heads/main.tar.gz"
DO_KITTY=1; DO_GHOSTTY=1; APPLY=0; UNINSTALL=0; LIST=0
DARK="EVA-01"; LIGHT="EVA-00"

while [ $# -gt 0 ]; do
  case "$1" in
    --kitty) DO_GHOSTTY=0 ;;
    --ghostty) DO_KITTY=0 ;;
    --apply) APPLY=1 ;;
    --dark) DARK="${2:?missing value}"; shift ;;
    --light) LIGHT="${2:?missing value}"; shift ;;
    --uninstall) UNINSTALL=1 ;;
    --list) LIST=1 ;;
    -h|--help) sed -n '2,14p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
  shift
done

# strip an optional "Noctis-" prefix so both EVA-01 and Noctis-EVA-01 work
DARK="${DARK#Noctis-}"; LIGHT="${LIGHT#Noctis-}"

# --- locate the theme files ---------------------------------------------------
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

if [ "$LIST" = 1 ]; then
  ls "$SRC/ghostty/themes" | sed 's/^Noctis-//'; exit 0
fi

# --- destinations -------------------------------------------------------------
KITTY_DIR="${KITTY_CONFIG_DIRECTORY:-${XDG_CONFIG_HOME:-$HOME/.config}/kitty}"
GHOSTTY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/ghostty"
if [ ! -d "$GHOSTTY_DIR" ] && [ -d "$HOME/Library/Application Support/com.mitchellh.ghostty" ]; then
  GHOSTTY_DIR="$HOME/Library/Application Support/com.mitchellh.ghostty"
fi

have_kitty()   { command -v kitty >/dev/null 2>&1 || [ -d "$KITTY_DIR" ]; }
have_ghostty() { command -v ghostty >/dev/null 2>&1 || [ -d "$GHOSTTY_DIR" ] || [ -d "/Applications/Ghostty.app" ]; }
backup() { if [ -f "$1" ] && [ ! -e "$1.pre-eva-noctis" ]; then cp "$1" "$1.pre-eva-noctis"; fi; }

# --- kitty --------------------------------------------------------------------
if [ "$DO_KITTY" = 1 ]; then
  if have_kitty; then
    if [ "$UNINSTALL" = 1 ]; then
      rm -f "$KITTY_DIR"/themes/Noctis-*.conf
      echo "kitty: removed Noctis-* themes from $KITTY_DIR/themes"
    else
      mkdir -p "$KITTY_DIR/themes"
      cp "$SRC"/kitty/themes/*.conf "$KITTY_DIR/themes/"
      echo "kitty: installed $(ls "$SRC"/kitty/themes | wc -l | tr -d ' ') themes in $KITTY_DIR/themes"
      if [ "$APPLY" = 1 ]; then
        for f in "$DARK" "$LIGHT"; do
          [ -f "$SRC/kitty/themes/Noctis-$f.conf" ] || { echo "kitty: unknown theme '$f' (see --list)" >&2; exit 1; }
        done
        backup "$KITTY_DIR/dark-theme.auto.conf"; backup "$KITTY_DIR/light-theme.auto.conf"
        cp "$SRC/kitty/themes/Noctis-$DARK.conf"  "$KITTY_DIR/dark-theme.auto.conf"
        cp "$SRC/kitty/themes/Noctis-$LIGHT.conf" "$KITTY_DIR/light-theme.auto.conf"
        echo "kitty: dark=$DARK light=$LIGHT (follows the system appearance). Reload with Ctrl+Shift+F5."
      else
        echo "kitty: pick one with 'kitten themes' (Custom) or use --apply"
      fi
    fi
  else
    echo "kitty: not found, skipping"
  fi
fi

# --- Ghostty ------------------------------------------------------------------
if [ "$DO_GHOSTTY" = 1 ]; then
  if have_ghostty; then
    if [ "$UNINSTALL" = 1 ]; then
      rm -f "$GHOSTTY_DIR"/themes/Noctis-*
      echo "Ghostty: removed Noctis-* themes from $GHOSTTY_DIR/themes"
    else
      mkdir -p "$GHOSTTY_DIR/themes"
      cp "$SRC"/ghostty/themes/* "$GHOSTTY_DIR/themes/"
      echo "Ghostty: installed $(ls "$SRC"/ghostty/themes | wc -l | tr -d ' ') themes in $GHOSTTY_DIR/themes"
      if [ "$APPLY" = 1 ]; then
        for f in "$DARK" "$LIGHT"; do
          [ -f "$SRC/ghostty/themes/Noctis-$f" ] || { echo "Ghostty: unknown theme '$f' (see --list)" >&2; exit 1; }
        done
        CFG="$GHOSTTY_DIR/config"; touch "$CFG"; backup "$CFG"
        grep -v '^[[:space:]]*theme[[:space:]]*=' "$CFG" > "$CFG.tmp" || true
        printf 'theme = light:Noctis-%s,dark:Noctis-%s\n' "$LIGHT" "$DARK" >> "$CFG.tmp"
        mv "$CFG.tmp" "$CFG"
        echo "Ghostty: theme = light:Noctis-$LIGHT,dark:Noctis-$DARK. Reload with Ctrl+Shift+,"
      else
        echo "Ghostty: set 'theme = light:Noctis-EVA-00,dark:Noctis-EVA-01' or use --apply"
      fi
    fi
  else
    echo "Ghostty: not found, skipping"
  fi
fi
