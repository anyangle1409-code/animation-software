import pathlib
import sys
import unittest

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from anatomy_fit.build_forearm_target_report import conditional


class ForearmTargetReportTests(unittest.TestCase):
    def test_conditional_linear_regression_exact_line(self):
        x = np.array([1600.0, 1700.0, 1800.0, 1900.0])
        y = 0.15 * x + 5.0
        r = conditional(x, y, 1820.0)
        self.assertAlmostEqual(r["predicted"], 278.0, places=9)
        self.assertAlmostEqual(r["slope"], 0.15, places=12)
        self.assertAlmostEqual(r["intercept"], 5.0, places=9)
        self.assertAlmostEqual(r["residual_sd"], 0.0, places=9)

    def test_conditional_reports_population_size(self):
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([2.0, 4.1, 5.9, 8.2])
        r = conditional(x, y, 2.5)
        self.assertEqual(r["n"], 4)
        self.assertGreaterEqual(r["residual_sd"], 0.0)
        self.assertEqual(len(r["p5_p95_residual"]), 2)


if __name__ == "__main__":
    unittest.main()
