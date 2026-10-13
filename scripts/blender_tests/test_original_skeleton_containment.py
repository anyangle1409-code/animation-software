import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_original_skeleton_containment_blender as a1


class OriginalSkeletonContainmentNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree, cls.V, cls.F = a1.body_tree()
        cls.report = a1.run()

    def test_signed_depth_sign_on_known_points(self):
        far, clear = a1.signed_depth_mm(self.tree, Vector((0.0, -2.0, 1.0)))       # 2 m in front of the body
        self.assertLess(far, -1000.0)
        self.assertTrue(clear)
        pelvis = bpy.data.objects[a1.MASTER].data.bones["anat_l3"]
        deep, clear = a1.signed_depth_mm(self.tree, bpy.data.objects[a1.MASTER].matrix_world @ pelvis.head_local)
        self.assertGreater(deep, 20.0)                                               # lumbar body is deep inside the trunk
        self.assertTrue(clear)

    def test_counts_and_inventory(self):
        s = self.report["summary"]
        self.assertEqual(s["bones"], 206)
        self.assertEqual(s["joint_centres"], 427)
        self.assertEqual(s["bilateral_pairs"], 86)
        self.assertEqual(len(self.V), 17946)
        self.assertFalse(self.report["approved"])

    def test_flags_agree_with_samples(self):
        r = self.report
        self.assertEqual({b["bone"] for b in r["outside_bones"]},
                         {b["bone"] for b in r["bones_all"] if min(b["depth_mm_samples"]) <= 0})
        self.assertEqual(r["summary"]["bones_outside_skin"], len(r["outside_bones"]))
        for b in r["shallow_bones"]:
            self.assertTrue(0 < b["min_depth_mm"] < a1.SHALLOW_MM)

    def test_recorded_findings_still_hold(self):
        # regression guard on the measured state (a change here means the mesh or skeleton changed: re-audit, re-document)
        r = self.report
        self.assertEqual(sorted(b["bone"] for b in r["outside_bones"]), ["anat_fibula_left", "anat_fibula_right"])
        self.assertEqual(r["summary"]["joint_centres_outside_skin"], 0)
        self.assertEqual(r["summary"]["bony_landmarks_outside_skin"], 0)
        self.assertLess(r["summary"]["bilateral_mirror_error_max_mm"], 0.5)
        self.assertAlmostEqual(r["summary"]["body_height_m"], 1.82, places=3)

    def test_audit_leaves_scene_unchanged(self):
        arm = bpy.data.objects[a1.MASTER]
        self.assertTrue(all(pb.matrix_basis.is_identity for pb in arm.pose.bones))
        body = bpy.data.objects[a1.BODY]
        self.assertTrue(all(kb.value == 0.0 for kb in body.data.shape_keys.key_blocks[1:]))


if __name__ == "__main__":
    unittest.main(argv=[__file__])
