#!/usr/bin/env python3
"""Genera los temas de terminal (kitty, Ghostty, Alacritty, WezTerm y los de scripts/formats.py) desde las mismas paletas que la extension de VS Code."""
import importlib.util, sys
from pathlib import Path
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "../noctis-src/themes"]
spec = importlib.util.spec_from_file_location("build", Path(__file__).with_name("build.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

OUT = Path(__file__).resolve().parent.parent / "terminals"
KITTY, GHOST = OUT / "kitty" / "themes", OUT / "ghostty" / "themes"
ALACRITTY, WEZTERM = OUT / "alacritty" / "themes", OUT / "wezterm" / "themes"
for d in (KITTY, GHOST, ALACRITTY, WEZTERM): d.mkdir(parents=True, exist_ok=True)
spec_f = importlib.util.spec_from_file_location("formats", Path(__file__).with_name("formats.py"))
F = importlib.util.module_from_spec(spec_f); spec_f.loader.exec_module(F)
for folder, _, _ in F.FORMATS: (OUT / folder / "themes").mkdir(parents=True, exist_ok=True)
NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")

def blend(fg, bg, a):
    f = [int(fg[i:i+2], 16) for i in (1, 3, 5)]; g = [int(bg[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x * a + y * (1 - a)) for x, y in zip(f, g))

def on(color):  # texto negro o blanco segun contraste
    return "#000000" if b.contrast(color, "#000000") >= b.contrast(color, "#ffffff") else "#ffffff"

def data(p):
    light = p["type"] == "light"
    ansi = b.ansi_colors(p)
    sel = p["select"]; alpha = int(sel[7:9], 16) / 255 if len(sel) > 7 else 1
    sel = b.ensure(blend(sel[:7], p["bg"], alpha), p["bg"], 1.5, light)  # la seleccion debe distinguirse del fondo
    while b.contrast(p["text"], sel) < 4.5 and sel != p["bg"]:  # sin perder legibilidad del texto seleccionado
        sel = blend(p["bg"], sel, 0.9)
    return dict(ansi=ansi, cursor=b.cursor_color(p), sel=sel, fn=b.ensure(p["tokens"]["function"], p["bg"], 4.5, light))

def kitty(name, p, d):
    a = p["accent"]
    lines = [f"# vim:ft=kitty", f"## name: {name}", "## author: RavenEibu", "## license: MIT",
      "## upstream: https://github.com/liviuschera/noctis (MIT, Liviu Schera)",
      "## blurb: EVA Noctis, a Rebuild of Evangelion take on the Noctis theme family", "",
      f"foreground {p['text']}", f"background {p['bg']}", f"selection_foreground {p['text']}", f"selection_background {d['sel']}",
      f"cursor {d['cursor']}", f"cursor_text_color {p['bg']}", f"url_color {d['ansi'][6]}", "",
      f"active_border_color {a}", f"inactive_border_color {d['ansi'][8]}", f"bell_border_color {d['ansi'][3]}", "",
      "wayland_titlebar_color system", "macos_titlebar_color system", "",
      f"active_tab_foreground {on(a)}", f"active_tab_background {a}", f"inactive_tab_foreground {d['fn']}",
      f"inactive_tab_background {p['bg']}", f"tab_bar_background {p['side']}", "",
      f"mark1_foreground {on(d['ansi'][4])}", f"mark1_background {d['ansi'][4]}",
      f"mark2_foreground {on(d['ansi'][5])}", f"mark2_background {d['ansi'][5]}",
      f"mark3_foreground {on(d['ansi'][6])}", f"mark3_background {d['ansi'][6]}", ""]
    lines += [f"color{i} {c}" for i, c in enumerate(d["ansi"])]
    return "\n".join(lines) + "\n"

def ghostty(p, d):
    o = [f"background = {p['bg']}", f"foreground = {p['text']}", f"cursor-color = {d['cursor']}", f"cursor-text = {p['bg']}",
         f"selection-background = {d['sel']}", f"selection-foreground = {p['text']}"]
    o += [f"palette = {i}={c}" for i, c in enumerate(d["ansi"])]
    return "\n".join(o) + "\n"

def toml_header(name):
    return [f"# {name}", "# EVA Noctis (MIT, RavenEibu), based on the Noctis theme family (MIT, Liviu Schera)"]

def alacritty(name, p, d):
    o = toml_header(name) + ["", "[colors.primary]", f'background = "{p["bg"]}"', f'foreground = "{p["text"]}"', "",
         "[colors.cursor]", f'text = "{p["bg"]}"', f'cursor = "{d["cursor"]}"', "",
         "[colors.selection]", f'text = "{p["text"]}"', f'background = "{d["sel"]}"']
    for table, colors in (("normal", d["ansi"][:8]), ("bright", d["ansi"][8:])):
        o += ["", f"[colors.{table}]"] + [f'{n} = "{c}"' for n, c in zip(NAMES, colors)]
    return "\n".join(o) + "\n"

def wezterm(name, slug, p, d):
    a = p["accent"]
    q = lambda cs: "[" + ", ".join(f'"{c}"' for c in cs) + "]"
    o = toml_header(name) + ["", "[colors]", f'foreground = "{p["text"]}"', f'background = "{p["bg"]}"',
         f'cursor_bg = "{d["cursor"]}"', f'cursor_fg = "{p["bg"]}"', f'cursor_border = "{d["cursor"]}"',
         f'selection_fg = "{p["text"]}"', f'selection_bg = "{d["sel"]}"',
         f"ansi = {q(d['ansi'][:8])}", f"brights = {q(d['ansi'][8:])}", "",
         "[colors.tab_bar]", f'background = "{p["side"]}"', "",
         "[colors.tab_bar.active_tab]", f'bg_color = "{a}"', f'fg_color = "{on(a)}"', "",
         "[colors.tab_bar.inactive_tab]", f'bg_color = "{p["bg"]}"', f'fg_color = "{d["fn"]}"', "",
         "[metadata]", f'name = "{slug}"', 'author = "RavenEibu"', 'origin_url = "https://github.com/RavenEibu/eva-noctis"']
    return "\n".join(o) + "\n"

for key, p in b.P.items():
    d = data(p)
    slug = p.get("slug") or ("Noctis-" + key.upper().replace("EVA-MARK06", "EVA-Mark06"))
    (KITTY / f"{slug}.conf").write_text(kitty(f"Noctis ({p['name'].split('(')[-1].rstrip(')')})", p, d))
    (GHOST / slug).write_text(ghostty(p, d))
    label = f"Noctis ({p['name'].split('(')[-1].rstrip(')')})"
    (ALACRITTY / f"{slug}.toml").write_text(alacritty(label, p, d))
    (WEZTERM / f"{slug}.toml").write_text(wezterm(label, slug, p, d))
    for folder, suffix, render in F.FORMATS:
        (OUT / folder / "themes" / f"{slug}{suffix}").write_text(render(label, slug, p, d, dict(blend=blend, on=on, contrast=b.contrast)))
    print(slug)
