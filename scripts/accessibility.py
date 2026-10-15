#!/usr/bin/env python3
"""Accesibilidad del color: pares de colores parecidos con vision normal y con daltonismo (protanopia, deuteranopia, tritanopia).

    python3 scripts/accessibility.py            # lista los pares debiles
    python3 scripts/accessibility.py --all      # todos los temas
    python3 scripts/accessibility.py --write    # actualiza la tabla del README y docs/color-vision.md

El test exige que los colores de texto sean distinguibles entre si con vision normal. Para cada tipo de daltonismo se
calcula una recomendacion por tema (ver assess): no cambia los colores, solo informa cuales son recomendables.
"""
import itertools
import math
import runpy
import sys
from pathlib import Path

MIN_NORMAL = 15.0   # distancia minima entre dos colores de texto (1-6 o 9-14) con vision normal
WEAK_DEUTERANOPIA = 6.0

B = runpy.run_path(str(Path(__file__).with_name("build.py")))


def _linear(channel):
    c = channel / 255
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def _rgb(hexcolor):
    return [_linear(int(hexcolor[i:i + 2], 16)) for i in (1, 3, 5)]


def lab(hexcolor):
    r, g, b = _rgb(hexcolor)
    x, y, z = (.4124 * r + .3576 * g + .1805 * b) / .95047, .2126 * r + .7152 * g + .0722 * b, (.0193 * r + .1192 * g + .9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def distance(a, b):
    return math.dist(lab(a), lab(b))


def deuteranopia(hexcolor):
    """Simulacion de Machado et al. (2009), severidad 1.0, sobre RGB lineal."""
    matrix = ((.367322, .860646, -.227968), (.280085, .672501, .047413), (-.011820, .042940, .968881))
    linear = _rgb(hexcolor)
    out = [max(0, min(1, sum(m * v for m, v in zip(row, linear)))) for row in matrix]
    encode = lambda v: 12.92 * v if v <= .0031308 else 1.055 * v ** (1 / 2.4) - .055
    return "#%02x%02x%02x" % tuple(round(encode(v) * 255) for v in out)


# Matrices de Machado, Oliveira y Fernandes (2009), severidad 1.0, sobre RGB lineal
CVD = {
    "protanopia": ((.152286, 1.052583, -.204868), (.114503, .786281, .099216), (-.003882, -.048116, 1.051998)),
    "deuteranopia": ((.367322, .860646, -.227968), (.280085, .672501, .047413), (-.011820, .042940, .968881)),
    "tritanopia": ((1.255528, -.076749, -.178779), (-.078411, .930809, .147602), (.004733, .691367, .303900)),
}
ANSI_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
SYNTAX = ("keyword", "string", "function", "number", "constant", "variable", "tag", "support", "misc")
# (minimo "recomendado", minimo "con cuidado") para la peor distancia entre dos colores
ANSI_LEVELS, RG_LEVELS, SYNTAX_LEVELS = (8.0, 4.0), (15.0, 8.0), (5.0, 2.5)


def simulate(hexcolor, kind):
    linear = _rgb(hexcolor)
    out = [max(0, min(1, sum(m * v for m, v in zip(row, linear)))) for row in CVD[kind]]
    encode = lambda v: 12.92 * v if v <= .0031308 else 1.055 * v ** (1 / 2.4) - .055
    return "#%02x%02x%02x" % tuple(round(encode(v) * 255) for v in out)


def _level(value, levels):
    return 2 if value >= levels[0] else 1 if value >= levels[1] else 0


def _worst(colors, names, kind, idx_groups):
    """Par mas parecido (distancia, nombre a, nombre b) entre los grupos de indices dados."""
    seen = [simulate(c, kind) for c in colors]
    return min((distance(seen[i], seen[j]), names[i], names[j]) for g in idx_groups for i, j in itertools.combinations(g, 2))


def assess(palette):
    """Para cada tipo de daltonismo: nivel 2 (recomendado), 1 (con cuidado) o 0 (no recomendado), con los numeros que lo explican.

    Se mira lo que lleva significado: los colores ANSI de texto (rojo/verde de exito y error aparte, porque es lo que mas se
    confunde en diffs y tests) y los 9 colores de sintaxis. El nivel final es el peor de los tres criterios.
    """
    ansi = B["ansi_colors"](palette)
    ansi_names = [("bright " if i > 7 else "") + ANSI_NAMES[i % 8] for i in range(16)]
    tokens = B["token_colors"](palette)
    result = {}
    for kind in CVD:
        a_dist, a1, a2 = _worst(ansi, ansi_names, kind, (range(1, 7), range(9, 15)))
        seen = [simulate(c, kind) for c in ansi]
        rg = min(distance(seen[1], seen[2]), distance(seen[9], seen[10]))
        s_dist, s1, s2 = _worst([tokens[k] for k in SYNTAX], SYNTAX, kind, (range(len(SYNTAX)),))
        levels = (_level(a_dist, ANSI_LEVELS), _level(rg, RG_LEVELS), _level(s_dist, SYNTAX_LEVELS))
        result[kind] = dict(level=min(levels), ansi=(a_dist, a1, a2), red_green=rg, syntax=(s_dist, s1, s2), levels=levels)
    return result


def pairs(ansi):
    for group in (range(1, 7), range(9, 15)):
        yield from itertools.combinations(group, 2)


def weakest_normal(palette):
    ansi = B["ansi_colors"](palette)
    return min((distance(ansi[i], ansi[j]), i, j) for i, j in pairs(ansi))


ROOT = Path(__file__).resolve().parent.parent
README, DETAILS = ROOT / "README.md", ROOT / "docs" / "color-vision.md"
MARK_START, MARK_END = "<!-- cvd:start -->", "<!-- cvd:end -->"
ICON = {2: "✅", 1: "⚠️", 0: "❌"}
LABEL = {"protanopia": "Protanopia", "deuteranopia": "Deuteranopia", "tritanopia": "Tritanopia"}


def _rows():
    return [(palette["name"].replace("Noctis (", "").rstrip(")"), assess(palette)) for palette in B["P"].values()]


def readme_table():
    rows = _rows()
    out = ["| Theme | " + " | ".join(LABEL.values()) + " |", "| --- | :---: | :---: | :---: |"]
    out += [f"| {name} | " + " | ".join(ICON[a[k]["level"]] for k in CVD) + " |" for name, a in rows]
    best = []
    for kind in CVD:
        names = [name for name, a in rows if a[kind]["level"] == 2]
        best.append(f"- **{LABEL[kind]}**: {', '.join(names) if names else 'none reaches ✅'}.")
    return "\n".join(out + ["", "Recommended per type:", *best])


def details():
    rows = _rows()
    out = ["# Color vision deficiency: details", "",
           "Generated by `python3 scripts/accessibility.py --write`; do not edit by hand.", "",
           "Colors are simulated with the Machado, Oliveira and Fernandes (2009) matrices at full severity and compared with CIE76 ΔE "
           "(about 2.3 is the smallest difference a person with normal vision notices; above ~15 two colors are clearly different). "
           "Each theme is rated per type of color blindness on three things, and the rating is the worst of the three:", "",
           f"| What | ✅ recommended | ⚠️ use with care | ❌ not recommended |", "| --- | --- | --- | --- |",
           f"| Closest pair of terminal text colors (ANSI 1-6, 9-14) | ΔE ≥ {ANSI_LEVELS[0]:g} | ≥ {ANSI_LEVELS[1]:g} | below |",
           f"| Red vs green, normal and bright (success/error, diffs) | ΔE ≥ {RG_LEVELS[0]:g} | ≥ {RG_LEVELS[1]:g} | below |",
           f"| Closest pair of the 9 syntax colors | ΔE ≥ {SYNTAX_LEVELS[0]:g} | ≥ {SYNTAX_LEVELS[1]:g} | below |", "",
           "❌ does not mean unusable: it means that some colors that carry meaning become (nearly) indistinguishable, so the theme "
           "should not be the only thing telling the two apart. Text contrast does not depend on color vision and is enforced for every theme "
           "(4.5:1 syntax, 4:1 comments, 7:1 in the high contrast themes).", "",
           "**Achromatopsia (no color at all)**: no theme separates its colors by lightness alone, so none is rated. Readability is still "
           "guaranteed by the contrast contract; the two high contrast themes (NERV High Contrast, EVA Mark.06 High Contrast) give the strongest "
           "text contrast, and bold/italic/position carry the rest.", ""]
    for kind in CVD:
        out += [f"## {LABEL[kind]}", "", "| Theme | Rating | Closest ANSI pair | Red/green | Closest syntax pair |", "| --- | :---: | --- | ---: | --- |"]
        for name, a in rows:
            v = a[kind]
            out.append(f"| {name} | {ICON[v['level']]} | {v['ansi'][1]} / {v['ansi'][2]} ({v['ansi'][0]:.1f}) | {v['red_green']:.1f} | "
                       f"{v['syntax'][1]} / {v['syntax'][2]} ({v['syntax'][0]:.1f}) |")
        out.append("")
    return "\n".join(out)


def readme_current():
    text = README.read_text()
    return MARK_START in text and text.split(MARK_START)[1].split(MARK_END)[0].strip() == readme_table().strip()


def write():
    text = README.read_text()
    head, rest = text.split(MARK_START)
    tail = rest.split(MARK_END)[1]
    README.write_text(f"{head}{MARK_START}\n{readme_table()}\n{MARK_END}{tail}")
    DETAILS.parent.mkdir(exist_ok=True)
    DETAILS.write_text(details())


def main():
    if "--write" in sys.argv:
        write()
        print("README.md and docs/color-vision.md updated")
        return
    show_all = "--all" in sys.argv
    print(f"Pares con vision normal < {MIN_NORMAL} o deuteranopia < {WEAK_DEUTERANOPIA} (CIE76):")
    for key, palette in B["P"].items():
        ansi = B["ansi_colors"](palette)
        rows = []
        for i, j in pairs(ansi):
            plain, deut = distance(ansi[i], ansi[j]), distance(deuteranopia(ansi[i]), deuteranopia(ansi[j]))
            if show_all or plain < MIN_NORMAL or deut < WEAK_DEUTERANOPIA:
                rows.append(f"  ANSI {i}/{j} {ansi[i]} {ansi[j]}  normal {plain:5.1f}  deuteranopia {deut:5.1f}")
        if rows:
            print(key); print("\n".join(rows))


if __name__ == "__main__":
    main()
