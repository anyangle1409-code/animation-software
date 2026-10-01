"""A replay must be complete, independent, source-bound and numerically identical."""
import json
from pathlib import Path
import unittest

class ReplayTests(unittest.TestCase):
    def fixture(self):
        from test_original_v1_evidence_merge import MergeTests
        import merge_original_v1_repair_group_reports as merger
        import original_v1_production_control as control
        helper=MergeTests();root=helper.fixture(merger);self.addCleanup(helper.doCleanups)
        (root/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json').write_bytes((control.ROOT/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json').read_bytes())
        rows,receipt=merger.collect_reports(root,'r29')
        primary=root/merger.RC/'full_r29_merged_pose_report.json';primary.write_text(json.dumps(rows))
        receipt['merged_pose_report_sha256']=control.digest(primary)
        (primary.parent/'full_r29_evidence_manifest.json').write_text(json.dumps(receipt))
        replay=primary.parent/'freeze_replay_r29';replay.mkdir()
        report=replay/'pose_test_report.json';report.write_text(json.dumps(rows))
        man={'candidate_sha256':receipt['candidate_sha256'],'render_script_sha256':'a'*64,
             'pose_report_sha256':control.digest(report),'blender_version':'test fixture only',
             'capture_mode':'numeric_replay','capture_arguments':[str(replay),'','--metrics-only'],'images':[]}
        (replay/'render_source_manifest.json').write_text(json.dumps(man))
        import verify_original_v1_replay as c
        return c,root,replay
    def test_complete_identical_replay_is_evidence_not_approval(self):
        c,root,replay=self.fixture();report=c.verify_replay(root,'r29',replay)
        self.assertEqual(report['status'],'PASS');self.assertFalse(report['production_approved'])
        self.assertEqual(report['pose_count'],15)
    def test_changed_pose_metric_is_refused(self):
        c,root,replay=self.fixture();p=replay/'pose_test_report.json';rows=json.loads(p.read_text());rows[0]['volume_ratio']+=.01;p.write_text(json.dumps(rows))
        m=replay/'render_source_manifest.json';data=json.loads(m.read_text());data['pose_report_sha256']=c.digest(p);m.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'replay metrics'):c.verify_replay(root,'r29',replay)
    def test_other_candidate_replay_is_refused(self):
        c,root,replay=self.fixture();p=replay/'render_source_manifest.json';data=json.loads(p.read_text());data['candidate_sha256']='c'*64;p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'candidate'):c.verify_replay(root,'r29',replay)
    def test_other_blender_or_script_is_refused(self):
        c,root,replay=self.fixture();p=replay/'render_source_manifest.json';data=json.loads(p.read_text());data['blender_version']='different';p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'Blender'):c.verify_replay(root,'r29',replay)
    def test_relabelled_primary_invocation_is_refused(self):
        c,root,replay=self.fixture();p=replay/'render_source_manifest.json';data=json.loads(p.read_text());data['capture_arguments']=['copied_primary','neutral'];p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'invocation'):c.verify_replay(root,'r29',replay)
    def test_incomplete_replay_is_refused(self):
        c,root,replay=self.fixture();p=replay/'pose_test_report.json';rows=json.loads(p.read_text());rows.pop();p.write_text(json.dumps(rows))
        m=replay/'render_source_manifest.json';data=json.loads(m.read_text());data['pose_report_sha256']=c.digest(p);m.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'coverage'):c.verify_replay(root,'r29',replay)

if __name__=='__main__':unittest.main()
