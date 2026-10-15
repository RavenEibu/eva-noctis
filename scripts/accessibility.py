#!/usr/bin/env python3
"""Informe de accesibilidad de los colores ANSI: distancia entre colores (CIE76) con vision normal y deuteranopia.

    python3 scripts/accessibility.py            # lista los pares debiles
    python3 scripts/accessibility.py --all      # todos los temas

El test exige que los colores de texto sean distinguibles entre si con vision normal. Para deuteranopia solo informa:
algunos temas (por ejemplo EVA-03) confunden azul y violeta, y no se pueden separar sin cambiar el caracter del tema.
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


def pairs(ansi):
    for group in (range(1, 7), range(9, 15)):
        yield from itertools.combinations(group, 2)


def weakest_normal(palette):
    ansi = B["ansi_colors"](palette)
    return min((distance(ansi[i], ansi[j]), i, j) for i, j in pairs(ansi))


def main():
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
