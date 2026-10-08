import copy, importlib.util, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
spec = importlib.util.spec_from_file_location('ax', ROOT / 'scripts/anatomy_fit/bodyparts3d_axial_shoulder.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
spec2 = importlib.util.spec_from_file_location('cp2', ROOT / 'scripts/anatomy_fit/cp2_preflight.py')
cp2 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(cp2)
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
REPORT = json.loads((ANAT / 'bodyparts3d_single_specimen_axial_shoulder_v1.json').read_text())


def slab(h=6.0, R=20.0, k=48):
    """Closed flat cylinder (a synthetic disc) centred at the origin, axis +Z."""
    v = [[R * math.cos(2 * math.pi * i / k), R * math.sin(2 * math.pi * i / k), z] for z in (-h / 2, h / 2) for i in range(k)]
    v += [[0, 0, -h / 2], [0, 0, h / 2]]
    f = []
    for i in range(k):
        j = (i + 1) % k
        f += [[i, j, k + i], [j, k + j, k + i], [2 * k, j, i], [2 * k + 1, k + i, k + j]]
    return np.array(v, float), np.array(f)


class Geometry(unittest.TestCase):
    def test_ray_hits_through_slab(self):
        v, f = slab()
        t = m.ray_hits(np.array([3.0, -2.0, 0.0]), np.array([0, 0, 1.0]), v, f)
        self.assertAlmostEqual(t.max() - t.min(), 6.0, places=9)
        self.assertEqual(len(m.ray_hits(np.array([30.0, 0, 0]), np.array([0, 0, 1.0]), v, f)), 0)

    def test_disc_frame_normal_is_superior_and_anterior_is_minus_y(self):
        v, f = slab()
        c, n, ant, lat, half = m.disc_frame(v)
        self.assertTrue(np.allclose(n, [0, 0, 1], atol=1e-9))
        self.assertTrue(np.allclose(ant, [0, -1, 0], atol=1e-9))
        self.assertAlmostEqual(half[0], 20.0, delta=0.1)


class CommittedReport(unittest.TestCase):
    def test_status_and_coverage(self):
        self.assertEqual(REPORT['status'], 'SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET')
        self.assertIn('Never freeze', REPORT['evidence_grade_note'])
        self.assertEqual(len(REPORT['spine']), 23)
        self.assertEqual(set(REPORT['disc_surfaces_for_cp2_preflight']), set(cp2.SPINAL_DISCS))
        self.assertTrue(REPORT['hyoid']['duplicate_entries_identical'])

    def test_every_level_has_real_disc_space(self):
        for k, row in REPORT['spine'].items():
            self.assertGreater(row['centre']['bone_to_bone_gap_mm'], 0, k)
            self.assertGreater(row['clearance_minimum_projected_gap_mm'], 0, k)

    def test_specimen_endplates_pass_through_cp2_clearance(self):
        inv, arts, add = cp2.load_reference()
        cand = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
        cand = copy.deepcopy(cand)
        cand['disc_surfaces'] = REPORT['disc_surfaces_for_cp2_preflight']
        res = cp2.check_candidate(cand, inv, arts, add)
        c = next(x for x in res['checks'] if x['id'] == 'disc_endplate_clearance')
        self.assertEqual(c['status'], 'PASS')
        self.assertEqual(len(c['measurements']), 23)
        # the bone sticks are still a003's, so the centre-line check must keep failing: surfaces do not mask it
        self.assertEqual(next(x for x in res['checks'] if x['id'] == 'spinal_disc_centre_gap_positive')['status'], 'FAIL')

    def test_shoulder_sides_and_symmetry(self):
        sh = REPORT['shoulder']
        for side, sign in (('left', 1), ('right', -1)):
            for key in ('SC_proxy_mm', 'AC_proxy_mm', 'GH_glenoid_proxy_mm'):
                self.assertGreater(sign * sh[side]['contact_2mm'][key][0], 0)
        self.assertLess(abs(sh['left']['clavicle_max_vertex_chord_mm'] - sh['right']['clavicle_max_vertex_chord_mm']), 5)
        self.assertGreater(sh['bilateral_AC_proxy_separation_2mm'], sh['bilateral_SC_proxy_separation_2mm'])


if __name__ == '__main__':
    unittest.main()
