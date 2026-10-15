"""terminals/install.sh must handle flags, bad themes and re-apply/uninstall in a disposable HOME."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
INSTALL = SOURCE / "terminals/install.sh"


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.kitty = self.home / ".config/kitty"
        self.ghostty = self.home / ".config/ghostty"
        self.kitty.mkdir(parents=True)
        self.ghostty.mkdir(parents=True)
        (self.ghostty / "config").write_text("theme = Old\nfont-size = 12\n")
        (self.kitty / "dark-theme.auto.conf").write_text("include old.conf\n")

    def run_install(self, *args):
        env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / ".config"),
                   KITTY_CONFIG_DIRECTORY=str(self.kitty), XDG_DATA_HOME=str(self.home / ".local/share"))
        return subprocess.run(["bash", str(INSTALL), *args], env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True)

    def test_kitty_and_ghostty_flags_add_up(self):
        result = self.run_install("--install", "--kitty", "--ghostty")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.kitty / "themes/Noctis-EVA-01.conf").is_file())
        self.assertTrue((self.ghostty / "themes/Noctis-EVA-01").is_file())

    def test_single_terminal_flag_skips_the_other(self):
        self.assertEqual(self.run_install("--install", "--kitty").returncode, 0)
        self.assertTrue((self.kitty / "themes/Noctis-EVA-01.conf").is_file())
        self.assertFalse((self.ghostty / "themes").exists())

    def test_unknown_theme_fails_without_installing(self):
        result = self.run_install("--install", "--apply", "--dark", "NOPE")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown theme 'NOPE'", result.stderr)
        self.assertFalse((self.kitty / "themes").exists())
        self.assertEqual((self.ghostty / "config").read_text(), "theme = Old\nfont-size = 12\n")

    def test_reapply_then_uninstall_restores_original_files(self):
        for _ in range(2):
            self.assertEqual(self.run_install("--install", "--apply").returncode, 0)
        self.assertEqual(self.run_install("--uninstall").returncode, 0)
        self.assertEqual((self.kitty / "dark-theme.auto.conf").read_text(), "include old.conf\n")
        self.assertFalse((self.kitty / "light-theme.auto.conf").exists())
        self.assertFalse(list(self.kitty.glob("*.pre-eva-noctis")))
        self.assertFalse(list(self.ghostty.glob("*.pre-eva-noctis")))
        self.assertEqual(sorted((self.ghostty / "config").read_text().splitlines()),
                         ["font-size = 12", "theme = Old"])

    def test_alacritty_and_wezterm_install_and_uninstall(self):
        result = self.run_install("--install", "--apply", "--alacritty", "--wezterm", "--dark", "EVA-13")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".config/alacritty/themes/Noctis-EVA-13.toml").is_file())
        self.assertTrue((self.home / ".config/wezterm/colors/Noctis-EVA-13.toml").is_file())
        self.assertIn("Noctis-EVA-13.toml", result.stdout)
        self.assertFalse((self.kitty / "themes").exists())
        self.assertEqual(self.run_install("--uninstall", "--alacritty", "--wezterm").returncode, 0)
        self.assertFalse(list((self.home / ".config").glob("*/themes/Noctis-*")))
        self.assertFalse(list((self.home / ".config/wezterm/colors").glob("Noctis-*")))

    def test_status_reports_active_pair_without_changes(self):
        self.assertEqual(self.run_install("--install", "--apply", "--kitty", "--ghostty").returncode, 0)
        result = self.run_install("--status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dark: Noctis (EVA-01)", result.stdout)
        self.assertIn("theme = light:Noctis-EVA-00,dark:Noctis-EVA-01", result.stdout)

    def test_ghostty_config_ghostty_is_used_when_present(self):
        (self.ghostty / "config").unlink()
        (self.ghostty / "config.ghostty").write_text("font-size = 12\n")
        self.assertEqual(self.run_install("--install", "--apply", "--ghostty").returncode, 0)
        self.assertFalse((self.ghostty / "config").exists())
        self.assertIn("Noctis-EVA-01", (self.ghostty / "config.ghostty").read_text())
        self.assertEqual(self.run_install("--uninstall", "--ghostty").returncode, 0)
        self.assertEqual((self.ghostty / "config.ghostty").read_text(), "font-size = 12\n")

    def test_folder_terminals_install_hint_and_uninstall(self):
        flags = ("--foot", "--konsole", "--zellij", "--tmux", "--xresources")
        env_data = self.home / ".local/share"
        result = self.run_install("--install", "--apply", *flags, "--dark", "EVA-13")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".config/foot/themes/Noctis-EVA-13.ini").is_file())
        self.assertTrue((self.home / ".config/zellij/themes/Noctis-EVA-13.kdl").is_file())
        self.assertTrue((self.home / ".config/tmux/themes/Noctis-EVA-13.conf").is_file())
        self.assertTrue((self.home / ".config/xresources/themes/Noctis-EVA-13").is_file())
        self.assertTrue(list((env_data / "konsole").glob("Noctis-*.colorscheme")))
        self.assertIn('theme "noctis-eva-13"', result.stdout)
        self.assertFalse((self.kitty / "themes").exists())
        self.assertEqual(self.run_install("--uninstall", *flags).returncode, 0)
        self.assertFalse(list(self.home.rglob("Noctis-*.ini")) + list(self.home.rglob("Noctis-*.kdl"))
                         + list(self.home.rglob("Noctis-*.colorscheme")))


if __name__ == "__main__":
    unittest.main()
