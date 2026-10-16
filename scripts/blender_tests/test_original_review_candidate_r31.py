"""Native checks of the ORIGINAL_v1 review candidate R31 (owner, on R29/R30: "The only joint will be the elbow.  That bone
should continue on into the shoulder not bend there"): the outer upper-arm skin re-bound to the humerus
(build_original_upperarm_follow_weights_blender.py, FOLLOW_T 0,0.08 m, FOLLOW_MEDIAL_RAMP -0.3,0.5), the S5 bake rebuilt on
the new binding (R15 chain), and the S7 lockout corrective rebuilt with the R30 recipe (lighter back fill LAT_WEB 0.35,
fade-in from 95 deg, keys 120/145/156/166).  Lineage R18 -> R18Wg5 -> B5 -> R31 (stage reports in stages/; the stage blends
are not committed).  Re-measured from the saved blends.  Review only."""
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
R18 = CAND / "claude_review_r18_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R18_CLAUDE.blend"
DIR = CAND / "claude_review_r31_20261016"
R31 = DIR / "HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R31_CLAUDE.blend"
REPORT = DIR / "r31_build.json"
VALIDATION = DIR / "r31_validation.json"
FOLLOW = DIR / "stages/r18wg5_follow_weights.json"
B5 = DIR / "stages/b5_s5_rebuild.json"
R29_VALIDATION = CAND / "claude_review_r29_20261016/r29_validation.json"
BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
SIDES = ("l", "r")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def upperarm_weights(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    out = {}
    for s in SIDES:
        g = body.vertex_groups[f"upperarm_{s}"].index
        out[s] = [next((e.weight for e in v.groups if e.group == g), 0.0) for v in body.data.vertices]
    return out


class ReviewCandidateR31NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_lineage_and_keys(self):
        follow, b5 = json.loads(FOLLOW.read_text()), json.loads(B5.read_text())
        self.assertEqual(sha(R18), follow["output"]["parent"]["sha256"])
        self.assertEqual(follow["output"]["sha256"], b5["output"]["parent"]["sha256"])
        self.assertEqual(b5["output"]["sha256"], self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R31), self.report["output"]["sha256"])
        self.assertEqual(follow["params"]["t0_m"], 0.0)
        self.assertEqual(follow["params"]["t1_m"], 0.08)
        self.assertEqual(follow["params"]["medial_ramp"], "-0.3,0.5")
        import original_v1_review_candidate_drives  # noqa: F401
        bpy.ops.wm.open_mainfile(filepath=str(R31))
        scene = bpy.context.scene
        self.assertIs(scene.get("hgpt_review_candidate_approved"), False)
        self.assertEqual(scene.get("hgpt_press_lockout_ht"), 166.0)
        self.assertIs(scene.get("hgpt_upperarm_follow"), True)
        body = bpy.data.objects[BODY]
        rig = body.find_armature()
        self.assertEqual(sum(b.use_deform for b in rig.data.bones), 67)
        keys = [kb.name for kb in body.data.shape_keys.key_blocks]
        self.assertEqual(self.report["keys_ht"], [120.0, 145.0, 156.0, 166.0])
        for s in SIDES:
            self.assertEqual(len([k for k in keys if k.startswith(f"HGPT_S7_DELT_{s}_")]), 4, s)
            self.assertEqual(len(rig[f"hgpt_s7_angles_{s}"]), 4)
            self.assertEqual(float(rig["hgpt_s7_angles_start"]), 95.0)
            self.assertEqual(len([k for k in keys if k.startswith(f"HGPT_S5_BAKE_{s}_")]), 6, s)
        recipe = self.report["targets_recipe"]
        self.assertEqual(recipe["lat_web"], "0.35:55:6")                     # R30: lighter back fill (R29 0.6)
        self.assertEqual(recipe["lockout_ht"], 166.0)
        for ht, k in recipe["log"].items():
            self.assertEqual(k["pairs"], 0, ht)
            # 156 deg: 4 crushed triangles left after the clean-up (trapezius by the neck, shoulder cap); recorded, not hidden
            self.assertLessEqual(k["whole_body_collapse"][1], 4, ht)

    def test_upper_arm_follows_the_humerus(self):
        a, b = upperarm_weights(R18), upperarm_weights(R31)
        for s in SIDES:
            gained = [y - x for x, y in zip(a[s], b[s])]
            # upper-arm weight increased, except on the 22 vertices per side at the top of the shoulder where the R18Wg5 stage's
            # 4-influence trim dropped a small upperarm weight (<= 0.032; script fixed after R31 was built, see the R31 doc)
            self.assertLessEqual(sum(g < -1e-3 for g in gained), 22, s)
            self.assertGreaterEqual(min(gained), -0.035, s)
            self.assertGreater(sum(g > 0.05 for g in gained), 400, s)      # 750 vertices changed per side recorded

    def test_press_path_and_benchmarks(self):
        rows = list(zip(self.report["press_path_without_s7"], self.report["press_path_r17"]))
        for a, b in rows:
            if a["ht"] <= 95.0:
                self.assertEqual((a["pairs"], a["collapse"], a["stretch"]), (b["pairs"], b["collapse"], b["stretch"]), a["t"])
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
            if a["ht"] > 95.0:
                self.assertEqual(b["pairs"], 0, a["t"])
        lock_a, lock_b = rows[-1]
        self.assertLess(lock_b["stretch"], 0.2 * lock_a["stretch"])          # 385 -> 47 measured (R29 83)
        self.assertEqual(lock_b["collapse"], 0)
        self.assertLess(abs(lock_b["volume_pct"]), 2.5)                       # +1.58 % (R29 +4.41 %: lighter back)
        v1 = json.loads(R29_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r29_worst"], v2[n]["r31_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"], n)
            self.assertLessEqual(b["stretch_gt_2"], a["stretch_gt_2"] + 12, n)   # push_up +10, shoulder_press +12 recorded


if __name__ == "__main__":
    unittest.main(argv=[__file__])
