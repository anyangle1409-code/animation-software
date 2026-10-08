"""Every number in canonical_forearm_ansur_direct_report_v1.json is recomputed from the committed ANSUR II file.

The committed report has no generator of its own (scripts/anatomy_fit/build_forearm_target_report.py emits a
different, smaller schema), so this test is its provenance check. Residual percentiles in the committed report
use NumPy's 'lower' percentile method, not the default 'linear'.
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'anatomy_fit'))
import build_forearm_target_report as b  # noqa: E402

REPORT = ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_forearm_ansur_direct_report_v1.json'


def fit(x, y, target):
    slope, intercept = np.polyfit(x, y, 1)
    res = y - (intercept + slope * x)
    return slope, intercept, float(intercept + slope * target), float(res.std(ddof=2)), res


class ForearmDirectReportProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(REPORT.read_text())
        cls.A = b.numeric_columns(ROOT / cls.r['dataset']['path'])
        cls.H = cls.r['dataset']['stature_target_mm']

    def close(self, a, b_, msg):
        self.assertTrue(np.isclose(a, b_, rtol=1e-9, atol=1e-9), f'{msg}: committed {a} vs recomputed {b_}')

    def test_radiale_stylion_regression(self):
        r = self.r['radialestylionlength']
        self.assertEqual(r['n'], len(self.A['stature']))
        slope, icpt, pred, sd, res = fit(self.A['stature'], self.A['radialestylionlength'], self.H)
        for k, v in (('slope_mm_per_mm_stature', slope), ('intercept_mm', icpt), ('predicted_at_target_stature_mm', pred),
                     ('residual_sd_mm', sd), ('dataset_mean_mm', self.A['radialestylionlength'].mean()),
                     ('residual_p5_mm', np.percentile(res, 5, method='lower')), ('residual_p95_mm', np.percentile(res, 95, method='lower'))):
            self.close(r[k], v, k)
        self.close(r['prediction_plus_minus_1sd_mm'][0], pred - sd, '-1sd')
        self.close(r['prediction_plus_minus_1sd_mm'][1], pred + sd, '+1sd')

    def test_a003_comparison(self):
        c = self.r['a003_comparison']
        add = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003_review_addendum.json').read_text())
        proxy = add['trotter_gleser_corrected']['bones']['radius_left']['length_m'] * 1000
        _, _, pred, sd, res = fit(self.A['stature'], self.A['radialestylionlength'], self.H)
        self.close(c['a003_radius_osteometric_proxy_mm'], proxy, 'proxy')
        self.close(c['difference_from_stature_conditioned_prediction_mm'], proxy - pred, 'difference')
        self.close(c['z_vs_regression_residual'], (proxy - pred) / sd, 'z')
        self.close(c['empirical_residual_percentile_percent'], 100 * np.mean(res < proxy - pred), 'percentile')

    def test_supporting_regressions(self):
        for col, v in self.r['supporting_direct_regressions'].items():
            _, _, pred, sd, _ = fit(self.A['stature'], self.A[col], self.H)
            self.close(v['predicted_mm'], pred, col)
            self.close(v['residual_sd_mm'], sd, col)


if __name__ == '__main__':
    unittest.main()
