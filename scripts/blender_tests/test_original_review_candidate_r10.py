"""Native checks of the ORIGINAL_v1 review candidate R10 = R9 + S4 sculpt corrective keys for the full-range overhead press
(deltoid, armpit hollow, trapezius, lockout-crease unfolding), solved on the scripts/original_v1_press_extension.py path.
Re-measured from the saved blends.  Review only."""
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
R9 = CAND / "claude_review_r9_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R9_CLAUDE.blend"     # parent
R10 = CAND / "claude_review_r10_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R10_CLAUDE.blend"  # under test
REPORT = CAND / "claude_review_r10_20261014/r10_build.json"
VALIDATION = CAND / "claude_review_r10_20261014/r10_validation.json"
R9_VALIDATION = CAND / "claude_review_r9_20261014/r9_validation.json"
SIDES = ("l", "r")
HTS = (85, 110, 145, 172)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
    rig = body.find_armature()
    names = {g.index: g.name for g in body.vertex_groups}
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "weights": [sorted((names[g.group], round(g.weight, 6)) for g in v.groups) for v in body.data.vertices],
            "deform": sum(b.use_deform for b in rig.data.bones),
            "s4_angles": {s: list(rig.get(f"hgpt_s4_angles_{s}", [])) for s in SIDES},
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR10NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r9 = snapshot(R9)
        cls.r10 = snapshot(R10)

    def test_identity(self):
        self.assertEqual(sha(R9), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R10), self.report["output"]["sha256"])
        self.assertFalse(self.report["approved"])
        self.assertIs(self.r10["approved"], False)

    def test_r10_is_r9_plus_eight_sculpt_keys_only(self):
        self.assertEqual(self.r10["deform"], 67)
        self.assertEqual(self.r10["weights"], self.r9["weights"])
        self.assertLess(max((a - b).length for a, b in zip(self.r9["basis"], self.r10["basis"])), 1e-9)
        new = sorted(set(self.r10["keys"]) - set(self.r9["keys"]))
        self.assertEqual(new, sorted(f"HGPT_S4_SCULPT_{s}_{h}" for s in SIDES for h in HTS))
        for name, co in self.r9["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r10["keys"][name])), 1e-9, name)
        for s in SIDES:
            self.assertEqual([round(x) for x in self.r10["s4_angles"][s]], list(HTS), s)

    def test_sculpt_deltas_are_bounded_and_symmetric(self):
        basis = self.r10["basis"]
        index = {(round(p.x, 5), round(p.y, 5), round(p.z, 5)): i for i, p in enumerate(basis)}
        for h in HTS:
            dl, dr = self.r10["keys"][f"HGPT_S4_SCULPT_l_{h}"], self.r10["keys"][f"HGPT_S4_SCULPT_r_{h}"]
            for s, k in (("l", dl), ("r", dr)):
                moved = [i for i in range(len(basis)) if (k[i] - basis[i]).length > 1e-7]
                self.assertTrue(moved, (h, s))
                self.assertLessEqual(max((k[i] - basis[i]).length for i in moved), 0.04 + 1e-6, (h, s))
                sign = 1.0 if s == "r" else -1.0
                self.assertTrue(all(basis[i].x * sign > 0.03 for i in moved), (h, s))
            worst = 0.0
            for i, p in enumerate(basis):
                if p.x <= 0.03:
                    continue
                j = index.get((round(-p.x, 5), round(p.y, 5), round(p.z, 5)))
                if j is None:
                    continue
                a, b = dr[i] - p, dl[j] - basis[j]
                worst = max(worst, (a - type(a)((-b.x, b.y, b.z))).length)
            self.assertLess(worst, 0.0005, h)

    def test_press_path_overlap_removed(self):
        rows = list(zip(self.report["press_path_r9"], self.report["press_path_r10"]))
        for a, b in rows:
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
        top = [(a, b) for a, b in rows if a["ht"] >= 160]
        self.assertTrue(top)
        self.assertLessEqual(max(b["pairs"] for _, b in top), 20)                      # R9 + full press: up to 95
        self.assertGreater(sum(a["pairs"] for a, _ in top), 3 * sum(b["pairs"] for _, b in top))
        self.assertLess(rows[-1][1]["stretch"], rows[-1][0]["stretch"])                # lockout 182 -> 158
        # KNOWN COST, recorded: more volume loss at the top (the armpit hollow pulls skin in)
        self.assertGreater(rows[-1][1]["volume_pct"], -2.0)

    def test_live_drive_reproduces_the_lockout_row(self):
        import build_original_movement_benchmarks_blender as bench
        import original_v1_press_extension as px
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R10))
        import build_functional_shoulder_correction_blender as correction
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        drives.setup(res)
        px.install()
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        bench._reset(rig)
        V0, F = bench._evaluated(body)
        dom = bench.dominant_groups(body)
        px.pose_press_full(res, 1.0)
        drives.drive(rig, body)
        keys = body.data.shape_keys.key_blocks
        for s in SIDES:
            self.assertAlmostEqual(keys[f"HGPT_S4_SCULPT_{s}_172"].value, 1.0, places=2)
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
        row = self.report["press_path_r10"][-1]
        self.assertEqual((m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"]),
                         (row["collapse"], row["stretch"], row["pairs"]))

    def test_benchmarks_versus_r9(self):
        v1 = json.loads(R9_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r9_worst"], v2[n]["r10_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"] + 2, n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 2, n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
