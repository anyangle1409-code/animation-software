"""Native checks of the ORIGINAL_v1 review candidate R24 = R18 + the press-lockout skin-slide corrective (HGPT_S7_DELT_
keys from 130 deg; targets from build_original_skin_slide_targets_blender.py: the ball behind the shoulder faired and the
skin slid along the surface from the squashed deltoid into the stretched armpit).  Re-measured from the saved blends.
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
R24 = CAND / "claude_review_r24_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R24_CLAUDE.blend"
REPORT = CAND / "claude_review_r24_20261015/r24_build.json"
VALIDATION = CAND / "claude_review_r24_20261015/r24_validation.json"
R18_VALIDATION = CAND / "claude_review_r18_20261015/r18_validation.json"
SIDES = ("l", "r")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class ReviewCandidateR24NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_and_keys(self):
        self.assertEqual(sha(R18), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R24), self.report["output"]["sha256"])
        import original_v1_review_candidate_drives  # noqa: F401
        bpy.ops.wm.open_mainfile(filepath=str(R24))
        scene = bpy.context.scene
        self.assertIs(scene.get("hgpt_review_candidate_approved"), False)
        self.assertEqual(scene.get("hgpt_press_path"), "v4")
        self.assertIs(scene.get("hgpt_shoulder_fold_flip"), True)
        body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
        rig = body.find_armature()
        self.assertEqual(sum(b.use_deform for b in rig.data.bones), 67)
        keys = [kb.name for kb in body.data.shape_keys.key_blocks]
        for s in SIDES:
            self.assertEqual(len([k for k in keys if k.startswith(f"HGPT_S7_DELT_{s}_")]), len(self.report["keys_ht"]), s)
            self.assertEqual(len(rig[f"hgpt_s7_angles_{s}"]), len(self.report["keys_ht"]))
        self.assertEqual(self.report["targets_recipe"]["mode"], "skin slide")

    def test_press_path_cleaner_with_s7(self):
        rows = list(zip(self.report["press_path_without_s7"], self.report["press_path_r17"]))
        for a, b in rows:
            if a["ht"] <= 130.0:
                self.assertEqual((a["pairs"], a["collapse"], a["stretch"]), (b["pairs"], b["collapse"], b["stretch"]), a["t"])
            self.assertLessEqual(b["pairs"], a["pairs"], a["t"])
            self.assertLessEqual(b["collapse"], a["collapse"], a["t"])
        lock_a, lock_b = rows[-1]
        self.assertLess(lock_b["stretch"], 0.5 * lock_a["stretch"])          # 314 -> 100 measured
        self.assertGreater(lock_b["volume_pct"], -2.5)                       # the faired ball: -1.11 -> -2.16 % (recorded)

    def test_benchmarks_versus_r18(self):
        v1 = json.loads(R18_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r18_worst"], v2[n]["r24_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 4, n)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
