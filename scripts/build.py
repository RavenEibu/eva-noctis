#!/usr/bin/env python3
"""Genera los temas EVA (Rebuild of Evangelion) a partir de Noctis (MIT, Liviu Schera).

Uso: python3 scripts/build.py <ruta-a-Noctis/themes>
Cada color de Noctis se transforma por familia de tono (fondos, acentos, tokens)
hacia una paleta EVA. Los ANSI de la terminal y los detalles clave se fijan a mano.
"""
import json, re, sys, colorsys
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
    bh, bs, _ = to_hls(P["bg"])
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

def tokens(comment, text, keyword, variable, annotation, constant, tag, string, interp, number, function, support, misc, invalid):
    return dict(comment=comment, text=text, keyword=keyword, variable=variable, annotation=annotation, constant=constant,
                tag=tag, string=string, interp=interp, number=number, function=function, support=support, misc=misc, invalid=invalid)

P = {}
# EVA-01: violeta + verde neón + naranja
P["eva-01"] = dict(name="Noctis (EVA-01)", type="dark", base="noctis", bg="#0d0620", side="#080315", text="#ece4ff",
    accent="#39ff14", accent2="#39ff14", status="#5a1fd1", status_fg="#ffffff", select="#7b2cff66",
    tokens=tokens("#7c64b5", "#ece4ff", "#ff4fd8", "#ff9440", "#ff7a59", "#ff6a00", "#ff2d6f", "#39ff14", "#2ed914",
                  "#9a5cff", "#b48cff", "#2ff0d0", "#7aa0ff", "#ff2d55"),
    ansi=["#1a0f33", "#ff2d55", "#39ff14", "#ff6a00", "#7b2cff", "#ff4fd8", "#2ff0d0", "#d8ccf5",
          "#4a3a7a", "#ff6b86", "#7dff5c", "#ff9440", "#a880ff", "#ff85e6", "#7bf7e2", "#ffffff"])
# EVA-02: rojo + naranja + amarillo de los ojos
P["eva-02"] = dict(name="Noctis (EVA-02)", type="dark", base="noctis", bg="#150409", side="#0e0206", text="#ffe9e4",
    accent="#ff1f3d", accent2="#ffe100", status="#c00f26", status_fg="#ffffff", select="#ff1f3d55",
    tokens=tokens("#a05a66", "#ffe9e4", "#ff3d3d", "#ffb020", "#ff8a4d", "#ff7a00", "#ff2a5f", "#9cf05a", "#6fcf3a",
                  "#ff5fa8", "#ff8a1a", "#ffe100", "#ff7a90", "#ff1f3d"),
    ansi=["#26090f", "#ff1f3d", "#9cf05a", "#ffb020", "#c77dff", "#ff5fa8", "#26e0d0", "#e8cfd0",
          "#6a3a42", "#ff5468", "#b8ff80", "#ffe100", "#dba3ff", "#ff8cc4", "#78f0e4", "#ffffff"])
# EVA-03: negro + hielo + rojo
P["eva-03"] = dict(name="Noctis (EVA-03)", type="dark", base="noctis", bg="#07080b", side="#030406", text="#e6eefc",
    accent="#ff2a2a", accent2="#28d4ff", status="#c41414", status_fg="#ffffff", select="#28d4ff44",
    tokens=tokens("#5f6f8a", "#e6eefc", "#ff3a3a", "#ffb84d", "#ff7a5c", "#ffa000", "#ff2a55", "#4dffb0", "#2ed98a",
                  "#8a7dff", "#28d4ff", "#7be8ff", "#5aa8ff", "#ff2a2a"),
    ansi=["#12151c", "#ff2a2a", "#4dffb0", "#ffa000", "#5aa8ff", "#c07dff", "#28d4ff", "#cdd8ee",
          "#3d4760", "#ff6262", "#8affcc", "#ffc84d", "#8ac4ff", "#d9a5ff", "#7be8ff", "#ffffff"])
