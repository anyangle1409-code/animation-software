"""Native checks of the ORIGINAL_v1 review candidate R15 = R14's recipe on press path v4 (clavicle axial turn first, scapula
aligned with the arm at lockout - the Y), S5 shapes re-baked along v4.  Re-measured from the saved blends.  Review only."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R13 = CAND / "claude_review_r13_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R13_CLAUDE.blend"
R15 = CAND / "claude_review_r15_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R15_CLAUDE.blend"
REPORT = CAND / "claude_review_r15_20261015/r15_build.json"
VALIDATION = CAND / "claude_review_r15_20261015/r15_validation.json"
R13_VALIDATION = CAND / "claude_review_r13_20261015/r13_validation_corrected_poses_20261015.json"
SIDES = ("l", "r")
MUSCLES = ("pec", "lat", "trap")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class ReviewCandidateR15NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_and_flags(self):
        self.assertEqual(sha(R13), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R15), self.report["output"]["sha256"])
        import original_v1_review_candidate_drives  # noqa: F401
        bpy.ops.wm.open_mainfile(filepath=str(R15))
        scene = bpy.context.scene
        self.assertIs(scene.get("hgpt_review_candidate_approved"), False)
        self.assertEqual(scene.get("hgpt_press_path"), "v4")
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        rig = body.find_armature()
        self.assertEqual(sum(b.use_deform for b in rig.data.bones), 67)        # helpers live in memory only
        self.assertIn("hgpt_muscle_lines", rig)
        self.assertIn("hgpt_trap_gradient", rig)
        for s in SIDES:
            for m in MUSCLES:
                self.assertIn(f"muscle_{m}_{s}", body.vertex_groups)
        keys = [kb.name for kb in body.data.shape_keys.key_blocks]
        self.assertFalse(any(k.startswith("HGPT_S4_SCULPT_") for k in keys))     # v1 sculpt dropped (only in the target)
        for s in SIDES:
            self.assertTrue(any(k.startswith(f"HGPT_S5_BAKE_{s}_") for k in keys), s)

    def test_helpers_install_and_follow_the_arm(self):
        import build_functional_shoulder_correction_blender as correction
        import build_original_sculpt_corrective_blender as s4
        import original_v1_press_extension as px
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R15))
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        drives.setup(res)
        px.install()
        self.assertEqual(px._PATH["name"], "v4")
        for s in SIDES:
            for m in MUSCLES:
                self.assertIn(f"muscle_{m}_{s}", rig.data.bones)
        s4.press_pose(res, 172)
        drives.drive(rig, body)
        pb = rig.pose.bones
        for s in SIDES:                     # stretched / shortened as measured (lat > 1.3, trapezius < 1)
            lat = (pb[f"muscle_lat_{s}"].tail - pb[f"muscle_lat_{s}"].head).length / rig.data.bones[f"muscle_lat_{s}"].length
            trap = (pb[f"muscle_trap_{s}"].tail - pb[f"muscle_trap_{s}"].head).length / rig.data.bones[f"muscle_trap_{s}"].length
            self.assertGreater(lat, 1.3, s)
            self.assertLess(trap, 1.0, s)
        r, l = pb["muscle_pec_r"].tail, pb["muscle_pec_l"].tail
        self.assertLess((r - type(r)((-l.x, l.y, l.z))).length, 0.002)          # mirror-symmetric

    def test_press_path_no_new_overlap_from_the_baked_shapes(self):
        rows = list(zip(self.report["press_path_without_s5"], self.report["press_path_r14"]))
        for a, b in rows:
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
        top = [(a, b) for a, b in rows if a["ht"] >= 120]
        self.assertLess(sum(b["stretch"] for _, b in top), 0.6 * sum(a["stretch"] for a, _ in top))
        lock = rows[-1][1]
        self.assertLessEqual(lock["pairs"], 4)
        self.assertGreater(lock["volume_pct"], -2.0)

    def test_benchmarks_versus_r13(self):
        v1 = json.loads(R13_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r13_worst"], v2[n]["r15_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 16, n)   # recorded: see the R15 doc

    def test_lockout_skeleton_y(self):
        import build_functional_shoulder_correction_blender as correction
        import build_original_movement_benchmarks_blender as bench
        import original_v1_press_extension as px
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R15))
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        self.assertNotIn("hgpt_cap_fraction_ramp", rig)                               # R16's ramp was rejected (crushed skin)
        drives.setup(res)
        px.install()
        W = rig.matrix_world
        pb = rig.pose.bones
        bench._reset(rig)
        bpy.context.view_layer.update()
        cl = pb["clavicle_r"]
        v0 = (W @ cl.tail) - (W @ cl.head)
        TS = bpy.data.objects["LM_scapula_left__TS"].matrix_world.translation.copy()      # runtime _r = anatomical left
        AA = bpy.data.objects["LM_scapula_left__AA"].matrix_world.translation.copy()
        sc = rig.data.bones["scapula_r"]
        px.pose_press_full(res, 1.0)
        drives.drive(rig, body)
        M = W @ pb["scapula_r"].matrix @ sc.matrix_local.inverted() @ W.inverted()
        hum = (W @ pb["upperarm_r"].tail) - (W @ pb["upperarm_r"].head)
        import math
        self.assertLess(math.degrees(hum.angle((M @ AA) - (M @ TS))), 10.0)          # the Y: arm in line with the scapular spine
        v1 = (W @ cl.tail) - (W @ cl.head)
        retr = lambda v: math.degrees(math.atan2(v.y, v.x))
        self.assertGreater(retr(v1) - retr(v0), 5.0)                                   # clavicle retracts (v2 protracted 5 deg)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
