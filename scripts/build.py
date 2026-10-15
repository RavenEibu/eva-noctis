#!/usr/bin/env python3
"""Genera los temas EVA (Rebuild of Evangelion) a partir de Noctis (MIT, Liviu Schera).

Uso: python3 scripts/build.py <ruta-a-Noctis/themes>
Cada color de Noctis se transforma por familia de tono (fondos, acentos, tokens)
hacia una paleta EVA. Los ANSI de la terminal y los detalles clave se fijan a mano.
"""
import copy, json, re, sys, colorsys, tomllib
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "../noctis-src/themes")
OUT = Path(__file__).resolve().parent.parent / "themes"
HEX = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?")

# Colores semánticos de cada tema base
SEM = {
    "noctis": dict(comment="#5b858b", text="#b2cacd", keyword="#df769b", variable="#e4b781", annotation="#d67e5c",
                   constant="#d5971a", tag="#e66533", string="#49e9a6", interp="#16b673", number="#7060eb",
                   function="#16a3b6", support="#49d6e9", misc="#49ace9", invalid="#e3541c"),
    "lux": dict(comment="#8ca6a6", text="#004d57", keyword="#ff5792", variable="#fa8900", annotation="#b3694d",
                constant="#a88c00", tag="#e64100", string="#00b368", interp="#009456", number="#5842ff",
                function="#0095a8", support="#00bdd6", misc="#0094f0", invalid="#ff530f"),
}

def to_hls(hx):
    r, g, b = (int(hx[i:i+2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l

def to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, min(1, max(0, l)), min(1, max(0, s)))
    return "#%02x%02x%02x" % tuple(round(x * 255) for x in (r, g, b))

def make_transform(P):
    light = P["type"] == "light"
    sem = SEM[P["base"]]
    tok = {sem[k].lower(): v for k, v in P["tokens"].items()}
    bh, bs, _ = to_hls(P.get("tint", P["bg"]))
    ah, as_, _ = to_hls(P["accent"])
    th, ts, _ = to_hls(P["text"])
    surf_k = bs / (0.9 if light else 0.78)
    acc_k = min(1.0, as_ / (1.0 if light else 0.78))
    fam = {  # (rango de tono, ancla de Noctis, destino)
        "pink": (330, 350, sem["keyword"], P["tokens"]["keyword"]),
        "red": (0, 25, sem["tag"], P["tokens"]["tag"]),
        "amber": (26, 55, sem["constant"], P["tokens"]["constant"]),
        "green": (120, 160, sem["string"], P["tokens"]["string"]),
        "blue": (195, 215, sem["misc"], P["tokens"]["misc"]),
        "violet": (235, 255, sem["number"], P["tokens"]["number"]),
    }

    def conv(c):
        base, alpha = c[:7].lower(), c[7:]
        if base in ("#000000", "#ffffff"):
            return c
        if base in tok:
            return tok[base] + alpha
        h, s, l = to_hls(base)
        cream = light and 36 <= h <= 58 and l > 0.75
        teal = 178 <= h <= 192
        if cream:
            new = to_hex(bh, s * surf_k, l)
        elif s < 0.4:
            new = to_hex(bh if not light else th, min(0.45, s * 1.6 + bs * 0.15), l)
        elif teal:
            if light and l < 0.26:
                new = to_hex(th, ts, l)
            elif light and l > 0.78:
                new = to_hex(bh, s * surf_k, l)
            elif not light and l < 0.30:
                new = to_hex(bh, s * surf_k, l)
            else:
                new = to_hex(ah, s * acc_k, l)
        else:
            new = base
            for lo, hi, ref, tgt in fam.values():
                if lo <= h <= hi:
                    rh, rs, rl = to_hls(ref)
                    nh, ns, nl = to_hls(tgt)
                    new = to_hex(nh, s * (ns / rs if rs else 1), l + (nl - rl))
                    break
        return new + alpha

    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, str):
            return HEX.sub(lambda m: conv(m.group(0)), o)
        return o
    return walk

TOKENS = ("comment", "text", "keyword", "variable", "annotation", "constant", "tag", "string", "interp", "number", "function",
          "support", "misc", "invalid")
REQUIRED = ("name", "type", "base", "bg", "side", "text", "accent", "accent2", "status", "status_fg", "select", "ansi", "tokens")

def load_palettes(path=Path(__file__).with_name("palettes.toml")):
    """Lee scripts/palettes.toml. Una paleta con `extends` copia a su padre y solo cambia lo que declara (los tokens se mezclan uno a uno)."""
    palettes = {}
    for key, spec in tomllib.loads(path.read_text()).items():
        spec = copy.deepcopy(spec)
        parent = spec.pop("extends", None)
        if parent:
            if parent not in palettes:
                raise ValueError(f"{key}: extends {parent!r}, which must be defined earlier in {path.name}")
            merged = copy.deepcopy(palettes[parent])
            merged["tokens"].update(spec.pop("tokens", {}))
            merged.update(spec)
            spec = merged
        missing = [k for k in REQUIRED if k not in spec]
        if missing or set(spec["tokens"]) != set(TOKENS) or len(spec["ansi"]) != 16:
            raise ValueError(f"{key}: palette needs {REQUIRED}, the 14 tokens {TOKENS} and 16 ANSI colors (missing: {missing})")
        palettes[key] = spec
    return palettes

P = load_palettes()

def lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)