# EVA-08: rosa fucsia + cian
P["eva-08"] = dict(name="Noctis (EVA-08)", type="dark", base="noctis", bg="#16051a", side="#0f0312", text="#ffe6f8",
    accent="#ff2fa0", accent2="#21e6ff", status="#d4157f", status_fg="#ffffff", select="#ff2fa055",
    tokens=tokens("#9a5c98", "#ffe6f8", "#ff2fa0", "#ffa64d", "#ff7a9a", "#ffb400", "#ff3d6e", "#4dffc0", "#2ed99a",
                  "#b26bff", "#21e6ff", "#7af0ff", "#6aa8ff", "#ff2d6a"),
    ansi=["#2a0d2c", "#ff3d6e", "#4dffc0", "#ffb400", "#6aa8ff", "#ff2fa0", "#21e6ff", "#f0d0ea",
          "#663a66", "#ff6f96", "#8affd8", "#ffd24d", "#95c0ff", "#ff70c4", "#7af0ff", "#ffffff"])
# EVA-13: version mas oscura de EVA-01 (violeta casi negro, verde toxico apagado, naranja sangre)
P["eva-13"] = dict(name="Noctis (EVA-13)", type="dark", base="noctis", bg="#060310", side="#030108", text="#ddd3f0",
    accent="#7a3cff", accent2="#2bd14a", status="#4a1fa8", status_fg="#ffffff", select="#6a2cd655",
    tokens=tokens("#6a5a92", "#ddd3f0", "#d13fc0", "#ff7a3d", "#e8683a", "#ff5a1f", "#e0143a", "#2fd45a", "#22a845",
                  "#8a55ff", "#a985ff", "#3ad1b8", "#6f8cff", "#e0143a"),
    ansi=["#150b26", "#e0143a", "#2fd45a", "#ff5a1f", "#6a2cd6", "#d13fc0", "#3ad1b8", "#c9bde6",
          "#3d2c66", "#ff4d6a", "#6ae88a", "#ff8a4d", "#9a7cf0", "#e36fd6", "#7be8d4", "#ffffff"])
# EVA-00: celeste + naranja (claro)
P["eva-00"] = dict(name="Noctis (EVA-00)", type="light", base="lux", bg="#eaf6ff", side="#d8ecfb", text="#0d2a4a",
    accent="#0a84e6", accent2="#ff6a00", status="#0a84e6", status_fg="#ffffff", select="#9fd3ff88",
    tokens=tokens("#6f8fb0", "#0d2a4a", "#e85a00", "#c76500", "#b8501f", "#b87800", "#d42a1f", "#0f9d58", "#0b7d46",
                  "#6a3df0", "#0a84e6", "#0aa0c0", "#2f6fe0", "#d42a1f"),
    ansi=["#33445c", "#d42a1f", "#0f9d58", "#e85a00", "#0a84e6", "#7a4fe0", "#0aa0c0", "#c6d8ea",
          "#6b7f96", "#f0584a", "#2fbf78", "#ff8a1a", "#3aa0ff", "#9a78f0", "#2fbcd6", "#ffffff"])
# Mark.06: blanco plata + rojo anaranjado (claro)
P["eva-mark06"] = dict(name="Noctis (EVA Mark.06)", type="light", base="lux", bg="#f4f5f9", side="#e6e8f0", text="#1a1d2e",
    accent="#6a3df0", accent2="#ff3d00", status="#1a1d2e", status_fg="#ffffff", select="#c9c2ff88",
    tokens=tokens("#8a8fa8", "#1a1d2e", "#ff3d00", "#c76a00", "#b8501f", "#b08000", "#d4143a", "#12a15c", "#0b7d46",
                  "#6a3df0", "#3a5bd9", "#0a9ab8", "#5a4fe0", "#d4143a"),
    ansi=["#2a2d40", "#d4143a", "#12a15c", "#ff6a00", "#3a5bd9", "#a03df0", "#0a9ab8", "#d0d3e0",
          "#6b7090", "#f0455f", "#35c47c", "#ff8a1a", "#5f80f0", "#bc70ff", "#2fbcd6", "#ffffff"])

