import unittest

import numpy as np

from original_v1_axilla_edge_localization import dihedral_rows, edge_ratio_rows


class AxillaEdgeLocalizationTests(unittest.TestCase):
    def test_edge_rows_are_local_and_ranked_by_absolute_log_strain(self):
        rest = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [4.0, 0.0, 0.0],
        ])
        posed = rest.copy()
        posed[1] = [2.0, 0.0, 0.0]
        posed[2] = [0.0, 0.5, 0.0]
        edges = np.array([[0, 1], [0, 2], [1, 2], [1, 3]])
        rows = edge_ratio_rows(rest, posed, edges, np.array([True, True, True, False]))
        self.assertEqual([(row["vertices"], row["ratio"]) for row in rows], [([0, 1], 2.0), ([0, 2], 0.5), ([1, 2], 1.457738)])

    def test_dihedral_rows_report_new_fold_on_local_shared_edge(self):
        rest = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
        ])
        posed = rest.copy()
        posed[3, 2] = 1.0
        tris = np.array([[0, 1, 2], [1, 3, 2]])
        rows = dihedral_rows(rest, posed, tris, np.ones(4, dtype=bool))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["shared_edge"], [1, 2])
        self.assertAlmostEqual(rows[0]["rest_cosine"], 1.0)
        self.assertLess(rows[0]["posed_cosine"], 0.8)
        self.assertGreater(rows[0]["cosine_drop"], 0.2)


if __name__ == "__main__":
    unittest.main()
