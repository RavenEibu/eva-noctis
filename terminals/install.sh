#!/usr/bin/env bash
# EVA Noctis - installer for the kitty and Ghostty themes.
#
# Run it without arguments for an interactive menu:
#   bash install.sh
#   curl -fsSL https://raw.githubusercontent.com/RavenEibu/eva-noctis/main/terminals/install.sh | bash
#
# Non-interactive flags:
#   --install | --uninstall     what to do (default: --install)
#   --kitty | --ghostty | --alacritty | --wezterm | --foot | --konsole | --zellij | --tmux | --xresources
#                               limit to those terminals (default: every detected one)
#                               (Windows Terminal, iTerm2, Warp and Termux files are manual: see the README)
#   --apply                     after installing, activate a dark/light pair
#   --dark NAME --light NAME    the pair to activate (default EVA-01 / EVA-00)
#   --list                      list the available themes
#   --status                    show what is installed and which pair is active
#   --dry-run                   print what would change without touching any file
#
# Environment: EVA_NOCTIS_REF=<tag|commit> installs from that ref instead of main;
#              EVA_NOCTIS_SHA256=<hash> verifies the downloaded archive (see SHA256SUMS in the release).
set -euo pipefail

# EVA_NOCTIS_REF pins a tag or commit (default: main), e.g. EVA_NOCTIS_REF=v0.8.1
REPO_TARBALL="${EVA_NOCTIS_URL:-https://github.com/RavenEibu/eva-noctis/archive/${EVA_NOCTIS_REF:-refs/heads/main}.tar.gz}"  # EVA_NOCTIS_URL: for mirrors and tests
EXPLICIT=0; ACTION=""; DO_KITTY=1; DO_GHOSTTY=1; WANT_KITTY=0; WANT_GHOSTTY=0; WANT_ALACRITTY=0; WANT_WEZTERM=0; DO_ALACRITTY=1; DO_WEZTERM=1; STATUS=0; DRY=0; WANT_SIMPLE=""; SIMPLE="foot konsole zellij tmux xresources"; APPLY=0; LIST=0; FLAGS=0; FAIL=0
DARK="EVA-01"; LIGHT="EVA-00"

while [ $# -gt 0 ]; do
  FLAGS=1
  case "$1" in
    --install) ACTION=install ;;
    --uninstall) ACTION=uninstall ;;
    --kitty) WANT_KITTY=1; EXPLICIT=1 ;;
    --ghostty) WANT_GHOSTTY=1; EXPLICIT=1 ;;
    --apply) APPLY=1 ;;
    --dark) DARK="${2:?missing value}"; shift ;;
    --light) LIGHT="${2:?missing value}"; shift ;;
    --alacritty) WANT_ALACRITTY=1; EXPLICIT=1 ;;
    --wezterm) WANT_WEZTERM=1; EXPLICIT=1 ;;
    --foot|--konsole|--zellij|--tmux|--xresources) WANT_SIMPLE="$WANT_SIMPLE ${1#--}"; EXPLICIT=1 ;;
    --list) LIST=1 ;;
    --status) STATUS=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,26p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
  shift
done
DARK="${DARK#Noctis-}"; LIGHT="${LIGHT#Noctis-}"
# --dry-run: shadow the commands that change files so nothing is written
if [ "$DRY" = 1 ]; then
  echo "(dry run: no file will be changed)"
  mkdir() { echo "[dry-run] create ${!#}"; }
  cp()    { echo "[dry-run] copy $(( $# - 1 )) file(s) to ${!#}"; }
  mv()    { echo "[dry-run] move $1 -> $2"; }
  rm()    { local a n=0; for a in "$@"; do case "$a" in -*) ;; *) n=$((n+1)) ;; esac; done; echo "[dry-run] remove $n path(s) matching ${!#}"; }
  touch() { echo "[dry-run] touch $1"; }
  TMPCFG=/dev/null
else
  TMPCFG=""