# MAGI: monitores de los superordenadores (negro calido, ambar, rojo de alerta, verde/cian de aprobacion)
P["magi"] = dict(name="Noctis (MAGI)", type="dark", base="noctis", bg="#0a0604", side="#050302", text="#ffc27a",
    accent="#ff6a00", accent2="#ffb000", status="#c24e00", status_fg="#ffffff", select="#ff6a0055",
    tokens=tokens("#9a6a3f", "#ffc27a", "#ff4d2e", "#ffc247", "#ff8f4d", "#ff9f1a", "#ff2a4d", "#3dffa8", "#24c98a",
                  "#ffe066", "#4dd8ff", "#19d3c5", "#6aa8ff", "#ff1f3d"),
    ansi=["#1f130b", "#ff2a2a", "#3dffa8", "#ff9f1a", "#4d9bff", "#c96bff", "#19d3c5", "#e8cfae",
          "#5c4028", "#ff5c4d", "#7dffc4", "#ffc247", "#85bbff", "#dd9bff", "#66eee0", "#ffffff"])

# NERV: negro, rojo NERV y blanco
P["nerv"] = dict(name="Noctis (NERV)", type="dark", base="noctis", bg="#0c0c0f", side="#060608", text="#f0f0f0",
    accent="#e60012", accent2="#ffffff", status="#c8000f", status_fg="#ffffff", select="#e6001255",
    tokens=tokens("#82828e", "#f0f0f0", "#ff2a3a", "#f0b060", "#ff7a5c", "#ffa726", "#e60012", "#52e08a", "#34b86a",
                  "#ffe27a", "#7fb2ff", "#66d9e8", "#a0a8ff", "#ff1f2d"),
    ansi=["#1a1a20", "#e60012", "#52e08a", "#ffa726", "#5e9bff", "#d16bd0", "#4fd1d9", "#e0e0e6",
          "#4a4a55", "#ff4d5a", "#86f0b0", "#ffd166", "#8cb8ff", "#e598e4", "#86e6ec", "#ffffff"])
# SEELE: vacio azul-negro, indigo frio y rojo de los monolitos
P["seele"] = dict(name="Noctis (SEELE)", type="dark", base="noctis", bg="#05060d", side="#020308", text="#d5dcf5",
    accent="#5b6cff", accent2="#ff3b30", status="#3a49d9", status_fg="#ffffff", select="#5b6cff55",
    tokens=tokens("#6874a8", "#d5dcf5", "#ff4d4d", "#c9b3ff", "#ff8f7a", "#ffb454", "#ff3b5c", "#4be0c6", "#34b8a2",
                  "#8fa0ff", "#6c8cff", "#7ad7ff", "#a58bff", "#ff2a4d"),
    ansi=["#12142a", "#ff3b30", "#4be0c6", "#ffb454", "#6c8cff", "#b48cff", "#7ad7ff", "#d5dcf5",
          "#454b78", "#ff6a60", "#86f0dc", "#ffcf85", "#9fb4ff", "#cdb0ff", "#a6e6ff", "#ffffff"])

# A.T. Field: crema calido con naranja hexagonal (claro)
P["at-field"] = dict(name="Noctis (A.T. Field)", type="light", base="lux", bg="#fff6ea", side="#ffe9d1", text="#3a1e0c", slug="Noctis-AT-Field",
    accent="#ff6a00", accent2="#d84a00", status="#c94f00", status_fg="#ffffff", select="#ffb36677",
    tokens=tokens("#a07a5a", "#3a1e0c", "#d43f00", "#a35a00", "#b8501f", "#9a6a00", "#c81e1e", "#1f8f5f", "#177a4d",
                  "#5a3fd0", "#0f7fb0", "#0a8f9a", "#3a5bd9", "#c81e1e"),
    ansi=["#3a2a20", "#c81e1e", "#1f8f5f", "#c86a00", "#2f6fd0", "#a03fb8", "#0a8f9a", "#d8c8b8",
          "#7a6252", "#e04a3a", "#3fb07f", "#ff8a1a", "#5a8ff0", "#bd60d4", "#2fb0bc", "#ffffff"])
