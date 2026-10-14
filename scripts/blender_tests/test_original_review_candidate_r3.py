"""Native checks of the ORIGINAL_v1 review candidate R3 (R2 + K1 wrist-extension keys), re-measured from the saved blends."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_knee_contact_corrective_blender as k1  # noqa: E402

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R2 = CAND / "claude_review_r2_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R2_CLAUDE.blend"
R3 = CAND / "claude_review_r3_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R3_CLAUDE.blend"
REPORT = CAND / "claude_review_r3_20261014/r3_wrist_build.json"
VALIDATION = CAND / "claude_review_r3_20261014/r3_validation.json"
R2_VALIDATION = CAND / "claude_review_r2_20261014/r2_validation.json"
WRIST_KEYS = [f"HGPT_K1_WRIST_{s}_{d}" for s in ("l", "r") for d in (60, 80, 100)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
    rig = body.find_armature()
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "weights": [sorted((g.group, round(g.weight, 6)) for g in v.groups) for v in body.data.vertices],
            "deform": sum(b.use_deform for b in rig.data.bones),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR3NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r2 = snapshot(R2)
        cls.r3 = snapshot(R3)

    def test_identity(self):
        self.assertEqual(sha(R2), self.report["parent"]["sha256"])
        self.assertEqual(sha(R3), self.report["output"]["sha256"])
        self.assertFalse(self.report["approved"])
        self.assertIs(self.r3["approved"], False)
        self.assertTrue(self.report["side_sign_matches_palmar"])

    def test_r3_is_r2_plus_six_wrist_keys_only(self):
        self.assertEqual(self.r3["deform"], 67)
        self.assertEqual(self.r3["weights"], self.r2["weights"])
        self.assertLess(max((a - b).length for a, b in zip(self.r2["basis"], self.r3["basis"])), 1e-7)
        self.assertEqual(sorted(set(self.r3["keys"]) - set(self.r2["keys"])), sorted(WRIST_KEYS))
        for name, co in self.r2["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r3["keys"][name])), 1e-7, name)

    def test_wrist_deltas_stay_on_their_own_forearm_and_hand(self):
        basis = self.r3["basis"]
        for d in (60, 80, 100):
            for s, sign in (("l", -1.0), ("r", 1.0)):                      # F-SIDE-001: runtime _r is +X
                key = self.r3["keys"][f"HGPT_K1_WRIST_{s}_{d}"]
                moved = [i for i in range(len(basis)) if (key[i] - basis[i]).length > 1e-7]
                self.assertTrue(moved, (s, d))
                self.assertTrue(all(basis[i].x * sign > 0.15 for i in moved), (s, d))     # wrist region only
                self.assertLessEqual(max((key[i] - basis[i]).length for i in moved), k1.DELTA_CAP_M + 1e-6)

    def test_pure_wrist_sweep_no_worse_folds_or_collisions(self):
        before, after = self.report["sweep_before"], self.report["sweep_after"]
        for a in before:
            x, y = before[a], after[a]
            self.assertLessEqual(y["collapse_lt_0_1"], x["collapse_lt_0_1"], a)
            self.assertLessEqual(y["self_intersecting_pairs"], x["self_intersecting_pairs"], a)
            self.assertLessEqual(y["stretch_gt_2"], x["stretch_gt_2"] + 2, a)     # known cost: +2 stretched faces, recorded
            self.assertLess(abs(y["body_volume_change_pct"] - x["body_volume_change_pct"]), 0.02, a)
        self.assertEqual(after["90"]["self_intersecting_pairs"], 0)
        self.assertGreater(before["90"]["self_intersecting_pairs"], 100)          # the dorsal crease it removes

    def test_benchmarks_unchanged_except_the_push_up_which_improves(self):
        v2 = json.loads(R2_VALIDATION.read_text())["benchmarks"]
        v3 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v2), sorted(v3))
        for n in v2:
            a, b = v2[n]["r2_worst"], v3[n]["r3_worst"]
            if n == "push_up":
                for k in ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs"):
                    self.assertLessEqual(b[k], a[k], k)
                self.assertLess(b["collapse_lt_0_1"], a["collapse_lt_0_1"])
            else:
                self.assertEqual(a, b, n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
