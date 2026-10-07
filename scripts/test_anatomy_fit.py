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
        # point query (the 1e-6 "segment" used for locators) must return the projection, not p0
        q0 = np.array([0.05, 0.1, -0.1500015])     # t lands inside the 1e-6 "segment": the old code returned p0 here
        p, _ = segment_closest(np.array([0., 0, 0]), np.array([0.1, 0, 0]), q0, q0 + 1e-6)
        self.assertTrue(np.allclose(p, [0.05, 0, 0], atol=1e-12))
        p, _ = segment_closest(np.array([0., 0, 0]), np.array([0.1, 0, 0]), np.array([0.3, 0.2, 0.1]), np.array([0.3, 0.2, 0.1]) + 1e-6)
        self.assertTrue(np.allclose(p, [0.1, 0, 0], atol=1e-12))


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


@unittest.skipIf(np is None, 'numpy unavailable')
class ShoulderComplexMirrorTests(unittest.TestCase):
    def test_girdle_motion_is_mirror_symmetric_and_retracts_both_clavicles(self):
        import isolated_tests as it
        rec = json.loads(RECORD.read_text())
        atlas = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
        F = it.frames(rec)
        T = {t['id']: t for t in it.specs(rec, atlas)}
        posed = {}
        for side in ('left', 'right'):
            t = T['shoulder_complex_scapular_plane_' + side]
            G = it.deltas(t, it.derive(t, {'elevation': 117.5}), F)
            Gs = G['clavicle_' + side] @ G['scapula_' + side]
            ac0 = np.append(t['landmarks']['AC'], 1.0)
            self.assertGreater((G['clavicle_' + side] @ ac0)[1] - ac0[1], 0.02, side + ': clavicle retraction moves AC posteriorly')
            posed[side] = {k: (Gs @ np.append(t['landmarks'][k], 1.0))[:3] for k in ('AC', 'GH', 'AI', 'TS')}
        for k in posed['left']:
            self.assertLess(np.linalg.norm(posed['left'][k] * [-1, 1, 1] - posed['right'][k]), 1e-3, k)


