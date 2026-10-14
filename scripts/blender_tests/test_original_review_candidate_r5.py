"""Native checks of the ORIGINAL_v1 review candidate R5 = R4 + scapular upward rotation/tilt held to the profile ("isb" drive
mode) + C1 upper-arm/trunk contact keys, re-measured from the saved blends.  Review only."""
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
C5 = CAND / "claude_foot_20261013/c5/HGPT_ORIGINAL_V1_FOOT_C5_CLAUDE.blend"
R4 = CAND / "claude_review_r5_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R5_CLAUDE.blend"     # (the file under test: R5)
REPORT = CAND / "claude_review_r5_20261014/r5_build.json"
VALIDATION = CAND / "claude_review_r5_20261014/r5_validation.json"
R4_VALIDATION = CAND / "claude_review_r4_20261014/r4_validation.json"
ANAT = {"r": "left", "l": "right"}                        # F-SIDE-001


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
    rig = body.find_armature()
    return {"basis": [v.co.copy() for v in body.data.vertices],
            "bones": {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in rig.data.bones},
            "deform": sum(b.use_deform for b in rig.data.bones),
            "influences": max(sum(1 for g in v.groups if g.weight > 0) for v in body.data.vertices),
            "weight_sums": [sum(g.weight for g in v.groups) for v in body.data.vertices],
            "gh": {s: bpy.data.objects[f"LM_scapula_{a}__GH"].matrix_world.translation.copy() for s, a in ANAT.items()},
            "drive": bpy.context.scene.get("hgpt_shoulder_drive"),
            "approved": bpy.context.scene.get("hgpt_review_candidate_approved")}


