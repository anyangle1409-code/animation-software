"""Native checks of the provisional C5 foot (C4 + plantar heel contact), re-measured from the saved blends."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_original_foot_c4_candidate_blender as c4
import build_original_foot_heel_contact_blender as c5

CAND = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013"
C4 = CAND / "c4/HGPT_ORIGINAL_V1_FOOT_C4_CLAUDE.blend"
C5 = CAND / "c5/HGPT_ORIGINAL_V1_FOOT_C5_CLAUDE.blend"
REPORT = CAND / "c5/c5_build.json"


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[c4.BODY]
    return ([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons],
            [tuple(e.vertices) for e in body.data.edges])


class FootC5HeelContactNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(REPORT.read_text())
        cls.P, cls.F, cls.E = load(C4)
        cls.Q, _, _ = load(C5)
        master = bpy.data.objects[c4.MASTER]
        cls.stations = c4.stations(master)
        heads = [cls.stations[f"metatarsal_{k}_left:tail"] for k in range(1, 6)]
        cls.y_ball, cls.x_mid = sum(h.y for h in heads) / 5, heads[2].x
        cls.ajc_y = bpy.data.objects["LM_tibia_left__AJC"].matrix_world.translation.y
        cls.body = bpy.data.objects[c4.BODY]

    def test_identity(self):
        self.assertEqual(hashlib.sha256(C4.read_bytes()).hexdigest(), self.report["parent"]["sha256"])
        self.assertEqual(hashlib.sha256(C5.read_bytes()).hexdigest(), self.report["output"]["sha256"])
        self.assertEqual(self.report["checks"]["verdict"], "PASS")

    def test_only_heel_z_lowered_never_below_floor(self):
        floor = min(p.z for p in self.P)
        moved = [i for i in range(len(self.P)) if self.Q[i] != self.P[i]]
        self.assertTrue(moved)
        for i in moved:
            self.assertEqual((self.Q[i].x, self.Q[i].y), (self.P[i].x, self.P[i].y))
            self.assertLess(self.Q[i].z, self.P[i].z)
            self.assertGreaterEqual(self.Q[i].z, floor)
            self.assertGreater(self.P[i].y, self.ajc_y + c5.FLAT_START - c5.BLEND - 1e-9)

    def test_heel_now_bears_on_the_floor_and_other_contacts_kept(self):
        before = c5.contact_zones(self.P, self.ajc_y, self.y_ball, self.x_mid)
        after = c5.contact_zones(self.Q, self.ajc_y, self.y_ball, self.x_mid)
        self.assertEqual(before["heel"], 0)            # the inherited defect
        self.assertGreater(after["heel"], 0)
        for k in ("metatarsal_heads", "toes", "midfoot_lateral"):
            self.assertEqual(after[k], before[k], k)
        floor = min(q.z for q in self.Q)
        for d in (0, 10, 20, 30):                        # flat pad behind the ankle (sections, mm)
            self.assertLess(c5.section_low(self.Q, self.E, self.ajc_y + d / 1000) - floor, 0.0015, d)

    def test_no_intersection_flip_and_stations_inside(self):
        sub = [f for f in self.F if all(abs(self.Q[i].x) > 0.02 and self.Q[i].z < 0.12 for i in f)]
        t = BVHTree.FromPolygons(self.Q, sub, all_triangles=True); fs = [set(f) for f in sub]
        self.assertEqual(sum(1 for a, b in t.overlap(t) if a < b and not (fs[a] & fs[b])), 0)
        for f in self.F:
            a0 = (self.P[f[1]] - self.P[f[0]]).cross(self.P[f[2]] - self.P[f[0]])
            a1 = (self.Q[f[1]] - self.Q[f[0]]).cross(self.Q[f[2]] - self.Q[f[0]])
            self.assertGreater(a0.dot(a1), 0.0)
        self.assertEqual(c4.inside_all(self.body, self.stations), [])

    def test_mirror_exact(self):
        index = {(round(p.x, 6), round(p.y, 6), round(p.z, 6)): i for i, p in enumerate(self.P)}
        for i in range(len(self.P)):
            if self.Q[i] != self.P[i]:
                j = index[(round(-self.P[i].x, 6), round(self.P[i].y, 6), round(self.P[i].z, 6))]
                self.assertAlmostEqual(self.Q[i].z, self.Q[j].z, places=7)


if __name__ == "__main__":
    unittest.main(argv=[__file__])
