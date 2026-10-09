"""Source-linked CT region observations are NOT validated osseous APP features."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'anatomy_fit'))
import nlm_ct_bony_landmark_coverage_audit as audit

SOURCES=HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit'
BUNDLE=SOURCES/'nlm_pelvic_ct_full_series_candidate_bundle_20261009.json'
REVIEWS=SOURCES/'nlm_pelvic_ct_full_series_candidate_review_20261009.json'


def read():
    return json.loads(BUNDLE.read_text()),json.loads(REVIEWS.read_text())


def out():
    return audit.audit(*read())


class TrueOsseousCoverageTests(unittest.TestCase):
    def test_all_ten_existing_observations_are_only_candidates(self):
        r=out()
        self.assertEqual(r['source_rows_verified'],72)
        self.assertEqual(r['original_candidate_review_count'],10)
        self.assertFalse(r['full_anatomical_pelvis_coverage_verified'])
        self.assertFalse(r['canonical_promotion_allowed'])

    def test_seven_physical_features_are_explicit_and_all_unverified(self):
        r=out()
        items=r['required_osseous_landmark_coverage']
        self.assertEqual(len(items),7)
        self.assertEqual({x['required_physical_osseous_landmark'] for x in items},
                         set(audit.REQUIRED_BONY_FEATURES))
        self.assertEqual(r['number_of_true_bony_landmarks_independently_verified'],0)
        self.assertTrue(all(x['specific_bony_landmark_verified'] is False for x in items))

    def test_bilateral_iliac_blades_do_not_become_bony_ASIS(self):
        items={x['required_physical_osseous_landmark']:x
               for x in out()['required_osseous_landmark_coverage']}
        self.assertEqual(items['asis_left']['region_review_observations'],2)
        self.assertEqual(items['asis_right']['region_review_observations'],2)
        self.assertEqual(items['asis_right']['unique_physical_scanner_levels'],[-372,-432])
        self.assertIn('not_an_identified_bony_ASIS',
                      items['asis_right']['reason_region_cannot_certify_landmark'])

    def test_pubic_region_never_claims_either_bony_pubic_tubercle(self):
        items={x['required_physical_osseous_landmark']:x
               for x in out()['required_osseous_landmark_coverage']}
        self.assertEqual(items['pubic_tubercle_left']['region_review_observations'],0)
        self.assertEqual(items['pubic_tubercle_right']['region_review_observations'],0)

    def test_sacrum_one_pixel_not_true_S1_rim_centre(self):
        items={x['required_physical_osseous_landmark']:x
               for x in out()['required_osseous_landmark_coverage']}
        self.assertEqual(items['s1_superior_endplate_centre']['region_review_observations'],1)
        self.assertEqual(items['s1_superior_endplate_centre']['unique_physical_scanner_levels'],[-402])
        self.assertTrue(items['s1_superior_endplate_centre']['requires_independently_segmented_or_traced_true_bone_feature'])

    def test_single_slice_femoral_region_not_spherical_head_centre(self):
        items={x['required_physical_osseous_landmark']:x
               for x in out()['required_osseous_landmark_coverage']}
        self.assertEqual(items['femoral_head_centre_left']['region_review_observations'],1)
        self.assertEqual(items['femoral_head_centre_right']['region_review_observations'],1)
        self.assertEqual(items['femoral_head_centre_left']['unique_physical_scanner_levels'],[-481])

    def test_true_ge_RAS_image_laterality_is_preserved(self):
        r=out()
        obs=r['candidate_observations']
        for o in obs:
            rcoord=o['candidate_scanner_RAS_mm_if_outer_FOV_origin'][0]
            if o['candidate_side_from_existing_review']=='right':
                self.assertGreater(rcoord,0)
            if o['candidate_side_from_existing_review']=='left':
                self.assertLess(rcoord,0)

    def test_candidate_pixel_coordinate_is_provisional_not_clinical(self):
        r=out()
        for obs in r['candidate_observations']:
            self.assertFalse(obs['original_GE_outer_edge_vs_pixel_centre_origin_verified'])
            self.assertFalse(obs['physical_bony_feature_identity_verified'])
            self.assertAlmostEqual(obs['axial_half_slice_thickness_mm'],1.5)
            self.assertAlmostEqual(obs['in_plane_half_pixel_mm'][0],.449219)

    def test_sample_bounds_and_groups_preserved_not_welded(self):
        r=out()
        a,b=r['source_scan_groups']
        self.assertEqual(a['source_S_covered_slab_mm'],[-451.5,-340.5])
        self.assertEqual(b['source_S_covered_slab_mm'],[-554.5,-449.5])
        self.assertEqual(a['slice_count'],37)
        self.assertEqual(b['slice_count'],35)
        self.assertFalse(a['full_bony_pelvis_coverage_proven'])
        self.assertFalse(b['full_bony_pelvis_coverage_proven'])

    def test_right_as_left_cannot_pass_orientation_check(self):
        b,r=read()
        # Previously observed left femoral head resides on negative scanner R.
        for o in r['observations']:
            if o['candidate_label']=='femoral_head_left':
                o['candidate_label']='femoral_head_right'
                break
        with self.assertRaisesRegex(ValueError,'laterality conflicts'):
            audit.audit(b,r)

    def test_right_candidate_pixel_on_opposite_scanner_side_is_rejected(self):
        b,r=read()
        for o in r['observations']:
            if o['candidate_label']=='femoral_head_right':
                o['pixel']['column']=400
                break
        with self.assertRaisesRegex(ValueError,'laterality conflicts'):
            audit.audit(b,r)

    def test_both_left_and_right_in_identifier_is_rejected(self):
        b,r=read()
        r['observations'][0]['observation_id']='obs-left-right-conflicting-side'
        with self.assertRaisesRegex(ValueError,'laterality conflicts'):
            audit.audit(b,r)

    def test_missing_sha_rejected(self):
        b,r=read()
        r['observations'][0]['source_png_sha256']='deadbeef'
        with self.assertRaisesRegex(ValueError,'source-byte identity mismatch'):
            audit.audit(b,r)

    def test_wrong_physical_level_rejected(self):
        b,r=read()
        r['observations'][0]['scanner_S_mm'] += 3
        with self.assertRaisesRegex(ValueError,'source scanner coordinate mismatch'):
            audit.audit(b,r)

    def test_missing_original_observation_fails_closed(self):
        b,r=read()
        r['observations'].pop()
        with self.assertRaisesRegex(ValueError,'ten unapproved'):
            audit.audit(b,r)

    def test_forged_approved_canonical_claim_rejected(self):
        b,r=read()
        r['canonical_promotion_allowed']=True
        with self.assertRaisesRegex(ValueError,'canonical promotion'):
            audit.audit(b,r)

    def test_malformed_original_candidate_pixel_index_rejected(self):
        b,r=read()
        r['observations'][0]['pixel']['column']=999
        with self.assertRaisesRegex(ValueError,'pixel row/column'):
            audit.audit(b,r)

    def test_reviewed_pubic_midline_observation_is_not_bilateral_feature(self):
        r=out()
        one=[x for x in r['candidate_observations']
             if x['candidate_label']=='pubic_region']
        self.assertEqual(len(one),1)
        self.assertEqual(one[0]['candidate_side_from_existing_review'],'midline')

    def test_no_external_approval_or_source_bytes_in_output(self):
        r=out()
        txt=json.dumps(r)
        self.assertNotIn('source_png_raw_pixels',txt)
        self.assertFalse(r['CT_PNG_to_HU_conversion_verified'])
        self.assertFalse(r['patient_scanner_to_HGPT_world_transform_verified'])
        self.assertFalse(r['skeleton_or_mesh_modified'])
        self.assertFalse(r['bony_source_meshes_independently_verified'])

    def test_input_data_unchanged_and_audit_repeatable(self):
        b,r=read()
        before=json.dumps([b,r],sort_keys=True)
        output=audit.audit(b,r)
        self.assertEqual(output,audit.audit(b,r))
        self.assertEqual(json.dumps([b,r],sort_keys=True),before)


if __name__=='__main__':
    unittest.main()
