"""Completeness and mutation tests for the reference-only anatomical programme."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'ORIGINAL_V1_WORK/anatomy'

class ArticulationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((DATA / 'adult_articulation_inventory.json').exists(),
                        'Phase 2 articulation inventory is missing')
        self.data = json.loads((DATA / 'adult_articulation_inventory.json').read_text())

    def validator(self):
        path = ROOT / 'scripts/validate_complete_anatomical_atlas.py'
        self.assertTrue(path.exists(), 'Phase 2 completeness validator is missing')
        spec = importlib.util.spec_from_file_location('anatomical_validator', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_live_inventory_has_no_unclassified_articulations(self):
        self.assertEqual([], self.validator().validate_inventory(self.data, DATA))

    def test_missing_individual_joint_is_rejected(self):
        for jid in ['distal_radioulnar_left', 'pisotriquetral_left',
                    'costotransverse_10_right', 'thumb_ip_right',
                    'hallux_ip_left', 'pubic_symphysis', 'atlantoaxial_median',
                    'facet_l5_sacrum_left', 'intermetatarsal_4_5_right']:
            with self.subTest(jid=jid):
                bad = copy.deepcopy(self.data)
                bad['articulations'] = [j for j in bad['articulations'] if j['id'] != jid]
                self.assertTrue(self.validator().validate_inventory(bad, DATA))

    def test_unknown_bone_duplicate_joint_and_unsourced_joint_rejected(self):
        for mode in ['bone', 'duplicate', 'source', 'class', 'side', 'fixed']:
            with self.subTest(mode=mode):
                bad = copy.deepcopy(self.data)
                j = bad['articulations'][0]
                if mode == 'bone': j['participants'][0] = 'imaginary_bone'
                if mode == 'duplicate': bad['articulations'].append(copy.deepcopy(j))
                if mode == 'source': j['sources'] = j['sources'][:1]
                if mode == 'class': j['structural_type'] = 'unclassified'
                if mode == 'side': j['side'] = 'maybe'
                if mode == 'fixed': j['exercise_motion'] = 'unknown'
                self.assertTrue(self.validator().validate_inventory(bad, DATA))

    def test_anatomical_exceptions_are_explicit(self):
        joints = {j['id']: j for j in self.data['articulations']}
        self.assertNotIn('costotransverse_11_left', joints)
        self.assertNotIn('costotransverse_12_right', joints)
        self.assertNotIn('disc_c1_c2', joints)
        self.assertNotIn('radiocarpal_ulna_scaphoid_left', joints)
        self.assertEqual('functional', joints['scapulothoracic_left']['structural_type'])
        self.assertTrue(self.data['non_articulating_bones']['hyoid']['reason'])
        self.assertTrue(self.data['scope']['excluded_teeth_gomphoses'])
        self.assertTrue(self.data['scope']['additional_structures_outside_206'])

    def test_forearm_synovial_source_binding_cannot_use_shaft_syndesmosis(self):
        for key in ['proximal_radioulnar_left','distal_radioulnar_right']:
            bad=copy.deepcopy(self.data)
            j=next(j for j in bad['articulations'] if j['id']==key)
            j['sources']=['OS_FIBROUS','ISB_II']
            self.assertTrue(self.validator().validate_inventory(bad,DATA))

class LandmarkTests(unittest.TestCase):
    setUp = ArticulationTests.setUp
    validator = ArticulationTests.validator
    def test_every_joint_has_semantic_landmarks_without_invented_coordinates(self):
        path = DATA / 'joint_landmark_frame_atlas.json'
        self.assertTrue(path.exists(), 'Phase 3 landmark/frame atlas missing')
        atlas = json.loads(path.read_text())
        self.assertEqual([], self.validator().validate_frames(atlas, self.data, DATA))

    def test_frame_math_is_right_handed_and_rejects_degenerate_landmarks(self):
        mod = self.validator()
        self.assertTrue(hasattr(mod, 'orthonormal_frame'), 'Frame construction not implemented')
        xyz = mod.orthonormal_frame([0, 1, 0], [1, 0, 0])
        self.assertEqual(xyz, [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        for y,x in [([0,0,0],[1,0,0]), ([0,1,0],[0,2,0]), ([0,float('nan'),0],[1,0,0])]:
            with self.assertRaises(ValueError): mod.orthonormal_frame(y,x)
        self.assertAlmostEqual(mod.frame_determinant(mod.orthonormal_frame([1,2,3],[2,-1,0])), 1.)
        self.assertLess(mod.frame_determinant([[0,0,1],[0,1,0],[1,0,0]]), 0.)

class MovementTests(unittest.TestCase):
    setUp = ArticulationTests.setUp
    validator = ArticulationTests.validator

    def atlas(self):
        path = DATA / 'whole_body_movement_atlas.json'
        self.assertTrue(path.exists(), 'Phase 4 movement evidence atlas missing')
        return json.loads(path.read_text())

    def test_every_articulation_has_contextual_motion_evidence(self):
        self.assertEqual([], self.validator().validate_movement(self.atlas(), self.data, DATA))

    def test_omission_or_unqualified_rom_cannot_pass(self):
        for mode in ['joint', 'passive', 'source', 'context', 'hard_limit', 'confidence']:
            with self.subTest(mode=mode):
                bad = copy.deepcopy(self.atlas())
                p = bad['profiles']['hip']
                if mode == 'joint': del bad['joint_assignments']['distal_radioulnar_left']
                if mode == 'passive': del p['rom']['passive']
                if mode == 'source': p['sources'] = p['sources'][:1]
                if mode == 'context': del bad['observations']['cdc_hip_flexion']['posture']
                if mode == 'hard_limit': bad['observations']['cdc_hip_flexion']['use_as_joint_limit'] = True
                if mode == 'confidence': p['confidence'] = 'LOCKED'
                self.assertTrue(self.validator().validate_movement(bad, self.data, DATA))

    def test_composite_motion_and_follower_dof_cannot_be_misassigned(self):
        for mode in ['gross_shoulder', 'carpal', 'variant']:
            with self.subTest(mode=mode):
                bad = copy.deepcopy(self.atlas())
                if mode == 'gross_shoulder': bad['profiles']['gh']['rom']['passive']['observations'] = ['cdc_shoulder_flexion']
                if mode == 'carpal': bad['joint_assignments']['midcarpal_scaphoid_capitate_left']['independent_command_dof'] = 2
                if mode == 'variant': bad['joint_assignments']['cuboideonavicular_left']['variant'] = 'none'
                self.assertTrue(self.validator().validate_movement(bad, self.data, DATA))

    def test_unspecified_clinical_mode_and_level_references_are_not_silent(self):
        for mode in ['clinical', 'level']:
            bad = copy.deepcopy(self.atlas())
            if mode == 'clinical':
                bad['clinical_reference_observations']['thumb_ip'].append('cdc_hip_flexion')
            else:
                bad['level_reference_observations']['l2_l3'] = ['lumbar_lift_l5_sacrum']
            self.assertTrue(self.validator().validate_movement(bad, self.data, DATA))

    def test_textbook_chapters_are_one_work(self):
        bad = copy.deepcopy(self.atlas())
        bad['profiles']['fixed']['sources'] = ['OS_FIBROUS','OS_CARTILAGE']
        self.assertTrue(self.validator().validate_movement(bad,self.data,DATA))

    def test_shared_contact_ownership_and_hindfoot_command_are_explicit(self):
        atlas = self.atlas()
        self.assertTrue('command_groups' in atlas,'Explicit command groups missing')
        for key,dof in [('mandible',3),('c0_c1',2),('hindfoot_left',1),('hindfoot_right',1)]:
            g=atlas['command_groups'][key]
            self.assertEqual(g['command_dof'],dof)
            self.assertTrue(g['owner_joint'] or g['owner_control'])
        for mode in ['split','duplicate','hindfoot','owner']:
            bad=copy.deepcopy(atlas)
            if mode=='split': bad['joint_assignments']['tmj_right']['coupled_group']='independent_right_tmj'
            if mode=='duplicate': bad['joint_assignments']['atlantooccipital_right']['independent_command_dof']=2
            if mode=='hindfoot': del bad['command_groups']['hindfoot_left']
            if mode=='owner': bad['command_groups']['mandible']['owner_joint']='glenohumeral_left'
            self.assertTrue(self.validator().validate_movement(bad,self.data,DATA))

    def test_equal_dof_profile_swaps_are_rejected(self):
        for key,profile in [('hip_left','gh'),('glenohumeral_right','hip'),('thumb_ip_left','pip')]:
            bad=copy.deepcopy(self.atlas())
            bad['joint_assignments'][key]['profile_id']=profile
            self.assertTrue(self.validator().validate_movement(bad,self.data,DATA))

class GapTests(unittest.TestCase):
    setUp = ArticulationTests.setUp
    validator = ArticulationTests.validator

    def matrix(self):
        path = DATA / 'current_rig_anatomical_gap_matrix.json'
        self.assertTrue(path.exists(), 'Phase 5 complete gap matrix missing')
        return json.loads(path.read_text())

    def test_gap_matrix_covers_all_bones_joints_and_profiles(self):
        self.assertEqual([], self.validator().validate_gaps(self.matrix(), DATA))

    def test_stale_inputs_omissions_and_premature_acceptance_rejected(self):
        for mode in ['hash', 'joint', 'bone', 'profile', 'accepted', 'fact']:
            bad = copy.deepcopy(self.matrix())
            if mode == 'hash': next(iter(bad['input_sha256'].values()))['sha256'] = '0'*64
            if mode == 'joint': del bad['joints']['distal_radioulnar_left']
            if mode == 'bone': del bad['bones']['talus_left']
            if mode == 'profile': del bad['profiles']['patella']
            if mode == 'accepted': bad['production_approved'] = True
            if mode == 'fact': bad['static_facts']['canonical_bone_count'] = 206
            self.assertTrue(self.validator().validate_gaps(bad, DATA))

if __name__ == '__main__': unittest.main()
