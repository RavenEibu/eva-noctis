#!/usr/bin/env python3
"""Empaqueta el .vsix a mano (alternativa a `vsce package`)."""
import json, zipfile, os
from xml.sax.saxutils import escape as esc
pkg = json.load(open('package.json'))
files = ['package.json', 'README.md', 'CHANGELOG.md', 'LICENSE.txt', 'NOCTIS-LICENSE.md', 'icon.png'] + [f'themes/{f}' for f in sorted(os.listdir('themes'))] + [f'images/{f}' for f in sorted(os.listdir('images'))]
ct = '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension=".json" ContentType="application/json"/><Default Extension=".md" ContentType="text/markdown"/><Default Extension=".png" ContentType="image/png"/><Default Extension=".txt" ContentType="text/plain"/><Default Extension=".vsixmanifest" ContentType="text/xml"/></Types>'
repo = pkg.get('repository', {}).get('url', '').removesuffix('.git')
links = ''
if repo:
    for k, v in (('Source', repo + '.git'), ('Getstarted', repo + '.git'), ('GitHub', repo + '.git'), ('Support', repo + '/issues'), ('Learn', repo + '#readme')):
        links += f'<Property Id="Microsoft.VisualStudio.Services.Links.{k}" Value="{v}"/>\n'
man = f'''<?xml version="1.0" encoding="utf-8"?>
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
out = f"{pkg['name']}-{pkg['version']}.vsix"
if os.path.exists(out): os.remove(out)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct); z.writestr('extension.vsixmanifest', man)
    for f in files: z.write(f, 'extension/' + f)
z = zipfile.ZipFile(out); assert z.testzip() is None
for n in z.namelist():
    if n.endswith('.json'): json.loads(z.read(n))
import xml.dom.minidom as m; m.parseString(z.read('extension.vsixmanifest'))
print(out, len(z.namelist()), 'archivos OK')
