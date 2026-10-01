"""Report lineage and execution-error cases for the full evidence merger."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]

class MergeTests(unittest.TestCase):
    def module(self):return importlib.import_module('merge_original_v1_repair_group_reports')
    def fixture(self,c):
        td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
        cand=root/'ORIGINAL_V1_WORK/candidates';cand.mkdir(parents=True)
        man=json.loads((ROOT/'ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json').read_text())
        (cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json').write_text(json.dumps(man))
        base=json.loads((ROOT/'ORIGINAL_V1_WORK/candidates/pose_test_report_r2.json').read_text())
        (cand/'pose_test_report_r2.json').write_text(json.dumps(base))
        rows={x['pose']:x for x in base}
        for group,poses in c.GROUP_POSES.items():
            p=cand/'repair_checks'/f'{group}_r29';p.mkdir(parents=True)
            report=p/'pose_test_report.json';report.write_text(json.dumps([rows[n] for n in poses]))
            source={'candidate_sha256':man['candidate_sha256'],'pose_report_sha256':c.sha256(report),
                    'render_script_sha256':'a'*64,'blender_version':'test fixture only','images':[]}
            (p/'render_source_manifest.json').write_text(json.dumps(source))
        return root
    def test_all_fifteen_poses_merge_without_replacing_sources(self):
        c=self.module();self.assertTrue(hasattr(c,'GROUP_POSES'),'source-aware merger not implemented')
        root=self.fixture(c);rows,manifest=c.collect_reports(root,'r29')
        self.assertEqual(len(rows),15);self.assertEqual(manifest['candidate_revision'],'r29')
        self.assertEqual(len(manifest['groups']),6);self.assertFalse(manifest['production_approved'])
    def test_same_pose_from_different_candidate_is_refused(self):
        c=self.module();self.assertTrue(hasattr(c,'GROUP_POSES'),'source-aware merger not implemented')
        root=self.fixture(c);p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/hand_r29/render_source_manifest.json'
        d=json.loads(p.read_text());d['candidate_sha256']='b'*64;p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'candidate'):c.collect_reports(root,'r29')
    def test_disagreeing_duplicate_pose_is_refused(self):
        c=self.module();self.assertTrue(hasattr(c,'GROUP_POSES'),'source-aware merger not implemented')
        root=self.fixture(c);p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/hand_r29/pose_test_report.json'
        d=json.loads(p.read_text());d[1]['volume_ratio']+=.01;p.write_text(json.dumps(d))
        m=p.with_name('render_source_manifest.json');md=json.loads(m.read_text());md['pose_report_sha256']=c.sha256(p);m.write_text(json.dumps(md))
        with self.assertRaisesRegex(ValueError,'conflicting.*pose'):c.collect_reports(root,'r29')
    def test_neutral_control_is_mandatory_for_new_full_evidence(self):
        c=self.module();self.assertTrue(hasattr(c,'GROUP_POSES'),'source-aware merger not implemented')
        root=self.fixture(c);p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/neutral_r29/pose_test_report.json';p.unlink()
        with self.assertRaisesRegex(ValueError,'neutral'):c.collect_reports(root,'r29')
    def test_mixed_capture_script_versions_are_refused(self):
        c=self.module();self.assertTrue(hasattr(c,'GROUP_POSES'),'source-aware merger not implemented')
        root=self.fixture(c);p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/row_r29/render_source_manifest.json'
        d=json.loads(p.read_text());d['render_script_sha256']='c'*64;p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'script'):c.collect_reports(root,'r29')

    def test_cli_preserves_regressions_as_completed_evidence(self):
        c=self.module();root=self.fixture(c)
        real={x['pose']:x for x in json.loads((ROOT/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json').read_text())}
        for group,poses in c.GROUP_POSES.items():
            p=root/'ORIGINAL_V1_WORK/candidates/repair_checks'/f'{group}_r29/pose_test_report.json'
            p.write_text(json.dumps([real[n] for n in poses]))
            m=p.with_name('render_source_manifest.json');d=json.loads(m.read_text());d['pose_report_sha256']=c.sha256(p);m.write_text(json.dumps(d))
        result=subprocess.run([sys.executable,str(ROOT/'scripts/merge_original_v1_repair_group_reports.py'),'r29','--root',str(root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads((root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_R2.json').read_text())
        self.assertEqual(report['status'],'REGRESSION');self.assertEqual(report['regression_count'],6)
        self.assertEqual(report['candidate_failed_checks'],7)

    def test_cli_does_not_mask_validation_subprocess_error(self):
        c=self.module();root=self.fixture(c)
        p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/hand_r29/pose_test_report.json'
        d=json.loads(p.read_text());del d[0]['volume_ratio'];p.write_text(json.dumps(d))
        m=p.with_name('render_source_manifest.json');md=json.loads(m.read_text());md['pose_report_sha256']=c.sha256(p);m.write_text(json.dumps(md))
        result=subprocess.run([sys.executable,str(ROOT/'scripts/merge_original_v1_repair_group_reports.py'),'r29','--root',str(root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('subprocess failed',result.stderr)
        self.assertFalse((root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_R2.json').exists())

    def test_cli_refuses_to_overwrite_existing_evidence(self):
        c=self.module();root=self.fixture(c)
        p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json'
        p.write_text('preserved partial checkpoint')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/merge_original_v1_repair_group_reports.py'),'r29','--root',str(root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertEqual(p.read_text(),'preserved partial checkpoint')

if __name__=='__main__':unittest.main()
