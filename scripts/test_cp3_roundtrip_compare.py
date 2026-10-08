import copy, importlib.util, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
spec = importlib.util.spec_from_file_location('rt', ROOT / 'scripts/anatomy_fit/cp3_roundtrip_compare.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import joint_markers as jm  # noqa: E402

REC = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json').read_text())


def fake_capture(rec):
    """What a perfect Blender build would return: float32-rounded coordinates and the intended bone Z."""
    f32 = lambda v: [float(np.float32(x)) for x in v]
    bones = {}
    for k, b in rec['bones'].items():
        h, t = np.array(b['head_m']), np.array(b['tail_m']); y = (t - h) / np.linalg.norm(t - h)
        R = jm.bone_frame(h, t); x = R[:, 0] if np.linalg.norm(np.cross(R[:, 0], y)) > 1e-9 else R[:, 1]
        p = x - (x @ y) * y; z = p / np.linalg.norm(p)
        bones[k] = {'head_m': f32(h), 'tail_m': f32(t), 'parent': b['parent'], 'parent_relation': b['parent_relation'], 'bone_z_axis': list(z)}
    markers = {k: {'centre_m': f32(v['centre_m']), 'frame_axes_columns_XYZ': [f32(r) for r in v['frame_axes_columns_XYZ']],
                   'frame_bone': v['frame_bone']} for k, v in rec['joint_markers'].items()}
    return {'bones': bones, 'joint_markers': markers}


class RoundTrip(unittest.TestCase):
    def test_nonfinite_geometry_cannot_hide_in_max_reduction(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            for section, key, field in [('bones', 'femur_left', 'tail_m'),
                                        ('bones', 'radius_left', 'bone_z_axis'),
                                        ('joint_markers', 'tibiofemoral_left', 'centre_m')]:
                with self.subTest(section=section, field=field, value=value):
                    c = fake_capture(REC); c[section][key][field][0] = value
                    self.assertFalse(m.compare(REC, c)['roundtrip_pass'])
            c = fake_capture(REC)
            c['joint_markers']['tibiofemoral_left']['frame_axes_columns_XYZ'][1][2] = value
            self.assertFalse(m.compare(REC, c)['roundtrip_pass'])

    def test_missing_empty_or_malformed_capture_returns_rejection(self):
        for mutate in (lambda c: c['bones'].pop('radius_left'),
                       lambda c: c.__setitem__('bones', {}),
                       lambda c: c.__setitem__('joint_markers', {}),
                       lambda c: c['bones']['femur_left'].__setitem__('tail_m', [1, 2]),
                       lambda c: c['joint_markers']['tibiofemoral_left'].__setitem__('frame_axes_columns_XYZ', [[1, 2]]),
                       lambda c: c['bones']['radius_left'].__setitem__('bone_z_axis', [0, 0, 0]),
                       lambda c: c['bones']['radius_left'].__setitem__('bone_z_axis', [100, 0, 0]),
                       lambda c: c['bones']['femur_left'].__setitem__('head_m', [True, 0, 0])):
            c = fake_capture(REC); mutate(c)
            r = m.compare(REC, c)
            self.assertFalse(r['roundtrip_pass'])
            self.assertTrue(r['input_errors'])
        for c in (None, [], {'bones': None}, {'bones': {}, 'joint_markers': []}):
            self.assertFalse(m.compare(REC, c)['roundtrip_pass'])

    def test_marker_frame_carrier_is_part_of_roundtrip_identity(self):
        c = fake_capture(REC)
        c['joint_markers']['tibiofemoral_left']['frame_bone'] = 'ulna_left'
        r = m.compare(REC, c)
        self.assertFalse(r['roundtrip_pass'])
        self.assertIn('tibiofemoral_left', r['marker_frame_bone_mismatches'])

    def test_degenerate_or_nonfinite_reference_rejects_before_frame_math(self):
        c = fake_capture(REC)
        for mutate in (lambda r: r['bones']['femur_left'].__setitem__('tail_m', r['bones']['femur_left']['head_m']),
                       lambda r: r['bones']['femur_left']['head_m'].__setitem__(0, float('nan'))):
            rec = copy.deepcopy(REC); mutate(rec)
            self.assertFalse(m.compare(rec, c)['roundtrip_pass'])
        rec = copy.deepcopy(REC); c = fake_capture(rec)
        rec['bones']['femur_left']['tail_m'][0] = 1e160
        c['bones']['femur_left']['tail_m'][0] = 1e160
        self.assertFalse(m.compare(rec, c)['roundtrip_pass'])

    def test_cli_rejects_missing_bone_with_machine_readable_report(self):
        import subprocess, tempfile
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp); c = fake_capture(REC); c['bones'].pop('radius_left')
            (base / 'capture.json').write_text(json.dumps(c))
            report = base / 'report.json'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/anatomy_fit/cp3_roundtrip_compare.py'),
                                     '--record', str(ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json'),
                                     '--capture', str(base / 'capture.json'), '--out', str(report)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)
            data = json.loads(report.read_text())
            self.assertFalse(data['roundtrip']['roundtrip_pass'])
            self.assertEqual(data['cp2_preflight_on_capture']['verdict'], 'FAIL')

    def test_float32_capture_passes(self):
        r = m.compare(REC, fake_capture(REC))
        self.assertTrue(r['roundtrip_pass'])
        self.assertLess(r['max_roll_error_deg'], 1e-6)
        self.assertEqual(r['bones_needing_superior_roll_reference']['count'], 74)

    def test_roll_rule_mirrors_exactly_on_a_mirrored_skeleton(self):
        rec = copy.deepcopy(REC)
        for k in rec['bones']:
            if k.endswith('_left') or '_left_' in k:
                o = k.replace('_left', '_right')
                for e in ('head_m', 'tail_m'):
                    rec['bones'][o][e] = [-rec['bones'][k][e][0], *rec['bones'][k][e][1:]]
        r = m.compare(rec, fake_capture(rec))
        self.assertLess(r['max_bilateral_roll_mirror_error_deg'], 1e-3)
        self.assertGreater(m.compare(REC, fake_capture(REC))['max_bilateral_roll_mirror_error_deg'], 0)   # a003 itself is not exactly mirrored

    def test_moved_bone_reparent_and_lost_marker_fail(self):
        for mutate in (lambda c: c['bones']['femur_left']['tail_m'].__setitem__(2, c['bones']['femur_left']['tail_m'][2] + 1e-4),
                       lambda c: c['bones']['radius_left'].__setitem__('parent', 'ulna_left'),
                       lambda c: c['joint_markers'].pop('tibiofemoral_right'),
                       lambda c: c['joint_markers']['tibiofemoral_left']['centre_m'].__setitem__(0, 0.0)):
            c = fake_capture(REC); mutate(c)
            self.assertFalse(m.compare(REC, c)['roundtrip_pass'])


if __name__ == '__main__':
    unittest.main()
