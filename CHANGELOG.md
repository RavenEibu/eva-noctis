# Changelog

## Unreleased
- New themes for Windows Terminal, iTerm2, foot, Konsole, Xresources (xterm/urxvt/st), tmux, Zellij, Termux and Warp, for all 28 variants. Packaging compares their background, foreground and ANSI colors with the VS Code terminal. `install.sh` installs foot, Konsole, Zellij, tmux and Xresources with `--foot`, `--konsole`, `--zellij`, `--tmux` and `--xresources`.
- New Alacritty (`terminals/alacritty`) and WezTerm (`terminals/wezterm`) themes for all 28 variants, generated from the same palettes. `install.sh` handles them with `--alacritty` / `--wezterm`.
- `install.sh --status` shows what is installed and the active pair; Ghostty's `config.ghostty` is used when it is the config file you have.
- Packaging now enforces the readability contract (syntax 4.5:1, comments 4:1, high contrast 7:1, status bar, cursor and ANSI colors) and checks Alacritty/WezTerm parity.
- `scripts/build_all.sh` (pinned Noctis base, `--check` mode) and a GitHub Actions workflow that fails when generated files are out of date.
- Terminal bright black (ANSI 8) now keeps at least 3:1 contrast against the background in every theme (it is used for comments and suggestions).
- Noctis (EVA Mark.06 High Contrast): bright white (ANSI 15) is no longer white on white and meets 7:1.
- Cursor color keeps at least 3:1 contrast in every theme (EVA-00, EVA-02 Light and EVA-08 Light were lower); kitty/Ghostty selections are now visibly distinct from the background while keeping readable text.
- kitty themes carry `author`, `license`, `upstream` and `blurb` metadata.
- `terminals/install.sh`: `EVA_NOCTIS_REF` pins the downloaded tag or commit instead of `main`.
- `terminals/install.sh`: `--kitty --ghostty` now installs both; an unknown theme in `--apply` exits with an error before installing; re-applying a pair no longer backs up an EVA Noctis theme as if it were your original, and uninstall cleans leftover backups.

## 0.8.1
- VSIX packaging now rejects missing or mismatched editor and terminal themes, checks OLED true-black surfaces, and verifies the final archive before replacing an existing package.

## 0.8.0
- Five new OLED themes with a true `#000000` background: **Noctis (EVA-01 OLED)**, **Noctis (MAGI OLED)**, **Noctis (EVA-02 OLED)**, **Noctis (EVA-00 OLED)** and **Noctis (Lilith OLED)**, each with matching kitty and Ghostty themes.

## 0.7.0
- The kitty and Ghostty themes now ship inside the extension (`terminals/` folder), together with `terminals/install.sh`, an interactive installer that asks for your terminal (kitty, Ghostty or both), can activate a dark/light pair and offers to uninstall when the themes are already installed.

## 0.6.1
- Preview images are now hosted in the GitHub repository so they display on the Marketplace and in the extension panel.
- Added the repository, issues and homepage links.
- README documents the kitty and Ghostty themes and how to rebuild everything.

## 0.6.0
- Five new light themes: **Noctis (EVA-01 Light)**, **Noctis (EVA-02 Light)**, **Noctis (EVA-08 Light)**, **Noctis (Geofront)** and **Noctis (Tabris)**.

## 0.5.0
- New theme: **Noctis (EVA-01 Berserk)**, a near-black violet dark theme with blood-red keywords, an acid yellow cursor and a red status bar.

## 0.4.0
- New themes: **Noctis (A.T. Field)** and **Noctis (Instrumentality)** (light), **Noctis (Terminal Dogma)**, **Noctis (Ramiel)** and **Noctis (Sachiel)** (dark).
- **Noctis (EVA-13)** redone as a darker take on EVA-01: near-black violet with toxic green and blood-orange accents (it was red and gold before).

## 0.3.0
- New themes: **Noctis (NERV)** and **Noctis (SEELE)**.
- New high contrast themes: **Noctis (NERV High Contrast)** (dark) and **Noctis (EVA Mark.06 High Contrast)** (light), with at least 7:1 text contrast and strong focus borders.
- README now includes preview images of every theme.

## 0.2.0
- New theme: **Noctis (MAGI)**, a warm-black dark theme with amber text, alert red and approval green, inspired by the MAGI system screens.

## 0.1.1
- Marketplace page rewritten in English with palette details, install and customization guides.
- Theme names are now `Noctis (EVA-NN)`.

## 0.1.0
- Initial release: Noctis (EVA-00), (EVA-01), (EVA-02), (EVA-03), (EVA-08), (EVA-13) and (EVA Mark.06).