class ReviewCandidateR5NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.c5 = snapshot(C5)
        cls.r4 = snapshot(R4)

    def test_identity_and_flags(self):
        self.assertEqual(sha(C5), self.report["parent"]["sha256"])
        self.assertEqual(sha(R4), self.report["output"]["sha256"])
        self.assertEqual(self.report["checks"]["verdict"], "PASS")
        self.assertIs(self.r4["approved"], False)
        self.assertEqual(self.r4["drive"], "R5")

    def test_only_the_upper_arm_pivots_moved_to_the_gh_landmark(self):
        self.assertEqual(self.r4["deform"], 67)
        self.assertLess(max((a - b).length for a, b in zip(self.c5["basis"], self.r4["basis"])), 1e-9)
        for name, (h, t) in self.c5["bones"].items():
            h4, t4 = self.r4["bones"][name]
            self.assertLess((t - t4).length, 1e-6, name)              # every tail (elbows included) unchanged
            if name.startswith("upperarm_"):
                s = name[-1]
                self.assertLess((h4 - self.r4["gh"][s]).length, 1e-5, name)
                self.assertAlmostEqual((h - h4).z, 0.0526, delta=0.002)   # 53 mm lower
            else:
                self.assertLess((h - h4).length, 1e-6, name)

    def test_weights_are_normalised_with_at_most_four_influences(self):
        self.assertLessEqual(self.r4["influences"], 4)
        self.assertLess(max(abs(x - 1.0) for x in self.r4["weight_sums"] if x > 0), 1e-3)

    def test_live_drive_keeps_the_blade_on_the_thorax_and_mirrors(self):
        import original_v1_review_candidate_drives as drives
        import original_v1_shoulder_r4 as r4
        bpy.ops.wm.open_mainfile(filepath=str(R4))
        import build_functional_shoulder_correction_blender as correction
        import original_v1_scapula_isb_drive as isb
        res = correction.build_corrected_scene()
        drives.setup(res)
        rig = res["runtime"]; pb = rig.pose.bones
        for ht in (90, 160):
            correction.apply_corrected_pose(res, ht)
            log = r4._S["last"]
            for s in ("r", "l"):
                self.assertEqual(log[s]["mode"], "isb")
                got, want = log[s]["scapula_isb_deg"], log[s]["scapula_isb_target_deg"]
                self.assertLess(abs(got[1] - want[1]), 2.0, (ht, s))                          # upward rotation held
                self.assertLess(abs(got[2] - want[2]), 2.0, (ht, s))                          # posterior tilt held
                self.assertLess(max(abs(x) for x in log[s]["contact_residual_mm"]), 50.0, (ht, s))   # KNOWN: AI lift-off
                self.assertLess(abs(log[s]["clavicle_extra_elevation_deg"]), 6.0, (ht, s))   # no shrug
            self.assertLess(abs(pb["upperarm_r"].head.x + pb["upperarm_l"].head.x), 1e-5)
            self.assertLess(abs(pb["scapula_r"].tail.z - pb["scapula_l"].tail.z), 1e-5)
            # anatomical upward rotation: the glenoid (arm pivot) rises with the arm
            self.assertGreater(pb["upperarm_r"].head.z, rig.data.bones["upperarm_r"].head_local.z, ht)
            q = drives._rel_quat(rig, "upperarm_r", "scapula_r")
            self.assertLess(math.degrees(min(q.angle, 2 * math.pi - q.angle)), 125.0, ht)   # was 162 at 160 HT

    def test_coupled_sweep_versus_todays_rig(self):
        before = {r["ht"]: r for r in self.report["coupled_sweep_c5_today"]}
        after = {r["ht"]: r for r in self.report["coupled_sweep_r4"]}
        for ht in (60, 80, 100, 120, 140, 160):
            self.assertLess(after[ht]["stretch"], before[ht]["stretch"], ht)
        for ht in (140, 160):
            self.assertLess(after[ht]["pairs"], before[ht]["pairs"], ht)
            self.assertLess(after[ht]["collapse"], before[ht]["collapse"], ht)
            self.assertGreater(after[ht]["volume_pct"], before[ht]["volume_pct"], ht)          # less volume loss
        for ht in (80, 100, 120):                                  # KNOWN COST, recorded: a few collapsed faces / pairs mid-range
            self.assertLessEqual(after[ht]["collapse"], 10, ht)
            self.assertLessEqual(after[ht]["pairs"], 10, ht)

    def test_c1_keys_stay_on_their_own_upper_arm(self):
        bpy.ops.wm.open_mainfile(filepath=str(R4))
        body = [o for o in bpy.data.objects if o.type == "MESH" and o.data.shape_keys and o.find_armature() is not None][0]
        rig = body.find_armature()
        names = {g.index: g.name for g in body.vertex_groups}
        keys = [kb for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_C1_ARMTRUNK_")]
        self.assertEqual(len(keys), 4)
        for kb in keys:
            s = kb.name.split("_")[-2]
            moved = [i for i, d in enumerate(kb.data) if (d.co - body.data.vertices[i].co).length > 1e-7]
            self.assertTrue(moved, kb.name)
            for i in moved:
                w = {names[g.group]: g.weight for g in body.data.vertices[i].groups}
                self.assertGreater(w.get(f"upperarm_{s}", 0.0), 0.0, (kb.name, i))
            self.assertLessEqual(max((kb.data[i].co - body.data.vertices[i].co).length for i in moved), 0.03 + 1e-6)
        for s in ("l", "r"):
            a = list(rig[f"hgpt_c1_angles_{s}"])
            self.assertEqual(len(a), 2)
            self.assertTrue(18.0 < a[0] < a[1], a)                   # above the walk's arm swing; ascending

    def test_row_contact_fixed_and_others_unchanged_versus_r4(self):
        v4 = json.loads(R4_VALIDATION.read_text())["benchmarks"]
        v5 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertLess(v5["bent_over_row"]["r5_worst"]["self_intersecting_pairs"], 0.5 * v4["bent_over_row"]["r4_worst"]["self_intersecting_pairs"])
        self.assertLessEqual(v5["bent_over_row"]["r5_worst"]["collapse_lt_0_1"], v4["bent_over_row"]["r4_worst"]["collapse_lt_0_1"])
        for n in ("walk_stride", "squat", "lunge", "deadlift", "calf_raise", "grip", "wrist_circuit", "forearm_rotation"):
            self.assertEqual(v5[n]["r5_worst"], v4[n]["r4_worst"], n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
