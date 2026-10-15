"""Terminal palettes must keep readable ANSI colors, including the 7:1 high-contrast themes."""

from pathlib import Path
import runpy
import unittest


SOURCE = Path(__file__).resolve().parents[1]
B = runpy.run_path(str(SOURCE / "scripts/build.py"))
A = runpy.run_path(str(SOURCE / "scripts/accessibility.py"))


class AnsiContrastTests(unittest.TestCase):
    def test_text_ansi_and_bright_black_reach_minimum_contrast(self):
        for key, palette in B["P"].items():
            for index, color in enumerate(B["ansi_colors"](palette)):
                minimum = B["ansi_min"](palette, index)
                self.assertGreaterEqual(B["contrast"](color, palette["bg"]), minimum - 0.05,
                                        f"{key} ANSI {index} {color}")

    def test_black_and_white_are_not_invisible(self):
        for key, palette in B["P"].items():
            ansi = B["ansi_colors"](palette)
            if palette["type"] == "light":
                self.assertGreaterEqual(B["contrast"](ansi[7], palette["bg"]), 3.45, f"{key} white")
                self.assertGreaterEqual(B["contrast"](ansi[15], palette["bg"]), 2.95, f"{key} bright white")
            else:
                self.assertGreaterEqual(B["contrast"](ansi[0], palette["bg"]), 1.45, f"{key} black")

    def test_high_contrast_light_has_no_white_on_white(self):
        palette = B["P"]["eva-mark06-hc"]
        self.assertGreaterEqual(B["contrast"](B["ansi_colors"](palette)[15], palette["bg"]), 6.95)

    def test_cursor_is_visible_on_every_background(self):
        for key, palette in B["P"].items():
            self.assertGreaterEqual(B["contrast"](B["cursor_color"](palette), palette["bg"]), 2.95, key)

    def test_text_colors_are_distinguishable_with_normal_vision(self):
        for key, palette in B["P"].items():
            distance, i, j = A["weakest_normal"](palette)
            self.assertGreaterEqual(distance, A["MIN_NORMAL"], f"{key}: ANSI {i} and {j} look alike")


class ColorVisionTests(unittest.TestCase):
    def test_every_theme_has_a_rating_for_each_type(self):
        for key, palette in B["P"].items():
            rating = A["assess"](palette)
            self.assertEqual(set(rating), {"protanopia", "deuteranopia", "tritanopia"}, key)
            for kind, value in rating.items():
                self.assertIn(value["level"], (0, 1, 2), f"{key} {kind}")
                self.assertEqual(value["level"], min(value["levels"]), f"{key} {kind}")

    def test_simulation_keeps_neutral_colors_neutral(self):
        for kind in A["CVD"]:
            for gray in ("#000000", "#808080", "#ffffff"):
                seen = A["simulate"](gray, kind)
                channels = [int(seen[i:i + 2], 16) for i in (1, 3, 5)]
                self.assertLessEqual(max(channels) - min(channels), 3, f"{kind} {gray} -> {seen}")

    def test_red_and_green_are_confusable_for_protan_and_deutan_but_not_tritan(self):
        red, green = "#d42a1f", "#0f9d58"
        for kind in ("protanopia", "deuteranopia"):
            self.assertLess(A["distance"](A["simulate"](red, kind), A["simulate"](green, kind)), A["distance"](red, green) / 2, kind)
        self.assertGreater(A["distance"](A["simulate"](red, "tritanopia"), A["simulate"](green, "tritanopia")), 40)

    def test_readme_table_and_details_are_current(self):
        self.assertTrue(A["readme_current"](), "run: python3 scripts/accessibility.py --write")
        self.assertEqual(A["DETAILS"].read_text(), A["details"](), "run: python3 scripts/accessibility.py --write")


class PaletteDataTests(unittest.TestCase):
    def load(self, text):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "palettes.toml"
            path.write_text(text)
            return B["load_palettes"](path)

    def test_variants_inherit_and_override(self):
        palettes = B["P"]
        self.assertEqual(palettes["eva-01-oled"]["ansi"], palettes["eva-01"]["ansi"])
        self.assertEqual(palettes["eva-01-oled"]["bg"], "#000000")
        self.assertEqual(palettes["eva-01-oled"]["tokens"]["keyword"], palettes["eva-01"]["tokens"]["keyword"])
        self.assertNotEqual(palettes["eva-01-oled"]["tokens"]["text"], palettes["eva-01"]["tokens"]["text"])

    def test_unknown_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "extends 'nope'"):
            self.load('[child]\nextends = "nope"\n')

    def test_incomplete_palette_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "palette needs"):
            self.load('[broken]\nname = "x"\n')


if __name__ == "__main__":
    unittest.main()
