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

RECORD = ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json'


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


@unittest.skipIf(np is None, 'numpy unavailable')
class SolverConventionTests(unittest.TestCase):
    def test_zxy_round_trip_and_clinical_signs(self):
        import joint_solver as js
        rng = np.random.default_rng(7)
        for _ in range(200):
            z, x, y = rng.uniform(-170, 170), rng.uniform(-80, 80), rng.uniform(-170, 170)
            self.assertTrue(np.allclose(js.zxy_angles(js.zxy_matrix(z, x, y)), (z, x, y), atol=1e-9))
        ant = np.array([0, -1.0, 0]); right = np.array([-1.0, 0, 0]); down = np.array([0, 0, -1.0])
        P0 = js.WORLD_FRAME
        # hip flexion moves the distal femur anteriorly on both sides; adduction moves it medially
        for side, medial in (('right', -right), ('left', right)):
            R = js.zxy_matrix(*js.clinical_to_zxy('hip', side, flexion=30))
            self.assertGreater((js.world_delta(P0, R) @ down) @ ant, 0.4)
            R = js.zxy_matrix(*js.clinical_to_zxy('hip', side, adduction=20))
            self.assertGreater((js.world_delta(P0, R) @ down) @ medial, 0.3)
            # internal rotation turns the anterior surface medially
            R = js.zxy_matrix(*js.clinical_to_zxy('hip', side, internal=30))
            self.assertGreater((js.world_delta(P0, R) @ ant) @ medial, 0.4)
            # knee flexion moves the distal tibia posteriorly
            R = js.zxy_matrix(*js.clinical_to_zxy('knee', side, flexion=40))
            self.assertLess((js.world_delta(P0, R) @ down) @ ant, -0.5)
            back = js.zxy_to_clinical('knee', side, *js.zxy_angles(R))
            self.assertAlmostEqual(back['flexion'], 40, places=9)

    def test_gh_swing_twist_round_trip_and_directions(self):
        import joint_solver as js
        ant = np.array([0, -1.0, 0]); down = np.array([0, 0, -1.0])
        for side, lateral in (('right', np.array([-1.0, 0, 0])), ('left', np.array([1.0, 0, 0]))):
            R = js.gh_command(side, 0, 90)
            self.assertGreater((js.WORLD_FRAME @ R @ js.WORLD_FRAME.T @ down) @ lateral, 0.999, 'plane 0 abducts')
            R = js.gh_command(side, 90, 90)
            self.assertGreater((js.WORLD_FRAME @ R @ js.WORLD_FRAME.T @ down) @ ant, 0.999, 'plane 90 flexes forward')
            for plane, elev, ir in [(0, 0, 30), (30, 60, -20), (90, 120, 45), (-30, 45, 10), (60, 150, -60)]:
                m = js.gh_measure(side, js.gh_command(side, plane, elev, ir))
                self.assertAlmostEqual(m['elevation'], elev, places=7)
                self.assertAlmostEqual(m['internal_rotation'], ir, places=7)
                if elev:
                    self.assertAlmostEqual(m['plane_of_elevation'], plane, places=7)


@unittest.skipIf(np is None, 'numpy unavailable')
class IsolatedTestDirectionTests(unittest.TestCase):
    """Command directions checked on the committed r95 fit, independent of Blender."""
    @classmethod
    def setUpClass(cls):
        import isolated_tests as it
        cls.it = it
        cls.rec = json.loads(RECORD.read_text())
        cls.atlas = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
        cls.F = it.frames(cls.rec)
        cls.T = {t['id']: t for t in it.specs(cls.rec, cls.atlas)}

    def moved(self, test_id, cmd, bone, vec):
        G = self.it.deltas(self.T[test_id], cmd, self.F)[bone]
        return G[:3, :3] @ np.asarray(vec, float)

    def test_subtalar_positive_is_inversion_on_both_feet(self):
        for side, medial in (('left', np.array([-1.0, 0, 0])), ('right', np.array([1.0, 0, 0]))):
            sole = self.moved(f'subtalar_inversion_eversion_{side}', {'angle': 20}, f'calcaneus_{side}', [0, 0, -1.0])
            self.assertGreater(sole @ medial, 0.1, side + ': inversion turns the sole medially')

    def test_elbow_flexion_forearm_pronation_and_ankle_directions(self):
        for side, medial in (('left', np.array([-1.0, 0, 0])), ('right', np.array([1.0, 0, 0]))):
            fore = self.moved(f'elbow_flexion_at_pronation_0_{side}', {'angle': 90}, f'ulna_{side}', [0, 0, -1.0])
            self.assertGreater(fore @ np.array([0, -1.0, 0]), 0.99, 'elbow flexion brings the forearm forward')
            palm0 = self.F[f'scaphoid_{side}'][:, 0]
            self.assertGreater(palm0 @ medial, 0.8, 'palms face medially at rest')
            palm = self.moved(f'forearm_rotation_at_elbow_0_{side}', {'pronation': 60}, f'radius_{side}', palm0)
            self.assertGreater(palm @ np.array([0, 1.0, 0]), 0.6, 'pronation turns the palm posteriorly')
            toes = self.moved(f'talocrural_dorsi_plantarflexion_{side}', {'angle': 20}, f'talus_{side}', [0, -1.0, 0])
            self.assertGreater(toes[2], 0.3, 'dorsiflexion lifts the toes')
            wrist = self.moved(f'wrist_flexion_{side}', {'flexion': 60}, f'lunate_{side}', [0, 0, -1.0])
            self.assertGreater(wrist @ palm0, 0.4, 'wrist flexion moves the hand toward the palm side')
        face = self.moved('c1_c2_axial_rotation', {'angle': 30}, 'c1', [0, -1.0, 0])
        self.assertGreater(face[0], 0.4, 'positive C1/C2 angle turns the face to the character left (+X)')