fi
# --kitty and --ghostty add up: with both (or neither) every terminal is in scope
if [ "$EXPLICIT" = 1 ]; then DO_KITTY=$WANT_KITTY; DO_GHOSTTY=$WANT_GHOSTTY; DO_ALACRITTY=$WANT_ALACRITTY; DO_WEZTERM=$WANT_WEZTERM; fi

# --- locate the theme files (local checkout / extension folder, or download) ---
SRC=""
SELF="${BASH_SOURCE[0]:-}"
if [ -n "$SELF" ] && [ -f "$SELF" ]; then
  HERE="$(cd "$(dirname "$SELF")" && pwd)"
  [ -d "$HERE/kitty/themes" ] && SRC="$HERE"
fi
if [ -z "$SRC" ] && [ "$STATUS" = 0 ]; then
  command -v curl >/dev/null || { echo "curl is required to download the themes" >&2; exit 1; }
  TMP="$(mktemp -d)"; trap 'command rm -rf "$TMP"' EXIT
  echo "Downloading themes..."
  curl -fsSL "$REPO_TARBALL" -o "$TMP/themes.tar.gz"
  if [ -n "${EVA_NOCTIS_SHA256:-}" ]; then
    if command -v sha256sum >/dev/null; then GOT="$(sha256sum "$TMP/themes.tar.gz" | cut -d' ' -f1)"
    else GOT="$(shasum -a 256 "$TMP/themes.tar.gz" | cut -d' ' -f1)"; fi
    [ "$GOT" = "$EVA_NOCTIS_SHA256" ] || { echo "Checksum mismatch: expected $EVA_NOCTIS_SHA256, got $GOT" >&2; exit 1; }
    echo "Checksum OK"
  fi
  tar -xz -C "$TMP" -f "$TMP/themes.tar.gz"
  SRC="$(echo "$TMP"/eva-noctis-*/terminals)"
fi

if [ "$LIST" = 1 ]; then ls "$SRC/ghostty/themes" | sed 's/^Noctis-//'; exit 0; fi

# --- paths and detection ---
KITTY_DIR="${KITTY_CONFIG_DIRECTORY:-${XDG_CONFIG_HOME:-$HOME/.config}/kitty}"
GHOSTTY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/ghostty"
ALACRITTY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/alacritty"
WEZTERM_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/wezterm"
if [ ! -d "$GHOSTTY_DIR" ] && [ -d "$HOME/Library/Application Support/com.mitchellh.ghostty" ]; then
  GHOSTTY_DIR="$HOME/Library/Application Support/com.mitchellh.ghostty"
fi
# Ghostty reads config.ghostty as well as config; keep using whichever file the user already has
ghostty_config() { if [ ! -f "$GHOSTTY_DIR/config" ] && [ -f "$GHOSTTY_DIR/config.ghostty" ]; then echo "$GHOSTTY_DIR/config.ghostty"; else echo "$GHOSTTY_DIR/config"; fi; }
has_alacritty() { command -v alacritty >/dev/null 2>&1 || [ -d "$ALACRITTY_DIR" ]; }
has_wezterm()   { command -v wezterm >/dev/null 2>&1 || [ -d "$WEZTERM_DIR" ] || [ -f "$HOME/.wezterm.lua" ]; }
# terminals that only need their theme files copied into a folder (nothing in your config is edited)
simple_dir()  { case "$1" in foot) echo "${XDG_CONFIG_HOME:-$HOME/.config}/foot/themes" ;; konsole) echo "${XDG_DATA_HOME:-$HOME/.local/share}/konsole" ;;
                  zellij) echo "${XDG_CONFIG_HOME:-$HOME/.config}/zellij/themes" ;; tmux) echo "${XDG_CONFIG_HOME:-$HOME/.config}/tmux/themes" ;;
                  xresources) echo "${XDG_CONFIG_HOME:-$HOME/.config}/xresources/themes" ;; esac; }
