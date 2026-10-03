"""Milestone coverage and actual-render evidence checks, without Blender."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class MilestoneTests(unittest.TestCase):
    def module(self):return importlib.import_module('original_v1_milestone_review')
    def test_exact_required_coverage_and_unique_filenames(self):
        c=self.module();plan=c.load_plan(ROOT);rows=c.views(plan)
        self.assertEqual(len(rows),57)
        self.assertEqual(len({x['file'] for x in rows}),57)
        self.assertEqual({x['view'] for x in rows if x['set']=='neutral'}, {'front','rear','side','three_quarter','three_quarter_rear'})
        self.assertEqual(len({x['region'] for x in rows if x['set']=='anatomy'}),11)
        self.assertEqual(len({x['pose'] for x in rows if x['set']=='exercise'}),10)
    def test_pushup_has_its_own_fixed_frame_and_other_poses_keep_the_shared_one(self):
        # The P3 push-up plank is 1.81 m long and offset in depth: the shared exercise frame (centre y=0, scale 2.65)
        # crops it. The fixed per-pose frame is explicit in the plan (never auto-fitted) and affects only that pose.
        c=self.module();plan=c.load_plan(ROOT);rows=c.views(plan)
        shared=plan['exercise']
        push=[x for x in rows if x['pose']=='pushup_bottom']
        self.assertEqual(len(push),3)
        frame=shared['pose_frames']['pushup_bottom']
        self.assertTrue(all(x['centre']==frame['centre'] and x['scale']==frame['orthographic_scale'] for x in push))
        self.assertGreaterEqual(frame['orthographic_scale']/2, 0.906)       # half the measured 1.81 m depth extent, centred
        others=[x for x in rows if x['set']=='exercise' and x['pose']!='pushup_bottom']
        self.assertTrue(all(x['centre']==shared['centre'] and x['scale']==shared['orthographic_scale'] for x in others))
    def test_plan_targets_only_owned_canonical_bones(self):
        c=self.module();plan=c.load_plan(ROOT)
        names={x['name'] for x in json.loads((ROOT/'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json').read_text())['bones']}
        for region in plan['anatomy']:
            self.assertTrue(all(anchor[0] in names for anchor in region['anchors']))
            self.assertTrue(all(anchor[1] in ('head','tail') for anchor in region['anchors']))
    def test_milestone_switch_does_not_change_frozen_poses(self):
        # Building the live production control re-verifies the hash-pinned frozen stress-pose definition and
        # frozen inputs; it must succeed (and not raise 'frozen stress-pose definition changed') on the live state
        # whatever the latest candidate revision is.
        from original_v1_production_control import build, read
        status=build(ROOT)[0]
        self.assertRegex(status['current_candidate'],r'^r\d+$')
        self.assertFalse(status['production_approved'])
        self.assertIn('frozen_pose_definition',read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json'))
    def test_incomplete_actual_capture_is_rejected(self):
        c=self.module();plan=c.load_plan(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'coverage'):
                c.verify_milestone(Path(temp),{'images':[]},plan)
    def test_fake_capture_settings_are_rejected(self):
        c=self.module();plan=c.load_plan(ROOT)
        records=[{'file':x['file'],'capture':{}} for x in c.views(plan)]
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'protocol'):
                c.verify_milestone(Path(temp),{'images':records},plan)
    def test_publication_uses_actual_source_and_refuses_collision(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cand=root/c.CAND;cand.mkdir(parents=True)
            (root/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json').write_bytes((ROOT/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json').read_bytes())
            (cand/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json').write_text(json.dumps({'candidate_sha256':'a'*64}))
            source=cand/'repair_checks/milestone_r29';source.mkdir(parents=True)
            plan=c.load_plan(root);records=[]
            for row in c.views(plan):
                image=source/row['file'];image.write_bytes(b'test fixture only, not user render')
                records.append({'file':row['file'],'sha256':c.digest(image),'capture':{
                    'protocol':plan['protocol'],'milestone_plan_sha256':c.digest(root/'ORIGINAL_V1_VISUAL_BOARD_PLAN.json'),
                    'view_id':row['file'],'dressed':False,'pose':row['pose']}})
            (root/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json').write_bytes((ROOT/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json').read_bytes())
            (source/'pose_test_report.json').write_bytes((ROOT/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json').read_bytes())
            data={'candidate_sha256':'a'*64,'images':records,'blender_version':'test fixture only',
                  'render_script_sha256':'b'*64,'pose_report_sha256':c.digest(source/'pose_test_report.json')}
            (source/'render_source_manifest.json').write_text(json.dumps(data))
            out=c.publish(root,'r29')
            self.assertEqual(len(list(out.glob('*.png'))),57)
            import original_v1_production_control as control
            pending=control.verified_review(root,'r29','a'*64,'milestone')
            self.assertEqual(pending['owner_review'],'pending');self.assertFalse(pending['blocking'])
            man=json.loads((out/'visual_review_manifest.json').read_text())
            self.assertEqual(man['owner_review'],'pending');self.assertFalse(man['blocking'])
            self.assertFalse(man['production_approved']);self.assertIn('r29',(out/'README.md').read_text())
            with self.assertRaisesRegex(ValueError,'collision'):c.publish(root,'r29')

if __name__=='__main__':unittest.main()