# Instrumentality: mar rojo, cielo rosado y blanco de Lilith (claro)
P["instrumentality"] = dict(name="Noctis (Instrumentality)", type="light", base="lux", bg="#fdf0f2", side="#f7dfe4", text="#3a0f1d", slug="Noctis-Instrumentality",
    accent="#d4142a", accent2="#b04fc0", status="#b30f24", status_fg="#ffffff", select="#f5a9b877",
    tokens=tokens("#a8798a", "#3a0f1d", "#d4142a", "#a0492e", "#b0603a", "#a0680a", "#a10f5a", "#1f8a6a", "#167a5a",
                  "#8a3fc0", "#b0308a", "#0e7f96", "#5a4fd0", "#d4142a"),
    ansi=["#3a1a26", "#d4142a", "#1f8a6a", "#b86a00", "#5a4fd0", "#b0308a", "#0e7f96", "#e4cdd2",
          "#7a5060", "#f0455f", "#3fae8a", "#e08a1a", "#7f78f0", "#cc55b0", "#2fb0c8", "#ffffff"])
# Terminal Dogma: negro verdoso, hueso y rojo oxidado (oscuro)
P["terminal-dogma"] = dict(name="Noctis (Terminal Dogma)", type="dark", base="noctis", bg="#04100f", side="#020808", text="#cfe3da", slug="Noctis-Terminal-Dogma",
    accent="#1fb5a0", accent2="#c23b3b", status="#0f6f66", status_fg="#ffffff", select="#1fb5a044",
    tokens=tokens("#5f8a80", "#cfe3da", "#d9534f", "#e6b566", "#c9743c", "#e0a030", "#c23b3b", "#6fe0b0", "#46b58a",
                  "#9aa4ff", "#3fd0c0", "#7be0d8", "#5ab0e0", "#e04545"),
    ansi=["#10201e", "#e04545", "#6fe0b0", "#e0a030", "#5ab0e0", "#b58cd6", "#3fd0c0", "#cfe3da",
          "#3d5a55", "#f06a66", "#9af0c8", "#f0c060", "#8ac8f0", "#cfa8e8", "#7be0d8", "#ffffff"])
# Ramiel: azul electrico cristalino con nucleo rojo (oscuro)
P["ramiel"] = dict(name="Noctis (Ramiel)", type="dark", base="noctis", bg="#020a1f", side="#01040c", text="#cfe0ff", slug="Noctis-Ramiel",
    accent="#1e6bff", accent2="#3ad9ff", status="#1550d8", status_fg="#ffffff", select="#1e6bff55",
    tokens=tokens("#5a78b0", "#cfe0ff", "#ff3b5c", "#8fd0ff", "#ff8a70", "#ffc04d", "#ff2a4d", "#3af0d0", "#26c4aa",
                  "#a08cff", "#4d9bff", "#52e0ff", "#7aa8ff", "#ff2a4d"),
    ansi=["#0e1a3a", "#ff3b5c", "#3af0d0", "#ffc04d", "#4d8bff", "#a08cff", "#52e0ff", "#cfe0ff",
          "#3a4f80", "#ff6a80", "#7af5e0", "#ffd985", "#7fb0ff", "#c2b0ff", "#8aeaff", "#ffffff"])
# Sachiel: pizarra azulada, hueso y nucleo rojo (oscuro)
P["sachiel"] = dict(name="Noctis (Sachiel)", type="dark", base="noctis", bg="#0e1218", side="#080b10", text="#e6dcc8", slug="Noctis-Sachiel",
    accent="#5b7fa8", accent2="#ff3030", status="#3d5a80", status_fg="#ffffff", select="#5b7fa855",
    tokens=tokens("#7d8797", "#e6dcc8", "#ff4d4d", "#e6c88a", "#e08a5c", "#f0a050", "#ff3030", "#7fd6a8", "#55b585",
                  "#b59cff", "#7fb0e0", "#6fd0e0", "#8fa8ff", "#ff3030"),
    ansi=["#1c222c", "#ff3030", "#7fd6a8", "#f0a050", "#6f9bd0", "#b59cff", "#6fd0e0", "#e6dcc8",
          "#4a5568", "#ff6a6a", "#a5e8c4", "#ffc880", "#9dbde8", "#cdb8ff", "#9ae2ee", "#ffffff"])

