"""Native checks of the provisional C4 foot candidate, re-measured from the saved blend (not from its build report)."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_original_foot_c4_candidate_blender as c4

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013"
C3 = CAND / "c3/HGPT_ORIGINAL_V1_FOOT_SKELETON_C3_CLAUDE.blend"
C4 = CAND / "c4/HGPT_ORIGINAL_V1_FOOT_C4_CLAUDE.blend"
REPORT = CAND / "c4/c4_build.json"
BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[BODY]
    return ([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons],
            [tuple(e.vertices) for e in body.data.edges])


class FootC4NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.P, cls.F, cls.E = load(C3)
        cls.Q, _, _ = load(C4)
        master = bpy.data.objects[c4.MASTER]
        heads = [master.matrix_world @ master.data.bones[f"anat_metatarsal_{k}_left"].tail_local for k in range(1, 6)]
        cls.y_ball = sum(h.y for h in heads) / 5
        cls.ajc_y = bpy.data.objects["LM_tibia_left__AJC"].matrix_world.translation.y
        cls.stations = c4.stations(master)
        cls.body = bpy.data.objects[BODY]

    def test_identity_and_status(self):
        self.assertEqual(hashlib.sha256(C3.read_bytes()).hexdigest(), self.report["parent"]["sha256"])
        self.assertEqual(hashlib.sha256(C4.read_bytes()).hexdigest(), self.report["output"]["sha256"])
        self.assertEqual(self.report["status"], "PROVISIONAL_DEVELOPMENT_CANDIDATE_NOT_ACCEPTED")
        self.assertEqual(self.report["checks"]["verdict"], "PASS")

    def test_only_foot_x_changed_and_mirror_exact(self):
        moved = [i for i in range(len(self.P)) if (self.Q[i] - self.P[i]).length > 1e-9]
        self.assertTrue(moved)
        for i in moved:
            self.assertEqual((self.Q[i].y, self.Q[i].z), (self.P[i].y, self.P[i].z))
            self.assertGreater(abs(self.P[i].x), 0.02)
            self.assertLess(self.P[i].z, 0.08)
        index = {(round(p.x, 6), round(p.y, 6), round(p.z, 6)): i for i, p in enumerate(self.P)}
        for i in moved:
            j = index[(round(-self.P[i].x, 6), round(self.P[i].y, 6), round(self.P[i].z, 6))]
            self.assertAlmostEqual(self.Q[i].x - self.P[i].x, -(self.Q[j].x - self.P[j].x), places=7)

    def test_ball_breadth_on_ansur_by_true_sections(self):
        self.assertAlmostEqual(c4.ball_breadth(self.Q, self.E, self.y_ball)[0], c4.ANSUR_BREADTH, delta=0.0005)

    def test_heel_unchanged_and_within_one_and_a_half_sd(self):
        h0, h1 = c4.heel_breadth(self.P, self.E, self.ajc_y)[0], c4.heel_breadth(self.Q, self.E, self.ajc_y)[0]
        self.assertAlmostEqual(h0, h1, places=9)
        self.assertLess(abs(h1 - c4.ANSUR_HEEL), 1.75 * 0.0053)

    def test_no_foot_self_intersection_or_flipped_triangle(self):
        idx = [f for f in self.F if all(abs(self.Q[i].x) > 0.02 and self.Q[i].z < 0.09 for i in f)]
        t = BVHTree.FromPolygons(self.Q, idx, all_triangles=True)
        fs = [set(f) for f in idx]
        self.assertEqual(sum(1 for a, b in t.overlap(t) if a < b and not (fs[a] & fs[b])), 0)
        for f in self.F:
            a0 = (self.P[f[1]] - self.P[f[0]]).cross(self.P[f[2]] - self.P[f[0]])
            a1 = (self.Q[f[1]] - self.Q[f[0]]).cross(self.Q[f[2]] - self.Q[f[0]])
            self.assertGreater(a0.dot(a1), 0.0)

    def test_toe_gaps_closed_but_open_along_every_toe(self):
        side = [i for i, p in enumerate(self.P) if p.x > 0.02 and p.z < 0.06 and p.y < -0.10]
        lab, tubes, webs = c4.toe_labels(self.P, self.E, side)
        ids = {k: {i for i, kk in lab.items() if kk == k and self.P[i].y < webs[k]} for k in range(1, 6)}
        grid = [round(-0.230 + n * c4.GRID, 6) for n in range(int((0.230 + max(webs.values())) / c4.GRID) + 2)]
        before = {k: c4.tube_sections(self.P, self.E, ids[k], grid) for k in ids}
        after = {k: c4.tube_sections(self.Q, self.E, ids[k], grid) for k in ids}
        for k in range(1, 5):
            common = [y for y in grid if y in after[k] and y in after[k + 1]]
            gaps = [after[k + 1][y][0] - after[k][y][1] for y in common]
            self.assertGreaterEqual(min(gaps), c4.TOE_GAP_MIN, k)
            ref = [y for y in common if c4.REF_BAND[0] <= y <= c4.REF_BAND[1]]
            g0 = min(before[k + 1][y][0] - before[k][y][1] for y in ref)
            g1 = min(after[k + 1][y][0] - after[k][y][1] for y in ref)
            self.assertLessEqual(g1, max(g0, 0.0011), k)       # closed to ~0.6-1.0 mm unless already that narrow

    def test_stations_inside_skin_floor_and_length_unchanged(self):
        self.assertEqual(c4.inside_all(self.body, self.stations), [])
        self.assertEqual(min(p.z for p in self.P), min(q.z for q in self.Q))
        flen = lambda V: max(v.y for v in V if v.x > 0.02 and v.z < 0.16) - min(v.y for v in V if v.x > 0.02 and v.z < 0.16)
        self.assertAlmostEqual(flen(self.P), flen(self.Q), places=9)
        self.assertAlmostEqual(flen(self.Q), 0.2799, delta=0.0002)

    def test_zz_rebuild_from_c3_is_deterministic(self):      # zz: runs last (it reopens files)
        exe = os.environ.get("BLENDER_BIN")                       # Blender binary (CI) or a python with the bpy module
        if not exe:
            self.skipTest("set BLENDER_BIN to rebuild in a subprocess")
        with tempfile.TemporaryDirectory() as d:
            out, rep = Path(d) / "c4.blend", Path(d) / "c4.json"
            script = str(ROOT / "scripts/build_original_foot_c4_candidate_blender.py")
            args = ["--blend", str(C3), "--expect-sha", self.report["parent"]["sha256"], "--out", str(out), "--report", str(rep)]
            if Path(exe).name.startswith("blender"):
                cmd = [exe, "--background", "--factory-startup", "--python", script, "--"] + args
            else:
                cmd = [exe, script, "--"] + args
            subprocess.run(cmd, check=True, capture_output=True)
            R, _, _ = load(out)
        self.assertEqual(max((r - q).length for r, q in zip(R, self.Q)), 0.0)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
