"""Native checks of the ORIGINAL_v1 review candidate R13 = R12 + the hip-crease helper joint (chain weights, hip_crease_l/r
vertex groups) and H1 baked delta-mush hip keys (HGPT_H1_BAKE_ at 45/70/90/110/135 deg hip flexion, smooth guard on the hip
benchmark paths).  Re-measured from the saved blends.  Review only."""
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
R12 = CAND / "claude_review_r12_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R12_CLAUDE.blend"
R13 = CAND / "claude_review_r13_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R13_CLAUDE.blend"
REPORT = CAND / "claude_review_r13_20261015/r13_build.json"
VALIDATION = CAND / "claude_review_r13_20261015/r13_validation.json"
R12_VALIDATION = CAND / "claude_review_r12_20261014/r12_validation.json"
SIDES = ("l", "r")
DEGS = (45, 70, 90, 110, 135)
HIP_REGION_M = 0.20


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    import original_v1_review_candidate_drives  # noqa: F401
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    rig = body.find_armature()
    names = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform} | {f"hip_crease_{s}" for s in SIDES}
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "weights": [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in body.data.vertices],
            "deform_groups": deform,
            "modifiers": [(m.name, m.type) for m in body.modifiers],
            "deform": sum(b.use_deform for b in rig.data.bones),
            "hips": {s: rig.data.bones[f"thigh_{s}"].head_local.copy() for s in SIDES},
            "h1_angles": {s: list(rig.get(f"hgpt_h1_angles_{s}", [])) for s in SIDES},
            "hip_fraction": rig.get("hgpt_hip_fraction"),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR13NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r12 = snapshot(R12)
        cls.r13 = snapshot(R13)

    def test_identity(self):
        self.assertEqual(sha(R12), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R13), self.report["output"]["sha256"])
        self.assertIs(self.r13["approved"], False)

    def test_r13_is_r12_plus_hip_weights_and_ten_baked_keys(self):
        self.assertEqual(self.r13["deform"], 67)                                     # helper bones live in memory only
        self.assertEqual(self.r13["modifiers"], self.r12["modifiers"])               # the delta mush is baked, not shipped
        self.assertAlmostEqual(self.r13["hip_fraction"], 0.45)
        self.assertLess(max((a - b).length for a, b in zip(self.r12["basis"], self.r13["basis"])), 1e-9)
        new = sorted(set(self.r13["keys"]) - set(self.r12["keys"]))
        self.assertEqual(new, sorted(f"HGPT_H1_BAKE_{s}_{d}" for s in SIDES for d in DEGS))
        for name, co in self.r12["keys"].items():
            self.assertLess(max((a - b).length for a, b in zip(co, self.r13["keys"][name])), 1e-9, name)
        for s in SIDES:
            self.assertEqual([round(x) for x in self.r13["h1_angles"][s]], list(DEGS), s)

    def test_weights_change_only_around_the_hips_thigh_never_gains(self):
        changed = 0
        for i, (a, b) in enumerate(zip(self.r12["weights"], self.r13["weights"])):
            if all(abs(a.get(k, 0.0) - b.get(k, 0.0)) < 1e-6 for k in set(a) | set(b)):
                continue
            changed += 1
            p = self.r13["basis"][i]
            self.assertLess(min((p - h).length for h in self.r13["hips"].values()), HIP_REGION_M + 1e-6, i)
            for s in SIDES:
                self.assertLessEqual(b.get(f"thigh_{s}", 0.0), a.get(f"thigh_{s}", 0.0) + 1e-6, i)
            dw = {k: x for k, x in b.items() if k in self.r13["deform_groups"]}
            self.assertLessEqual(len(dw), 4, i)
            self.assertAlmostEqual(sum(dw.values()), 1.0, places=4, msg=i)
        self.assertGreater(changed, 1000)
        for s in SIDES:
            self.assertTrue(any(f"hip_crease_{s}" in w for w in self.r13["weights"]), s)

    def test_baked_deltas_bounded_side_correct_and_symmetric(self):
        basis = self.r13["basis"]
        index = {(round(p.x, 5), round(p.y, 5), round(p.z, 5)): i for i, p in enumerate(basis)}
        for d in DEGS:
            dl, dr = self.r13["keys"][f"HGPT_H1_BAKE_l_{d}"], self.r13["keys"][f"HGPT_H1_BAKE_r_{d}"]
            for s, k in (("l", dl), ("r", dr)):
                moved = [i for i in range(len(basis)) if (k[i] - basis[i]).length > 1e-7]
                self.assertTrue(moved, (d, s))
                self.assertLessEqual(max((k[i] - basis[i]).length for i in moved), 0.05 + 1e-6, (d, s))
                sign = 1.0 if s == "r" else -1.0
                self.assertTrue(all(basis[i].x * sign >= -1e-4 for i in moved), (d, s))
            worst = 0.0
            for i, p in enumerate(basis):
                if p.x <= 0.0:
                    continue
                j = index.get((round(-p.x, 5), round(p.y, 5), round(p.z, 5)))
                if j is None:
                    continue
                a, b = dr[i] - p, dl[j] - basis[j]
                worst = max(worst, (a - type(a)((-b.x, b.y, b.z))).length)
            self.assertLess(worst, 0.001, d)

    def test_live_drive_hip_flexion_and_key_values(self):
        import build_original_movement_benchmarks_blender as bench
        import original_v1_hip_crease_helper as hip
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R13))
        import build_functional_shoulder_correction_blender as correction
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        drives.setup(res)
        self.assertIn("hip_crease_l", rig.data.bones)
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        bench._reset(rig)
        heads = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in SIDES}
        keys = body.data.shape_keys.key_blocks
        bench.pose_squat(rig, 1.0, heads)
        drives.drive(rig, body)
        for s in SIDES:
            self.assertAlmostEqual(hip.hip_flexion_deg(rig, s), 110.0, places=0)
            self.assertAlmostEqual(keys[f"HGPT_H1_BAKE_{s}_110"].value, 1.0, places=2)
            self.assertEqual(keys[f"HGPT_H1_BAKE_{s}_135"].value, 0.0)
            q = rig.pose.bones[f"hip_crease_{s}"].rotation_quaternion
            self.assertGreater(q.angle, 0.3)
        bench._reset(rig)
        bench.pose_walk(rig, body, 0.5)                     # right hip in extension (-10 deg): no H1 key on that side
        drives.drive(rig, body)
        self.assertLess(hip.hip_flexion_deg(rig, "r"), 0.0)
        self.assertTrue(all(keys[f"HGPT_H1_BAKE_r_{d}"].value == 0.0 for d in DEGS))

    def test_benchmarks_versus_r12(self):
        v1 = json.loads(R12_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        a = {n: v1[n]["r12_worst"] for n in v1}
        b = {n: v2[n]["r13_worst"] for n in v2}
        for n in ("squat", "deadlift"):
            self.assertLess(b[n]["self_intersecting_pairs"], a[n]["self_intersecting_pairs"], n)
            self.assertLess(b[n]["collapse_lt_0_1"], a[n]["collapse_lt_0_1"], n)
        for n in v1:
            if n in ("squat", "deadlift"):
                continue
            self.assertLessEqual(b[n]["self_intersecting_pairs"], a[n]["self_intersecting_pairs"], n)
            self.assertLessEqual(b[n]["collapse_lt_0_1"], a[n]["collapse_lt_0_1"], n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
