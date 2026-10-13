import math
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_shoulder_correction_blender as builder
import functional_shoulder_correction as corr


class FunctionalShoulderCorrectionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = builder.build_corrected_scene()
        cls.runtime = cls.result["runtime"]
        cls.anatomy = cls.result["anatomy"]
        cls.body = cls.result["body"]
        cls.metrics = builder.measure(cls.result)

    def tearDown(self):
        builder.apply_corrected_pose(self.result, 0)

    def test_scapula_outline_matches_lee_182cm_and_stays_on_the_glenoid(self):
        lee = corr.lee_reference_distances()
        for side, rep in self.result["scapula_report"].items():
            L = rep["landmarks"]
            for name, ref in lee.items():
                i, j = ref["pair_1based"]
                self.assertLess(abs(math.dist(L[i - 1], L[j - 1]) * 1000 - ref["pred_mm"]), ref["resid_sd_mm"], (side, name))
            after = rep["medial_clearance_mm_after"]
            self.assertTrue(all(4.0 <= c <= 20.0 for c in after), (side, after))
            self.assertLessEqual(abs(rep["rotation_about_glenoid_deg"]["yaw_z"]), 25)

    def test_guides_are_inside_the_original_skin_at_rest(self):
        rest = self.metrics[0]
        self.assertEqual(rest["ht_elevation_deg"], 0)
        self.assertEqual(sum(rest["guide_vertices_outside_skin"].values()), 0, rest["guide_vertices_outside_skin"])

    def test_rib_guides_keep_frozen_a003_endpoints(self):
        for number in (1, 6, 11):
            for side in ("left", "right"):
                bone = self.anatomy.data.bones[f"anat_rib_{number:02d}_{side}"]
                guide = self.result["objects"][f"rib_{number:02d}_{side}"]
                pts = builder.attachment._world_points(guide)
                for end in (bone.head_local, bone.tail_local):
                    nearest = min((p - end).length for p in pts)
                    self.assertLessEqual(nearest, builder.RIB_RADIUS_M + 1e-4, (number, side))
                self.assertEqual(guide["rib_scope"], corr.RIB_SCOPE)

    def test_humeral_axial_channel_is_exact_and_shaft_matches_pr110(self):
        for angle in (0, 90, 160):
            profile = builder.apply_corrected_pose(self.result, angle)
            ext = corr.humeral_external_rotation_deg(angle)
            for side, name in builder.HUMERI:
                self.assertAlmostEqual(profile["humeral_axial_realized_rel_rest_deg"][side],
                                       corr.external_rotation_sign(side) * ext, places=4)
                bone = self.runtime.pose.bones[name]
                sign = 1 if side == "left" else -1
                e, p = math.radians(angle), math.radians(profile["plane_deg"])
                want = Vector((sign * math.sin(e) * math.cos(p), -math.sin(e) * math.sin(p), -math.cos(e)))
                self.assertLess(((bone.tail - bone.head).normalized() - want).length, 1e-5, (angle, side))

    def test_external_rotation_moves_a_bone_carried_anterior_probe_laterally(self):
        """Physical direction check, independent of the axial-angle measure used to solve the delta."""
        import functional_shoulder_correction as module
        original = module.HUMERAL_AXIAL_TOP_DEG
        try:
            for side, name in builder.HUMERI:
                lateral = 1.0 if side == "left" else -1.0
                probes = []
                for top in (0.0, 40.0):
                    module.HUMERAL_AXIAL_TOP_DEG = top
                    builder.apply_corrected_pose(self.result, 80)
                    bone = self.runtime.pose.bones[name]
                    rest_bone = self.runtime.data.bones[name]
                    anterior_local = rest_bone.matrix_local.to_3x3().inverted() @ Vector((0.0, -1.0, 0.0))
                    probes.append((bone.matrix.to_3x3() @ anterior_local).normalized())
                d = (bone.tail - bone.head).normalized()
                turn = probes[0].cross(probes[1]).dot(d)
                # smoothstep(80/160) = 0.5, so raising the top from 0 to 40 deg must turn the probe 20 deg about the shaft
                self.assertAlmostEqual(math.degrees(math.asin(min(1.0, abs(turn)))), 20.0, delta=0.5)
                moved = probes[1] - probes[0]
                self.assertGreater(moved.x * lateral, 0.0, (side, moved))
        finally:
            module.HUMERAL_AXIAL_TOP_DEG = original
            builder.apply_corrected_pose(self.result, 0)

    def test_clavicle_and_scapula_runtime_poses_are_pr110_unchanged(self):
        """The axial step does not touch clavicle/scapula; PR110's own native test guards their semantics."""
        for angle in (90, 160):
            builder.coupled.apply_coupled_pose(self.result, angle)
            pr110 = {n: self.runtime.pose.bones[n].matrix_basis.copy()
                     for n in ("clavicle_r", "clavicle_l", "scapula_r", "scapula_l")}
            builder.apply_corrected_pose(self.result, angle)
            for n, m in pr110.items():
                diff = sum(abs(a - b) for ra, rb in zip(m, self.runtime.pose.bones[n].matrix_basis) for a, b in zip(ra, rb))
                self.assertLess(diff, 1e-12, (angle, n))

    def test_source_rests_body_driver_unchanged_and_keys_reset(self):
        builder.apply_corrected_pose(self.result, 160)
        self.assertTrue(all(b.matrix_basis.is_identity for b in self.anatomy.pose.bones))
        active = [m for m in self.body.modifiers if m.type == "ARMATURE" and (m.show_viewport or m.show_render)]
        self.assertEqual(len(active), 1)
        self.assertIs(active[0].object, self.runtime)
        self.assertEqual(len(self.body.data.vertices), 17946)
        self.assertTrue(all(kb.value == 0.0 for kb in self.body.data.shape_keys.key_blocks[1:]))

    def test_deformation_metrics_are_finite_and_rest_is_identity(self):
        rest, mid, top = self.metrics
        self.assertEqual(rest["deformation"]["self_intersecting_face_pairs_in_region"], 0)  # unposed skin is clean
        for row in (mid, top):
            d = row["deformation"]
            for key in ("area_ratio_min", "area_ratio_max", "body_volume_change_pct"):
                self.assertTrue(math.isfinite(d[key]))
            self.assertIn("deformation_pr110_unchanged_pose", row)
            self.assertIn("deformation_with_existing_correctives_diagnostic", row)
        self.assertIsInstance(top["deformation"]["self_intersecting_face_pairs_in_region"], int)  # recorded, not gated
        self.assertIn("humeral_axial_pr110_implicit_rel_rest_deg", top)

    def test_invalid_input_fails_before_mutation_and_scene_is_unapproved(self):
        builder.apply_corrected_pose(self.result, 90)
        before = {n: b.matrix_basis.copy() for n, b in self.runtime.pose.bones.items()}
        with self.assertRaisesRegex(ValueError, "finite HT elevation 0..160"):
            builder.apply_corrected_pose(self.result, float("nan"))
        for n, m in before.items():
            self.assertEqual(m, self.runtime.pose.bones[n].matrix_basis)
        self.assertFalse(bpy.context.scene["functional_shoulder_correction_approved"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