def ensure(fg, bg, minimum, light):
    """Ajusta la luminosidad hasta alcanzar el contraste minimo, conservando tono y saturacion."""
    h, s, l = to_hls(fg)
    step = -0.01 if light else 0.01
    while contrast(fg, bg) < minimum and 0.0 <= l + step <= 1.0:
        l += step
        fg = to_hex(h, s, l)
    return fg

def cursor_color(p):
    """Color del cursor con al menos 3:1 sobre el fondo (los temas claros usaban un naranja demasiado palido)."""
    return ensure(p["accent2"], p["bg"], 7.0 if p.get("hc") else 3.0, p["type"] == "light")

def ansi_min(p, i):
    """Contraste minimo contra el fondo de cada color ANSI.
    Texto (1-6, 9-14) y gris (8, comentarios y sugerencias): 3:1. En alto contraste todo exige 7:1.
    El negro (0) de los temas oscuros y el blanco (7, 15) de los claros eran casi invisibles (~1.1:1): ahora son un gris legible,
    como en otros temas claros/oscuros populares, para que `ls` o `git diff` no pinten texto invisible."""
    if p.get("hc"):
        return 7.0
    if p["type"] == "light":
        return {7: 3.5, 15: 3.0}.get(i, 3.0 if i != 0 else 0)
    return 1.5 if i == 0 else 0 if i in (7, 15) else 3.0

def ansi_colors(p):
    """16 colores ANSI ajustados a ansi_min (negro de los temas claros y blanco de los oscuros se respetan)."""
    light = p["type"] == "light"
    out = []
    for i, v in enumerate(p["ansi"]):
        if light and i in (7, 15) and not p.get("hc"):  # el "blanco" de un tema claro es un gris neutro, no un azul que se confunda con el color 4
            h, sat, l = to_hls(v)
            v = to_hex(h, min(sat, 0.12), l)
        out.append(ensure(v, p["bg"], ansi_min(p, i), light) if ansi_min(p, i) else v)
    return out

ANSI = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]

def build(key, p):
    light = p["type"] == "light"
    hc = p.get("hc", False)
    mn = 7.0 if hc else 4.5
    p["tokens"] = {k: (v if k in ("text",) else ensure(v, p["bg"], 4.0 if (k == "comment" and not hc) else mn, light))
                   for k, v in p["tokens"].items()}
    p["ansi"] = ansi_colors(p)
    base = json.loads((SRC / f"{p['base']}.json").read_text())
    t = make_transform(p)(base)
    t["name"], t["type"] = p["name"], p["type"]
    c = t["colors"]
    for i, n in enumerate(ANSI):
        c[f"terminal.ansi{n}"], c[f"terminal.ansiBright{n}"] = p["ansi"][i], p["ansi"][i + 8]
    c.update({
        "editor.background": p["bg"], "editor.foreground": p["text"], "terminal.background": p["bg"],
        "terminal.foreground": p["text"], "sideBar.background": p["side"], "activityBar.background": p["side"],
        "titleBar.activeBackground": p["side"], "titleBar.inactiveBackground": p["side"],
        "statusBar.background": p["status"], "statusBar.foreground": p["status_fg"],
        "editorCursor.foreground": cursor_color(p), "tab.activeBorderTop": p["accent2"],
        "editor.selectionBackground": p["select"], "focusBorder": p["accent"],
        "editorWarning.foreground": ensure(p["tokens"]["constant"], p["bg"], mn, light),
        "editorError.foreground": ensure(p["tokens"]["invalid"], p["bg"], mn, light),
    })
    if p.get("oled"):
        edge = "#1e1e1e"
        for k in ("panel.background", "editorGroupHeader.tabsBackground", "tab.inactiveBackground", "tab.activeBackground", "tab.unfocusedActiveBackground",
                  "breadcrumb.background", "sideBarSectionHeader.background", "terminal.background", "editorGroup.emptyBackground",
                  "activityBar.background", "sideBar.background", "titleBar.activeBackground", "titleBar.inactiveBackground", "editor.background"):
            c[k] = "#000000"
        for k in ("sideBar.border", "panel.border", "editorGroup.border", "tab.border", "activityBar.border", "titleBar.border",
                  "editorGroupHeader.tabsBorder", "sideBarSectionHeader.border", "statusBar.border", "breadcrumb.border"):
            c[k] = edge
        c["editor.lineHighlightBackground"] = "#ffffff0d"
        c["editor.lineHighlightBorder"] = "#00000000"
        c["tab.activeBorder"] = p["accent"]
    if hc:
        c["contrastBorder"] = "#ffffff" if not light else "#000000"
        c["contrastActiveBorder"] = p["accent"]
    if p["status_fg"] == "#ffffff":  # texto blanco: oscurece el fondo hasta contraste legible
        c["statusBar.background"] = ensure(c["statusBar.background"], "#ffffff", 4.5, True)
    (OUT / f"{key}.json").write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n")
    print("ok", key)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for k, v in P.items():
        build(k, v)
