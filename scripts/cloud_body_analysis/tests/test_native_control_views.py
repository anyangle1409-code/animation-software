"""Synthetic layout guards; actual Blender render must pass cloud execution."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[2] / 'phone_blender/native_control_views.py'


class NativeControlViewTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.exists(), 'native control views not implemented')
        spec = importlib.util.spec_from_file_location('control_views', PATH)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.v = [(0, 0, 0), (1, 0.2, 0.5), (100, 100, 100)]

    def test_camera_uses_fixed_observed_focus_not_whole_body_outliers(self):
        plan = self.mod.camera_plan(self.v, (0, 1))
        self.assertEqual(plan['focus_world_m'], [0.5, 0.1, 0.25])
        self.assertAlmostEqual(plan['ortho_scale_m'], 1.45)
        self.assertEqual(set(plan['axis_views']), {'axis_negY', 'axis_posY', 'axis_posX'})

    def test_global_translation_preserves_scale_and_moves_camera(self):
        a = self.mod.camera_plan(self.v, (0, 1))
        b = self.mod.camera_plan([(x+5, y-2, z+9) for x,y,z in self.v], (0, 1))
        self.assertAlmostEqual(a['ortho_scale_m'], b['ortho_scale_m'])
        self.assertEqual(b['focus_world_m'], [5.5, -1.9, 9.25])

    def test_bad_or_missing_focus_rejected(self):
        for ids in ((), (0, 9)):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                self.mod.camera_plan(self.v, ids)
        self.v[1] = (float('nan'), 0, 0)
        with self.assertRaisesRegex(ValueError, 'finite'):
            self.mod.camera_plan(self.v, (0, 1))

    def test_renderer_never_opens_or_saves_source_model(self):
        import ast
        calls = [ast.unparse(n.func) for n in ast.walk(ast.parse(PATH.read_text()))
                 if isinstance(n, ast.Call)]
        self.assertFalse(any('open_mainfile' in c or 'save_as_mainfile' in c for c in calls))

    def test_replay_exposure_and_light_options_available_without_blender_import(self):
        import subprocess, sys
        result = subprocess.run([sys.executable, str(PATH), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--exposure', result.stdout)
        self.assertIn('--light-energy', result.stdout)

    def test_nonfinite_replay_settings_rejected_before_blender_import(self):
        import subprocess, sys
        result = subprocess.run([sys.executable, str(PATH), '--snapshots', '/unused',
                                 '--out', '/unused', '--exposure', 'nan'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('finite render settings', result.stderr)

    def test_individual_groups_are_narrow_and_deny_anatomical_side(self):
        self.assertTrue(hasattr(self.mod, 'individual_comparison_groups'))
        groups = self.mod.individual_comparison_groups()
        self.assertEqual([(g['sample'], g['family'], g['authored_suffix']) for g in groups],
                         [(0, 'S5', 'l'), (0, 'S5', 'r'),
                          (6, 'S7', 'l'), (6, 'S7', 'r')])
        self.assertTrue(all(g['authored_suffix_is_anatomical_side'] is False
                            for g in groups))
        self.assertEqual(groups[0]['conditions'], [
            'observed',
            'individual_key_muted::HGPT_S5_BAKE_l_85',
            'individual_key_muted::HGPT_S5_BAKE_l_110',
            'S5_muted',
        ])
        self.assertEqual(groups[2]['conditions'], [
            'observed',
            'individual_key_muted::HGPT_S7_DELT_l_145',
            'individual_key_muted::HGPT_S7_DELT_l_156',
            'S7_muted',
        ])

    def test_snapshot_filename_is_portable_and_selection_is_exact(self):
        self.assertTrue(hasattr(self.mod, 'snapshot_filename'))
        condition = 'individual_key_muted::HGPT_S5_BAKE_l_85'
        self.assertEqual(self.mod.snapshot_filename(0, condition),
                         'sample00__individual_key_muted--HGPT_S5_BAKE_l_85.npz')
        self.assertTrue(self.mod.selected_snapshot_condition(0, condition))
        self.assertFalse(self.mod.selected_snapshot_condition(
            6, 'individual_key_muted::HGPT_S5_BAKE_l_85'))
        with self.assertRaisesRegex(ValueError, 'condition'):
            self.mod.snapshot_filename(0, '../unsafe')

    def test_sheet_plan_keeps_six_baselines_and_adds_twelve_focused_views(self):
        self.assertTrue(hasattr(self.mod, 'comparison_sheet_specs'))
        specs = self.mod.comparison_sheet_specs(include_individual=True)
        self.assertEqual(len(specs), 18)
        self.assertEqual(len({s['file'] for s in specs}), 18)
        baseline = [s for s in specs if s['kind'] == 'family_baseline']
        focused = [s for s in specs if s['kind'] == 'individual_key_focus']
        self.assertEqual(len(baseline), 6)
        self.assertEqual(len(focused), 12)
        self.assertTrue(all(len(s['conditions']) == 4 for s in specs))
        self.assertTrue(all(s['authored_suffix_is_anatomical_side'] is False
                            for s in focused))

    def test_default_plan_remains_compatible_with_frozen_eight_snapshots(self):
        specs = self.mod.comparison_sheet_specs()
        self.assertEqual(len(specs), 6)
        self.assertTrue(all(s['kind'] == 'family_baseline' for s in specs))
        import subprocess, sys
        result = subprocess.run([sys.executable, str(PATH), '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--include-individual', result.stdout)


if __name__ == '__main__':
    unittest.main()
