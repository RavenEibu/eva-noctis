#!/usr/bin/env python3
"""Genera los temas de kitty y Ghostty desde las mismas paletas que la extension de VS Code."""
import importlib.util, sys
from pathlib import Path
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "../noctis-src/themes"]
spec = importlib.util.spec_from_file_location("build", Path(__file__).with_name("build.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

OUT = Path(__file__).resolve().parent.parent / "terminals"
KITTY, GHOST = OUT / "kitty" / "themes", OUT / "ghostty" / "themes"
for d in (KITTY, GHOST): d.mkdir(parents=True, exist_ok=True)

def blend(fg, bg, a):
    f = [int(fg[i:i+2], 16) for i in (1, 3, 5)]; g = [int(bg[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x * a + y * (1 - a)) for x, y in zip(f, g))

def on(color):  # texto negro o blanco segun contraste
    return "#000000" if b.contrast(color, "#000000") >= b.contrast(color, "#ffffff") else "#ffffff"

def data(p):
    light = p["type"] == "light"
    ansi = [b.ensure(v, p["bg"], 7.0 if p.get("hc") else 3.0, light) if (p.get("hc") or i not in (0, 7, 8, 15)) else v for i, v in enumerate(p["ansi"])]
    sel = p["select"]; alpha = int(sel[7:9], 16) / 255 if len(sel) > 7 else 1
    return dict(ansi=ansi, sel=blend(sel[:7], p["bg"], alpha), fn=b.ensure(p["tokens"]["function"], p["bg"], 4.5, light))

def kitty(name, p, d):
    a, o = p["accent"], p["accent2"]
    lines = [f"# vim:ft=kitty", f"## name: {name}", "## based on the Noctis theme family (MIT, Liviu Schera)", "",
      f"foreground {p['text']}", f"background {p['bg']}", f"selection_foreground {p['text']}", f"selection_background {d['sel']}",
      f"cursor {o}", f"cursor_text_color {p['bg']}", f"url_color {d['ansi'][6]}", "",
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
    o = [f"background = {p['bg']}", f"foreground = {p['text']}", f"cursor-color = {p['accent2']}", f"cursor-text = {p['bg']}",
         f"selection-background = {d['sel']}", f"selection-foreground = {p['text']}"]
    o += [f"palette = {i}={c}" for i, c in enumerate(d["ansi"])]
    return "\n".join(o) + "\n"

for key, p in b.P.items():
    d = data(p)
    slug = p.get("slug") or ("Noctis-" + key.upper().replace("EVA-MARK06", "EVA-Mark06"))
    (KITTY / f"{slug}.conf").write_text(kitty(f"Noctis ({p['name'].split('(')[-1].rstrip(')')})", p, d))
    (GHOST / slug).write_text(ghostty(p, d))
    print(slug)
