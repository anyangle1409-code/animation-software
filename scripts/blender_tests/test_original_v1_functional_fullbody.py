"""Actual Blender inventory guard for the provisional original-body bridge."""
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import original_v1_functional_fullbody as bridge


class NativeFunctionalFullBodyBridge(unittest.TestCase):
    def test_original_body_is_bound_to_runtime_beside_complete_anatomical_master(self):
        anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        result = bridge.validate_blender_bridge(anatomy, runtime, body)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(anatomy.data.bones), 206)
        self.assertEqual(len(runtime.data.bones), 67)
        targets = {m.object.name for m in body.modifiers if m.type == "ARMATURE" and m.object}
        self.assertIn(runtime.name, targets)

    def test_disabled_or_wrong_target_modifier_is_refused(self):
        anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        modifier = next(m for m in body.modifiers if m.type == "ARMATURE")
        original_target, original_viewport = modifier.object, modifier.show_viewport
        try:
            modifier.show_viewport = False
            self.assertTrue(bridge.validate_blender_bridge(anatomy, runtime, body)["errors"])
            modifier.show_viewport = True
            modifier.object = anatomy
            self.assertTrue(bridge.validate_blender_bridge(anatomy, runtime, body)["errors"])
        finally:
            modifier.object = original_target
            modifier.show_viewport = original_viewport

    def test_additional_enabled_anatomical_driver_is_refused(self):
        anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        extra = body.modifiers.new("TEST_FORBIDDEN_ANATOMICAL_DRIVER", "ARMATURE")
        extra.object = anatomy
        try:
            errors = "\n".join(bridge.validate_blender_bridge(anatomy, runtime, body)["errors"])
            self.assertIn("exactly one", errors)
        finally:
            body.modifiers.remove(extra)

    def test_nonrest_anatomical_master_is_refused(self):
        anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        bone = anatomy.pose.bones[0]
        original = bone.matrix_basis.copy()
        try:
            bone.matrix_basis = Matrix.Translation((0.001, 0, 0))
            errors = "\n".join(bridge.validate_blender_bridge(anatomy, runtime, body)["errors"])
            self.assertIn("rest", errors)
        finally:
            bone.matrix_basis = original


if __name__ == "__main__":
    result = unittest.TextTestRunner().run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeFunctionalFullBodyBridge)
    )
    if not result.wasSuccessful():
        raise RuntimeError("native functional full-body bridge tests failed")