@unittest.skipIf(np is None, 'numpy unavailable')
class AbsoluteDirectionTests(unittest.TestCase):
    """Every isolated test spec must move its bones in the anatomically named direction in WORLD space.

    Integrity checks inside the Blender run compare commands with measurements through mutually inverse
    mappings, so they cannot detect a sign-convention error; these assertions can.
    """
    @classmethod
    def setUpClass(cls):
        import isolated_tests as it
        cls.it = it
        cls.rec = json.loads(RECORD.read_text())
        cls.atlas = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
        cls.F = it.frames(cls.rec)
        cls.specs = it.specs(cls.rec, cls.atlas)

    def pose(self, t, cmd, derive=True):
        """World 4x4 of every moved bone, composing ancestor deltas as Blender does."""
        it = self.it
        cmd = it.derive(t, cmd) if derive else dict(cmd)
        G = it.deltas(t, cmd, self.F)
        bones = self.rec['bones']
        def world(b):
            M, cur, chain = np.eye(4), b, []
            while cur is not None:
                chain.append(cur)
                cur = bones[cur]['parent']
            for a in reversed(chain):
                M = M @ G.get(a, np.eye(4))
            return M
        return world

    def check(self, t):
        it, B, side = self.it, self.rec['bones'], t['side']
        ant, up = np.array([0, -1.0, 0]), np.array([0, 0, 1.0])
        lat = np.array([1.0 if side == 'left' else -1.0, 0, 0]); med = -lat
        right = np.array([-1.0, 0, 0])
        tid, prim = t['id'], t['primary']
        peak = max(t['keys'], key=lambda k: k.get(prim, 0.0))
        trough = min(t['keys'], key=lambda k: k.get(prim, 0.0))
        def moved(cmd, bone, pt='tail'):
            w = self.pose(t, cmd)(bone)
            p = np.append(B[bone][pt + '_m'], 1.0)
            return (w @ p)[:3] - p[:3]
        def vec(cmd, bone, v):
            return self.pose(t, cmd)(bone)[:3, :3] @ np.asarray(v, float)
        hand = self.F.get(f'capitate_{side}')
        if hand is not None:
            palmar = hand[:, 0]
            radial = hand[:, 2] * (1.0 if side == 'right' else -1.0)
        # ---- Phase 9 supplementary specs (anatomical definitions, written independently of the solver's sign probes)
        if tid.startswith('c0_c1'):
            inc = np.append(B['mandible']['tail_m'], 1.0)
            dz = lambda c: (self.pose(t, c)('mandible') @ inc)[2] - inc[2]
            return dz(peak) < -0.003 and dz(trough) > 0.003          # flexion (nodding) lowers the chin; extension raises it
        if tid.startswith('rib_'):
            return moved(peak, t['moving'][0])[2] > 0.005            # inspiration: the anterior end rises (about 12 mm expected)
        if '_mcp_abduction' in tid:
            d = int(tid[5])
            away = radial if d == 2 else -radial                     # index spreads radially; ring and little ulnarly
            return moved(peak, f'digit{d}_proximal_phalanx_{side}') @ away > 0.01    # about 15-20 mm expected
        if tid.startswith('thumb_opposition'):
            mc1 = B[f'metacarpal_1_{side}']
            d0 = np.asarray(mc1['tail_m']) - np.asarray(mc1['head_m']); d0 /= np.linalg.norm(d0)
            pulp = -radial - (-radial @ d0) * d0; pulp /= np.linalg.norm(pulp)
            top = max(t['keys'], key=lambda k: (k['abduction'], k['pronation']))
            tip = np.append(t['thumb_tip'], 1.0)
            def facing(cmd):          # pulp normal against the direction from the thumb tip to the little-finger MCP
                W = self.pose(t, cmd)(f'metacarpal_1_{side}')
                to5 = np.asarray(t['opposition_target']) - (W @ tip)[:3]
                return (W[:3, :3] @ pulp) @ (to5 / np.linalg.norm(to5))
            return moved(top, f'metacarpal_1_{side}') @ palmar > 0.003 and facing(top) > facing(dict(top, pronation=0.0)) + 0.01
        if tid.startswith('knee_flexion_with_patellar'):
            pole = moved(peak, f'patella_{side}')                  # inferior pole (bone tail) rides down the trochlea in flexion
            return moved(peak, f'tibia_{side}') @ ant < -0.1 and pole[2] < -0.01 and pole @ ant < -0.005
        if tid.startswith('talocrural_with_fibular'):
            G = self.pose(t, peak)(f'fibula_{side}')
            return vec(peak, f'talus_{side}', ant)[2] > 0.2 and G[:3, 3] @ lat > 0.0004 and G[:3, 3] @ (-ant) > 0.0004   # DF: mortise widens, fibula back (0.52 mm each)
        if tid.startswith('hip_flexion'):
            return moved(peak, f'femur_{side}') @ ant > 0.05 and moved(trough, f'femur_{side}') @ ant < -0.01
        if tid.startswith('hip_abduction'):
            return moved(peak, f'femur_{side}') @ med > 0.05 and moved(trough, f'femur_{side}') @ lat > 0.05
        if tid.startswith('hip_rotation_at_0'):
            return vec(peak, f'femur_{side}', ant) @ med > 0.3
        if tid.startswith('hip_rotation_at_90'):
            base = dict(peak, internal=0.0)
            return (vec(peak, f'femur_{side}', ant) - vec(base, f'femur_{side}', ant)) @ med > 0.3
        if tid.startswith('knee_flexion_with_screw_home'):
            # coupled follower: the tibia rotates internally as the knee flexes out of terminal extension
            cmd = it.derive(t, {'flexion': 20.0})
            tib_ant = lambda c: self.pose(t, c, derive=False)(f'tibia_{side}')[:3, :3] @ ant
            return cmd['internal'] > 3.0 and moved(peak, f'tibia_{side}') @ ant < -0.1 \
                and (tib_ant(cmd) - tib_ant(dict(cmd, internal=0.0))) @ med > 0.03
        if tid.startswith('knee_flexion'):
            return moved(peak, f'tibia_{side}') @ ant < -0.1
        if tid.startswith('talocrural'):
            return vec(peak, f'talus_{side}', ant)[2] > 0.2 and vec(trough, f'talus_{side}', ant)[2] < -0.2
        if tid.startswith('subtalar'):
            return vec(peak, f'calcaneus_{side}', -up) @ med > 0.1
        if tid.startswith('gh_elevation_plane_0'):
            d = moved(peak, f'humerus_{side}'); return d @ lat > 0.1 and d[2] > 0.1
        if tid.startswith('gh_elevation_plane_40'):
            d = moved(peak, f'humerus_{side}'); return d @ lat > 0.05 and d @ ant > 0.05 and d[2] > 0.1
        if tid.startswith('gh_elevation_plane_90'):
            d = moved(peak, f'humerus_{side}'); return d @ ant > 0.1 and abs(d @ lat) < 0.02
        if tid.startswith('gh_axial_rotation_at_0'):
            return vec(peak, f'humerus_{side}', ant) @ med > 0.3
        if tid.startswith('gh_axial_rotation_at_90'):
            base = dict(peak, internal=0.0)
            return (vec(peak, f'humerus_{side}', ant) - vec(base, f'humerus_{side}', ant)) @ (-up) > 0.3
        if tid.startswith('elbow_flexion'):
            return moved(peak, f'ulna_{side}') @ ant > 0.15
        if tid.startswith('forearm_rotation'):
            base = dict(peak, pronation=0.0)
            return (vec(peak, f'radius_{side}', self.F[f'scaphoid_{side}'][:, 0]) - vec(base, f'radius_{side}', self.F[f'scaphoid_{side}'][:, 0])) @ (-ant if not peak.get('angle') else -up) > 0.3
        if tid.startswith('wrist_flexion'):
            return moved(peak, f'capitate_{side}') @ palmar > 0.003
        if tid.startswith('wrist_adduction'):
            return moved(peak, f'capitate_{side}') @ (-radial) > 0.003
        if tid.startswith('digit'):
            d = int(tid[5]); return moved(peak, f'digit{d}_distal_phalanx_{side}') @ palmar > 0.01
        if tid.startswith('thumb_flexion'):
            return moved(peak, f'thumb_distal_phalanx_{side}') @ (-radial) > 0.005
        if tid.startswith('thumb_cmc_radial'):
            return moved(peak, f'metacarpal_1_{side}') @ radial > 0.003
        if tid.startswith('thumb_cmc_ante'):
            return moved(peak, f'metacarpal_1_{side}') @ palmar > 0.003
        if tid.startswith('hallux'):
            return moved(peak, f'hallux_proximal_phalanx_{side}')[2] > 0.005
        if tid.startswith('sacroiliac'):
            return moved(peak, f'hip_bone_{side}')[2] > 0.0005
        if tid.startswith('c1_c2'):
            return vec(peak, 'c1', ant)[0] > 0.3
        if tid.startswith(('cervical', 'thoracic', 'lumbar')):
            b = t['moving'][0]
            if tid.endswith('_flexion'):
                return moved(peak, b) @ ant > 0.0003 and moved(trough, b) @ ant < -0.0003
            if tid.endswith('_extension'):
                return moved(trough, b) @ ant < -0.0003
            if tid.endswith('_adduction'):
                return moved(peak, b) @ right > 0.0003
            if tid.endswith('_internal'):          # axial rotation to the left: the anterior surface turns to +X (amplitude-relative)
                return vec(peak, b, ant)[0] > 0.5 * np.sin(np.radians(peak['internal']))
        if tid == 'tmj_opening':
            inc = np.append(t['incisor'], 1.0)
            return (self.pose(t, peak)('mandible') @ inc)[2] - inc[2] < -0.01
        if tid.startswith('shoulder_complex'):
            hum = moved(peak, f'humerus_{side}')
            ai = np.append(t['landmarks']['AI'], 1.0)
            ai_d = (self.pose(t, peak)(f'scapula_{side}') @ ai)[:3] - ai[:3]
            c = it.derive(t, peak)
            if not all(c[k] > 0 for k in ('upward', 'tilt', 'scap_er', 'clav_post', 'clav_ret')):
                return False
            raw = lambda cmd, bone: self.pose(t, cmd, derive=False)(bone)
            L = {k: np.append(v, 1.0) for k, v in t['landmarks'].items()}
            ai_tilt = (raw({'tilt': 30.0}, f'scapula_{side}') @ L['AI'])[:3] - L['AI'][:3]     # posterior tilt: inferior angle forward
            aa = L['AA'] + np.append(0.05 * lat, 0.0)
            aa_er = (raw({'scap_er': 24.0}, f'scapula_{side}') @ aa)[:3] - aa[:3]              # external rotation: lateral end posterior
            clav_ant = raw({'clav_post': 31.0}, f'clavicle_{side}')[:3, :3] @ ant                 # posterior rotation: anterior surface up
            ac_ret = (raw({'clav_ret': 15.0}, f'clavicle_{side}') @ L['AC'])[:3] - L['AC'][:3]  # retraction: lateral end posterior
            return hum[2] > 0.3 and ai_d @ lat > 0.03 and ai_tilt @ ant > 0.01 and aa_er @ ant < -0.01 \
                and clav_ant[2] > 0.3 and ac_ret @ ant < -0.01
        return None

    def test_every_spec_moves_in_its_named_direction(self):
        missing, wrong = [], []
        for t in self.specs:
            r = self.check(t)
            if r is None:
                missing.append(t['id'])
            elif not r:
                wrong.append(t['id'])
        self.assertEqual(missing, [], 'Specs without a world-space direction assertion')
        self.assertEqual(wrong, [], 'Specs moving opposite to their anatomical label')

    def test_paired_specs_are_exact_mirrors_in_the_solver(self):
        Mx = np.diag([-1.0, 1.0, 1.0, 1.0])
        by = {t['id']: t for t in self.specs}
        for tid, t in by.items():
            if not tid.endswith('_left') or tid[:-5] + '_right' not in by:
                continue
            r = by[tid[:-5] + '_right']
            for cmd in t['keys']:
                GL = self.it.deltas(t, self.it.derive(t, cmd), self.F)
                GR = self.it.deltas(r, self.it.derive(r, cmd), self.F)
                for b, g in GL.items():
                    rb = b[:-5] + '_right' if b.endswith('_left') else b
                    self.assertLess(np.linalg.norm(Mx @ g @ Mx - GR[rb]), 2e-3, f'{tid} {b} {cmd}')

    def test_wrist_half_rotation_is_exact(self):
        import joint_solver as js
        R = js.zxy_matrix(30, 15, -10)
        H = self.it.half_rotation(R)
        self.assertTrue(np.allclose(H @ H, R, atol=1e-12))


