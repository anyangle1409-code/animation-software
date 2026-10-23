import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'recovery_summary.py'


class NativeSummary(unittest.TestCase):
    def load(self):
        self.assertTrue(path.exists(), 'native result summary must exist')
        spec = importlib.util.spec_from_file_location('summary', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_empty_results_cannot_pass(self):
        summary = self.load().summarize({}, ['squat'], 9)
        self.assertFalse(summary['complete'])
        self.assertFalse(summary['quality_pass'])

    def test_missing_frame_cannot_pass(self):
        summary = self.load().summarize({'squat': {'frames': [{}] * 8}}, ['squat'], 9)
        self.assertFalse(summary['complete'])

    def test_existing_deformation_failures_stay_failed(self):
        frames = [{'collapse_lt_0_1': 0, 'stretch_gt_2': 0, 'self_intersecting_pairs': 0}] * 9
        frames[4] = {**frames[4], 'stretch_gt_2': 2}
        summary = self.load().summarize({'squat': {'frames': frames}}, ['squat'], 9)
        self.assertTrue(summary['complete'])
        self.assertFalse(summary['quality_pass'])
        self.assertEqual(len(summary['quality_failures']), 1)

    def test_complete_clean_trajectory_passes(self):
        frames = [{'collapse_lt_0_1': 0, 'stretch_gt_2': 0, 'self_intersecting_pairs': 0}] * 9
        summary = self.load().summarize({'squat': {'frames': frames}}, ['squat'], 9)
        self.assertTrue(summary['quality_pass'])

    def test_missing_metric_does_not_count_as_zero(self):
        summary = self.load().summarize({'squat': {'frames': [{}] * 9}}, ['squat'], 9)
        self.assertFalse(summary['quality_pass'])

class RecoveryIdentity(unittest.TestCase):
    def test_remesh_bridge_requires_matching_verified_source_and_count(self):
        spec = importlib.util.spec_from_file_location('summary', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, 'verified_remesh_count'), 'validated in-memory remesh bridge is required')
        report = {'sha256': 'abc', 'summary': {'pass': 7, 'fail': 0}, 'measured': {'body_vertices': 219974}}
        self.assertEqual(module.verified_remesh_count(report, 'abc', 219974), 219974)
        for sha, count in [('wrong', 219974), ('abc', 21600)]:
            with self.assertRaises(ValueError): module.verified_remesh_count(report, sha, count)
        report['summary']['fail'] = 1
        with self.assertRaises(ValueError): module.verified_remesh_count(report, 'abc', 219974)
