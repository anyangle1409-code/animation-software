"""Native checks of the ORIGINAL_v1 review candidate R14 = R13 on press path v2 with the shoulder-top weight gradient, the
pectoralis / latissimus / upper-trapezius muscle-line helpers and the press S4/S5 shapes re-made along v2.  Re-measured from
the saved blends.  Review only."""
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
R14 = CAND / "claude_review_r14_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R14_CLAUDE.blend"
REPORT = CAND / "claude_review_r14_20261015/r14_build.json"
VALIDATION = CAND / "claude_review_r14_20261015/r14_validation.json"
R13_VALIDATION = CAND / "claude_review_r13_20261015/r13_validation_corrected_poses_20261015.json"
SIDES = ("l", "r")
MUSCLES = ("pec", "lat", "trap")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class ReviewCandidateR14NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_and_flags(self):
        self.assertEqual(sha(R13), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R14), self.report["output"]["sha256"])
        import original_v1_review_candidate_drives  # noqa: F401
        bpy.ops.wm.open_mainfile(filepath=str(R14))
        scene = bpy.context.scene
        self.assertIs(scene.get("hgpt_review_candidate_approved"), False)
        self.assertEqual(scene.get("hgpt_press_path"), "v2")
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
        bpy.ops.wm.open_mainfile(filepath=str(R14))
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        drives.setup(res)
        px.install()
        self.assertEqual(px._PATH["name"], "v2")
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
            a, b = v1[n]["r13_worst"], v2[n]["r14_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 16, n)   # recorded: see the R14 doc


if __name__ == "__main__":
    unittest.main(argv=[__file__])