@unittest.skipIf(np is None, 'numpy unavailable')
class ProportionEvidenceTests(unittest.TestCase):
    """F-PROP-001 / F-GH-001 / F-HJC-001 evidence is bound to committed data and stays honest."""
    REPORT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/proportion_audit_001/proportion_report.json'
    ANSUR = ROOT / 'ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv'

    @classmethod
    def setUpClass(cls):
        import hashlib
        cls.r = json.loads(cls.REPORT.read_text())
        cls.ansur_sha = hashlib.sha256(cls.ANSUR.read_bytes()).hexdigest()

    def test_report_is_bound_to_the_committed_ansur_file_and_published_values(self):
        import csv
        self.assertEqual(self.r['sources']['ANSUR_II_MALE']['file_sha256'], self.ansur_sha)
        rows = list(csv.DictReader(open(self.ANSUR, encoding='cp1252')))
        self.assertEqual(len(rows), 4082)
        rsl = np.array([float(r['radialestylionlength']) for r in rows])
        self.assertAlmostEqual(rsl.mean(), 267.9, delta=0.1)          # published male mean
        self.assertAlmostEqual(rsl.std(ddof=1), 15.4, delta=0.1)

    def test_stature_equation_chain_is_biased_on_real_men(self):
        c = self.r['stature_equation_chain_on_ansur']
        for bone in ('femur', 'humerus'):
            self.assertLess(c[bone]['ansur_mean_bias_cm'], -5.0, bone)
            self.assertGreater(c[bone]['fraction_of_ansur_beyond_minus_2se'], 0.4, bone)
            self.assertTrue(2.5 <= c[bone]['character_percentile_in_ansur_chain'] <= 97.5, bone)
        self.assertLess(c['radius']['character_percentile_in_ansur_chain'], 2.5, 'forearm shortness must stay visible')

    def test_fitted_joint_centres_agree_with_ansur_landmarks(self):
        j = self.r['joint_centres_vs_ansur_landmarks']
        self.assertLess(abs(j['HJC']['difference_m']), j['HJC']['trochanterion_residual_sd_m'])
        self.assertLess(abs(j['KJC']['difference_m']), j['KJC']['residual_sd_m'])
        self.assertLess(abs(j['upper_arm_surface_check']['difference_m']), j['upper_arm_surface_check']['arl_residual_sd_m'])
        depth = j['GH']['depth_below_acromion_skin_m']
        for v in (j['GH']['open_model_marker_offsets']['Arm26 (Holzbaur 2005 derived)']['acromion_marker_minus_gh_vertical_m'],
                  j['GH']['open_model_marker_offsets']['Rajagopal2016 (1.70 m generic)']['scaled_to_character_m']):
            self.assertLess(abs(v - depth), 0.012)

    def test_character_specific_proportions_are_reported_not_hidden(self):
        s = self.r['surface_vs_ansur']
        self.assertLess(s['acromion_to_dactylion (ARL+RSL+hand)']['z'], -2.0)
        self.assertGreater(s['foot_length']['z'], 2.0)


