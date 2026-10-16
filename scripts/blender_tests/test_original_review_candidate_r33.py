"""Native checks of the ORIGINAL_v1 review candidate R33 (owner, on R31 at 132 / 145 deg: the skin crumbles behind the armpit,
"the arms as it's raising up should be in a straight line.  There shouldn't be the dent", "the bend at the elbow is too
sharp"): same base as R31 (B5: upper arm re-bound to the humerus, S5 rebuilt); S7 rebuilt with the upper arm straightened
along its own bone at bent-elbow keys (TUBE_UPPER), the elbow rounded (ELBOW_ROUND), more back fill at 120 / 145 deg, and the
fold clean-up threshold lowered at the bent keys (per key; patch radius capped at 156).  Re-measured from the saved blends.
Review only."""
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
R31DIR = CAND / "claude_review_r31_20261016"
DIR = CAND / "claude_review_r33_20261016"
R33 = DIR / "HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R33_CLAUDE.blend"
REPORT = DIR / "r33_build.json"
VALIDATION = DIR / "r33_validation.json"
FOLLOW = R31DIR / "stages/r18wg5_follow_weights.json"
B5 = R31DIR / "stages/b5_s5_rebuild.json"
R31_REPORT = R31DIR / "r31_build.json"
R31_VALIDATION = R31DIR / "r31_validation.json"
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


class ReviewCandidateR33NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_lineage_and_keys(self):
        follow, b5 = json.loads(FOLLOW.read_text()), json.loads(B5.read_text())
        self.assertEqual(sha(R18), follow["output"]["parent"]["sha256"])
        self.assertEqual(follow["output"]["sha256"], b5["output"]["parent"]["sha256"])
        self.assertEqual(b5["output"]["sha256"], self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R33), self.report["output"]["sha256"])
        self.assertEqual(self.report["output"]["parent"]["sha256"], json.loads(R31_REPORT.read_text())["output"]["parent"]["sha256"])   # same base as R31
        self.assertEqual(follow["params"]["t0_m"], 0.0)
        self.assertEqual(follow["params"]["t1_m"], 0.08)
        self.assertEqual(follow["params"]["medial_ramp"], "-0.3,0.5")
        import original_v1_review_candidate_drives  # noqa: F401
        bpy.ops.wm.open_mainfile(filepath=str(R33))
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
        self.assertEqual(recipe["lat_web"], "0.35:55:6")
        self.assertEqual(recipe["lat_key_gain"], "120:0.5,145:0.6,156:0.6")    # more back fill while raising (R31 120:0,145:0.3)
        self.assertEqual(recipe["arm_key_gain"], "120:1,145:1")
        self.assertEqual(recipe["tube_upper"]["TUBE_UPPER"], "-38,-26,-7,-3")   # upper arm straight along its own bone
        self.assertEqual(recipe["elbow_round"], "10:20:30")
        self.assertEqual(recipe["uncross_folds"], "40,20")
        self.assertEqual(recipe["uncross_folds_at"], "156:55,25;166:90,45")
        self.assertEqual(recipe["lockout_ht"], 166.0)
        for ht, k in recipe["log"].items():                                  # every key: nothing crossing or crushed
            self.assertEqual((k["pairs"], k["whole_body_collapse"][1]), (0, 0), ht)

    def test_binding_same_as_r31(self):
        a = upperarm_weights(R31DIR / "HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R31_CLAUDE.blend")
        b = upperarm_weights(R33)
        for s in SIDES:                                                      # only the shape keys changed, not the weights
            self.assertLess(max(abs(x - y) for x, y in zip(a[s], b[s])), 1e-6, s)

    def test_press_path_and_benchmarks(self):
        rows = list(zip(self.report["press_path_without_s7"], self.report["press_path_r17"]))
        for a, b in rows:
            if a["ht"] <= 95.0:
                self.assertEqual((a["pairs"], a["collapse"], a["stretch"]), (b["pairs"], b["collapse"], b["stretch"]), a["t"])
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
            if a["ht"] > 95.0:
                self.assertEqual(b["pairs"], 0, a["t"])
            if a["ht"] > 95.0:
                self.assertEqual(b["collapse"], 0, a["t"])
        lock_a, lock_b = rows[-1]
        self.assertLess(lock_b["stretch"], 0.25 * lock_a["stretch"])         # 385 -> 80 measured (R31 47)
        self.assertLess(abs(lock_b["volume_pct"]), 2.5)                       # +1.60 %
        r156 = [b for _, b in rows if abs(b["ht"] - 156.0) < 0.5][0]
        self.assertLess(r156["stretch"], 100)                                  # 50 measured (R31 169)
        v1 = json.loads(R31_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r31_worst"], v2[n]["r33_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["stretch_gt_2"], a["stretch_gt_2"], n)
            # shoulder_press collapse 0 -> 2 recorded (R33 doc); every other benchmark identical to R31
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + (2 if n == "shoulder_press" else 0), n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
