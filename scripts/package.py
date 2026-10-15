#!/usr/bin/env python3
"""Build a VSIX only when its editor and terminal themes match the manifest."""

import configparser
import json
import plistlib
import re
import os
from pathlib import Path
import runpy
import tomllib
import tempfile
import xml.dom.minidom
from xml.sax.saxutils import escape as esc
import zipfile


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_THEME_COUNT = 28
ANSI = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")
OLED_SURFACES = (
    "editor.background", "sideBar.background", "activityBar.background",
    "titleBar.activeBackground", "tab.activeBackground", "tab.inactiveBackground",
    "panel.background", "terminal.background",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def theme_slug(key, palette):
    return palette.get("slug") or "Noctis-" + key.upper().replace("EVA-MARK06", "EVA-Mark06")


def color_settings(path, separator):
    settings = {}
    for line in path.read_text().splitlines():
        if separator not in line or line.startswith("#"):
            continue
        key, value = line.split(separator, 1)
        settings[key.strip()] = value.strip()
    return settings


HEX = r"#[0-9a-fA-F]{6}"


def _hex(r, g, b):
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def parse_extra(folder, path):
    """Return (background, foreground, ansi colors) from a terminal theme; ansi may be shorter or None when the format has fewer."""
    text = path.read_text()
    if folder == "windows-terminal":
        scheme = json.loads(text)["schemes"][0]
        names = ("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")
        ansi = [scheme[n] for n in names] + [scheme["bright" + n.capitalize()] for n in names]
        return scheme["background"], scheme["foreground"], ansi
    if folder == "iterm2":
        data = plistlib.loads(path.read_bytes())
        color = lambda k: _hex(data[k]["Red Component"], data[k]["Green Component"], data[k]["Blue Component"])
        return color("Background Color"), color("Foreground Color"), [color(f"Ansi {i} Color") for i in range(16)]
    if folder == "foot":
        ini = configparser.ConfigParser(interpolation=None)
        ini.read_string(text)
        section = ini["colors-light" if "colors-light" in ini else "colors-dark"]
        x = lambda k: "#" + section[k]
        return x("background"), x("foreground"), [x(f"regular{i}") for i in range(8)] + [x(f"bright{i}") for i in range(8)]
    if folder == "konsole":
        ini = configparser.ConfigParser(interpolation=None)
        ini.optionxform = str
        ini.read_string(text)
        c = lambda sec: _hex(*(int(v) / 255 for v in ini[sec]["Color"].split(",")))
        return c("Background"), c("Foreground"), [c(f"Color{i}") for i in range(8)] + [c(f"Color{i}Intense") for i in range(8)]
    if folder == "xresources":
        v = dict(re.findall(rf"^\*\.(\w+):\s*({HEX})", text, re.M))
        return v["background"], v["foreground"], [v[f"color{i}"] for i in range(16)]
    if folder == "termux":
        v = dict(re.findall(rf"^(\w+)=({HEX})", text, re.M))
        return v["background"], v["foreground"], [v[f"color{i}"] for i in range(16)]
    if folder == "zellij":
        v = dict(re.findall(rf'^\s+(\w+) "({HEX})"', text, re.M))
        names = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
        return v["bg"], v["fg"], [v[n] for n in names]
    if folder == "warp":
        top = dict(re.findall(rf"^(\w+): '({HEX})'", text, re.M))
        nested = re.findall(rf"^    (\w+): '({HEX})'", text, re.M)
        require(len(nested) == 16, "warp must define 16 ANSI colors")
        return top["background"], top["foreground"], [c for _, c in nested]
    if folder == "tmux":
        v = dict(re.findall(r'set -g (status-style) "bg=(#[0-9a-fA-F]{6}),fg=#[0-9a-fA-F]{6}"', text))
        fg = re.search(r'set -g status-style "bg=#[0-9a-fA-F]{6},fg=(#[0-9a-fA-F]{6})"', text).group(1)
        return v["status-style"], fg, None
    raise KeyError(folder)


EXTRA_TERMINALS = {  # carpeta -> extension, True si el fondo del tema es el del terminal (tmux usa el de la barra lateral)
    "windows-terminal": ".json", "iterm2": ".itermcolors", "foot": ".ini", "konsole": ".colorscheme", "xresources": "",
    "tmux": ".conf", "zellij": ".kdl", "termux": ".properties", "warp": ".yaml",
}


def contrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
        return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def validate_contrast(key, theme, palette):
    """Documented readability contract: syntax 4.5:1, comments 4:1, high-contrast 7:1, plus UI and terminal colors."""
    colors, hc = theme["colors"], bool(palette.get("hc"))
    bg, tol = colors["editor.background"], 0.005

    def need(label, fg, background, minimum):
        if len(fg) > 7:  # alpha channels are not part of the contract
            return
        ratio = contrast(fg, background)
        require(ratio + tol >= minimum, f"{key}: {label} {fg} on {background} has {ratio:.2f}:1, needs {minimum}:1")

    need("editor.foreground", colors["editor.foreground"], bg, 7.0 if hc else 4.5)
    need("statusBar text", colors["statusBar.foreground"], colors["statusBar.background"], 4.5)
    need("cursor", colors["editorCursor.foreground"], bg, 7.0 if hc else 3.0)
    for rule in theme.get("tokenColors", []):
        fg = rule.get("settings", {}).get("foreground")
        if not fg:
            continue
        scopes = rule.get("scope", [])
        scopes = [scopes] if isinstance(scopes, str) else scopes
        comment = "comment" in scopes
        need(f"token {scopes[:1]}", fg, bg, 7.0 if hc else 4.0 if comment else 4.5)
    ansi_min = runpy.run_path(str(ROOT / "scripts/build.py"))["ansi_min"]
    for index, name in enumerate(ANSI + tuple("Bright" + n for n in ANSI)):
        if ansi_min(palette, index):  # black on light and white on dark themes are surfaces, not text colors
            need(f"terminal ansi {index}", colors["terminal.ansi" + name], colors["terminal.background"], ansi_min(palette, index))


def validate_source(pkg):
    palettes = runpy.run_path(str(ROOT / "scripts/build.py"))["P"]
    registrations = pkg["contributes"]["themes"]
    require(registrations, "package.json has no registered themes")
    require(len(palettes) == EXPECTED_THEME_COUNT,
            f"expected {EXPECTED_THEME_COUNT} generated palettes; found {len(palettes)}")
    paths = [entry["path"].removeprefix("./") for entry in registrations]
    expected = {f"themes/{key}.json" for key in palettes}
    require(len(paths) == len(set(paths)), "package.json has duplicate theme paths")
    require(set(paths) == expected,
            f"package.json theme paths differ from generated palettes: missing={sorted(expected - set(paths))}, extra={sorted(set(paths) - expected)}")
    require({f"themes/{p.name}" for p in (ROOT / "themes").glob("*.json")} == expected,
            "generated VS Code theme files differ from package.json")
    require(sum(bool(p.get("oled")) for p in palettes.values()) == 5,
            "the current theme family must contain five OLED variants")

    for entry in registrations:
        path = entry["path"].removeprefix("./")
        key = Path(path).stem
        palette = palettes[key]
        theme = json.loads((ROOT / path).read_text())
        require(theme.get("name") == entry["label"] == palette["name"], f"theme name differs: {path}")
        colors = theme["colors"]
        slug = theme_slug(key, palette)
        kitty = ROOT / "terminals/kitty/themes" / f"{slug}.conf"
        ghostty = ROOT / "terminals/ghostty/themes" / slug
        require(kitty.is_file() and ghostty.is_file(), f"missing terminal theme for {key}")
        k = color_settings(kitty, " ")
        g = color_settings(ghostty, "=")
        for terminal, data in (("kitty", k), ("Ghostty", g)):
            require(data.get("background", "").lower() == colors["terminal.background"].lower(),
                    f"{terminal} background differs: {key}")
            require(data.get("foreground", "").lower() == colors["terminal.foreground"].lower(),
                    f"{terminal} foreground differs: {key}")
        ghostty_lines = [line.strip().lower() for line in ghostty.read_text().splitlines() if line.startswith("palette = ")]
        require(len(ghostty_lines) == 16, f"Ghostty must define 16 ANSI colors: {key}")
        for index, name in enumerate(ANSI + tuple("Bright" + n for n in ANSI)):
            vscode = colors["terminal.ansi" + name].lower()
            require(k.get(f"color{index}", "").lower() == vscode,
                    f"kitty ANSI {index} differs: {key}")
            require(ghostty_lines[index] == f"palette = {index}={vscode}",
                    f"Ghostty ANSI {index} differs: {key}")
        if palette.get("oled"):
            require(entry["uiTheme"] == "vs-dark", f"OLED theme must register as dark: {key}")
            for surface in OLED_SURFACES:
                require(colors.get(surface, "").lower() == "#000000",
                        f"OLED surface {surface} is not true black: {key}")
            require(k["background"].lower() == g["background"].lower() == "#000000",
                    f"OLED terminal background is not true black: {key}")
        require((ROOT / "images" / f"{key}.png").is_file(), f"missing preview: {key}")
        validate_contrast(key, theme, palette)
        for terminal in ("alacritty", "wezterm"):
            path = ROOT / "terminals" / terminal / "themes" / f"{slug}.toml"
            require(path.is_file(), f"missing {terminal} theme for {key}")
            data = tomllib.loads(path.read_text())["colors"]
            primary = data["primary"] if terminal == "alacritty" else data
            require(primary["background"].lower() == colors["terminal.background"].lower()
                    and primary["foreground"].lower() == colors["terminal.foreground"].lower(),
                    f"{terminal} background/foreground differ: {key}")
            if terminal == "alacritty":
                ansi = list(data["normal"].values()) + list(data["bright"].values())
            else:
                ansi = data["ansi"] + data["brights"]
            require(len(ansi) == 16, f"{terminal} must define 16 ANSI colors: {key}")
            for index, name in enumerate(ANSI + tuple("Bright" + n for n in ANSI)):
                require(ansi[index].lower() == colors["terminal.ansi" + name].lower(),
                        f"{terminal} ANSI {index} differs: {key}")
            if palette.get("oled"):
                require(primary["background"].lower() == "#000000", f"{terminal} OLED background is not true black: {key}")
        for folder, suffix in EXTRA_TERMINALS.items():
            path = ROOT / "terminals" / folder / "themes" / f"{slug}{suffix}"
            require(path.is_file(), f"missing {folder} theme for {key}")
            try:
                background, foreground, ansi = parse_extra(folder, path)
            except (KeyError, ValueError, AttributeError, IndexError, configparser.Error) as exc:
                raise ValueError(f"{folder} theme is malformed for {key}: {exc!r}") from exc
            if folder == "tmux":
                require(background.lower() == colors["sideBar.background"].lower(), f"tmux status background differs: {key}")
            else:
                require(background.lower() == colors["terminal.background"].lower(), f"{folder} background differs: {key}")
            require(foreground.lower() == colors["terminal.foreground"].lower(), f"{folder} foreground differs: {key}")
            for index, value in enumerate(ansi or []):
                name = (ANSI + tuple("Bright" + n for n in ANSI))[index]
                require(value.lower() == colors["terminal.ansi" + name].lower(), f"{folder} ANSI {index} differs: {key}")
            if palette.get("oled") and folder != "tmux":
                require(background.lower() == "#000000", f"{folder} OLED background is not true black: {key}")

    for terminal, suffix in (("kitty", ".conf"), ("ghostty", ""), ("alacritty", ".toml"), ("wezterm", ".toml"), *EXTRA_TERMINALS.items()):
        actual = {p.name for p in (ROOT / "terminals" / terminal / "themes").iterdir() if p.is_file()}
        wanted = {theme_slug(key, palette) + suffix for key, palette in palettes.items()}
        require(actual == wanted, f"{terminal} theme files differ: missing={sorted(wanted - actual)}, extra={sorted(actual - wanted)}")


def package_files():
    required = [
        "package.json", "README.md", "CHANGELOG.md", "LICENSE.txt",
        "NOCTIS-LICENSE.md", "icon.png", "terminals/install.sh",
    ]
    files = required + [str(p.relative_to(ROOT)) for folder in (
        "themes", "images", "terminals/kitty/themes", "terminals/ghostty/themes",
        "terminals/alacritty/themes", "terminals/wezterm/themes",
        *(f"terminals/{folder}/themes" for folder in EXTRA_TERMINALS),
    ) for p in sorted((ROOT / folder).iterdir()) if p.is_file()]
    for name in files:
        require((ROOT / name).is_file(), f"missing package file: {name}")
    return files


def manifest(pkg):
    repo = pkg.get("repository", {}).get("url", "").removesuffix(".git")
    links = "".join(
        f'<Property Id="Microsoft.VisualStudio.Services.Links.{key}" Value="{value}"/>\n'
        for key, value in (
            ("Source", repo + ".git"), ("Getstarted", repo + ".git"),
            ("GitHub", repo + ".git"), ("Support", repo + "/issues"),
            ("Learn", repo + "#readme"),
        )
    ) if repo else ""
    return f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata>
<Identity Language="en-US" Id="{pkg['name']}" Version="{pkg['version']}" Publisher="{pkg['publisher']}"/>
<DisplayName>{esc(pkg['displayName'])}</DisplayName>
<Description xml:space="preserve">{esc(pkg['description'])}</Description>
<Tags>{','.join(pkg['keywords'])}</Tags>
<Categories>Themes</Categories>
<GalleryFlags>Public</GalleryFlags>
<Properties>
<Property Id="Microsoft.VisualStudio.Code.Engine" Value="{pkg['engines']['vscode']}"/>
<Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/>
<Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/>
<Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui,workspace"/>
<Property Id="Microsoft.VisualStudio.Code.LocalizedLanguages" Value=""/>
<Property Id="Microsoft.VisualStudio.Code.EnabledApiProposals" Value=""/>
{links}<Property Id="Microsoft.VisualStudio.Services.GitHubFlavoredMarkdown" Value="true"/>
<Property Id="Microsoft.VisualStudio.Services.Content.Pricing" Value="Free"/>
<Property Id="Microsoft.VisualStudio.Services.GalleryBanner.Color" Value="{pkg['galleryBanner']['color']}"/>
<Property Id="Microsoft.VisualStudio.Services.GalleryBanner.Theme" Value="{pkg['galleryBanner']['theme']}"/>
</Properties>
<License>extension/LICENSE.txt</License>
<Icon>extension/icon.png</Icon>
</Metadata>
<Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
<Dependencies/>
<Assets>
<Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.Changelog" Path="extension/CHANGELOG.md" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE.txt" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Icons.Default" Path="extension/icon.png" Addressable="true"/>
</Assets>
</PackageManifest>'''


def main():
    pkg = json.loads((ROOT / "package.json").read_text())
    validate_source(pkg)
    files = package_files()
    terminal_files = [name for name in files if name.startswith("terminals/")]
    content_types = '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension=".json" ContentType="application/json"/><Default Extension=".md" ContentType="text/markdown"/><Default Extension=".png" ContentType="image/png"/><Default Extension=".txt" ContentType="text/plain"/><Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>'
    content_types = content_types.replace('</Types>', ''.join(
        f'<Override PartName="/extension/{name}" ContentType="text/plain"/>' for name in terminal_files
    ) + '</Types>')
    output = ROOT / f"{pkg['name']}-{pkg['version']}.vsix"
    with tempfile.NamedTemporaryFile(dir=ROOT, prefix=".eva-package-", suffix=".vsix", delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("extension.vsixmanifest", manifest(pkg))
            for name in files:
                archive.write(ROOT / name, "extension/" + name)
        with zipfile.ZipFile(temporary) as archive:
            require(archive.testzip() is None, "VSIX checksum validation failed")
            wanted = {"[Content_Types].xml", "extension.vsixmanifest"} | {"extension/" + name for name in files}
            require(set(archive.namelist()) == wanted, "VSIX payload differs from validated source files")
            for name in files:
                require(archive.read("extension/" + name) == (ROOT / name).read_bytes(),
                        f"VSIX payload differs from source: {name}")
            for name in wanted:
                if name.endswith(".json"):
                    json.loads(archive.read(name))
            xml.dom.minidom.parseString(archive.read("extension.vsixmanifest"))
            xml.dom.minidom.parseString(archive.read("[Content_Types].xml"))
        os.replace(temporary, output)
        print(output.name, len(wanted), "archivos OK")
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"Packaging validation failed: {exc}") from exc
