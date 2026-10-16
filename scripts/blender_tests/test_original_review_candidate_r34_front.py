"""R34 front-armpit regression goals; run on R33 first to demonstrate failures.

These limits are fixed before implementing R34. They supplement existing tests.
"""
import os
import sys
import unittest
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/anatomy_fit"))
import original_v1_review_candidate_drives as drives
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as sculpt
import original_v1_press_extension as press

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates"
DEFAULT = CAND / "codex_review_r34_20261016/HGPT_ORIGINAL_V1_REVIEW_R34_CODEX.blend"
BLEND = Path(os.environ.get("HGPT_FRONT_TEST_BLEND", str(DEFAULT)))
TARGETS = CAND / "claude_review_r33_20261016/stages/r33_targets.npz"

class FrontAxillaRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bpy.ops.wm.open_mainfile(filepath=str(BLEND.resolve()))
        cls.res = correction.build_corrected_scene()
        cls.body, cls.rig = cls.res["body"], cls.res["runtime"]
        drives.setup(cls.res)
        press.install()
        with np.load(TARGETS) as z:
            cls.targets = {k: z[k].copy() for k in ("120.0", "145.0")}

    def posed(self, ht):
        bench._reset(self.rig)
        sculpt.press_pose(self.res, ht)
        drives.drive(self.rig, self.body)
        vertices, faces = bench._evaluated(self.body)
        return np.array([tuple(v) for v in vertices]), np.asarray(faces)

    def test_front_target_fit_at_120_and_145_degrees(self):
        for ht in (120.0, 145.0):
            with self.subTest(elevation=ht):
                p, _ = self.posed(ht)
                error_mm = float(np.linalg.norm(p[18633] - self.targets[str(ht)][18633]) * 1000)
                print("FRONT_TARGET_FIT", ht, error_mm, flush=True)
                self.assertLess(error_mm, 10.0, "front patch must remain within 10 mm of the unchanged R33 target")

    def test_front_edge_at_130_degrees(self):
        p, f = self.posed(130.0)
        edge_faces = defaultdict(list)
        for i, face in enumerate(f):
            for j in range(3):
                edge_faces[tuple(sorted((int(face[j]), int(face[(j + 1) % 3]))))].append(i)
        edges = np.array([edge for edge, fs in edge_faces.items() if len(fs) == 2])
        ff = np.array([edge_faces[tuple(edge)] for edge in edges])
        normals = np.cross(p[f[:, 1]] - p[f[:, 0]], p[f[:, 2]] - p[f[:, 0]])
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-15)
        dihedral = np.degrees(np.arccos(np.clip((normals[ff[:, 0]] * normals[ff[:, 1]]).sum(1), -1, 1)))
        gh = np.array(tuple(self.rig.matrix_world @ self.rig.pose.bones["upperarm_r"].head))
        rel = (p[edges[:, 0]] + p[edges[:, 1]]) / 2 - gh
        front_patch = ((np.linalg.norm(rel, axis=1) < 0.08)
                       & (rel[:, 0] > 0) & (rel[:, 1] < 0) & (rel[:, 2] < 0))
        self.assertTrue(front_patch.any())
        peak = float(dihedral[front_patch].max())
        print("FRONT_EDGE_130", peak, flush=True)
        self.assertLess(peak, 100.0, "reduce the measured 132-degree front crease below 100 degrees")

if __name__ == "__main__":
    unittest.main(argv=[__file__])