# EVA-01 Berserk: violeta casi negro, sangre roja y amarillo acido de los ojos (oscuro)
P["eva-01-berserk"] = dict(name="Noctis (EVA-01 Berserk)", type="dark", base="noctis", bg="#07030a", side="#040107", text="#eee4f7", slug="Noctis-EVA-01-Berserk",
    accent="#7a2cff", accent2="#e6ff00", status="#a30f1c", status_fg="#ffffff", select="#e6ff0033",
    tokens=tokens("#7a5f96", "#eee4f7", "#ff2a3a", "#ff7a1a", "#ff5a3a", "#ffb020", "#ff1f5a", "#9cff2e", "#6fd12a",
                  "#a06cff", "#c19cff", "#40d8c0", "#7a8cff", "#ff1f3d"),
    ansi=["#170c24", "#ff2a3a", "#9cff2e", "#ffb020", "#6a2cd6", "#ff3d8a", "#40d8c0", "#d5c6e8",
          "#4a3468", "#ff5a66", "#c4ff6a", "#f0ff3a", "#a985ff", "#ff7ab0", "#7be8d4", "#ffffff"])

# ---------- Pares claros de los Evas y temas claros nuevos ----------
P["eva-01-light"] = dict(name="Noctis (EVA-01 Light)", type="light", base="lux", bg="#f4f0ff", side="#e8e0fb", text="#1e1238", slug="Noctis-EVA-01-Light",
    accent="#6a2cd6", accent2="#1f9d2b", status="#5a1fb8", status_fg="#ffffff", select="#b79cff77",
    tokens=tokens("#8a78b0", "#1e1238", "#c02aa8", "#c25a00", "#b8501f", "#d15000", "#d4144a", "#1a8a1f", "#147a1a",
                  "#6a2cd6", "#7a4fe0", "#0e8f7c", "#4a5fe0", "#d4144a"),
    ansi=["#2a1a4a", "#d4144a", "#1a8a1f", "#d15000", "#6a2cd6", "#c02aa8", "#0e8f7c", "#d8ccf0",
          "#6a5a90", "#f0455f", "#3fb04a", "#ff7a1a", "#8a5cf0", "#dd55c8", "#2fb0a0", "#ffffff"])
P["eva-02-light"] = dict(name="Noctis (EVA-02 Light)", type="light", base="lux", bg="#fff4f1", side="#ffe4de", text="#3a0d10", slug="Noctis-EVA-02-Light",
    accent="#d4142a", accent2="#d99a00", status="#b30f24", status_fg="#ffffff", select="#ffb0a877",
    tokens=tokens("#a86a6a", "#3a0d10", "#d4142a", "#c25a00", "#b8501f", "#a87000", "#c81e5a", "#2f8a3a", "#237a30",
                  "#8a3fc0", "#b0308a", "#0e7f96", "#4a5fd0", "#d4142a"),
    ansi=["#3a1a1a", "#d4142a", "#2f8a3a", "#c25a00", "#4a5fd0", "#b0308a", "#0e7f96", "#f0d8d2",
          "#7a5050", "#f0455f", "#4fae5a", "#e08a1a", "#7080f0", "#cc55b0", "#2fb0c8", "#ffffff"])
P["eva-08-light"] = dict(name="Noctis (EVA-08 Light)", type="light", base="lux", bg="#fff0f8", side="#fbdcee", text="#3a0a2a", slug="Noctis-EVA-08-Light",
    accent="#d4157f", accent2="#0aa6c0", status="#b30f6a", status_fg="#ffffff", select="#ffa0d477",
    tokens=tokens("#a8709a", "#3a0a2a", "#d4157f", "#b86a00", "#b04a70", "#a86a00", "#d42a5a", "#0f8a5f", "#0a7a52",
                  "#7a3fd0", "#0a7f9a", "#0898a8", "#4a5fd0", "#d4142a"),
    ansi=["#3a1a30", "#d4142a", "#0f8a5f", "#b86a00", "#4a5fd0", "#d4157f", "#0a7f9a", "#f0d0e6",
          "#7a4a68", "#f0455f", "#2fae80", "#e08a1a", "#7080f0", "#f055a8", "#2fb0c8", "#ffffff"])
