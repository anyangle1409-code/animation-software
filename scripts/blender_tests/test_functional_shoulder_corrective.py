import math
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_functional_shoulder_corrective_blender as builder
import functional_coupled_corrective as contract


class FunctionalShoulderCorrectiveNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = builder.build_corrective_scene()
        cls.body = cls.result["body"]
        cls.runtime = cls.result["runtime"]
        cls.anatomy = cls.result["anatomy"]
        cls.rows = {r["ht_elevation_deg"]: r for r in builder.measure(cls.result)}

    def tearDown(self):
        builder.apply_pose_with_correctives(self.result, 0)

    def test_forward_skinning_check_mirror_and_bounded_deltas_for_every_key(self):
        log = self.result["solve_log"]
        self.assertEqual(sorted(int(k) for k in log), [int(k) for k in contract.KEY_POSES_DEG])
        for k, entry in log.items():
            self.assertLess(entry["lbs_inverse_max_error_m"], 1e-5, k)
            self.assertLess(entry["mirror_map_max_error_m"], 1e-5, k)
            self.assertLessEqual(entry["max_rest_delta_m"], builder.DELTA_CAP_M + 1e-9, k)
        keys = self.body.data.shape_keys.key_blocks
        basis = keys["Basis"].data
        for label in log:
            kb = keys[builder.KEY_PREFIX + label].data
            worst = max((kb[i].co - basis[i].co).length for i in range(len(basis)))
            self.assertLessEqual(worst, builder.DELTA_CAP_M * 1.001, label)

    def test_posed_correction_is_bounded_at_keys_and_between_keys(self):
        # blended LBS matrices have singular values <= 1, so a capped rest delta cannot move posed skin further
        for e, row in self.rows.items():
            self.assertLessEqual(row["max_posed_correction_mm"], builder.DELTA_CAP_M * 1000 * 1.01, e)

    def test_keys_change_nothing_at_rest_and_ninety(self):
        for e in (0, 90):
            row = self.rows[e]
            self.assertEqual(row["max_posed_correction_mm"], 0.0, e)

    def test_volume_and_thorax_clearance_improve_at_every_key_pose(self):
        for k in contract.KEY_POSES_DEG:
            row = self.rows[int(k)]
            w, wo = row["with_correctives"], row["without_correctives"]
            self.assertLessEqual(abs(w["body_volume_change_pct"]), contract.TARGETS["body_volume_change_abs_pct_max"], k)
            self.assertGreater(w["torso_thorax_hull_clearance_min_mm"], wo["torso_thorax_hull_clearance_min_mm"], k)

    def test_thorax_clearance_excludes_neck_and_stays_in_rib_span(self):
        body = self.body
        dom = builder.correction._dominant_groups(body)
        lo, hi = self.result["rib_clearance"].z_span
        rest = self.result["rest"][0]
        for i, flag in enumerate(self.result["torso"]):
            if flag:
                self.assertFalse(dom[i].startswith("neck"), i)
                self.assertTrue(lo <= rest[i].z <= hi, i)

    def test_unmet_targets_are_recorded_for_every_pose(self):
        for e, row in self.rows.items():
            for label in ("with_correctives", "without_correctives"):
                m = row[label]
                self.assertEqual(m["unmet_targets"], contract.meets_targets(m, m["torso_thorax_hull_clearance_min_mm"]))

    def test_source_rests_driver_unchanged_and_keys_reset(self):
        builder.apply_pose_with_correctives(self.result, 160)
        self.assertTrue(all(b.matrix_basis.is_identity for b in self.anatomy.pose.bones))
        active = [m for m in self.body.modifiers if m.type == "ARMATURE" and (m.show_viewport or m.show_render)]
        self.assertEqual(len(active), 1)
        self.assertIs(active[0].object, self.runtime)
        keys = self.body.data.shape_keys.key_blocks
        self.assertTrue(all(keys[n].value == 0.0 for n in ("HGPT_SHOULDER_CORR_L", "HGPT_SHOULDER_CORR_R",
                                                             "HGPT_SHOULDER_FLEX_L", "HGPT_SHOULDER_FLEX_R",
                                                             "HGPT_SHOULDER_SCAP_L", "HGPT_SHOULDER_SCAP_R")))
        self.assertEqual(keys[builder.KEY_PREFIX + "160"].value, 1.0)
        builder.apply_pose_with_correctives(self.result, 0)
        self.assertTrue(all(kb.value == 0.0 for kb in keys[1:]))
        self.assertEqual(len(self.body.data.vertices), 17946)

    def test_invalid_input_fails_before_mutation_and_scene_is_unapproved(self):
        builder.apply_pose_with_correctives(self.result, 130)
        before = {n: b.matrix_basis.copy() for n, b in self.runtime.pose.bones.items()}
        values = [kb.value for kb in self.body.data.shape_keys.key_blocks]
        with self.assertRaisesRegex(ValueError, "finite HT elevation 0..160"):
            builder.apply_pose_with_correctives(self.result, math.nan)
        for n, m in before.items():
            self.assertEqual(m, self.runtime.pose.bones[n].matrix_basis)
        self.assertEqual(values, [kb.value for kb in self.body.data.shape_keys.key_blocks])
        self.assertFalse(bpy.context.scene["functional_coupled_corrective_approved"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
