"""Native checks of the ORIGINAL_v1 review candidate R7 = R6 + top-of-shoulder fold keys (HGPT_S2_FOLD_, S1 method in
"smooth" mode on the measured fold zone, 125-140 deg with an empty closing key at 145), re-measured from the saved blends."""
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
R1 = CAND / "claude_review_r6_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R6_CLAUDE.blend"   # parent (R6)
R2 = CAND / "claude_review_r7_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R7_CLAUDE.blend"   # under test (R7)
REPORT = CAND / "claude_review_r7_20261014/r7_s2_build.json"
VALIDATION = CAND / "claude_review_r7_20261014/r7_validation.json"
R1_VALIDATION = CAND / "claude_review_r6_20261014/r6_validation.json"
HTS = (125, 130, 135, 140)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
    rig = body.find_armature()
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "groups": sorted(g.name for g in body.vertex_groups),
            "weights": [sorted((g.group, round(g.weight, 6)) for g in v.groups) for v in body.data.vertices],
            "deform": sum(b.use_deform for b in rig.data.bones),
            "s1_angles": {s: list(rig.get(f"hgpt_s1_angles_{s}", [])) for s in ("l", "r")},
            "s2_angles": {s: list(rig.get(f"hgpt_s2_angles_{s}", [])) for s in ("l", "r")},
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR7NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r1 = snapshot(R1)
        cls.r2 = snapshot(R2)

    def test_identity(self):
        self.assertEqual(sha(R1), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R2), self.report["output"]["sha256"])
        self.assertFalse(self.report["approved"])
        self.assertIs(self.r2["approved"], False)

    def test_r7_is_r6_plus_ten_fold_keys_only(self):
        self.assertEqual(self.r2["deform"], 67)
        self.assertEqual(self.r2["groups"], self.r1["groups"])
        self.assertEqual(self.r2["weights"], self.r1["weights"])
        self.assertLess(max((a - b).length for a, b in zip(self.r1["basis"], self.r2["basis"])), 1e-7)
        new = sorted(set(self.r2["keys"]) - set(self.r1["keys"]))
        self.assertEqual(new, sorted(f"HGPT_S2_FOLD_{s}_{h}" for s in ("l", "r") for h in HTS + (145,)))
        for name, co in self.r1["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r2["keys"][name])), 1e-7, name)
        for s in ("l", "r"):
            self.assertEqual(self.r2["s1_angles"][s], self.r1["s1_angles"][s], s)
            self.assertEqual(len(self.r2["s2_angles"][s]), 5, s)
            basis = self.r2["basis"]
            closing = self.r2["keys"][f"HGPT_S2_FOLD_{s}_145"]               # empty closing key: fold keys fade out by 145
            self.assertLess(max((a - b).length for a, b in zip(closing, basis)), 1e-9, s)

    def test_fold_deltas_are_bounded_and_symmetric(self):
        basis = self.r2["basis"]
        for h in HTS:
            dl = self.r2["keys"][f"HGPT_S2_FOLD_l_{h}"]
            dr = self.r2["keys"][f"HGPT_S2_FOLD_r_{h}"]
            moved_l = {i: dl[i] - basis[i] for i in range(len(basis)) if (dl[i] - basis[i]).length > 1e-7}
            moved_r = {i: dr[i] - basis[i] for i in range(len(basis)) if (dr[i] - basis[i]).length > 1e-7}
            self.assertTrue(moved_l and moved_r, h)
            self.assertLessEqual(max(v.length for v in moved_l.values()), 0.030 + 0.009, h)
            self.assertTrue(all(basis[i].x < 0 for i in moved_l) and all(basis[i].x > 0 for i in moved_r), h)
            index = {(round(-basis[i].x, 5), round(basis[i].y, 5), round(basis[i].z, 5)): i for i in moved_r}
            worst = 0.0
            for i, dl_i in moved_l.items():
                j = index.get((round(basis[i].x, 5), round(basis[i].y, 5), round(basis[i].z, 5)))
                if j is None:
                    continue
                dr_j = moved_r[j]
                worst = max(worst, (dl_i - type(dl_i)((-dr_j.x, dr_j.y, dr_j.z))).length)
            self.assertLess(worst, 0.0005, h)

    def test_coupled_sweep_fold_improves_with_recorded_costs(self):
        rows = {a["ht"]: (a, b) for a, b in zip(self.report["sweep_r1"], self.report["sweep_r1_s1"])}
        for ht, (a, b) in rows.items():
            self.assertLessEqual(b["pairs"], a["pairs"], ht)                        # never more overlapping skin
            self.assertLess(abs(b["volume_pct"] - a["volume_pct"]), 0.05, ht)
            if ht <= 100 or ht >= 150:                                             # outside the keyed range: unchanged
                self.assertLessEqual(b["collapse"], a["collapse"], ht)
                self.assertLessEqual(b["stretch"], a["stretch"] + 2, ht)
        self.assertEqual(rows[120][1]["pairs"], 0)                                 # was 10
        self.assertLessEqual(rows[130][1]["pairs"], rows[130][0]["pairs"] // 3)    # 84 -> 22: the targeted fold
        self.assertLess(rows[110][1]["collapse"], rows[110][0]["collapse"])        # 6 -> 2
        # KNOWN COSTS, recorded so they stay visible: +2 collapsed faces at 130, up to +8 faces > 2x at 120-140, and the
        # 140-160 deg fold (98-216 pairs) is NOT reduced by these keys
        self.assertLessEqual(rows[130][1]["collapse"], rows[130][0]["collapse"] + 2)
        for ht in (120, 130, 140):
            self.assertLessEqual(rows[ht][1]["stretch"], rows[ht][0]["stretch"] + 8, ht)
        self.assertEqual(rows[160][1]["pairs"], rows[160][0]["pairs"])

    def test_live_drive_reproduces_the_160_degree_row(self):
        import build_original_movement_benchmarks_blender as bench
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R2))
        import build_functional_shoulder_correction_blender as correction
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        keys = body.data.shape_keys.key_blocks
        drives.setup(res)
        bench._reset(rig)
        for kb in keys[1:]:
            kb.value = 0.0
        V0, F = bench._evaluated(body)
        dom = bench.dominant_groups(body)
        drives.drive(rig, body)                                              # rest: every S1 key off
        self.assertTrue(all(kb.value == 0.0 for kb in keys if kb.name.startswith(("HGPT_S1_", "HGPT_S2_"))))
        correction.apply_corrected_pose(res, 130)
        drives.drive(rig, body)
        for s in ("l", "r"):
            self.assertAlmostEqual(keys[f"HGPT_S2_FOLD_{s}_130"].value, 1.0, places=3)
            self.assertAlmostEqual(keys[f"HGPT_S2_FOLD_{s}_125"].value, 0.0, places=3)
        correction.apply_corrected_pose(res, 160)
        drives.drive(rig, body)
        for s in ("l", "r"):
            self.assertAlmostEqual(keys[f"HGPT_S1_SHOULDER_{s}_160"].value, 1.0, places=3)
            self.assertTrue(all(keys[f"HGPT_S2_FOLD_{s}_{h}"].value == 0.0 for h in HTS), s)   # faded out by 145
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
        row = self.report["sweep_r1_s1"][-1]
        self.assertEqual(row["ht"], 160)
        self.assertEqual((m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"]),
                         (row["collapse"], row["stretch"], row["pairs"]))

    def test_benchmarks_unchanged_except_the_press(self):
        v1 = json.loads(R1_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r6_worst"], v2[n]["r7_worst"]
            if n == "shoulder_press":       # worst frame is the top (160 deg), outside the fold keys: pairs/collapse equal
                self.assertEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"])
                self.assertEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"])
                self.assertLessEqual(b["stretch_gt_2"], a["stretch_gt_2"] + 2)     # recorded cost (62 -> 64)
            else:
                self.assertEqual(a, b, n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
