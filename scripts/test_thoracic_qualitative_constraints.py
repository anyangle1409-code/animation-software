"""The thoracic qualitative constraints stay qualitative: no per-level angles, and the committed cadaveric disc heights
are checked only for sign consistency with the reported lower-thoracic lordotic disc pattern."""
import json, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
Q = json.loads((ANAT / 'canonical_thoracic_qualitative_constraints_v1.json').read_text())


class Qualitative(unittest.TestCase):
    def test_status_and_prohibitions(self):
        self.assertEqual(Q['status'], 'QUALITATIVE_CONSTRAINTS_ONLY_NO_PER_LEVEL_VALUES')
        self.assertIn('inventing per-level wedge or tilt angles from these summaries', Q['not_allowed'])
        self.assertEqual(set(Q['sources']), {'PMID_41047402', 'PMID_31513104'})

    def test_no_per_level_numeric_angles(self):
        text = json.dumps(Q['sources'])
        self.assertIsNone(re.search(r'T\d{1,2}[^"]{0,20}?-?\d+(\.\d+)?\s*deg', text.replace('~ 0 deg', '')))

    def test_lower_thoracic_discs_lordotic_in_committed_data(self):
        src = {s['id']: s for s in json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())['sources']}['THORACIC_BODY_DISC_2011']
        d = {k: src['disc_anterior_mean_sd_mm'][k][0] - src['disc_posterior_mean_sd_mm'][k][0] for k in src['disc_anterior_mean_sd_mm']}
        for k in ('T7/T8', 'T8/T9', 'T9/T10', 'T10/T11', 'T11/T12'):
            self.assertGreater(d[k], 0, k)                       # anterior taller: lordotic disc wedge
        for k in ('T2/T3', 'T3/T4', 'T4/T5', 'T5/T6', 'T6/T7'):
            self.assertLessEqual(abs(d[k]), 0.3, k)              # near equal; sign of tiny differences not interpreted


if __name__ == '__main__':
    unittest.main()
