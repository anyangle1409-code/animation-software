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


if __name__ == '__main__':
    unittest.main()
