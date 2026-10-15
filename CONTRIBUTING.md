# Contributing

Everything is generated from `scripts/palettes.toml`; do not edit files under `themes/` or `terminals/*/themes/` by hand.

```bash
bash scripts/build_all.sh --check   # clone the pinned Noctis base, regenerate, test, package, fail if outputs are stale
bash scripts/smoke_terminals.sh     # load the themes with whichever terminals you have installed
bash scripts/check_vsce.sh          # the VSIX ships what `vsce package` would ship (needs node)
python3 scripts/accessibility.py    # ANSI colors that look alike; add --write to refresh the color-vision table in the README
```

## Changing or adding a palette
1. Edit `scripts/palettes.toml` (a variant can `extends` another palette and override only what changes). List new palettes in `ORDER` of `scripts/screenshots.py` and in `package.json`.
2. Run `bash scripts/build_all.sh`. Text colors are adjusted automatically to the contrast targets; packaging fails if a target is missed.
3. `python3 scripts/screenshots.py` refreshes `images/` (needs Playwright with Chromium).
4. Commit the regenerated `themes/` and `terminals/` together with the palette change.

## Adding a terminal format
Write a renderer in `scripts/formats.py`, add it to `FORMATS`, add its parser to `parse_extra` and `EXTRA_TERMINALS` in `scripts/package.py` so its colors are compared with the VS Code terminal, and (if it is just a folder of files) add it to `SIMPLE` in `terminals/install.sh`. Prefer validating it with the real application and say in the README how it was checked.

## Conventions
- Keep `install.sh` shellcheck-clean (`shellcheck -S warning`) and bash 3.2 compatible.
- Anything the README promises (contrast, true-black OLED, parity) must be enforced by `scripts/package.py`.
- Releases: bump `package.json` and `CHANGELOG.md`, merge, tag `vX.Y.Z`; the release workflow publishes the VSIX, the terminals zip and `SHA256SUMS`.