simple_ext()  { case "$1" in foot) echo .ini ;; konsole) echo .colorscheme ;; zellij) echo .kdl ;; tmux) echo .conf ;; xresources) echo "" ;; esac; }
simple_has()  { case "$1" in xresources) command -v xrdb >/dev/null 2>&1 ;; konsole) command -v konsole >/dev/null 2>&1 || [ -d "$(simple_dir konsole)" ] ;;
                  *) command -v "$1" >/dev/null 2>&1 || [ -d "$(dirname "$(simple_dir "$1")")" ] ;; esac; }
simple_hint() { # simple_hint <terminal> <dark theme> <light theme>
  local d; d="$(simple_dir "$1")"
  case "$1" in
    foot) echo "add to foot.ini:  include=$d/Noctis-$2.ini" ;;
    konsole) echo "Konsole: Settings > Edit Current Profile > Appearance > Noctis ($2)" ;;
    zellij) echo "add to config.kdl:  theme \"noctis-$(echo "$2" | tr 'A-Z' 'a-z')\"" ;;
    tmux) echo "add to tmux.conf:  source-file $d/Noctis-$2.conf" ;;
    xresources) echo "add to ~/.Xresources:  #include \"$d/Noctis-$2\"  (then: xrdb -merge ~/.Xresources)" ;;
  esac
}
simple_installed() { compgen -G "$(simple_dir "$1")/Noctis-*$(simple_ext "$1")" >/dev/null; }
simple_wanted()    { [ "$EXPLICIT" = 0 ] || [[ " $WANT_SIMPLE " == *" $1 "* ]]; }
install_simple()   { local d e; d="$(simple_dir "$1")"; e="$(simple_ext "$1")"; mkdir -p "$d"; cp "$SRC/$1/themes/"* "$d/"
                     echo "$1: installed $(ls "$SRC/$1/themes" | wc -l | tr -d ' ') themes in $d"; }
apply_simple()     { echo "$1: $(simple_hint "$1" "$DARK" "$LIGHT")"; }
uninstall_simple() { local d; d="$(simple_dir "$1")"; rm -f "$d"/Noctis-*; echo "$1: removed the Noctis themes from $d (remove the line you added to your config, if any)"; }

has_kitty()    { command -v kitty >/dev/null 2>&1 || [ -d "$KITTY_DIR" ]; }
has_ghostty()  { command -v ghostty >/dev/null 2>&1 || [ -d "$GHOSTTY_DIR" ] || [ -d /Applications/Ghostty.app ]; }
kitty_installed()   { compgen -G "$KITTY_DIR/themes/Noctis-*.conf" >/dev/null; }
alacritty_installed() { compgen -G "$ALACRITTY_DIR/themes/Noctis-*.toml" >/dev/null; }
wezterm_installed()   { compgen -G "$WEZTERM_DIR/colors/Noctis-*.toml" >/dev/null; }
ghostty_installed() { compgen -G "$GHOSTTY_DIR/themes/Noctis-*" >/dev/null; }
# true when file $1 is a verbatim copy of one of the installed Noctis kitty themes
is_noctis_kitty() { local t; for t in "$KITTY_DIR"/themes/Noctis-*.conf; do [ -f "$t" ] && cmp -s "$1" "$t" && return 0; done; return 1; }
# keep the user's original file once; never back up a file that is already an EVA Noctis theme
backup() { if [ -f "$1" ] && [ ! -e "$1.pre-eva-noctis" ] && ! is_noctis_kitty "$1"; then cp "$1" "$1.pre-eva-noctis"; fi; }

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
    is_noctis_kitty "$f" || continue
    if [ -f "$f.pre-eva-noctis" ] && ! is_noctis_kitty "$f.pre-eva-noctis"; then mv "$f.pre-eva-noctis" "$f"; echo "kitty: restored $f from backup"
    else rm -f "$f" "$f.pre-eva-noctis"; echo "kitty: removed $f"; fi
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
  CFG="$(ghostty_config)"; touch "$CFG"; backup "$CFG"
  { grep -v '^[[:space:]]*theme[[:space:]]*=' "$CFG" || true; } > "${TMPCFG:-$CFG.tmp}"
  printf 'theme = light:Noctis-%s,dark:Noctis-%s\n' "$LIGHT" "$DARK" >> "${TMPCFG:-$CFG.tmp}"
  mv "$CFG.tmp" "$CFG"
  echo "Ghostty: theme = light:Noctis-$LIGHT,dark:Noctis-$DARK. Reload with Ctrl+Shift+,"
}
uninstall_ghostty() {
  CFG="$(ghostty_config)"
  if [ -f "$CFG" ] && grep -q '^[[:space:]]*theme[[:space:]]*=.*Noctis-' "$CFG"; then
    grep -v '^[[:space:]]*theme[[:space:]]*=.*Noctis-' "$CFG" > "${TMPCFG:-$CFG.tmp}" || true
    # bring back the theme line you had before, if the backup has one
    if [ -f "$CFG.pre-eva-noctis" ]; then grep '^[[:space:]]*theme[[:space:]]*=' "$CFG.pre-eva-noctis" | grep -v 'Noctis-' >> "${TMPCFG:-$CFG.tmp}" || true; fi
    mv "$CFG.tmp" "$CFG"; rm -f "$CFG.pre-eva-noctis"
    echo "Ghostty: removed the Noctis 'theme =' line from $CFG"
  fi
  rm -f "$GHOSTTY_DIR"/themes/Noctis-*
  echo "Ghostty: removed the Noctis themes from $GHOSTTY_DIR/themes"
}

