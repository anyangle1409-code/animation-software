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
        x = jm.bone_frame(h, t)[:, 0]; p = x - (x @ y) * y
        z = p / np.linalg.norm(p) if np.linalg.norm(p) > 1e-6 else np.cross(y, [1.0, 0, 0])
        bones[k] = {'head_m': f32(h), 'tail_m': f32(t), 'parent': b['parent'], 'parent_relation': b['parent_relation'], 'bone_z_axis': list(z)}
    markers = {k: {'centre_m': f32(v['centre_m']), 'frame_axes_columns_XYZ': [f32(r) for r in v['frame_axes_columns_XYZ']],
                   'frame_bone': v['frame_bone']} for k, v in rec['joint_markers'].items()}
    return {'bones': bones, 'joint_markers': markers}


class RoundTrip(unittest.TestCase):
    def test_float32_capture_passes(self):
        r = m.compare(REC, fake_capture(REC))
        self.assertTrue(r['roundtrip_pass'])
        self.assertLess(r['max_roll_error_deg'], 1e-6)
        self.assertEqual(r['roll_target_parallel_to_bone']['count'], 74)

    def test_moved_bone_reparent_and_lost_marker_fail(self):
        for mutate in (lambda c: c['bones']['femur_left']['tail_m'].__setitem__(2, c['bones']['femur_left']['tail_m'][2] + 1e-4),
                       lambda c: c['bones']['radius_left'].__setitem__('parent', 'ulna_left'),
                       lambda c: c['joint_markers'].pop('tibiofemoral_right'),
                       lambda c: c['joint_markers']['tibiofemoral_left']['centre_m'].__setitem__(0, 0.0)):
            c = fake_capture(REC); mutate(c)
            self.assertFalse(m.compare(REC, c)['roundtrip_pass'])


if __name__ == '__main__':
    unittest.main()
