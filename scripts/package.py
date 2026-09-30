#!/usr/bin/env python3
"""Build a VSIX only when its editor and terminal themes match the manifest."""

import json
import os
from pathlib import Path
import runpy
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

    for terminal, suffix in (("kitty", ".conf"), ("ghostty", "")):
        actual = {p.name for p in (ROOT / "terminals" / terminal / "themes").iterdir() if p.is_file()}
        wanted = {theme_slug(key, palette) + suffix for key, palette in palettes.items()}
        require(actual == wanted, f"{terminal} theme files differ: missing={sorted(wanted - actual)}, extra={sorted(actual - wanted)}")


def package_files():
    required = [
        "package.json", "README.md", "CHANGELOG.md", "LICENSE.txt",
        "NOCTIS-LICENSE.md", "icon.png", "terminals/install.sh",
    ]
    files = required + [str(p.relative_to(ROOT)) for folder in (
        "themes", "images", "terminals/kitty/themes", "terminals/ghostty/themes"
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
