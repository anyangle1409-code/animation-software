"""Interrupted-run recovery must preserve candidates and existing evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import inspect_original_v1_interrupted_run as recovery

class InterruptedRunTests(unittest.TestCase):
    def fixture(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root=Path(tmp.name);cand=root/recovery.CAND;cand.mkdir(parents=True)
        blend=cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.blend';blend.write_bytes(b'test-only-blend-bytes')
        solution=cand/'weight_solutions/o22.npz';solution.parent.mkdir();solution.write_bytes(b'test-only-solution')
        parent='a'*64
        (cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json').write_text(json.dumps({'candidate_sha256':parent}))
        man={'candidate':blend.name,'candidate_sha256':recovery.sha256(blend),'source_candidate':'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.blend','source_sha256':parent,'solution':'o22.npz','solution_sha256':recovery.sha256(solution)}
        (cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.json').write_text(json.dumps(man))
        return root,blend
    def test_missing_groups_print_existing_runner_commands_without_writes(self):
        root,_=self.fixture();before=sorted(str(p) for p in root.rglob('*'))
        report=recovery.inspect(root,'r30')
        self.assertEqual(report['state'],'COLLECT MISSING EVIDENCE')
        self.assertEqual(len(report['missing_groups']),6)
        self.assertIn('RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder',report['commands'][0])
        self.assertEqual(before,sorted(str(p) for p in root.rglob('*')))
    def test_wrong_blend_hash_stops(self):
        root,blend=self.fixture();blend.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'candidate hash'):recovery.inspect(root,'r30')
    def test_changed_solution_stops(self):
        root,_=self.fixture();(root/recovery.CAND/'weight_solutions/o22.npz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'solution hash'):recovery.inspect(root,'r30')
    def test_unfinished_group_is_preserved_and_stops(self):
        root,_=self.fixture();p=root/recovery.RC/'hand_r30';p.mkdir(parents=True);(p/'unfinished.txt').write_text('preserve')
        with self.assertRaisesRegex(ValueError,'unfinished/conflicting group'):recovery.inspect(root,'r30')
        self.assertEqual((p/'unfinished.txt').read_text(),'preserve')
    def test_full_output_collision_stops(self):
        root,_=self.fixture();p=root/recovery.RC/'full_r30_merged_pose_report.json';p.parent.mkdir(parents=True);p.write_text('preserve')
        with self.assertRaisesRegex(ValueError,'full outputs'):recovery.inspect(root,'r30')
        self.assertEqual(p.read_text(),'preserve')
    def test_complete_groups_are_verified_before_merge_instruction(self):
        root,_=self.fixture()
        for group in recovery.GROUP_POSES:(root/recovery.RC/f'{group}_r30').mkdir(parents=True)
        with patch.object(recovery,'verify_group'),patch.object(recovery,'collect_reports') as full:
            report=recovery.inspect(root,'r30')
        full.assert_called_once_with(root,'r30')
        self.assertEqual(report['state'],'MERGE VERIFIED GROUPS')
        self.assertIn('--prior r29',report['commands'][0])

if __name__=='__main__':unittest.main()
