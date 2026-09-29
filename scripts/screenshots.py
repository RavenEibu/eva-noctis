#!/usr/bin/env python3
"""Genera imagenes de vista previa (un editor + terminal simulados) para cada tema."""
import json, html, glob
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"; IMG.mkdir(exist_ok=True)

CODE = [
  [("import","keyword"),(" { ","text"),("useState","function"),(" } ","text"),("from","keyword"),(" ","text"),("'react'","string"),(";","text")],
  [],
  [("// Sync the pilot with the unit","comment")],
  [("export function","keyword"),(" ","text"),("Entryplug","function"),("({ ","text"),("sync","variable"),(" }: ","text"),("Props","support"),(") {","text")],
  [("  ","text"),("const","keyword"),(" [","text"),("ratio","variable"),(", ","text"),("setRatio","function"),("] = ","text"),("useState","function"),("(","text"),("0.0","number"),(");","text")],
  [("  ","text"),("const","keyword"),(" ","text"),("LIMIT","constant"),(" = ","text"),("400","number"),(";","text")],
  [],
  [("  ","text"),("if","keyword"),(" (","text"),("ratio","variable"),(" > ","text"),("LIMIT","constant"),(") {","text")],
  [("    ","text"),("throw","keyword"),(" ","text"),("new","keyword"),(" ","text"),("Error","support"),("(","text"),("`Out of range: ${ratio}`","string"),(");","text")],
  [("  }","text")],
  [("  ","text"),("return","keyword"),(" <","text"),("div","tag"),(" ","text"),("className","annotation"),("=","text"),("\"plug\"","string"),(">{","text"),("ratio","variable"),("}</","text"),("div","tag"),(">;","text")],
  [("}","text")],
]
FILES = [("src", None), ("  Entryplug.tsx", 1), ("  Magi.tsx", 0), ("  theme.ts", 0), ("package.json", 0), ("README.md", 0)]

