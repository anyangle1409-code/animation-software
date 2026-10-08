"""ANSUR endpoint correspondence audit: provenance limitation recorded, classes pinned, robust conclusions pinned,
no geometry change and no target selection."""
import hashlib, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import ansur_endpoint_correspondence_audit as m  # noqa: E402
from report_compare import report_differences  # noqa: E402

A = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/ansur_endpoint_correspondence_v1.json').read_text())


class Correspondence(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(A, json.loads(json.dumps(m.build()))), [])

    def test_provenance_limitation_recorded(self):
        s = A['source']
        self.assertEqual(s['definition_status'], 'OWNER_SUPPLIED_NOT_INDEPENDENTLY_VERIFIED')
        self.assertIsNone(s['pdf_sha256'])
        self.assertEqual(s['url'], 'https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf')
        self.assertEqual({d['section'] for k, d in A['definitions_owner_supplied'].items() if k != 'acromion'}, {'5.2.5', '5.2.33', '5.2.36', '5.2.39', '6.4.68'})

    def test_classes(self):
        c = {k: v['class'] for k, v in A['correspondence'].items()}
        self.assertEqual(c, {'suprasternale': 'DEFENSIBLE', 'acromion': 'BRACKETED', 'cervicale': 'UNRESOLVED', 'radiale': 'UNRESOLVED',
                             'stylion': 'UNRESOLVED', 'radiale_stylion_length': 'UNRESOLVED'})

    def test_robust_conclusions_and_withdrawn_forearm_claim(self):
        r = A['robust_across_bracket']
        self.assertTrue(r['wrist_high_on_c003']); self.assertTrue(r['upper_arm_drop_short_on_c003'])
        self.assertFalse(r['forearm_radiale_stylion_short_on_c003'])      # depends on the unsourced offsets
        self.assertEqual(len(A['sensitivity']['c003']['rows']), 16)

    def test_no_target_no_geometry_change(self):
        self.assertTrue(A['status'].startswith('AUDIT_ONLY'))
        self.assertIn('NOT SELECTED', A['decision']['humerus_or_forearm_target'])
        h = hashlib.sha256((ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json').read_bytes()).hexdigest()
        self.assertTrue(h.startswith('3eb4fa1e2f7d815e'))


if __name__ == '__main__':
    unittest.main()
