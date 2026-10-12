"""Actual Blender inventory guard for the provisional original-body bridge."""
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import original_v1_functional_fullbody as bridge


class NativeFunctionalFullBodyBridge(unittest.TestCase):
    def test_original_body_is_bound_to_runtime_beside_complete_anatomical_master(self):
        anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        result = bridge.validate_inventory(
            {b.name for b in anatomy.data.bones},
            {b.name for b in runtime.data.bones},
            len(body.data.vertices),
        )
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(anatomy.data.bones), 206)
        self.assertEqual(len(runtime.data.bones), 67)
        targets = {m.object.name for m in body.modifiers if m.type == "ARMATURE" and m.object}
        self.assertIn(runtime.name, targets)


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeFunctionalFullBodyBridge)
    )
    if not result.wasSuccessful():
        raise RuntimeError("native functional full-body bridge tests failed")