def page(t):
    c = t["colors"]; name = t["name"]
    g = lambda k, d: c.get(k, d)
    bg = c["editor.background"]; fg = c["editor.foreground"]
    tok = {x["name"].lower(): x["settings"].get("foreground", "")[:7] for x in t["tokenColors"] if "foreground" in x["settings"]}
    tok["text"] = fg
    ln = g("editorLineNumber.foreground", fg); lna = g("editorLineNumber.activeForeground", fg)
    side_fg = g("sideBar.foreground", fg); act_fg = g("activityBar.foreground", fg)
    title = g("titleBar.activeBackground", g("sideBar.background", bg))
    tabbar = g("editorGroupHeader.tabsBackground", g("sideBar.background", bg))
    tab_act = g("tab.activeBackground", bg); tab_in = g("tab.inactiveBackground", tabbar)
    tab_in_fg = g("tab.inactiveForeground", side_fg); tab_act_fg = g("tab.activeForeground", fg)
    border = g("contrastBorder", g("sideBar.border", "#00000022"))
    err, warn = g("editorError.foreground", "#f00"), g("editorWarning.foreground", "#fa0")
    lines = ""
    for i, line in enumerate(CODE, 1):
        toks = "".join(f'<span style="color:{tok.get(k, fg)}{";font-style:italic" if k=="comment" else ""}">{html.escape(s)}</span>' for s, k in line) or "&nbsp;"
        style = "border-bottom:2px dotted %s" % err if i == 9 else ""
        cur = f"background:{g('editor.lineHighlightBackground', 'transparent')}" if i == 5 else ""
        lines += f'<div class=l style="{cur}"><i style="color:{lna if i==5 else ln}">{i}</i><span style="{style}">{toks}</span></div>'
    tree = ""
    for n, kind in FILES:
        sel = "background:%s;" % g("list.activeSelectionBackground", "#ffffff18") if n.strip() == "Entryplug.tsx" else ""
        tree += f'<div class=f style="{sel}color:{side_fg}">{html.escape(n).replace(" ", "&nbsp;")}</div>'
    a = lambda n: c[f"terminal.ansi{n}"]; ab = lambda n: c[f"terminal.ansiBright{n}"]
    names = ["Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White"]
    sw = "".join(f'<i class=sw style="background:{a(n)}"></i>' for n in names) + "".join(f'<i class=sw style="background:{ab(n)}"></i>' for n in names)
    tbg = c["terminal.background"]; tfg = c["terminal.foreground"]
    term = (f'<div><span style="color:{a("Green")}">pilot</span><span style="color:{tfg}">@</span><span style="color:{a("Blue")}">nerv</span> '
            f'<span style="color:{a("Cyan")}">~/entryplug</span> <span style="color:{a("Yellow")}">$</span> git status</div>'
            f'<div style="color:{a("Green")}">  modified:   src/Entryplug.tsx</div><div style="color:{a("Red")}">  deleted:    src/legacy.ts</div>'
            f'<div><span style="color:{a("Yellow")}">warning:</span> sync ratio near limit</div><div style="margin-top:6px">{sw}</div>')
    return f'''<style>
*{{box-sizing:border-box}} body{{margin:0;font:13px/20px "JetBrains Mono","DejaVu Sans Mono",monospace;background:{bg}}}
.w{{width:960px;height:560px;display:flex;flex-direction:column;background:{bg};color:{fg};border:1px solid {border}}}
.title{{height:30px;background:{title};color:{side_fg};text-align:center;line-height:30px;font-size:12px}}
.main{{flex:1;display:flex;min-height:0}} .act{{width:46px;background:{g("activityBar.background", bg)};display:flex;flex-direction:column;align-items:center;gap:14px;padding-top:12px}}
.act b{{width:22px;height:22px;border:2px solid {act_fg};border-radius:5px;opacity:.55}} .act b:first-child{{opacity:1;border-color:{g("activityBar.activeBorder", act_fg)}}}
.side{{width:200px;background:{g("sideBar.background", bg)};padding:10px 0;border-right:1px solid {border}}} .side h6{{margin:0 0 8px 14px;font-size:11px;font-weight:400;color:{g("sideBarTitle.foreground", side_fg)};letter-spacing:.08em}}
.f{{padding:0 14px;font-size:12.5px}}
.ed{{flex:1;display:flex;flex-direction:column;min-width:0}} .tabs{{height:34px;background:{tabbar};display:flex}}
.tab{{padding:0 16px;line-height:34px;font-size:12.5px;color:{tab_in_fg};background:{tab_in}}} .tab.a{{background:{tab_act};color:{tab_act_fg};border-top:2px solid {g("tab.activeBorderTop", g("focusBorder", fg))}}}
.code{{flex:1;padding:12px 0;overflow:hidden}} .l{{display:flex;padding-right:10px;white-space:pre}} .l i{{width:44px;text-align:right;padding-right:16px;font-style:normal}}
.panel{{height:150px;background:{tbg};color:{tfg};border-top:1px solid {border};padding:8px 16px;font-size:12.5px}} .sw{{display:inline-block;width:22px;height:14px;margin-right:2px}}
.st{{height:24px;background:{g("statusBar.background", bg)};color:{g("statusBar.foreground", fg)};line-height:24px;padding:0 12px;font-size:12px;display:flex;justify-content:space-between}}
</style><div class=w><div class=title>Entryplug.tsx — eva-noctis — {html.escape(name)}</div>
<div class=main><div class=act><b></b><b></b><b></b><b></b></div><div class=side><h6>EXPLORER</h6>{tree}</div>
<div class=ed><div class=tabs><div class="tab a">Entryplug.tsx</div><div class=tab>Magi.tsx</div><div class=tab>theme.ts</div></div><div class=code>{lines}</div></div></div>
<div class=panel>{term}</div><div class=st><span>&#9679; main &nbsp; 1 error &nbsp; 1 warning</span><span>{html.escape(name)} &nbsp; TypeScript React</span></div></div>'''

ORDER = ["eva-00", "eva-01", "eva-01-berserk", "eva-01-light", "eva-02", "eva-02-light", "eva-03", "eva-08", "eva-08-light", "eva-13", "eva-mark06", "magi", "nerv", "seele",
         "at-field", "instrumentality", "geofront", "tabris", "terminal-dogma", "ramiel", "sachiel", "nerv-hc", "eva-mark06-hc"]

def overview(cols=4, w=640, h=373, pad=12):
    from PIL import Image
    rows = -(-len(ORDER) // cols)
    im = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad), "#1b1b22")
    for i, k in enumerate(ORDER):
        t = Image.open(IMG / f"{k}.png").convert("RGB").resize((w, h), Image.LANCZOS)
        im.paste(t, (pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)))
    im.save(IMG / "overview.png", optimize=True)

def main():
    themes = sorted(glob.glob(str(ROOT / "themes" / "*.json")))
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 960, "height": 560}, device_scale_factor=1.5)
        for f in themes:
            t = json.load(open(f)); pg.set_content(page(t)); pg.wait_for_timeout(100)
            out = IMG / (Path(f).stem + ".png"); pg.screenshot(path=str(out)); print(out.name)
        b.close()
    overview()

if __name__ == "__main__":
    main()