install_alacritty() {
  mkdir -p "$ALACRITTY_DIR/themes"
  cp "$SRC"/alacritty/themes/*.toml "$ALACRITTY_DIR/themes/"
  echo "Alacritty: installed $(ls "$SRC"/alacritty/themes | wc -l | tr -d ' ') themes in $ALACRITTY_DIR/themes"
}
apply_alacritty() {  # Alacritty has no light/dark pair; the config is yours, so only print what to add
  echo "Alacritty: add this to alacritty.toml (Alacritty 0.14+; older versions use a top-level 'import'):"
  printf '  [general]\n  import = ["%s/themes/Noctis-%s.toml"]\n' "$ALACRITTY_DIR" "$DARK"
}
uninstall_alacritty() {
  rm -f "$ALACRITTY_DIR"/themes/Noctis-*.toml
  echo "Alacritty: removed the Noctis themes from $ALACRITTY_DIR/themes (remove the import line from alacritty.toml if you added one)"
}
install_wezterm() {
  mkdir -p "$WEZTERM_DIR/colors"
  cp "$SRC"/wezterm/themes/*.toml "$WEZTERM_DIR/colors/"
  echo "WezTerm: installed $(ls "$SRC"/wezterm/themes | wc -l | tr -d ' ') color schemes in $WEZTERM_DIR/colors"
}
apply_wezterm() {
  echo "WezTerm: add this to wezterm.lua (color_scheme_dirs is needed for ~/.config/wezterm/colors on some versions):"
  printf '  config.color_scheme_dirs = { "%s/colors" }\n  config.color_scheme = wezterm.gui.get_appearance():find("Dark") and "Noctis-%s" or "Noctis-%s"\n' "$WEZTERM_DIR" "$DARK" "$LIGHT"
}
uninstall_wezterm() {
  rm -f "$WEZTERM_DIR"/colors/Noctis-*.toml
  echo "WezTerm: removed the Noctis color schemes from $WEZTERM_DIR/colors (remove color_scheme from wezterm.lua if you set one)"
}

is_simple() { [[ " $SIMPLE " == *" $1 "* ]]; }

status() {
  local t cfg
  for t in kitty ghostty alacritty wezterm $SIMPLE; do
    if is_simple "$t"; then
      if simple_installed "$t"; then printf '%-10s themes installed' "$t:"; else printf '%-10s %s' "$t:" "$(simple_has "$t" && echo 'detected, no Noctis themes' || echo 'not detected')"; fi
    elif "${t}_installed"; then printf '%-10s themes installed' "$t:"; else printf '%-10s %s' "$t:" "$("has_$t" && echo 'detected, no Noctis themes' || echo 'not detected')"; fi
    case "$t" in
      kitty) for m in dark light; do f="$KITTY_DIR/$m-theme.auto.conf"
               if [ -f "$f" ] && is_noctis_kitty "$f"; then printf ' | %s: %s' "$m" "$(sed -n 's/^## name: //p' "$f")"; fi; done ;;
      ghostty) cfg="$(ghostty_config)"; [ -f "$cfg" ] && grep -q '^[[:space:]]*theme[[:space:]]*=.*Noctis-' "$cfg" && printf ' | %s' "$(grep '^[[:space:]]*theme[[:space:]]*=' "$cfg" | tail -1 | sed 's/^[[:space:]]*//')" ;;
    esac
    echo
  done
}

