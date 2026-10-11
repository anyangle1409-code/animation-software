import importlib.util
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'anatomy_fit'))

class ThoraxShapes(unittest.TestCase):
    def module(self):
        path = Path(__file__).parent / 'anatomy_fit/functional_thorax_shapes.py'
        self.assertTrue(path.exists(), 'thorax shape helper missing')
        spec = importlib.util.spec_from_file_location('thorax', path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_rib_preserves_endpoints_and_authored_lateral_bow(self):
        m = self.module()
        p = m.rib_points((.02, .10, 1.5), (.04, -.10, 1.4), 'left', .12)
        self.assertEqual(p[0], (.02, .10, 1.5))
        self.assertEqual(p[-1], (.04, -.10, 1.4))
        self.assertAlmostEqual(p[20][0], .15)
        self.assertAlmostEqual(p[20][1], 0)
        self.assertAlmostEqual(p[20][2], 1.45)

    def test_right_rib_mirrors_without_reversing_anterior(self):
        m = self.module()
        a = m.rib_points((.02, .1, 1.5), (.04, -.1, 1.4), 'left', .12)
        b = m.rib_points((-.02, .1, 1.5), (-.04, -.1, 1.4), 'right', .12)
        for left, right in zip(a, b):
            self.assertAlmostEqual(left[0], -right[0])
            self.assertEqual(left[1:], right[1:])

    def test_invalid_bow_side_and_coordinates_refused(self):
        m = self.module()
        for side, bow in [('unknown', .1), ('left', True), ('left', 0), ('left', .5), ('left', float('nan'))]:
            with self.assertRaises(ValueError):
                m.rib_points((.02, .1, 1.5), (.04, -.1, 1.4), side, bow)
        with self.assertRaises(ValueError):
            m.rib_points((10**400, .1, 1.5), (.04, -.1, 1.4), 'left', .1)

if __name__ == '__main__':
    unittest.main()
