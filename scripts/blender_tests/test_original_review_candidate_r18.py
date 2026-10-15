"""Native checks of the ORIGINAL_v1 review candidate R18 = R15 with the shoulder edges re-routed along the folds (the
shoulder/armpit mesh rebuild, stage 1: build_original_shoulder_fold_flip_blender.py).  Every vertex, weight and shape key is
R15's; only the triangulation differs.  Re-measured from the saved blends.  Review only."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
R15 = CAND / "claude_review_r15_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R15_CLAUDE.blend"
R18 = CAND / "claude_review_r18_20261015/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R18_CLAUDE.blend"
REPORT = CAND / "claude_review_r18_20261015/r18_build.json"
VALIDATION = CAND / "claude_review_r18_20261015/r18_validation.json"
R15_VALIDATION = CAND / "claude_review_r15_20261015/r15_validation.json"
BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def layers(path):
    import original_v1_review_candidate_drives  # noqa: F401
    bpy.ops.wm.open_mainfile(filepath=str(path))
    me = bpy.data.objects[BODY].data
    keys = {kb.name: np.array([tuple(d.co) for d in kb.data]) for kb in me.shape_keys.key_blocks}
    names = {g.index: g.name for g in bpy.data.objects[BODY].vertex_groups}
    w = [sorted((names[g.group], round(g.weight, 6)) for g in v.groups) for v in me.vertices]
    faces = {frozenset(p.vertices) for p in me.polygons}
    return keys, w, faces, bpy.context.scene.get("hgpt_press_path"), bpy.context.scene.get("hgpt_shoulder_fold_flip")


class ReviewCandidateR18NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())

    def test_identity_and_unchanged_vertex_layers(self):
        self.assertEqual(sha(R15), self.report["output"]["parent"]["sha256"])
        self.assertEqual(sha(R18), self.report["output"]["sha256"])
        k15, w15, f15, _, _ = layers(R15)
        k18, w18, f18, path, flip = layers(R18)
        self.assertEqual(path, "v4")
        self.assertIs(flip, True)
        self.assertIs(bpy.context.scene.get("hgpt_review_candidate_approved"), False)
        self.assertEqual(sorted(k15), sorted(k18))
        for n in k15:
            self.assertTrue(np.array_equal(k15[n], k18[n]), n)          # every shape key, every vertex: identical
        self.assertEqual(w15, w18)                                       # every weight: identical
        self.assertEqual(len(f15), len(f18))                             # same face count, different triangulation
        changed = len(f18 - f15)
        self.assertGreater(changed, 2000)
        self.assertLessEqual(changed, 4 * self.report["flips_per_side"])  # 2 new triangles per flip, both sides (fewer where
                                                                          # a later flip re-used the same triangles)

    def test_folds_reduced(self):
        b, a = self.report["folds_before"], self.report["folds_after"]
        self.assertLess(a["p172"]["sharp_folds"], 0.7 * b["p172"]["sharp_folds"])
        for k in b:
            self.assertLessEqual(a[k]["sharp_folds"], b[k]["sharp_folds"], k)
            self.assertLessEqual(a[k]["bending"], b[k]["bending"], k)

    def test_benchmarks_versus_r15(self):
        v1 = json.loads(R15_VALIDATION.read_text())["benchmarks"]
        v2 = json.loads(VALIDATION.read_text())["benchmarks"]
        self.assertEqual(sorted(v1), sorted(v2))
        for n in v1:
            a, b = v1[n]["r15_worst"], v2[n]["r18_worst"]
            self.assertLessEqual(b["self_intersecting_pairs"], a["self_intersecting_pairs"], n)
            self.assertLessEqual(b["collapse_lt_0_1"], a["collapse_lt_0_1"] + 4, n)   # recorded: shoulder_press 16 -> 20


if __name__ == "__main__":
    unittest.main(argv=[__file__])
