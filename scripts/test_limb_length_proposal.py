import importlib.util, json, unittest
from pathlib import Path

from report_compare import report_differences

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('llp', ROOT / 'scripts/anatomy_fit/limb_length_proposal.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
STORED = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_limb_length_proposal_182_v1.json').read_text())


class LimbLengthProposal(unittest.TestCase):
    def test_reproduces_from_committed_ansur(self):
        self.assertEqual(report_differences(STORED, m.build()), [])

    def test_is_a_proposal_not_a_selection(self):
        self.assertEqual(STORED['status'], 'PROPOSAL_FOR_GPT_REVIEW_NOT_SELECTED')
        self.assertIs(STORED['freeze_ready'], False)
        sel = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_target_selection_v1.json').read_text())
        self.assertIs(sel['freeze_ready'], False)

    def test_forearm_short_under_every_method(self):
        f = STORED['spans']['forearm_EJC_WJC']
        self.assertLess(f['a003_z_vs_ansur'], -3)
        for ref in (f['proposed_mm'], f['crosscheck_trotter_gleser_mm'], f['crosscheck_de_leva_scaled_mm'],
                    *[v for v in f['sensitivity_mm'].values()]):
            self.assertLess(f['a003_mm'], ref - 20)
        self.assertTrue(f['reading'].startswith('ROBUST'))

    def test_thigh_is_contested_not_declared_short(self):
        t = STORED['spans']['thigh_HJC_KJC']
        self.assertGreater(t['a003_z_vs_ansur'], -1)
        self.assertGreater(t['crosscheck_de_leva_scaled_mm'] - t['proposed_mm'], t['ansur_residual_sd_mm'])
        self.assertTrue(t['reading'].startswith('CONTESTED'))

    def test_primary_de_leva_endpoint_rows_replace_recalled_values(self):
        self.assertEqual(m.DE_LEVA['shank_KJC_AJC'][0], 440.3)
        status = {k: v['de_leva_status'] for k, v in STORED['spans'].items()}
        self.assertEqual(set(status.values()), {'PRIMARY_TABLE4_VERIFIED_CONTEXT_ONLY'})
        self.assertEqual(STORED['de_leva_source_review'], 'canonical_de_leva_primary_endpoint_review_v1.json')
        self.assertTrue(STORED['spans']['forearm_EJC_WJC']['ansur_residual_sd_excludes_joint_conversion_uncertainty'])


if __name__ == '__main__':
    unittest.main()
