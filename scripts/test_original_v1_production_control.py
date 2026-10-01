"""Safety cases for model production control; no Blender required."""
import copy
import importlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ControlTests(unittest.TestCase):
    def module(self):
        self.assertTrue((ROOT/'scripts/original_v1_production_control.py').exists(),
                        'evidence-led production control is not implemented')
        return importlib.import_module('original_v1_production_control')

    def test_live_evidence_preserves_tradeoff_and_baseline(self):
        c = self.module()
        status, ledger = c.build(ROOT)
        self.assertEqual(status['current_candidate'], 'r29')
        self.assertEqual(status['development_failure_count'], 7)
        self.assertFalse(status['production_approved'])
        self.assertEqual(status['pinned_baseline']['revision'], 'R2')
        r29 = next(x for x in ledger['candidates'] if x['revision'] == 'r29')
        self.assertEqual(r29['comparisons']['r28']['regression_count'], 12)
        self.assertEqual(r29['classification'], 'TRADE-OFF')
        self.assertEqual(status['phases']['3D']['state'], 'refinement')
        self.assertEqual(status['next_action']['action'], 'RUN r30')

    def fixture(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        root = Path(td.name)
        shutil.copytree(ROOT/'ORIGINAL_V1_WORK', root/'ORIGINAL_V1_WORK')
        for p in ROOT.glob('ORIGINAL_V1*.json'): shutil.copy(p, root/p.name)
        return root

    def test_partial_new_candidate_cannot_replace_latest_complete(self):
        c = self.module(); root = self.fixture()
        cand = root/'ORIGINAL_V1_WORK/candidates'
        man = json.loads((cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json').read_text())
        man['candidate'] = man['candidate'].replace('r29.blend','r30.blend')
        (cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.json').write_text(json.dumps(man))
        status, _ = c.build(root)
        self.assertEqual(status['current_candidate'], 'r29')
        self.assertEqual(status['next_action']['action'], 'STOP')
        self.assertIn('incomplete', status['next_action']['reason'])

    def test_stale_comparison_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_R2.json'
        d = json.loads(p.read_text()); d['candidate_failed_checks'] = 0
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'comparison.*disagrees'): c.build(root)

    def test_missing_extended_pose_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json'
        d = json.loads(p.read_text()); p.write_text(json.dumps([x for x in d if x['pose'] != 'lunge']))
        with self.assertRaisesRegex(ValueError, 'coverage'): c.build(root)

    def test_rejected_history_survives_regeneration(self):
        c = self.module(); root = self.fixture()
        old = {'schema_version':1,'candidates':[{'revision':'r99_rejected','sha256':'a'*64,
               'state':'rejected','reason':'owner rejected silhouette','evidence_location':None}]}
        (root/'ORIGINAL_V1_CANDIDATE_LEDGER.json').write_text(json.dumps(old))
        _, ledger = c.build(root)
        self.assertIn('r99_rejected',[x['revision'] for x in ledger['candidates']])

    def test_frozen_gate_drift_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json'
        d = json.loads(p.read_text()); d['profiles']['development_blocker']['grip_max_penetration_mm'] = 6
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'frozen'): c.build(root)

if __name__ == '__main__': unittest.main()