@unittest.skipIf(np is None, 'numpy unavailable')
class SupplementarySourceBindingTests(unittest.TestCase):
    """New Phase 9 amplitudes and follower magnitudes are taken from the recorded sources, not typed in."""
    @classmethod
    def setUpClass(cls):
        import isolated_tests as it
        cls.sup = json.loads(it.SUPPLEMENT.read_text())
        rec = json.loads(RECORD.read_text())
        atlas = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
        cls.T = {t['id']: t for t in it.specs(rec, atlas)}

    def test_amplitudes_and_followers_match_their_sources(self):
        O = self.sup['observations']
        c0 = self.T['c0_c1_flexion_extension']['keys']
        self.assertAlmostEqual(max(k['angle'] for k in c0) - min(k['angle'] for k in c0), O['c0c1_fe_total']['value']['mean'])
        for lv in ('c3_c4', 'c4_c5', 'c5_c6', 'c6_c7'):
            k = self.T[f'cervical_{lv}_flexion']['keys']
            self.assertAlmostEqual(max(x['flexion'] for x in k), O[f'cervical_ctrl_{lv}_flexion']['value']['mean'])
            self.assertAlmostEqual(-min(x['flexion'] for x in k), O[f'cervical_ctrl_{lv}_extension']['value']['mean'])
        self.assertEqual(self.T['knee_flexion_with_patellar_follower_left']['follower']['ratio'], O['patellar_flexion_ratio']['value']['ratio'])
        arc = O['fibula_ankle_rsa']['value']['arc_deg']
        k = self.T['talocrural_with_fibular_follower_left']['keys']
        self.assertEqual([min(x['angle'] for x in k), max(x['angle'] for x in k)], arc)
        per = np.asarray(self.T['talocrural_with_fibular_follower_left']['follower']['per_degree_m']) * (arc[1] - arc[0]) * 1000
        self.assertAlmostEqual(abs(per[0]), O['fibula_ankle_rsa']['value']['mortise_widening_mm'])
        self.assertAlmostEqual(per[1], O['fibula_ankle_rsa']['value']['posterior_translation_mm'])
        self.assertAlmostEqual(per[2], 0.0)
        import isolated_tests as it
        for side in ('left', 'right'):            # opposition never exceeds the clinical anteposition maximum
            t = self.T[f'thumb_opposition_{side}']
            im = t['intermetacarpal']
            a = max(k['abduction'] for k in t['keys'])
            mc = json.loads(RECORD.read_text())['bones'][f'metacarpal_1_{side}']
            d0 = np.asarray(mc['tail_m']) - np.asarray(mc['head_m']); d0 /= np.linalg.norm(d0)
            peak = it.intermetacarpal_angle(it.rodrigues(t['abduction_axis'], a) @ d0, np.asarray(im['mc2_dir']), np.asarray(im['plane_normal']))
            self.assertAlmostEqual(peak, im['target_deg'], places=6)
            self.assertEqual(im['target_deg'], 61.2)

    def test_unresolved_items_stay_untested(self):
        self.assertNotIn('lumbar_l1_l2_extension', self.T)
        self.assertFalse([t for t in self.T if t.startswith(('rib_08', 'rib_09', 'rib_10', 'rib_11', 'rib_12'))])
        for key in ('l1_l2', 'sc_elevation', 'thumb_pronation_magnitude', 'patellar_translation_path'):
            self.assertIn(key, self.sup['unresolved'])
