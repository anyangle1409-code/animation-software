"""Native checks of the ORIGINAL_v1 review candidate R9 = R8 + S3 mid-range shape keys (the skin above the shoulder pivot
pulled back to R5's posed surface at 45/75/100 deg, faded out by 125 deg).  Re-measured from the saved blends.  Review only."""
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
R5 = CAND / "claude_review_r5_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R5_CLAUDE.blend"   # shape reference
R8 = CAND / "claude_review_r8_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R8_CLAUDE.blend"   # parent
R9 = CAND / "claude_review_r9_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R9_CLAUDE.blend"   # under test
REPORT = CAND / "claude_review_r9_20261014/r9_build.json"
VALIDATION = CAND / "claude_review_r9_20261014/r9_validation.json"
R8_VALIDATION = CAND / "claude_review_r8_20261014/r8_validation.json"
SIDES = ("l", "r")
HTS = (45, 75, 100)


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
            "s3_angles": {s: list(rig.get(f"hgpt_s3_angles_{s}", [])) for s in SIDES},
            "pivot": {s: rig.data.bones[f"upperarm_{s}"].head_local.copy() for s in SIDES},
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR9NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r8 = snapshot(R8)
        cls.r9 = snapshot(R9)

    def test_identity(self):
        self.assertEqual(sha(R8), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R9), self.report["output"]["sha256"])
        self.assertEqual(sha(R5), self.report["reference"]["sha256"])
        self.assertFalse(self.report["approved"])
        self.assertIs(self.r9["approved"], False)

    def test_r9_is_r8_plus_eight_shape_keys_only(self):
        self.assertEqual(self.r9["deform"], 67)
        self.assertEqual(self.r9["weights"], self.r8["weights"])
        self.assertLess(max((a - b).length for a, b in zip(self.r8["basis"], self.r9["basis"])), 1e-9)
        new = sorted(set(self.r9["keys"]) - set(self.r8["keys"]))
        self.assertEqual(new, sorted(f"HGPT_S3_SHAPE_{s}_{h}" for s in SIDES for h in HTS + (125,)))
        for name, co in self.r8["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r9["keys"][name])), 1e-9, name)
        for s in SIDES:
            self.assertEqual(len(self.r9["s3_angles"][s]), 4, s)
            closing = self.r9["keys"][f"HGPT_S3_SHAPE_{s}_125"]
            self.assertLess(max((a - b).length for a, b in zip(closing, self.r9["basis"])), 1e-9, s)

    def test_shape_deltas_are_local_bounded_and_symmetric(self):
        basis = self.r9["basis"]
        for h in HTS:
            for s in SIDES:
                k = self.r9["keys"][f"HGPT_S3_SHAPE_{s}_{h}"]
                moved = {i: k[i] - basis[i] for i in range(len(basis)) if (k[i] - basis[i]).length > 1e-7}
                self.assertTrue(moved, (h, s))
                self.assertLessEqual(max(v.length for v in moved.values()), 0.04 + 1e-6, (h, s))
                sign = 1.0 if s == "r" else -1.0
                self.assertTrue(all(basis[i].x * sign > 0.03 for i in moved), (h, s))
                self.assertLess(max((basis[i] - self.r9["pivot"][s]).length for i in moved), 0.35, (h, s))
            dl, dr = self.r9["keys"][f"HGPT_S3_SHAPE_l_{h}"], self.r9["keys"][f"HGPT_S3_SHAPE_r_{h}"]
            index = {(round(p.x, 5), round(p.y, 5), round(p.z, 5)): i for i, p in enumerate(basis)}
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

    def test_sweep_mid_range_volume_back_near_r5_and_high_range_unchanged(self):
        rows = {a["ht"]: (a, b) for a, b in zip(self.report["sweep_r8"], self.report["sweep_r9"])}
        for ht, (a, b) in rows.items():
            self.assertLessEqual(b["pairs"], a["pairs"], ht)
            if ht >= 125:                                        # keys faded out: exactly R8
                self.assertEqual((a["collapse"], a["stretch"], a["pairs"]), (b["collapse"], b["stretch"], b["pairs"]), ht)
        for ht in (60, 70, 80, 90):
            self.assertLess(rows[ht][1]["volume_pct"], 0.6, ht)              # R8 +1.3..+1.5 ("shoulder pad")
            self.assertLess(rows[ht][1]["volume_pct"], rows[ht][0]["volume_pct"] - 0.7, ht)
        # KNOWN COST, recorded: 2 collapsed faces at 80 deg (R8: 0)
        self.assertLessEqual(rows[80][1]["collapse"], 2)

    def test_live_drive_fades_the_shape_keys(self):
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R9))
        import build_functional_shoulder_correction_blender as correction
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        keys = body.data.shape_keys.key_blocks
        drives.setup(res)
        for ht, on in ((75, 75), (160, None)):
            correction.apply_corrected_pose(res, ht)
            drives.drive(rig, body)
            for s in SIDES:
                for h in HTS:
                    v = keys[f"HGPT_S3_SHAPE_{s}_{h}"].value
                    if on == h:
                        self.assertAlmostEqual(v, 1.0, places=2)
                    elif on is None:
                        self.assertEqual(v, 0.0, (ht, s, h))

    def test_benchmarks_versus_r8(self):
        v1 = json.loads(R8_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r8_worst"], v2[n]["r9_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 2, n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
