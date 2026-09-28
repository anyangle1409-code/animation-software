import unittest

from original_o2_mesh_checks import inspect_mesh


class MeshChecksTests(unittest.TestCase):
    def test_closed_symmetric_tetrahedron(self):
        vertices = [(0, 0, 0), (-1, 0, 1), (1, 0, 1), (0, 1, 1)]
        faces = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)]
        result = inspect_mesh(vertices, faces, symmetry_tolerance=.001)
        self.assertEqual(result['boundary_edges'], 0)
        self.assertEqual(result['nonmanifold_edges'], 0)
        self.assertEqual(result['degenerate_faces'], 0)
        self.assertEqual(result['unmatched_mirror_vertices'], 0)

    def test_open_asymmetric_mesh_reports_failures(self):
        result = inspect_mesh([(0, 0, 0), (-1, 0, 0), (0, 0, 1)], [(0, 1, 2)])
        self.assertEqual(result['boundary_edges'], 3)
        self.assertEqual(result['unmatched_mirror_vertices'], 1)

    def test_degenerate_and_duplicate_faces(self):
        result = inspect_mesh([(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 2), (2, 1, 0)])
        self.assertEqual(result['degenerate_faces'], 2)
        self.assertEqual(result['duplicate_faces'], 1)


if __name__ == '__main__':
    unittest.main()
