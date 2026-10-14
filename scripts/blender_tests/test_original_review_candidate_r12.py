"""Native checks of the ORIGINAL_v1 review candidate R12 = R11 + S5 baked delta-mush shapes (HGPT_S5_BAKE_ keys at
85/110/130/145/160/172 deg of the full press, smooth collision guard).  Re-measured from the saved blends.  Review only."""
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
R11 = CAND / "claude_review_r11_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R11_CLAUDE.blend"
R12 = CAND / "claude_review_r12_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R12_CLAUDE.blend"
REPORT = CAND / "claude_review_r12_20261014/r12_build.json"
VALIDATION = CAND / "claude_review_r12_20261014/r12_validation.json"
R11_VALIDATION = CAND / "claude_review_r11_20261014/r11_validation.json"
SIDES = ("l", "r")
HTS = (85, 110, 130, 145, 160, 172)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    import original_v1_review_candidate_drives  # noqa: F401
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    rig = body.find_armature()
    names = {g.index: g.name for g in body.vertex_groups}
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "weights": [sorted((names[g.group], round(g.weight, 6)) for g in v.groups) for v in body.data.vertices],
            "modifiers": [(m.name, m.type) for m in body.modifiers],
            "deform": sum(b.use_deform for b in rig.data.bones),
            "s5_angles": {s: list(rig.get(f"hgpt_s5_angles_{s}", [])) for s in SIDES},
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR12NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r11 = snapshot(R11)
        cls.r12 = snapshot(R12)

    def test_identity(self):
        self.assertEqual(sha(R11), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R12), self.report["output"]["sha256"])
        self.assertIs(self.r12["approved"], False)

    def test_r12_is_r11_plus_twelve_baked_keys_and_no_new_deformer(self):
        self.assertEqual(self.r12["deform"], 67)
        self.assertEqual(self.r12["modifiers"], self.r11["modifiers"])          # the delta mush is baked, not shipped
        self.assertEqual(self.r12["weights"], self.r11["weights"])
        self.assertLess(max((a - b).length for a, b in zip(self.r11["basis"], self.r12["basis"])), 1e-9)
        new = sorted(set(self.r12["keys"]) - set(self.r11["keys"]))
        self.assertEqual(new, sorted(f"HGPT_S5_BAKE_{s}_{h}" for s in SIDES for h in HTS))
        for name, co in self.r11["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r12["keys"][name])), 1e-9, name)
        for s in SIDES:
            self.assertEqual([round(x) for x in self.r12["s5_angles"][s]], list(HTS), s)

    def test_baked_deltas_bounded_and_symmetric(self):
        basis = self.r12["basis"]
        index = {(round(p.x, 5), round(p.y, 5), round(p.z, 5)): i for i, p in enumerate(basis)}
        for h in HTS:
            dl, dr = self.r12["keys"][f"HGPT_S5_BAKE_l_{h}"], self.r12["keys"][f"HGPT_S5_BAKE_r_{h}"]
            for s, k in (("l", dl), ("r", dr)):
                moved = [i for i in range(len(basis)) if (k[i] - basis[i]).length > 1e-7]
                self.assertTrue(moved, (h, s))
                self.assertLessEqual(max((k[i] - basis[i]).length for i in moved), 0.05 + 1e-6, (h, s))
                sign = 1.0 if s == "r" else -1.0
                self.assertTrue(all(basis[i].x * sign >= 0.0 for i in moved), (h, s))
            worst = 0.0
            for i, p in enumerate(basis):
                if p.x <= 0.03:
                    continue
                j = index.get((round(-p.x, 5), round(p.y, 5), round(p.z, 5)))
                if j is None:
                    continue
                a, b = dr[i] - p, dl[j] - basis[j]
                worst = max(worst, (a - type(a)((-b.x, b.y, b.z))).length)
            self.assertLess(worst, 0.001, h)

    def test_press_path_no_new_overlap_less_stretch(self):
        rows = list(zip(self.report["press_path_r11"], self.report["press_path_r12"]))
        for a, b in rows:
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
        top = [(a, b) for a, b in rows if a["ht"] >= 120]
        self.assertLess(sum(b["stretch"] for _, b in top), 0.7 * sum(a["stretch"] for a, _ in top))
        # KNOWN COST, recorded: more body volume at the start (contracted deltoid) and slightly more loss at lockout
        self.assertLess(rows[0][1]["volume_pct"], 1.2)
        self.assertGreater(rows[-1][1]["volume_pct"], -2.2)

    def test_live_drive_reproduces_the_lockout_row(self):
        import build_original_movement_benchmarks_blender as bench
        import original_v1_press_extension as px
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R12))
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
        for s in SIDES:
            self.assertAlmostEqual(body.data.shape_keys.key_blocks[f"HGPT_S5_BAKE_{s}_172"].value, 1.0, places=2)
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
        row = self.report["press_path_r12"][-1]
        self.assertEqual((m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"]),
                         (row["collapse"], row["stretch"], row["pairs"]))

    def test_benchmarks_versus_r11(self):
        v1 = json.loads(R11_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r11_worst"], v2[n]["r12_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 4, n)   # press 0 -> 4, recorded
        self.assertLess(v2["shoulder_press"]["r12_worst"]["stretch_gt_2"], v1["shoulder_press"]["r11_worst"]["stretch_gt_2"])


if __name__ == "__main__":
    unittest.main(argv=[__file__])
