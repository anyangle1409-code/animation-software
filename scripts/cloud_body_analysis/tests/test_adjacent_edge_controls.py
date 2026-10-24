"""Topology-selected controls are synthetic software QA, never anatomy."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[2] / 'phone_blender/corrective_edge_isolation.py'
spec = importlib.util.spec_from_file_location('edge_controls', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AdjacentEdgeControlTests(unittest.TestCase):
    def setUp(self):
        self.faces = [(0, 1, 2), (1, 0, 3), (3, 4, 5)]

    def test_only_edges_of_incident_seed_triangles_selected(self):
        self.assertTrue(hasattr(mod, 'adjacent_controls'), 'adjacent controls missing')
        report = mod.adjacent_controls(self.faces, seeds=((0, 1),))
        self.assertEqual(report, [{'seed_vertex_ids': [0, 1], 'incident_triangle_count': 2,
                                  'control_edges': [[0, 2], [0, 3], [1, 2], [1, 3]]}])

    def test_invariant_to_face_order_winding_and_seed_direction(self):
        a = mod.adjacent_controls(self.faces, seeds=((0, 1),))
        b = mod.adjacent_controls([tuple(reversed(f)) for f in reversed(self.faces)], seeds=((1, 0),))
        self.assertEqual(a, b)

    def test_missing_seed_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'missing seed'):
            mod.adjacent_controls(self.faces, seeds=((8, 9),))

    def test_duplicate_seed_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate seed'):
            mod.adjacent_controls(self.faces, seeds=((0, 1), (1, 0)))

    def test_degenerate_or_duplicate_triangle_rejected(self):
        for faces in ([(0, 1, 1)], [(0, 1, 2), (2, 1, 0)]):
            with self.subTest(faces=faces), self.assertRaisesRegex(ValueError, 'triangle'):
                mod.adjacent_controls(faces, seeds=((0, 1),))

    def test_seed_edges_never_counted_as_adjacent_controls(self):
        result = mod.adjacent_controls([(0, 1, 2)], seeds=((0, 1), (1, 2)))
        self.assertEqual(result[0]['control_edges'], [[0, 2]])
        self.assertEqual(result[1]['control_edges'], [[0, 2]])


if __name__ == '__main__':
    unittest.main()