run() { # run <install|uninstall> <kitty|ghostty>; returns non-zero on failure
  local act="$1" term="$2" f
  if [ "$act" = install ]; then
    if [ "$APPLY" = 1 ]; then  # check the pair before touching anything
      for f in "$DARK" "$LIGHT"; do
        [ -f "$SRC/ghostty/themes/Noctis-$f" ] || { echo "$term: unknown theme '$f' (see --list)" >&2; return 1; }
      done
    fi
    if is_simple "$term"; then install_simple "$term"; else "install_$term"; fi
    if [ "$APPLY" = 1 ]; then if is_simple "$term"; then apply_simple "$term"; else "apply_$term" || return 1; fi; fi
  else
    if is_simple "$term"; then uninstall_simple "$term"; else "uninstall_$term"; fi
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
  DO_ALACRITTY=0; DO_WEZTERM=0; WANT_SIMPLE=" "; EXPLICIT=1  # the menu only covers kitty and Ghostty; use flags for the others
  case "$WHICH" in kitty) DO_GHOSTTY=0; EXPLICIT=1 ;; ghostty) DO_KITTY=0; EXPLICIT=1 ;; esac
  if [ "$ACTION" = install ]; then
    local a; a="$(ask "Activate a dark/light pair now? (dark $DARK / light $LIGHT) [Y/n/c=choose]: ")"
    case "$a" in n|N) APPLY=0 ;; c|C) APPLY=1; choose_pair ;; *) APPLY=1 ;; esac
  else
    local a; a="$(ask "Really uninstall? [y/N]: ")"; [[ "$a" =~ ^[yY] ]] || { echo "Cancelled."; exit 0; }
  fi
  echo
}

if [ "$STATUS" = 1 ]; then status; exit 0; fi

if [ "$FLAGS" = 0 ] && [ -z "$ACTION" ]; then
  if [ "$TTY_OK" = 1 ]; then interactive
  else ACTION=install; echo "No terminal available for prompts: installing for every detected terminal (use --help for options)."; fi
fi
[ -z "$ACTION" ] && ACTION=install

for term in kitty ghostty alacritty wezterm $SIMPLE; do
  if is_simple "$term"; then
    simple_wanted "$term" || continue
    if [ "$ACTION" = uninstall ]; then
      if simple_installed "$term"; then run uninstall "$term" || FAIL=1; else echo "$term: nothing to uninstall"; fi
    elif [ "$EXPLICIT" = 1 ] || simple_has "$term"; then run install "$term" || FAIL=1
    else echo "$term: not found, skipping"; fi
    continue
  fi
  case "$term" in kitty) [ "$DO_KITTY" = 1 ] || continue ;; ghostty) [ "$DO_GHOSTTY" = 1 ] || continue ;;
    alacritty) [ "$DO_ALACRITTY" = 1 ] || continue ;; wezterm) [ "$DO_WEZTERM" = 1 ] || continue ;; esac
  if [ "$ACTION" = uninstall ]; then
    if "${term}_installed"; then run uninstall "$term" || FAIL=1; else echo "$term: nothing to uninstall"; fi
  else
    # a terminal that was not asked for explicitly is skipped when it is not present
    if [ "$EXPLICIT" = 1 ] || "has_$term"; then run install "$term" || FAIL=1
    else echo "$term: not found, skipping"; fi
  fi
done
exit "$FAIL"
