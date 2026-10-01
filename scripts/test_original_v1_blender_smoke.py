"""Blender smoke runner keeps current candidate selection deterministic."""
from __future__ import annotations
from pathlib import Path
import unittest

import original_v1_blender_smoke as s


class BlenderSmokeTests(unittest.TestCase):
    def test_blender_script_is_declared_and_repository_local(self):
        self.assertEqual(s.BLENDER_SCRIPT,"scripts/smoke_original_v1_candidate_blender.py")
        self.assertTrue((s.ROOT/s.BLENDER_SCRIPT).is_file())


if __name__=="__main__":
    unittest.main()
