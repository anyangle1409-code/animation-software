"""Synthetic software guards for temporary native-key isolation, not anatomy."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

PATH = Path(__file__).resolve().parents[2] / 'phone_blender' / 'corrective_edge_isolation.py'


class CorrectiveIsolationTests(unittest.TestCase):
    def setUp(self):
        if not PATH.exists():
            self.fail('native corrective edge isolation module not implemented')
        spec = importlib.util.spec_from_file_location('isolation', PATH)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.keys = [NS(name='Basis', value=0, mute=False),
                     NS(name='HGPT_S7_DELT_l_145', value=0.5, mute=False),
                     NS(name='HGPT_K1_ELBOW_l_90', value=0.25, mute=False),
                     NS(name='OTHER', value=1.0, mute=True)]
        self.body = NS(data=NS(shape_keys=NS(key_blocks=self.keys)))
        self.faces = [(0, 1, 2)]
        self.rest = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        self.calls = 0
        self.pose = (1, 2, 3)

    def evaluate(self):
        self.calls += 1
        length = 1 + sum(k.value for k in self.keys[1:] if not k.mute)
        return [(0, 0, 0), (length, 0, 0), (0, 1, 0)], self.faces

    def run_probe(self, evaluate=None):
        baseline, faces = self.evaluate()
        return self.mod.measure(self.body, evaluate or self.evaluate, lambda: None,
                                lambda: self.pose, self.rest, baseline, faces,
                                edges=((0, 1),))

    def test_fixed_pose_separates_observed_s7_k1_and_all_muted(self):
        report = self.run_probe()
        row = report['edges'][0]
        self.assertEqual(row['length_ratios_to_benchmark_rest_NOT_strain'],
                         {'observed': 1.75, 'S7_muted': 1.25,
                          'K1_muted': 1.5, 'S1_muted': 1.75,
                          'S3_muted': 1.75, 'S5_muted': 1.75,
                          'all_nonbasis_keys_muted': 1.0})
        self.assertFalse(report['anatomical_approval'])
        self.assertFalse(report['skinning_alone_certified'])
        self.assertTrue(report['pose_and_key_state_restored'])

    def test_preserves_existing_mutes_values_and_skeleton(self):
        before = [(k.value, k.mute) for k in self.keys]
        self.run_probe()
        self.assertEqual([(k.value, k.mute) for k in self.keys], before)
        self.assertEqual(self.pose, (1, 2, 3))

    def test_s1_s3_s5_controls_are_independent_and_restore_combined_keys(self):
        self.keys.extend([NS(name='HGPT_S1_SHOULDER_l_105', value=0.2, mute=False),
                          NS(name='HGPT_S3_SHAPE_l_100', value=0.3, mute=False),
                          NS(name='HGPT_S5_BAKE_l_110', value=0.4, mute=False)])
        report = self.run_probe()
        values = report['edges'][0]['length_ratios_to_benchmark_rest_NOT_strain']
        self.assertEqual(values['observed'], 2.65)
        self.assertEqual(values['S1_muted'], 2.45)
        self.assertEqual(values['S3_muted'], 2.35)
        self.assertEqual(values['S5_muted'], 2.25)
        self.assertTrue(all(not k.mute for k in self.keys[4:]))
        text = self.mod.markdown([{'sample': 0, 'corrective_edge_isolation': report}])
        self.assertIn('S3 muted', text)
        self.assertIn('2.350000', text)

    def test_restores_keys_on_evaluation_failure(self):
        before = [(k.value, k.mute) for k in self.keys]
        def broken():
            raise RuntimeError('simulated dependency graph failure')
        with self.assertRaisesRegex(RuntimeError, 'dependency graph'):
            self.run_probe(broken)
        self.assertEqual([(k.value, k.mute) for k in self.keys], before)

    def test_rejects_topology_change_and_restores(self):
        before = [k.mute for k in self.keys]
        def changed():
            v, _ = self.evaluate()
            return v, [(0, 2, 1)]
        with self.assertRaisesRegex(ValueError, 'topology'):
            self.run_probe(changed)
        self.assertEqual([k.mute for k in self.keys], before)

    def test_rejects_skeleton_change(self):
        def moved():
            self.pose = (9, 9, 9)
            return self.evaluate()
        with self.assertRaisesRegex(ValueError, 'skeletal pose'):
            self.run_probe(moved)
        self.assertFalse(self.keys[1].mute)

    def test_rejects_nonfinite_coordinates(self):
        def bad():
            v, f = self.evaluate()
            v[1] = (float('nan'), 0, 0)
            return v, f
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            self.run_probe(bad)

    def test_rejects_degenerate_rest_edge(self):
        self.rest[1] = self.rest[0]
        with self.assertRaisesRegex(ValueError, 'reference edge'):
            self.run_probe()

    def test_rejects_missing_pinned_endpoint(self):
        self.rest = self.rest[:1]
        with self.assertRaisesRegex(ValueError, 'vertex count|endpoint'):
            self.run_probe()

    def test_rejects_failed_coordinate_restoration(self):
        def drifted():
            v, f = self.evaluate()
            if not self.keys[1].mute and not self.keys[2].mute:
                v[1] = (2.0, 0, 0)
            return v, f
        with self.assertRaisesRegex(ValueError, 'restored coordinates'):
            self.run_probe(drifted)

    def test_no_save_or_rig_assignment(self):
        import ast
        tree = ast.parse(PATH.read_text())
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertFalse(any('save' in c or 'bpy.ops' in c or 'keyframe' in c for c in calls))

    def test_phone_report_keeps_native_and_anatomical_status_distinct(self):
        report = self.run_probe()
        text = self.mod.markdown([{'sample': 0, 'corrective_edge_isolation': report}])
        self.assertIn('1.750000', text)
        self.assertIn('NOT ANATOMICAL APPROVAL', text)
        self.assertIn('helpers', text)


if __name__ == '__main__':
    unittest.main()
