"""Packaging must reject missing or inconsistent generated payloads."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ("themes", "images", "terminals", "scripts"):
            shutil.copytree(SOURCE / folder, self.root / folder)
        for name in ("package.json", "README.md", "CHANGELOG.md", "LICENSE.txt", "NOCTIS-LICENSE.md", "icon.png"):
            shutil.copy2(SOURCE / name, self.root / name)
        version = json.loads((self.root / "package.json").read_text())["version"]
        self.output = self.root / f"eva-noctis-{version}.vsix"

    def package(self):
        return subprocess.run(
            [sys.executable, "scripts/package.py"], cwd=self.root,
            capture_output=True, text=True,
        )

    def test_complete_vsix_contains_registered_themes_and_terminals(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("archivos OK", result.stdout)
        self.assertTrue(self.output.is_file())

    def test_missing_registered_theme_fails_before_replacing_package(self):
        self.assertEqual(self.package().returncode, 0)
        original = self.output.read_bytes()
        (self.root / "themes/eva-01-oled.json").unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("generated VS Code theme files differ", result.stderr)
        self.assertEqual(self.output.read_bytes(), original)

    def test_missing_terminal_theme_fails(self):
        (self.root / "terminals/kitty/themes/Noctis-EVA-01-OLED.conf").unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing terminal theme", result.stderr)

    def test_nonblack_oled_surface_fails(self):
        path = self.root / "themes/eva-01-oled.json"
        theme = json.loads(path.read_text())
        theme["colors"]["panel.background"] = "#010101"
        path.write_text(json.dumps(theme))
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OLED surface panel.background", result.stderr)

    def test_low_contrast_token_fails(self):
        path = self.root / "themes/eva-01.json"
        theme = json.loads(path.read_text())
        theme["tokenColors"][0]["settings"]["foreground"] = theme["colors"]["editor.background"]
        path.write_text(json.dumps(theme))
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("needs 4", result.stderr)

    def test_missing_alacritty_or_wezterm_theme_fails(self):
        for terminal in ("alacritty", "wezterm"):
            (self.root / f"terminals/{terminal}/themes/Noctis-EVA-01.toml").unlink()
            result = self.package()
            self.assertNotEqual(result.returncode, 0, terminal)
            self.assertIn(terminal, result.stderr)
            shutil.copy2(SOURCE / f"terminals/{terminal}/themes/Noctis-EVA-01.toml",
                         self.root / f"terminals/{terminal}/themes/Noctis-EVA-01.toml")

    def test_alacritty_ansi_mismatch_fails(self):
        path = self.root / "terminals/alacritty/themes/Noctis-EVA-01.toml"
        path.write_text(path.read_text().replace('red = "#ff2d55"', 'red = "#000001"'))
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alacritty ANSI 1 differs", result.stderr)

    def test_missing_extra_terminal_theme_fails(self):
        for folder, name in (("foot", "Noctis-EVA-01.ini"), ("iterm2", "Noctis-EVA-01.itermcolors"),
                             ("windows-terminal", "Noctis-EVA-01.json"), ("tmux", "Noctis-EVA-01.conf")):
            path = self.root / "terminals" / folder / "themes" / name
            backup = path.read_bytes()
            path.unlink()
            result = self.package()
            self.assertNotEqual(result.returncode, 0, folder)
            self.assertIn(f"missing {folder} theme", result.stderr)
            path.write_bytes(backup)

    def test_extra_terminal_color_mismatch_fails(self):
        path = self.root / "terminals/konsole/themes/Noctis-EVA-01.colorscheme"
        path.write_text(path.read_text().replace("[Color1]\nColor=255,45,85", "[Color1]\nColor=1,2,3"))
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("konsole ANSI 1 differs", result.stderr)

    def test_malformed_extra_terminal_theme_fails(self):
        (self.root / "terminals/warp/themes/Noctis-EVA-01.yaml").write_text("name: broken\n")
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("warp theme is malformed", result.stderr)


if __name__ == "__main__":
    unittest.main()
