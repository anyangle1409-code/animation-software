import importlib.util, json, math, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bp3d', ROOT / 'scripts/anatomy_fit/bodyparts3d_crosscheck.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
REPORT = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/bodyparts3d_single_specimen_crosscheck_v1.json').read_text())


def box(lo, hi, split_normals=False):
    """Closed axis-aligned box; with split_normals every face gets its own vertices (as in the packed atlas)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    c = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], float)
    quads = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 4, 7, 3]]
    if not split_normals:
        return c, np.array([[q[0], q[i], q[i + 1]] for q in quads for i in (1, 2)])
    v, f = [], []
    for q in quads:
        base = len(v); v.extend(c[q]); f += [[base, base + 1, base + 2], [base, base + 2, base + 3]]
    return np.array(v), np.array(f)


def tube_arc(R=100.0, r=5.0, sweep=math.pi, n=120, k=12):
    """Closed curved tube along a circular arc in the XY plane (centre at origin), capped at both ends."""
    v, f = [], []
    for i in range(n + 1):
        t = sweep * i / n
        c, tng = np.array([R * math.cos(t), R * math.sin(t), 0]), np.array([-math.sin(t), math.cos(t), 0])
        rad, up = np.array([math.cos(t), math.sin(t), 0]), np.array([0, 0, 1.0])
        for j in range(k):
            a = 2 * math.pi * j / k
            v.append(c + r * (math.cos(a) * rad + math.sin(a) * up))
    for i in range(n):
        for j in range(k):
            a, b = i * k + j, i * k + (j + 1) % k
            f += [[a, a + k, b], [b, a + k, b + k]]
    s, e = len(v), len(v) + 1
    v += [np.array([R, 0, 0]), np.array([R * math.cos(sweep), R * math.sin(sweep), 0])]
    for j in range(k):
        f += [[s, (j + 1) % k, j], [e, n * k + j, n * k + (j + 1) % k]]
    return np.array(v), np.array(f)


class Geometry(unittest.TestCase):
    def test_axis_change_is_a_proper_rotation(self):
        self.assertAlmostEqual(np.linalg.det(m.TO_HGPT), 1.0)
        self.assertTrue(np.allclose(m.TO_HGPT @ [0, 0, 1], [0, -1, 0]))   # atlas anterior +z -> HGPT anterior -Y
        self.assertTrue(np.allclose(m.TO_HGPT @ [0, 1, 0], [0, 0, 1]))    # atlas superior +y -> HGPT +Z

    def test_box_volume_centroid_extents_and_welding(self):
        for split in (False, True):
            s = m.shape(*box((1, 2, 3), (5, 4, 4), split))
            self.assertTrue(s['closed'])
            self.assertAlmostEqual(s['volume_mm3'], 8.0, places=9)
            self.assertTrue(np.allclose(s['centroid_mm'], [3, 3, 3.5]))
            self.assertTrue(np.allclose(sorted(s['extents_mm']), [1, 2, 4]))

    def test_open_mesh_is_reported(self):
        v, f = box((0, 0, 0), (1, 1, 1))
        self.assertFalse(m.shape(v, f[:-2])['closed'])

    def test_geodesic_centreline_of_curved_tube(self):
        v, f = tube_arc()
        c, mode = m.rib_curve(v, f)
        arc = np.linalg.norm(np.diff(c, axis=0), axis=1).sum()
        self.assertEqual(mode, 'geodesic')
        dev = np.abs(np.linalg.norm(c[:, :2], axis=1) - 100)
        self.assertTrue(np.all(dev[1:-1] < 0.5))                      # interior bins stay on the arc
        self.assertTrue(np.all(dev[[0, -1]] < 5.0))                   # end bins: biased by up to about the tube radius
        self.assertGreater(arc, 0.9 * math.pi * 100); self.assertLess(arc, math.pi * 100)


class CommittedReport(unittest.TestCase):
    def test_status_and_grade_never_a_target(self):
        self.assertEqual(REPORT['status'], 'SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET')
        self.assertIn('Never freeze', REPORT['evidence_grade_note'])
        self.assertIn('CC BY 4.0', REPORT['source']['license'])
        self.assertEqual(len(REPORT['source']['access_path'].split(' at ')[1].split(',')[0]), 40)

    def test_coverage_and_closure(self):
        for side in ('left', 'right'):
            self.assertEqual(set(REPORT['carpals'][side]), set(m.CARPALS))
            self.assertEqual(set(REPORT['tarsals'][side]), set(m.TARSALS))
            for b in (*REPORT['carpals'][side].values(), *REPORT['tarsals'][side].values()):
                self.assertTrue(b['closed_mesh'])
        self.assertEqual(len(REPORT['ribs']['per_rib']), 24)

    def test_sides_and_rib_orientation(self):
        for side, sign in (('left', 1), ('right', -1)):
            for group in ('carpals', 'tarsals'):
                for b in REPORT[group][side].values():
                    self.assertGreater(sign * b['centroid_mm'][0], 0)
        for k, rib in REPORT['ribs']['per_rib'].items():
            p, a = rib['posterior_end_mm'], rib['anterior_end_mm']
            self.assertLess(abs(p[0]), abs(a[0]) + 1e-9 if k.startswith('rib_12') else abs(a[0]))
            self.assertGreater(p[1], a[1] if not k.startswith('rib_12') else a[1] - 10)

    def test_crosscheck_numbers_recompute_from_stored_values(self):
        c = REPORT['crosschecks']
        for side in ('left', 'right'):
            b = REPORT['carpals'][side]
            cap = b['capitate']['principal_extents_mm'][0]
            d = math.dist(b['capitate']['centroid_mm'], b['triquetrum']['centroid_mm'])
            self.assertAlmostEqual(c[f'carpal_{side}']['canovas_capitate_triquetrum_pct']['specimen'], 100 * d / cap, delta=0.2)
            vols = {k: v['volume_mm3_approx'] for k, v in b.items()}
            self.assertEqual(c[f'carpal_{side}']['specimen_order_by_volume'], sorted(vols, key=lambda k: -vols[k]))
        for k, row in c['rib_span_vs_holcombe2017']['levels'].items():
            mean, sd = row['source_mean_sd_mm']
            for chord, z in zip(row['specimen_left_right_mm'], row['z_left_right']):
                self.assertAlmostEqual(z, (chord - mean) / sd, delta=0.01)


if __name__ == '__main__':
    unittest.main()
