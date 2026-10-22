import copy
import json
from pathlib import Path
import unittest
from experiments.anatomical_muscles import contract, registry

ROOT=Path(__file__).resolve().parents[3]
SEED=json.loads((ROOT/'docs/ORIGINAL_V1_MUSCLE_REGISTRY_SEED_20261022.json').read_text())
EXERCISES=ROOT/'experiments/anatomical_muscles/exercise_contracts.json'

class ExerciseContractTests(unittest.TestCase):
    def setUp(self):
        self.muscles=registry.expand(SEED)
        self.contracts=json.loads(EXERCISES.read_text()) if EXERCISES.exists() else {'exercises':[]}

    def test_permanent_ids_are_namespaced_unique_and_bilateral(self):
        data=self.muscles
        ids=[m['id'] for m in data['muscles']]
        self.assertEqual(len(ids),120)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertIn('hgpt.muscle.biceps_brachii_long.L',ids)
        self.assertIn('hgpt.muscle.biceps_brachii_long.R',ids)
        self.assertTrue(all(m['identity']['immutable'] for m in data['muscles']))

    def test_example_contracts_validate_and_resolve(self):
        errors=contract.validate_library(self.contracts,self.muscles)
        self.assertEqual(errors,[])
        self.assertEqual({e['id'] for e in self.contracts['exercises']},{
          'hgpt.exercise.biceps_curl.bilateral.v1',
          'hgpt.exercise.shoulder_press.bilateral.v1',
          'hgpt.exercise.squat.bodyweight.v1'})

    def test_every_rule_has_pose_length_activation_stabilization_and_skin(self):
        for exercise in self.contracts['exercises']:
            for phase in exercise['phases']:
                self.assertTrue(phase['joint_targets'])
                self.assertTrue(phase['stabilization']['muscle_ids'])
                for rule in phase['muscles']:
                    self.assertIn(rule['length_change'],{'shortening','lengthening','near_isometric','variable'})
                    self.assertEqual(rule['activation_estimate']['kind'],'normalized_visual_estimate')
                    self.assertLessEqual(rule['activation_estimate']['range'][1],1)
                    self.assertIn(rule['role'],{'agonist','antagonist','synergist','stabilizer'})
                    self.assertTrue(rule['deformation']['mode'])
                    self.assertTrue(rule['skin_response']['mode'])

    def test_joint_pose_and_activation_are_independent_inputs(self):
        ex=self.contracts['exercises'][0]
        a=contract.sample_phase(ex,'concentric',.5,activation_scale=0)
        b=contract.sample_phase(ex,'concentric',.5,activation_scale=1)
        self.assertEqual(a['joint_targets'],b['joint_targets'])
        self.assertTrue(all(m['visual_activation']==0 for m in a['muscles']))
        self.assertTrue(any(m['visual_activation']>0 for m in b['muscles']))
        self.assertEqual([m['length_change'] for m in a['muscles']],[m['length_change'] for m in b['muscles']])

    def test_progress_moves_pose_without_silently_changing_activation(self):
        ex=self.contracts['exercises'][0]
        a=contract.sample_phase(ex,'concentric',0,1)
        b=contract.sample_phase(ex,'concentric',1,1)
        self.assertNotEqual(a['joint_targets'],b['joint_targets'])
        self.assertEqual([m['visual_activation'] for m in a['muscles']],[m['visual_activation'] for m in b['muscles']])

    def test_phase_sampling_interpolates_ranges_without_inferring_force(self):
        squat=next(e for e in self.contracts['exercises'] if '.squat.' in e['id'])
        result=contract.sample_phase(squat,'descent',.5,.8)
        knee=next(j for j in result['joint_targets'] if j['joint_id']=='hgpt.joint.knee.L')
        self.assertGreater(knee['angle_deg'][0],0)
        self.assertFalse(result['claims']['force'])
        self.assertFalse(result['claims']['emg'])
        self.assertEqual(result['activation_source'],'explicit_exercise_rule_scaled_by_caller')

    def test_invalid_ids_ranges_and_pose_coupling_rejected(self):
        bad=copy.deepcopy(self.contracts)
        bad['exercises'][0]['phases'][0]['muscles'][0]['muscle_id']='unknown'
        self.assertTrue(contract.validate_library(bad,self.muscles))
        bad=copy.deepcopy(self.contracts)
        bad['exercises'][0]['phases'][0]['muscles'][0]['activation_estimate']['range']=[.9,.2]
        self.assertTrue(contract.validate_library(bad,self.muscles))
        bad=copy.deepcopy(self.contracts)
        bad['exercises'][0]['phases'][0]['muscles'][0]['activation_estimate']['source']='joint_angle'
        self.assertTrue(contract.validate_library(bad,self.muscles))

    def test_library_has_sources_and_no_exact_emg_claim(self):
        self.assertTrue(self.contracts['sources'])
        self.assertEqual(self.contracts['activation_semantics']['meaning'],'visual_relative_estimate_not_emg_force_or_clinical_prescription')
        self.assertFalse(self.contracts['activation_semantics']['derive_from_pose'])

if __name__=='__main__': unittest.main()
