"""Native checks of the full-range press (scripts/original_v1_press_extension.py) on the R9 review blend: identical poses up
to 160 deg without a shrug, near-vertical lockout, the shoulder rises with the shrug, and the hook is off by default."""
import math
import sys
import unittest
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

R9 = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r9_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R9_CLAUDE.blend"


class PressExtensionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build_functional_shoulder_correction_blender as correction
        import build_original_movement_benchmarks_blender as bench
        import original_v1_review_candidate_drives as drives
        import original_v1_press_extension as px
        import original_v1_shoulder_r4 as r4
        bpy.ops.wm.open_mainfile(filepath=str(R9))
        cls.res = correction.build_corrected_scene()
        cls.rig, cls.body = cls.res["runtime"], cls.res["body"]
        drives.setup(cls.res)
        cls.hook_default = r4._S.get("extend")
        cls.correction, cls.bench, cls.drives, cls.px, cls.r4 = correction, bench, drives, px, r4

    def _pose(self, fn):
        fn()
        self.drives.drive(self.rig, self.body)
        V, _ = self.bench._evaluated(self.body)
        return np.array([tuple(v) for v in V])

    def test_hook_is_off_by_default(self):
        self.assertIsNone(self.hook_default)

    def test_identical_up_to_160_without_shrug(self):
        for ht in (60, 120, 160):
            self.r4._S.pop("extend", None)
            a = self._pose(lambda: self.correction.apply_corrected_pose(self.res, ht))
            self.px.install()
            b = self._pose(lambda: self.px.apply_pose(self.res, ht, 0.0))
            self.assertLess(float(np.abs(a - b).max()), 1e-9, ht)

    def test_lockout_is_near_vertical_and_the_shoulder_rises(self):
        self.px.install()
        pb = self.rig.pose.bones
        self.px.apply_pose(self.res, 160, 0.0)
        ac160 = pb["clavicle_r"].tail.z
        ht, elbow, shrug = self.px.press_state(1.0)
        self.assertEqual((ht, elbow, shrug), (172.0, 0.0, 12.0))
        self.px.pose_press_full(self.res, 1.0)
        for s in ("r", "l"):
            arm = (pb[f"upperarm_{s}"].tail - pb[f"upperarm_{s}"].head).normalized()
            self.assertLess(math.degrees(math.acos(arm.z)), 10.0, s)        # 160 deg path: 20 deg from vertical
        self.assertGreater(pb["clavicle_r"].tail.z - ac160, 0.020)          # AC joint rises > 20 mm (shrug)
        self.assertLess(abs(pb["clavicle_r"].tail.z - pb["clavicle_l"].tail.z), 1e-5)    # mirror (float32, as R4)
        self.assertEqual(self.px._STATE["shrug_deg"], 0.0)                  # shrug state does not leak

    def test_press_path_is_monotonic(self):
        prev = None
        for i in range(21):
            ht, elbow, shrug = self.px.press_state(i / 20)
            if prev:
                self.assertGreaterEqual(ht, prev[0]); self.assertLessEqual(elbow, prev[1]); self.assertGreaterEqual(shrug, prev[2])
            prev = (ht, elbow, shrug)


    def test_press_path_v2_is_opt_in_and_matches_the_reference_shape(self):
        # v2 (owner's 7-view photo series): plane 15 deg, start 70 deg / elbow 140 deg, forearms aimed at the dumbbells just
        # outside the shoulders; R10-R13 blends carry no scene flag and stay on v1
        self.px.install()
        self.assertEqual(self.px._PATH["name"], "v1")
        bpy.context.scene["hgpt_press_path"] = "v2"
        try:
            self.px.install()
            pb = self.rig.pose.bones
            self.assertEqual(self.px.press_state(0.0)[:2], (70.0, 140.0))
            for t in (0.0, 0.5, 1.0):
                a = self.px.pose_press_full(self.res, t)
                self.drives.drive(self.rig, self.body)
                sh, el, ha = pb["upperarm_r"].head, pb["forearm_r"].head, pb["hand_r"].head
                u = el - sh
                self.assertAlmostEqual(math.degrees(math.atan2(-u.y, abs(u.x))), 15.0, delta=0.5)
                for n in ("forearm", "hand"):                      # mirror-symmetric
                    r, l = pb[f"{n}_r"].head, pb[f"{n}_l"].head
                    self.assertLess((r - type(r)((-l.x, l.y, l.z))).length, 1e-3, (t, n))
                if t == 0.0:
                    self.assertGreater(ha.z, el.z + 0.2)               # hands above the elbows, by the head
                    self.assertLess(ha.x, el.x - 0.1)                  # elbows out wider than the hands
                    self.assertLess(abs(ha.x - (sh.x + self.px.HAND_OUT_M)), 0.05)
            self.assertAlmostEqual(a["humerothoracic_elevation"], self.px.LOCKOUT_HT)
        finally:
            del bpy.context.scene["hgpt_press_path"]
            self.px.install()
            self.r4._S["extend"] = self.hook_default
        self.assertEqual(self.px._PATH["name"], "v1")


if __name__ == "__main__":
    unittest.main(argv=[__file__])
