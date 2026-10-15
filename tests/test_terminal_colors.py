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


if __name__ == "__main__":
    unittest.main()
