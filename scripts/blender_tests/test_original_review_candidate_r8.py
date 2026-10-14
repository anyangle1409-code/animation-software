"""Native checks of the ORIGINAL_v1 review candidate R8 = R5 + shoulder-cap helper joint (girdle -> shoulder_cap_<s> ->
upper arm chain weights, bones recreated in memory) + S1 stretch-zone relax keys re-solved on that base.  Re-measured from
the saved blends.  Review only."""
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R5 = CAND / "claude_review_r5_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R5_CLAUDE.blend"   # parent
R8 = CAND / "claude_review_r8_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R8_CLAUDE.blend"   # under test
REPORT = CAND / "claude_review_r8_20261014/r8_build.json"
VALIDATION = CAND / "claude_review_r8_20261014/r8_validation.json"
R5_VALIDATION = CAND / "claude_review_r5_20261014/r5_validation.json"
SIDES = ("l", "r")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
    rig = body.find_armature()
    names = {g.index: g.name for g in body.vertex_groups}
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "keys": {kb.name: [d.co.copy() for d in kb.data] for kb in body.data.shape_keys.key_blocks[1:]},
            "groups": sorted(g.name for g in body.vertex_groups),
            "weights": [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in body.data.vertices],
            "bones": {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones},
            "deform": sum(b.use_deform for b in rig.data.bones),
            "cap_fraction": rig.get("hgpt_cap_fraction"),
            "drive": bpy.context.scene.get("hgpt_shoulder_drive"),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR8NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.r5 = snapshot(R5)
        cls.r8 = snapshot(R8)

    def test_identity_and_flags(self):
        self.assertEqual(sha(R5), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R8), self.report["output"]["sha256"])
        self.assertFalse(self.report["approved"])
        self.assertIs(self.r8["approved"], False)
        self.assertEqual(self.r8["drive"], "R5")                       # same anatomical shoulder drive as R5

    def test_file_stays_67_bones_with_cap_weights_and_s1_keys_only(self):
        self.assertEqual(self.r8["deform"], 67)                        # helper bones are not saved
        self.assertEqual(self.r8["bones"].keys(), self.r5["bones"].keys())
        for n, (h, t) in self.r5["bones"].items():
            self.assertLess((h - self.r8["bones"][n][0]).length + (t - self.r8["bones"][n][1]).length, 1e-9, n)
        self.assertEqual(sorted(set(self.r8["groups"]) - set(self.r5["groups"])), ["shoulder_cap_l", "shoulder_cap_r"])
        self.assertAlmostEqual(self.r8["cap_fraction"], 0.45)
        self.assertLess(max((a - b).length for a, b in zip(self.r5["basis"], self.r8["basis"])), 1e-9)
        new = sorted(set(self.r8["keys"]) - set(self.r5["keys"]))
        self.assertEqual(new, sorted(f"HGPT_S1_SHOULDER_{s}_{h}" for s in SIDES for h in (105, 120, 145, 160)))
        for name, co in self.r5["keys"].items():                       # K1 / C1 keys unchanged
            self.assertLess(max((a - b).length for a, b in zip(co, self.r8["keys"][name])), 1e-9, name)

    def test_weights_change_only_around_the_shoulders_and_stay_normalised(self):
        changed = []
        for i, (a, b) in enumerate(zip(self.r5["weights"], self.r8["weights"])):
            self.assertLessEqual(len(b), 4, i)
            self.assertAlmostEqual(sum(b.values()), 1.0, delta=1e-3)
            if set(a) != set(b) or any(abs(a[k] - b[k]) > 1e-5 for k in a):
                changed.append(i)
        self.assertTrue(changed)
        for i in changed:                                              # within the fade radius of either GH pivot
            p = self.r5["basis"][i]
            d = min((p - self.r5["bones"][f"upperarm_{s}"][0]).length for s in SIDES)
            self.assertLess(d, 0.18 + 1e-6, i)
        # mirror: the two cap groups carry the same weights on mirrored vertices
        index = {(round(p.x, 5), round(p.y, 5), round(p.z, 5)): i for i, p in enumerate(self.r8["basis"])}
        worst = 0.0
        for i, w in enumerate(self.r8["weights"]):
            if "shoulder_cap_r" in w:
                p = self.r8["basis"][i]
                j = index.get((round(-p.x, 5), round(p.y, 5), round(p.z, 5)))
                if j is not None:
                    worst = max(worst, abs(w["shoulder_cap_r"] - self.r8["weights"][j].get("shoulder_cap_l", 0.0)))
        self.assertLess(worst, 1e-4)

    def test_live_drive_installs_and_turns_the_cap_with_the_arm(self):
        import build_original_movement_benchmarks_blender as bench
        import original_v1_review_candidate_drives as drives
        bpy.ops.wm.open_mainfile(filepath=str(R8))
        import build_functional_shoulder_correction_blender as correction
        res = correction.build_corrected_scene()
        rig, body = res["runtime"], res["body"]
        drives.setup(res)
        self.assertEqual(sum(b.use_deform for b in rig.data.bones), 69)   # 67 + 2 in memory
        for kb in body.data.shape_keys.key_blocks[1:]:
            kb.value = 0.0
        bench._reset(rig)
        V0, F = bench._evaluated(body)
        dom = bench.dominant_groups(body)
        correction.apply_corrected_pose(res, 160)
        drives.drive(rig, body)
        for s in SIDES:
            arm = drives._rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
            capq = drives._rel_quat(rig, f"shoulder_cap_{s}", f"scapula_{s}")
            a = math.degrees(min(arm.angle, 2 * math.pi - arm.angle))
            c = math.degrees(min(capq.angle, 2 * math.pi - capq.angle))
            self.assertAlmostEqual(c, 0.45 * a, delta=0.5, msg=s)
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
        row = self.report["sweep_r8"][-1]
        self.assertEqual(row["ht"], 160)
        self.assertEqual((m["collapse_lt_0_1"], m["stretch_gt_2"], m["self_intersecting_pairs"]),
                         (row["collapse"], row["stretch"], row["pairs"]))

    def test_coupled_sweep_removes_the_fold_with_recorded_costs(self):
        rows = {a["ht"]: (a, b) for a, b in zip(self.report["sweep_r5"], self.report["sweep_r8"])}
        for ht, (a, b) in rows.items():
            self.assertLessEqual(b["pairs"], a["pairs"], ht)
            self.assertLessEqual(b["collapse"], a["collapse"], ht)
        for ht in (120, 130, 140, 150, 160):
            self.assertEqual(rows[ht][1]["pairs"], 0, ht)                  # R5: 10 / 84 / 98 / 156 / 216
            self.assertLessEqual(rows[ht][1]["collapse"], 4, ht)           # R5: 10 / 26 / 14 / 14 / 26
            self.assertGreater(rows[ht][1]["volume_pct"], rows[ht][0]["volume_pct"], ht)   # less volume loss
        # KNOWN COSTS, recorded so they stay visible: more faces stretched > 2x at 120-160 (front of the armpit / chest
        # side) and a volume gain at 60-100 deg (the deltoid cap no longer collapses)
        for ht in (120, 140, 160):
            self.assertLessEqual(rows[ht][1]["stretch"], rows[ht][0]["stretch"] + 30, ht)
        for ht in (60, 90):
            self.assertLess(rows[ht][1]["volume_pct"], 1.6, ht)

    def test_benchmarks_versus_r5(self):
        v1 = json.loads(R5_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r5_worst"], v2[n]["r8_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 2, n)
        press = v2["shoulder_press"]["r8_worst"]
        self.assertEqual(press["self_intersecting_pairs"], 0)            # R5 216


if __name__ == "__main__":
    unittest.main(argv=[__file__])
