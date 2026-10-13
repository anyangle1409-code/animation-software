import math
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_original_coupled_motion_blender as builder


class FunctionalOriginalCoupledMotionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = builder.build_coupled_scene()
        cls.runtime = cls.result["runtime"]
        cls.anatomy = cls.result["anatomy"]
        cls.body = cls.result["body"]

    def tearDown(self):
        builder.apply_coupled_pose(self.result, 0)

    def _body_sample(self):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = self.body.evaluated_get(depsgraph)
        indices = builder.DEFORMATION_SAMPLE_INDICES
        return [evaluated.matrix_world @ evaluated.data.vertices[index].co for index in indices]

    def test_absolute_humeral_direction_reaches_guarded_targets(self):
        for angle in (0, 90, 160):
            profile = builder.apply_coupled_pose(self.result, angle)
            elevation = math.radians(angle)
            plane = math.radians(profile["plane_deg"])
            for side, sign, runtime_name in (("left", 1, "upperarm_r"),
                                             ("right", -1, "upperarm_l")):
                bone = self.runtime.pose.bones[runtime_name]
                actual = (bone.tail - bone.head).normalized()
                expected = Vector((sign * math.sin(elevation) * math.cos(plane),
                                   -math.sin(elevation) * math.sin(plane),
                                   -math.cos(elevation)))
                self.assertLess((actual - expected).length, 1e-5, (angle, side, actual))

    def test_guides_move_progressively_while_source_armature_stays_at_rest(self):
        guide = self.result["objects"]["scapula_left"]
        positions = []
        for angle in (0, 90, 160):
            builder.apply_coupled_pose(self.result, angle)
            positions.append(builder.evaluated_centroid(guide))
            self.assertTrue(all(bone.matrix_basis.is_identity for bone in self.anatomy.pose.bones))
        self.assertGreater((positions[1] - positions[0]).length, 0.002)
        self.assertGreater((positions[2] - positions[0]).length,
                           (positions[1] - positions[0]).length)

    def test_clavicle_named_components_use_shaft_and_perpendicular_axes(self):
        zeros = {name: 0.0 for name in builder.motion.COUPLED_COMPONENTS}
        for runtime_name, side_sign in (("clavicle_r", 1.0), ("clavicle_l", -1.0)):
            bone = self.runtime.pose.bones[runtime_name]
            data_bone = self.runtime.data.bones[runtime_name]
            rest = (data_bone.tail_local - data_bone.head_local).normalized()

            axial = dict(zeros, clavicle_posterior_rotation_deg=28.0)
            bone.matrix_basis = builder.clavicle_basis(axial, side_sign)
            bpy.context.view_layer.update()
            axial_direction = (bone.tail - bone.head).normalized()
            self.assertLess((axial_direction - rest).length, 1e-5)

            elevation = dict(zeros, clavicle_elevation_deg=12.0)
            bone.matrix_basis = builder.clavicle_basis(elevation, side_sign)
            bpy.context.view_layer.update()
            elevation_direction = (bone.tail - bone.head).normalized()
            self.assertGreater(elevation_direction.z - rest.z, 0.1)

            retraction = dict(zeros, clavicle_retraction_deg=8.0)
            bone.matrix_basis = builder.clavicle_basis(retraction, side_sign)
            bpy.context.view_layer.update()
            retraction_direction = (bone.tail - bone.head).normalized()
            self.assertGreater((Vector((retraction_direction.x, retraction_direction.y, 0)) -
                                Vector((rest.x, rest.y, 0))).length, 0.05)

    def test_invalid_input_fails_before_runtime_mutation(self):
        builder.apply_coupled_pose(self.result, 90)
        before = {name: bone.matrix_basis.copy() for name, bone in self.runtime.pose.bones.items()}
        with self.assertRaisesRegex(ValueError, "finite HT elevation 0..160"):
            builder.apply_coupled_pose(self.result, float("nan"))
        for name, matrix in before.items():
            self.assertLess(sum(abs(a - b) for row_a, row_b in
                                zip(matrix, self.runtime.pose.bones[name].matrix_basis)
                                for a, b in zip(row_a, row_b)), 1e-12)

    def test_original_body_deforms_without_changing_its_single_driver(self):
        builder.apply_coupled_pose(self.result, 0)
        rest = self._body_sample()
        builder.apply_coupled_pose(self.result, 160)
        posed = self._body_sample()
        self.assertGreater(max((a - b).length for a, b in zip(rest, posed)), 0.01)
        active = [modifier for modifier in self.body.modifiers
                  if modifier.type == "ARMATURE" and
                  (modifier.show_viewport or modifier.show_render)]
        self.assertEqual(len(active), 1)
        self.assertIs(active[0].object, self.runtime)

    def test_profile_and_scene_remain_explicitly_unapproved(self):
        profile = builder.apply_coupled_pose(self.result, 160)
        self.assertFalse(profile["human_motion_accepted"])
        self.assertFalse(profile["approval"])
        self.assertFalse(bpy.context.scene["functional_coupled_motion_approved"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
