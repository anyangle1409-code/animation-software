"""Regression tests for the Phase 6/7 anatomical fitting geometry and the committed r95 fit record."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
try:
    import numpy as np
except ImportError:  # pragma: no cover - system python without numpy
    np = None

RECORD = ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a002.json'


def cylinder(r=0.05, h=0.2, n=64):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = lambda z: np.c_[r * np.cos(ang), r * np.sin(ang), np.full(n, z)]
    V = np.vstack([ring(0.0), ring(h), [[0, 0, 0]], [[0, 0, h]]])
    T = []
    for i in range(n):
        j = (i + 1) % n
        T += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    return V, np.array(T)


@unittest.skipIf(np is None, 'numpy unavailable')
class GeometryTests(unittest.TestCase):
    def test_plane_section_of_cylinder_has_known_perimeter_area_and_centroid(self):
        from mesh_sections import loop_metrics, plane_section
        V, T = cylinder()
        loops = plane_section(V, T, (0, 0, 0.1), (0, 0, 1))
        self.assertEqual(len(loops), 1)
        per, cent, area = loop_metrics(loops[0], (0, 0, 1))
        polygon_per = 64 * 2 * 0.05 * math.sin(math.pi / 64)
        self.assertAlmostEqual(per, polygon_per, places=9)
        self.assertAlmostEqual(area, 0.5 * 64 * 0.05 ** 2 * math.sin(2 * math.pi / 64), places=9)
        self.assertLess(np.linalg.norm(cent - [0, 0, 0.1]), 1e-12)

    def test_closest_point_and_winding_containment(self):
        from character_fit import closest_point_on_triangle
        from joint_markers import winding_inside
        a, b, c = np.array([0., 0, 0]), np.array([1., 0, 0]), np.array([0., 1, 0])
        self.assertTrue(np.allclose(closest_point_on_triangle(np.array([0.2, 0.2, 1.0]), a, b, c), [0.2, 0.2, 0]))
        self.assertTrue(np.allclose(closest_point_on_triangle(np.array([2.0, -1.0, 0.0]), a, b, c), b))
        V, T = cylinder()
        w = winding_inside(np.array([[0, 0, 0.1], [0.049, 0, 0.1], [0.06, 0, 0.1], [0, 0, 0.25]]), V, T)
        self.assertEqual(list(w > 0.5), [True, True, False, False])

    def test_marker_frames_are_proper_isb_pattern_with_z_to_character_right(self):
        from joint_markers import bone_frame
        for head, tail in [([0.08, 0, 0.93], [0.09, 0, 0.52]), ([0.09, 0.03, 0.02], [0.09, -0.2, 0.02]), ([0, 0.05, 1.1], [0, 0.04, 1.14])]:
            R = bone_frame(head, tail)
            self.assertTrue(np.allclose(R.T @ R, np.eye(3), atol=1e-12))
            self.assertAlmostEqual(np.linalg.det(R), 1.0, places=12)
            self.assertGreater(R[:, 2] @ np.array([-1, 0, 0]), 0.9, 'ISB Z must point to the character right (-X)')
            self.assertGreater(R[:, 1] @ np.array([0, 0, 1]) + R[:, 0] @ np.array([0, -1, 0]), 0.9)

    def test_segment_closest_points(self):
        from joint_markers import segment_closest
        p, q = segment_closest(np.array([0., 0, 0]), np.array([1., 0, 0]), np.array([0.5, 1, -1]), np.array([0.5, 1, 1]))
        self.assertTrue(np.allclose(p, [0.5, 0, 0]) and np.allclose(q, [0.5, 1, 0]))


class RecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(RECORD.read_text())
        cls.inv = {j['id']: j for j in json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/adult_articulation_inventory.json').read_text())['articulations']}
        cls.ids = {b['id'] for b in json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/adult_bone_inventory_206.json').read_text())['bones']}

    def test_record_binds_existing_audit_files_by_hash(self):
        p = self.rec['provenance']
        for key in ('source_blend', 'out_blend'):
            path = ROOT / p[key]
            expected = p['source_blend_sha256_before'] if key == 'source_blend' else p['out_blend_sha256']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, key)
        self.assertEqual(p['source_blend_sha256_before'], p['source_blend_sha256_after'])

    def test_every_conventional_bone_once_with_valid_tree_and_roles(self):
        bones = self.rec['bones']
        self.assertEqual(set(bones), self.ids)
        for bid, b in bones.items():
            self.assertIn(b['role'], {'ACTIVE', 'FOLLOWER', 'FIXED', 'REFERENCE'})
            seen, cur = set(), bid
            while cur is not None:
                self.assertNotIn(cur, seen, 'cycle at ' + bid)
                seen.add(cur)
                cur = bones[cur]['parent']
            rel = b['parent_relation']
            if rel['type'] == 'articular':
                j = self.inv[rel['joint_id']]
                self.assertIn(bid, j['participants'])
                self.assertIn(b['parent'], j['participants'])
            else:
                self.assertTrue(rel.get('reason'), bid + ' carrier/root needs an explicit reason')
        self.assertEqual(bones['hyoid']['role'], 'REFERENCE')
        self.assertIsNone(bones['hyoid']['parent'], 'hyoid has no osseous articulation')

    def test_markers_cover_inventory_and_are_distinct(self):
        markers = self.rec['joint_markers']
        self.assertEqual(set(markers), set(self.inv))
        pts = np.array([m['centre_m'] for m in markers.values()]) if np else None
        if np is not None:
            d = np.linalg.norm(pts[:, None] - pts[None], axis=2) + np.eye(len(pts))
            self.assertGreater(d.min(), 1e-4)
        ac, gh = markers['acromioclavicular_left']['centre_m'], markers['glenohumeral_left']['centre_m']
        self.assertGreater(math.dist(ac, gh), 0.02, 'AC and GH centres must stay distinct')

    def test_side_binding_follows_geometric_chirality(self):
        ch = self.rec['landmarks_and_joint_centres']['chirality']
        self.assertEqual(ch['left']['world_x_side'], '+X')
        self.assertEqual(ch['left']['geometric_hand'], 'left')
        self.assertEqual(ch['right']['geometric_hand'], 'right')
        self.assertEqual(self.rec['conventions']['runtime_side_binding'], {'left': '_r', 'right': '_l'})
        for bid, b in self.rec['bones'].items():
            mid = (b['head_m'][0] + b['tail_m'][0]) / 2
            if bid.endswith('_left'):
                self.assertGreater(mid, 0, bid)
            elif bid.endswith('_right'):
                self.assertLess(mid, 0, bid)

    def test_failed_and_unverified_checks_stay_visible(self):
        c = self.rec['checks']
        self.assertEqual(c['trotter_gleser_cross_check']['status'], 'FAIL')
        self.assertFalse(self.rec['character_accepted'])
        self.assertEqual(self.rec['completed_tracker_gates'], [])
        for key in ('bones_inside_body', 'joint_markers_inside_body', 'bilateral_symmetry', 'distinct_centres', 'ordering', 'authored_feature_presence'):
            self.assertEqual(c[key]['status'], 'PASS', key)


if __name__ == '__main__':
    unittest.main()
