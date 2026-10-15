"""Terminal palettes must keep readable ANSI colors, including the 7:1 high-contrast themes."""

from pathlib import Path
import runpy
import unittest


SOURCE = Path(__file__).resolve().parents[1]
B = runpy.run_path(str(SOURCE / "scripts/build.py"))


class AnsiContrastTests(unittest.TestCase):
    def test_text_ansi_and_bright_black_reach_minimum_contrast(self):
        for key, palette in B["P"].items():
            minimum = 7.0 if palette.get("hc") else 3.0
            for index, color in enumerate(B["ansi_colors"](palette)):
                if index in (0, 7, 15) and not palette.get("hc"):
                    continue
                self.assertGreaterEqual(B["contrast"](color, palette["bg"]), minimum - 0.05,
                                        f"{key} ANSI {index} {color}")

    def test_high_contrast_light_has_no_white_on_white(self):
        palette = B["P"]["eva-mark06-hc"]
        self.assertGreaterEqual(B["contrast"](B["ansi_colors"](palette)[15], palette["bg"]), 6.95)

    def test_cursor_is_visible_on_every_background(self):
        for key, palette in B["P"].items():
            self.assertGreaterEqual(B["contrast"](B["cursor_color"](palette), palette["bg"]), 2.95, key)


if __name__ == "__main__":
    unittest.main()
