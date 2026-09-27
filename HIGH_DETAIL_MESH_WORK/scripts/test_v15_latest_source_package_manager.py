import unittest
from unittest.mock import patch
from pathlib import Path

import run_v15_latest_source_validation as validation


class PackageManagerTests(unittest.TestCase):
    def test_prefers_npm_when_available(self):
        with patch.object(validation.shutil, "which", side_effect=lambda name: "npm.cmd" if name == "npm" else None):
            self.assertEqual(validation.package_manager(), ("npm.cmd", "npm"))

    def test_uses_pnpm_when_npm_is_missing(self):
        with patch.object(validation.shutil, "which", side_effect=lambda name: "pnpm.cmd" if name == "pnpm" else None):
            self.assertEqual(validation.package_manager(), ("pnpm.cmd", "pnpm"))

    def test_windows_cleanup_path_uses_extended_prefix(self):
        path = validation.cleanup_path(Path(r"C:\very\long\worktree"))
        self.assertTrue(str(path).startswith("\\\\?\\"))


if __name__ == "__main__":
    unittest.main()
