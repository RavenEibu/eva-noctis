"""Formatos de terminal adicionales, generados desde las mismas paletas.

Cada funcion recibe: label ("Noctis (EVA-01)"), slug ("Noctis-EVA-01"), p (paleta), d (datos de terminals.data)
y h (ayudantes: blend, on, contrast). Devuelve el texto del archivo.
"""
import json
import plistlib

NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
HEADER = "EVA Noctis (MIT, RavenEibu), based on the Noctis theme family (MIT, Liviu Schera)"


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def windows_terminal(label, slug, p, d, h):
    """Fragmento con "schemes": se pega en settings.json o se instala como fragment extension."""
    scheme = {"name": label, "foreground": p["text"], "background": p["bg"], "cursorColor": d["cursor"],
              "selectionBackground": d["sel"]}
    for i, name in enumerate(("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")):
        scheme[name] = d["ansi"][i]
        scheme["bright" + name.capitalize()] = d["ansi"][i + 8]
    return json.dumps({"schemes": [scheme]}, indent=2) + "\n"


def iterm2(label, slug, p, d, h):
    def color(c):
        r, g, b = (x / 255 for x in rgb(c))
        return {"Color Space": "sRGB", "Red Component": r, "Green Component": g, "Blue Component": b, "Alpha Component": 1.0}
    out = {f"Ansi {i} Color": color(c) for i, c in enumerate(d["ansi"])}
    out.update({"Background Color": color(p["bg"]), "Foreground Color": color(p["text"]), "Bold Color": color(p["text"]),
                "Cursor Color": color(d["cursor"]), "Cursor Text Color": color(p["bg"]),
                "Selection Color": color(d["sel"]), "Selected Text Color": color(p["text"]), "Link Color": color(d["ansi"][6])})
    return plistlib.dumps(out, sort_keys=True).decode()


def foot(label, slug, p, d, h):
    section = "colors-light" if p["type"] == "light" else "colors-dark"
    x = lambda c: c[1:]
    o = [f"# {label}", f"# {HEADER}", "# Needs foot 1.24+ (colors-dark / colors-light sections)", "", f"[{section}]",
         f"foreground={x(p['text'])}", f"background={x(p['bg'])}", f"selection-foreground={x(p['text'])}",
         f"selection-background={x(d['sel'])}", f"cursor={x(p['bg'])} {x(d['cursor'])}", f"urls={x(d['ansi'][6])}"]
    o += [f"regular{i}={x(c)}" for i, c in enumerate(d["ansi"][:8])] + [f"bright{i}={x(c)}" for i, c in enumerate(d["ansi"][8:])]
    return "\n".join(o) + "\n"


def konsole(label, slug, p, d, h):
    t = lambda c: "%d,%d,%d" % rgb(c)
    o = []
    def section(name, color):
        o.extend([f"[{name}]", f"Color={t(color)}", ""])
    section("Background", p["bg"]); section("BackgroundFaint", p["bg"]); section("BackgroundIntense", p["bg"])
    section("Foreground", p["text"]); section("ForegroundFaint", h["blend"](p["text"], p["bg"], 0.6)); section("ForegroundIntense", p["text"])
    for i in range(8):
        section(f"Color{i}", d["ansi"][i])
        section(f"Color{i}Faint", h["blend"](d["ansi"][i], p["bg"], 0.6))
        section(f"Color{i}Intense", d["ansi"][i + 8])
    o += ["[General]", f"Description={label}", "Opacity=1", ""]
    return "\n".join(o)


def xresources(label, slug, p, d, h):
    o = [f"! {label}", f"! {HEADER}", f"*.foreground: {p['text']}", f"*.background: {p['bg']}", f"*.cursorColor: {d['cursor']}"]
    return "\n".join(o + [f"*.color{i}: {c}" for i, c in enumerate(d["ansi"])]) + "\n"


def tmux(label, slug, p, d, h):
    a, bg = p["accent"], p["bg"]
    o = [f"# {label}", f"# {HEADER}", "# Usage: source-file ~/.config/tmux/themes/" + slug + ".conf", "",
         f'set -g status-style "bg={p["side"]},fg={p["text"]}"',
         f'set -g window-status-style "bg={p["side"]},fg={d["ansi"][8]}"',
         f'set -g window-status-current-style "bg={a},fg={h["on"](a)},bold"',
         f'set -g window-status-activity-style "fg={d["ansi"][3]}"',
         f'set -g window-status-bell-style "fg={d["ansi"][1]},bold"',
         f'set -g pane-border-style "fg={d["ansi"][8]}"',
         f'set -g pane-active-border-style "fg={a}"',
         f'set -g message-style "bg={a},fg={h["on"](a)}"',
         f'set -g message-command-style "bg={p["side"]},fg={p["text"]}"',
         f'set -g mode-style "bg={d["sel"]},fg={p["text"]}"',
         f'set -g display-panes-colour "{d["ansi"][8]}"',
         f'set -g display-panes-active-colour "{a}"',
         f'set -g clock-mode-colour "{a}"']
    return "\n".join(o) + "\n"


def zellij(label, slug, p, d, h):
    """Formato clasico de Zellij (fg/bg + 9 colores), aceptado por las versiones actuales."""
    c = d["ansi"]
    pairs = [("fg", p["text"]), ("bg", p["bg"]), ("black", c[0]), ("red", c[1]), ("green", c[2]), ("yellow", c[3]),
             ("blue", c[4]), ("magenta", c[5]), ("orange", p["accent"]), ("cyan", c[6]), ("white", c[7])]
    body = "\n".join(f'        {k} "{v}"' for k, v in pairs)
    return f"// {label}\n// {HEADER}\nthemes {{\n    {slug.lower()} {{\n{body}\n    }}\n}}\n"


def termux(label, slug, p, d, h):
    o = [f"# {label}", f"# {HEADER}", f"foreground={p['text']}", f"background={p['bg']}", f"cursor={d['cursor']}"]
    return "\n".join(o + [f"color{i}={c}" for i, c in enumerate(d["ansi"])]) + "\n"


def warp(label, slug, p, d, h):
    names = lambda cs: "\n".join(f"    {n}: '{c}'" for n, c in zip(NAMES, cs))
    return (f"# {label}\n# {HEADER}\nname: '{label}'\naccent: '{p['accent']}'\nbackground: '{p['bg']}'\nforeground: '{p['text']}'\n"
            f"details: {'lighter' if p['type'] == 'light' else 'darker'}\nterminal_colors:\n  normal:\n{names(d['ansi'][:8])}\n"
            f"  bright:\n{names(d['ansi'][8:])}\n")


# (carpeta, extension, funcion)
FORMATS = [
    ("windows-terminal", ".json", windows_terminal), ("iterm2", ".itermcolors", iterm2), ("foot", ".ini", foot),
    ("konsole", ".colorscheme", konsole), ("xresources", "", xresources), ("tmux", ".conf", tmux),
    ("zellij", ".kdl", zellij), ("termux", ".properties", termux), ("warp", ".yaml", warp),
]
