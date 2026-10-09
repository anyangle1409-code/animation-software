"""Protect single-specimen CT source status from accidental anatomy promotion."""
import json
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/potential_bone_geometry_sources_20261009.json'


class SingleSpecimenSourcePolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads(SOURCE.read_text())
        cls.source=cls.record['sources'][0]

    def test_explicitly_unapproved_source_register(self):
        self.assertFalse(self.record['canonical_promotion_allowed'])
        self.assertEqual(self.record['status'],'POTENTIAL_GEOMETRY_REFERENCE_NOT_COORDINATE_TARGET')

    def test_one_donor_cannot_select_population_mean(self):
        self.assertEqual(self.source['individuals'],1)
        self.assertTrue(self.source['no_stature_assumed'])
        self.assertIsNone(self.source['stature_m'])
        self.assertTrue(self.record['independent_population_reference_required'])

    def test_no_ct_data_or_real_bony_surfaces_claimed(self):
        for key in ('data_downloaded','bone_surfaces_generated',
                    'specific_landmarks_selected','human_anatomy_validated'):
            self.assertFalse(self.source[key])
        self.assertFalse(self.source['derived_segmented_bone_mesh_currently_available_in_repo'])
        self.assertIsNone(self.source['current_segmentation_sha256'])

    def test_official_custodian_and_access_link(self):
        self.assertIn('National Library of Medicine',self.source['custodian'])
        self.assertEqual(self.source['source_urls']['official_access'],
                         'https://www.nlm.nih.gov/research/visible/getting_data.html')

    def test_geometry_use_and_population_source_separated(self):
        self.assertIn('SURFACE shape',self.source['allowed_role'])
        self.assertIn('cannot establish',self.source['disallowed_role'])
        self.assertGreaterEqual(len(self.source['must_verify']),6)

    def test_upstream_reference_not_silent_medical_approval(self):
        self.assertIn('bone_feature_observation_packet.py',
                      ' '.join(self.record['consumer_tools']))
        self.assertEqual(self.record['source_count'],len(self.record['sources']))


if __name__=='__main__':
    unittest.main()
