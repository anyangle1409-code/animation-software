import hashlib
import sys
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_shoulder_correction_blender as correction
import build_original_knee_contact_corrective_blender as k1


class KneeContactCorrectiveNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = correction.build_corrected_scene()
        cls.before = k1.knee_sweep(cls.result, False, angles=(0, 60, 90, 110, 120))
        cls.elbow_before = k1.hinge_sweep(cls.result, False, "elbow", angles=(0, 60, 90, 110))
        cls.log = k1.build(cls.result)
        cls.elbow_log = k1.build(cls.result, "elbow")
        cls.after = k1.knee_sweep(cls.result, True, angles=(0, 60, 90, 110, 120))
        cls.elbow_after = k1.hinge_sweep(cls.result, True, "elbow", angles=(0, 60, 90, 110))

    def test_hinge_angle_ignores_forearm_twist(self):
        import build_original_movement_benchmarks_blender as bench
        rig = self.result["runtime"]
        try:
            for pro in (0.0, 68.8, -82.4):                    # atlas pronation / supination means
                for el in (60.0, 100.0, 120.0):
                    bench._reset(rig)
                    for s in k1.SIDES:
                        bench._forearm(rig, s, el, pro)
                    bpy.context.view_layer.update()
                    for s in k1.SIDES:
                        self.assertAlmostEqual(k1.hinge_angle_deg(rig, "elbow", s), el, places=3, msg=(pro, el, s))
        finally:
            bench._reset(rig)

    def test_activation_hats(self):
        self.assertEqual(set(k1.activations(0).values()), {0.0})
        self.assertEqual(set(k1.activations(k1.ACTIVATION_START).values()), {0.0})
        for key in k1.KEYS_DEG:
            a = k1.activations(key)
            self.assertAlmostEqual(a[key], 1.0)
            self.assertAlmostEqual(sum(a.values()), 1.0)
        for ang in (95, 100, 117, 125, 150):
            self.assertAlmostEqual(sum(k1.activations(ang).values()), 1.0, msg=ang)

    def test_keys_are_bounded_and_mirror_symmetric(self):
        body = self.result["body"]
        keys = body.data.shape_keys.key_blocks
        basis = keys["Basis"].data
        co = [v.co for v in body.data.vertices]
        index = {(round(c.x, 5), round(c.y, 5), round(c.z, 5)): i for i, c in enumerate(co)}
        for deg in k1.KEYS_DEG:
            r, l = keys[f"{k1.KEY_PREFIX}r_{deg}"].data, keys[f"{k1.KEY_PREFIX}l_{deg}"].data
            worst_mirror = 0.0
            for i in range(len(basis)):
                dr = r[i].co - basis[i].co
                self.assertLessEqual(dr.length, k1.DELTA_CAP_M * 1.001)
                if dr.length > 0:
                    j = index.get((round(-co[i].x, 5), round(co[i].y, 5), round(co[i].z, 5)))
                    if j is not None:
                        dl = l[j].co - basis[j].co
                        worst_mirror = max(worst_mirror, (dl - Vector((-dr.x, dr.y, dr.z))).length)
            self.assertLess(worst_mirror, 1e-4, deg)

    def test_no_effect_at_rest_or_below_activation(self):
        for a in (0, 60):
            self.assertEqual(self.after[a], self.before[a], a)

    def test_contact_cleared_without_new_stretch_or_volume_loss(self):
        for a in (90, 110, 120):
            b, c = self.before[a], self.after[a]
            self.assertGreater(b["self_intersecting_pairs"], 0, a)
            self.assertEqual(c["self_intersecting_pairs"], 0, a)
            self.assertLessEqual(c["stretch_gt_2"], b["stretch_gt_2"], a)
            self.assertLessEqual(c["collapse_lt_0_1"], b["collapse_lt_0_1"] + 2, a)
            self.assertGreaterEqual(c["body_volume_change_pct"], b["body_volume_change_pct"] - 1e-4, a)

    def test_elbow_crease_cleared_through_110_without_new_collapse_or_stretch(self):
        for a in (0, 60):
            self.assertEqual(self.elbow_after[a], self.elbow_before[a], a)
        for a in (90, 110):
            b, c = self.elbow_before[a], self.elbow_after[a]
            self.assertGreater(b["self_intersecting_pairs"], 0, a)
            self.assertEqual(c["self_intersecting_pairs"], 0, a)
            self.assertLessEqual(c["collapse_lt_0_1"], b["collapse_lt_0_1"], a)
            self.assertLessEqual(c["stretch_gt_2"], b["stretch_gt_2"], a)
        self.assertEqual(self.elbow_log["90"]["rest_deltas_clipped"], 0)

    def test_solve_is_well_conditioned_and_unclipped_through_120(self):
        for deg in (90, 110):
            e = self.log[str(deg)]
            self.assertGreater(e["blended_lbs_sigma_min"], 0.4)
            self.assertEqual(e["rest_deltas_clipped"], 0)

    def test_scene_rests_and_is_not_saved(self):
        rig = self.result["runtime"]
        self.assertTrue(all(pb.matrix_basis.is_identity for pb in rig.pose.bones))
        self.assertTrue(all(kb.value == 0.0 for kb in self.result["body"].data.shape_keys.key_blocks[1:]))
        src = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend"
        self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),
                         "670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56")   # keys never written to disk
        self.assertEqual(len(self.result["body"].data.vertices), 17946)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
