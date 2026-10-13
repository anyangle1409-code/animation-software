import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_original_attachment_blender as builder


class FunctionalOriginalAttachmentNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = builder.build_attachment_scene()
        cls.anatomy = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
        cls.runtime = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
        cls.body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]

    def tearDown(self):
        for pose_bone in self.runtime.pose.bones:
            pose_bone.matrix_basis.identity()
        bpy.context.view_layer.update()

    def test_expected_authored_guides_are_attached_without_retargeting_source(self):
        objects = self.result["objects"]
        self.assertEqual(len(objects), 29)
        self.assertEqual(self.result["contract"]["errors"], [])
        self.assertTrue(self.result["contract"]["non_bijective"])
        self.assertFalse(self.result["contract"]["anatomy_approved"])
        self.assertEqual(objects["clavicle_left"]["runtime_control"], "clavicle_r")
        self.assertEqual(objects["scapula_left"]["runtime_control"], "scapula_r")
        self.assertEqual(objects["rib_01_left"]["runtime_control"], "spine_02")
        for obj in objects.values():
            modifiers = [modifier for modifier in obj.modifiers if modifier.type == "ARMATURE"]
            self.assertEqual(len(modifiers), 1)
            self.assertIs(modifiers[0].object, self.runtime)
            self.assertEqual(len(obj.vertex_groups), 1)
            self.assertEqual(obj.vertex_groups[0].name, obj["runtime_control"])
            self.assertFalse(obj["anatomy_approved"])
        self.assertTrue(all(pose_bone.matrix_basis.is_identity for pose_bone in self.anatomy.pose.bones))

    def test_clavicle_guide_uses_anatomical_sc_and_ac_without_moving_them(self):
        for side in ("left", "right"):
            source = self.anatomy.data.bones[f"anat_clavicle_{side}"]
            guide = self.result["objects"][f"clavicle_{side}"]
            self.assertLess((builder.Vector(guide["source_head"]) - source.head_local).length, 1e-10)
            self.assertLess((builder.Vector(guide["source_tail"]) - source.tail_local).length, 1e-10)
            self.assertEqual(guide["curve_kind"], "project-authored S curve")

    def test_runtime_pose_delta_moves_guide_while_source_stays_at_rest(self):
        guide = self.result["objects"]["clavicle_left"]
        base = guide.matrix_world @ guide.data.vertices[len(guide.data.vertices) // 2].co
        source_before = self.anatomy.data.bones["anat_clavicle_left"].head_local.copy()
        control = self.runtime.pose.bones[guide["runtime_control"]]
        control.rotation_mode = "XYZ"
        control.rotation_euler.z = 0.17
        bpy.context.view_layer.update()
        evaluated = guide.evaluated_get(bpy.context.evaluated_depsgraph_get())
        posed = evaluated.matrix_world @ evaluated.data.vertices[len(evaluated.data.vertices) // 2].co
        self.assertGreater((posed - base).length, 0.005)
        self.assertLess((self.anatomy.data.bones["anat_clavicle_left"].head_local - source_before).length, 1e-12)
        self.assertTrue(all(pose_bone.matrix_basis.is_identity for pose_bone in self.anatomy.pose.bones))

    def test_original_body_driver_and_source_counts_remain_unchanged(self):
        self.assertEqual(len(self.anatomy.data.bones), 206)
        self.assertEqual(len(self.runtime.data.bones), 67)
        self.assertEqual(len(self.body.data.vertices), 17_946)
        active = [modifier for modifier in self.body.modifiers
                  if modifier.type == "ARMATURE" and (modifier.show_viewport or modifier.show_render)]
        self.assertEqual(len(active), 1)
        self.assertIs(active[0].object, self.runtime)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
