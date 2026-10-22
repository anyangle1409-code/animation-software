import json
from pathlib import Path
import tempfile
import unittest
from experiments.anatomical_muscles.compile_exercise import compile_request

class CompileExerciseTests(unittest.TestCase):
    def test_reusable_curl_example(self):
        result=compile_request('hgpt.exercise.biceps_curl.bilateral.v1','concentric',.5,.8)
        self.assertEqual(result['exercise_id'],'hgpt.exercise.biceps_curl.bilateral.v1')
        self.assertTrue(any(x['muscle_id']=='hgpt.muscle.biceps_brachii_long.L' for x in result['muscles']))
        self.assertEqual(result['activation_source'],'explicit_exercise_rule_scaled_by_caller')
    def test_unknown_exercise_rejected(self):
        with self.assertRaises(ValueError): compile_request('unknown','concentric',.5,1)

if __name__=='__main__': unittest.main()
