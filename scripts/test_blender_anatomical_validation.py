"""Synthetic numerical/report regressions; these do not execute Blender."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest
import tempfile

ROOT=Path(__file__).resolve().parents[1]

class ValidationPackageTests(unittest.TestCase):
    def module(self):
        path=ROOT/'scripts/anatomical_blender_validation.py'
        self.assertTrue(path.exists(),'Offline Blender validation core missing')
        spec=importlib.util.spec_from_file_location('anatomical_capture',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod

    def matrix(self,x=0):
        return [[1,0,0,x],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

    def capture(self):
        return {'schema_version':1,'units':'metres','metres_per_world_unit':1,
                'provenance':{'blend_sha256':'a'*64,'dirty_before_capture':False,
                    'blender_version':'fixture_only','armature':'synthetic_fixture',
                    'atlas_sha256':self.module().atlas_hashes()},
                'rest_bones':{'anat_femur_left':{'anatomical_id':'femur_left','parent':None,
                    'head_world_m':[0,0,0],'tail_world_m':[0,1,0],'matrix_world':self.matrix()}},
                'samples':[]}

    def test_absent_evidence_never_passes_anatomical_acceptance(self):
        mod=self.module();r=mod.analyze_capture(self.capture(),mod.build_plan())
        self.assertFalse(r['character_accepted'])
        self.assertEqual(r['checks']['bone_coverage']['status'],'FAIL')
        self.assertEqual(r['checks']['anatomical_placement']['status'],'UNVERIFIED')
        self.assertEqual(r['checks']['joint_operation']['status'],'UNVERIFIED')

    def test_provenance_requires_explicit_consistent_preservation_evidence(self):
        mod=self.module();cap=self.capture();p=cap['provenance']
        p.update(blend_sha256_after='a'*64,source_file_unchanged=True,
                 frame_restored=True,automatic_python_execution_failed=False)
        self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['provenance']['status'],'PASS')
        for key in ['blend_sha256_after','source_file_unchanged','frame_restored','automatic_python_execution_failed']:
            altered=copy.deepcopy(cap);del altered['provenance'][key]
            self.assertEqual(mod.analyze_capture(altered,mod.build_plan())['checks']['provenance']['status'],'UNVERIFIED')
        altered=copy.deepcopy(cap);altered['provenance']['blend_sha256_after']='b'*64
        self.assertEqual(mod.analyze_capture(altered,mod.build_plan())['checks']['provenance']['status'],'FAIL')
        for key in ['blend_sha256','blend_sha256_after']:
            altered=copy.deepcopy(cap);altered['provenance'][key]='z'*64
            self.assertNotEqual(mod.analyze_capture(altered,mod.build_plan())['checks']['provenance']['status'],'PASS')

    def test_empty_geometry_is_unverified(self):
        mod=self.module();cap=self.capture();cap['rest_bones']={}
        self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['geometry_integrity']['status'],'UNVERIFIED')

    def test_nonfinite_zero_bones_and_cycles_fail_integrity(self):
        mod=self.module()
        for kind in ['nan','zero','cycle','unknown_parent']:
            cap=self.capture();b=cap['rest_bones']['anat_femur_left']
            if kind=='nan':b['head_world_m'][0]=float('nan')
            if kind=='zero':b['tail_world_m']=b['head_world_m'][:]
            if kind=='cycle':b['parent']='anat_femur_left'
            if kind=='unknown_parent':b['parent']='missing'
            self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['geometry_integrity']['status'],'FAIL')

    def test_stale_atlas_and_dirty_character_are_not_accepted(self):
        mod=self.module()
        for kind in ['hash','dirty']:
            cap=self.capture()
            if kind=='hash':cap['provenance']['atlas_sha256']={}
            else:cap['provenance']['dirty_before_capture']=True
            self.assertNotEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['provenance']['status'],'PASS')

    def test_shared_runtime_names_cannot_count_as_206_reference_bones(self):
        mod=self.module();cap=self.capture()
        other=copy.deepcopy(cap['rest_bones']['anat_femur_left'])
        cap['rest_bones']['copy']=other
        self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['identity']['status'],'FAIL')

    def test_missing_joint_markers_are_not_guessed_from_bone_heads(self):
        mod=self.module();cap=self.capture()
        cap['samples']=[{'test_id':'unassigned_current_pose','time_seconds':0,'bones':{},'joint_frames':{}}]
        r=mod.analyze_capture(cap,mod.build_plan())
        self.assertEqual(r['checks']['joint_marker_coverage']['status'],'UNVERIFIED')
        self.assertEqual(r['joint_centres'],{})

    def test_exact_coincident_ac_and_gh_markers_fail(self):
        mod=self.module();cap=self.capture()
        cap['samples']=[{'test_id':'unassigned_current_pose','time_seconds':0,'bones':{},
             'joint_frames':{key:{'matrix_world':self.matrix()} for key in ['acromioclavicular_left','glenohumeral_left']}}]
        self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['distinct_centres']['status'],'FAIL')

    def test_rigid_relative_transform_and_rotation_ignore_global_translation(self):
        mod=self.module();a=self.matrix(10);b=self.matrix(12)
        self.assertEqual(mod.relative_transform(a,b)[0][3],2)
        b=[[0,-1,0,12],[1,0,0,0],[0,0,1,0],[0,0,0,1]]
        self.assertAlmostEqual(mod.rotation_difference_degrees(a,b),90)
        bad=self.matrix();bad[0][0]=-1
        with self.assertRaises(ValueError):mod.relative_transform(bad,b)

    def test_trajectory_uses_seconds_and_rejects_duplicate_times(self):
        mod=self.module()
        r=mod.trajectory_metrics([[0,0,0],[1,0,0],[3,0,0]],[0,1,2])
        self.assertEqual(r['speeds_m_per_s'],[1,2])
        self.assertEqual(r['acceleration_m_per_s2'],[1])
        with self.assertRaises(ValueError):mod.trajectory_metrics([[0,0,0],[1,0,0]],[0,0])

    def test_manifest_is_source_bound_and_has_all_functional_tasks(self):
        mod=self.module();p=mod.build_plan()
        self.assertEqual(len(p['expected_bones']),206)
        self.assertEqual(len(p['joint_markers']),427)
        self.assertEqual(set(p['profile_cases']),set(json.loads((ROOT/'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())['profiles']))
        self.assertEqual(len(p['functional_cases']),12)
        self.assertFalse(p['samples'])
        for case in p['profile_cases'].values():
            self.assertGreaterEqual(len(case['sources']),2)
            self.assertTrue(case['acceptance_criteria'])
        self.assertFalse(p['character_accepted'])

    def test_full_named_geometry_still_cannot_prove_correct_fit(self):
        mod=self.module();cap=self.capture();cap['rest_bones']={}
        for key,name in mod.build_plan()['expected_bones'].items():
            cap['rest_bones'][name]={'anatomical_id':key,'parent':None,'head_world_m':[0,0,0],
                'tail_world_m':[0,1,0],'matrix_world':self.matrix()}
        r=mod.analyze_capture(cap,mod.build_plan())
        self.assertEqual(r['checks']['bone_coverage']['status'],'PASS')
        self.assertFalse(r['character_accepted'])
        self.assertNotEqual(r['overall_status'],'PASS')

    def test_missing_samples_do_not_pass_sample_or_trajectory_integrity(self):
        mod=self.module();r=mod.analyze_capture(self.capture(),mod.build_plan())
        self.assertEqual(r['checks']['sample_integrity']['status'],'UNVERIFIED')
        self.assertEqual(r['checks']['trajectory_integrity']['status'],'UNVERIFIED')

    def test_modified_contract_cannot_hide_missing_bones(self):
        mod=self.module();plan=mod.build_plan()
        plan['expected_bones']={'femur_left':'anat_femur_left'}
        self.assertEqual(mod.analyze_capture(self.capture(),plan)['checks']['provenance']['status'],'FAIL')

    def test_frame_sampling_restores_frame_even_when_measurement_fails(self):
        mod=self.module()
        self.assertTrue(hasattr(mod,'sample_with_frame_restore'),'Frame preservation helper missing')
        class Scene:
            frame_current=7
            frame_subframe=.25
            def frame_set(self,frame,subframe=0):self.frame_current=frame;self.frame_subframe=subframe
        scene=Scene()
        result=mod.sample_with_frame_restore(scene,[{'frame':1},{'frame':3}],lambda _:scene.frame_current)
        self.assertEqual(result,[1,3]);self.assertEqual((scene.frame_current,scene.frame_subframe),(7,.25))
        def broken(_):raise ValueError('measurement failed')
        with self.assertRaises(ValueError):mod.sample_with_frame_restore(scene,[{'frame':2}],broken)
        self.assertEqual((scene.frame_current,scene.frame_subframe),(7,.25))

    def test_audit_outputs_cannot_overwrite_existing_files(self):
        mod=self.module()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'audit.json';path.write_text('preserve')
            with self.assertRaises(FileExistsError):mod.write_new_json(path,{'audit':True})
            self.assertEqual(path.read_text(),'preserve')
            with self.assertRaises(ValueError):mod.write_new_json(Path(directory)/'character.blend',{})

    def test_blender_exporter_is_separate_and_has_no_save_or_pose_driver_execution(self):
        import ast
        path=ROOT/'scripts/capture_anatomical_validation_blender.py'
        self.assertTrue(path.exists(),'Read-only Blender exporter missing')
        tree=ast.parse(path.read_text())
        forbidden={'save_as_mainfile','save_mainfile','save','exec','eval','reset','aim','rot'}
        for node in ast.walk(tree):
            if isinstance(node,ast.Call):
                name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
                self.assertNotIn(name,forbidden)

    def test_source_mutation_or_failed_scene_restore_cannot_pass_provenance(self):
        mod=self.module()
        for key in ['source_file_unchanged','frame_restored']:
            cap=self.capture();cap['provenance'][key]=False
            self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['provenance']['status'],'FAIL')

    def test_disabled_animation_execution_is_unverified(self):
        mod=self.module();cap=self.capture();cap['provenance']['automatic_python_execution_failed']=True
        self.assertEqual(mod.analyze_capture(cap,mod.build_plan())['checks']['provenance']['status'],'UNVERIFIED')

    def test_requested_subframe_is_measured_and_original_restored(self):
        mod=self.module()
        class Scene:
            frame_current=7
            frame_subframe=.25
            def frame_set(self,frame,subframe=0):self.frame_current=frame;self.frame_subframe=subframe
        scene=Scene()
        result=mod.sample_with_frame_restore(scene,[{'frame':4,'subframe':.5}],lambda _:(scene.frame_current,scene.frame_subframe))
        self.assertEqual(result,[(4,.5)])
        self.assertEqual((scene.frame_current,scene.frame_subframe),(7,.25))

    def test_landmark_positions_are_reported_and_bad_or_duplicate_ids_fail(self):
        mod=self.module();cap=self.capture()
        cap['samples']=[{'test_id':'unassigned_current_pose','time_seconds':0,'bones':{},'joint_frames':{},
            'landmarks':{'marker1':{'landmark_id':'femur_left/head','position_world_m':[1,2,3]}}}]
        report=mod.analyze_capture(cap,mod.build_plan())
        self.assertTrue('landmark_positions' in report,'Landmark measurements missing from report')
        self.assertEqual(report['landmark_positions']['femur_left/head'][0]['position_m'],[1,2,3])
        for mode in ['nan','duplicate']:
            bad=copy.deepcopy(cap)
            if mode=='nan':bad['samples'][0]['landmarks']['marker1']['position_world_m'][0]=float('nan')
            else:bad['samples'][0]['landmarks']['marker2']=copy.deepcopy(bad['samples'][0]['landmarks']['marker1'])
            self.assertEqual(mod.analyze_capture(bad,mod.build_plan())['checks']['landmark_integrity']['status'],'FAIL')

if __name__=='__main__':unittest.main()