P["geofront"] = dict(name="Noctis (Geofront)", type="light", base="lux", bg="#f0faf4", side="#dff3e6", text="#123326", slug="Noctis-Geofront",
    accent="#1f9d6a", accent2="#2a8fd0", status="#157a52", status_fg="#ffffff", select="#a6e3c288",
    tokens=tokens("#6f9a86", "#123326", "#d4501a", "#b25e10", "#b06a2a", "#9a6a00", "#c81e3a", "#0f8a4f", "#0b7a44",
                  "#6a48d6", "#1a7fc0", "#0a8f9a", "#3a6fd0", "#c81e3a"),
    ansi=["#1f3a2e", "#c81e3a", "#0f8a4f", "#b25e10", "#1a7fc0", "#8a4fc0", "#0a8f9a", "#cfe6d8",
          "#5a7a6a", "#e5455f", "#2fb070", "#e08a1a", "#4a9ff0", "#a870d8", "#2fb0b8", "#ffffff"])
P["tabris"] = dict(name="Noctis (Tabris)", type="light", base="lux", bg="#f3f2f8", side="#e6e4f0", text="#26243a", slug="Noctis-Tabris",
    accent="#6a5fb0", accent2="#6a5fb0", status="#5a5098", status_fg="#ffffff", select="#cbc5f088",
    tokens=tokens("#8a88a8", "#26243a", "#8a4fc0", "#a06a3a", "#a05a6a", "#a0742a", "#b03a6a", "#2a8a78", "#227a68",
                  "#5a5fd0", "#4a6fc0", "#2a8aa0", "#6a5fd0", "#b8323a"),
    ansi=["#2a2840", "#b8323a", "#2a8a78", "#a0742a", "#4a6fc0", "#8a4fc0", "#2a8aa0", "#dcdae8",
          "#6a6888", "#d8555a", "#4aad98", "#c8963a", "#6a90e0", "#a870d8", "#4aaac0", "#ffffff"])

import copy
# Variantes de alto contraste (uiTheme hc-black / hc-light): fondo puro, texto con contraste >= 7:1 y bordes marcados
P["nerv-hc"] = copy.deepcopy(P["nerv"]); P["nerv-hc"].update(name="Noctis (NERV High Contrast)", bg="#000000", side="#000000", hc=True,
    text="#ffffff", status="#b30010", select="#e6001299")
P["nerv-hc"]["tokens"]["text"] = "#ffffff"
P["eva-mark06-hc"] = copy.deepcopy(P["eva-mark06"]); P["eva-mark06-hc"].update(name="Noctis (EVA Mark.06 High Contrast)", bg="#ffffff", side="#ffffff", hc=True,
    text="#000000", status="#000000", select="#6a3df088")
P["eva-mark06-hc"]["tokens"]["text"] = "#000000"

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
    while contrast(fg, bg) < minimum and 0.02 < l < 0.98:
        l += -0.01 if light else 0.01
        fg = to_hex(h, s, l)
    return fg

ANSI = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]

def build(key, p):
    light = p["type"] == "light"
    hc = p.get("hc", False)
    mn = 7.0 if hc else 4.5
    p["tokens"] = {k: (v if k in ("text",) else ensure(v, p["bg"], 4.0 if (k == "comment" and not hc) else mn, light))
                   for k, v in p["tokens"].items()}
    p["ansi"] = [ensure(v, p["bg"], 7.0 if hc else 3.0, light) if (hc or i not in (0, 7, 8, 15)) else v for i, v in enumerate(p["ansi"])]
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
        "editorCursor.foreground": p["accent2"], "tab.activeBorderTop": p["accent2"],
        "editor.selectionBackground": p["select"], "focusBorder": p["accent"],
        "editorWarning.foreground": ensure(p["tokens"]["constant"], p["bg"], mn, light),
        "editorError.foreground": ensure(p["tokens"]["invalid"], p["bg"], mn, light),
    })
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
