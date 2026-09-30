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


if __name__ == "__main__":
    unittest.main()
