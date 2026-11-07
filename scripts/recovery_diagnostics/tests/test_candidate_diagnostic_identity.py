import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'diagnose_candidates_blender.py'

class DiagnosticIdentity(unittest.TestCase):
    def test_only_hash_pinned_recovered_cohort_is_accepted_for_diagnostics(self):
        self.assertTrue(PATH.exists(), 'separate recovered-candidate diagnostic adapter required')
        spec=importlib.util.spec_from_file_location('diagnostic',PATH)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        self.assertEqual(mod.candidate_name('2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c'),'W8')
        with self.assertRaises(ValueError):mod.candidate_name('not-the-source')
        self.assertEqual(mod.PRODUCTION_BONES,67)
        self.assertEqual(mod.CANDIDATE_BONES,77)
