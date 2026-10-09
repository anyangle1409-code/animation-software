"""Raw original CT 3D occupancy threshold stability, NEVER a bone segmentation."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'anatomy_fit'))
import nlm_original_ct_raw_threshold_sensitivity as audit

SOURCE=(HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/'
        'nlm_pelvic_ct_full_series_candidate_bundle_20261009.json')


def blank():
    return {'any':[0]*audit.TILE_COUNT,'eight':[0]*audit.TILE_COUNT}


def set_tile(blocks,index,raw=1550):
    blocks['any'][index]=raw
    blocks['eight'][index]=raw


class RawThresholdSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=json.loads(SOURCE.read_text())

    def test_real_source_manifest_has_original_72_frames(self):
        self.assertEqual(sum(len(x['slices']) for x in self.bundle['series']),72)
        self.assertEqual(len(self.bundle['series']),2)
        self.assertFalse(self.bundle['canonical_promotion_allowed'])

    def test_one_bright_pixel_counts_for_any_not_eight(self):
        pixels=[0]*(512*512)
        pixels[0]=1800
        s=audit.compute_tile_order_stats(pixels)
        self.assertEqual(s['any'][0],1800)
        self.assertEqual(s['eight'][0],0)

    def test_eight_bright_pixels_required_for_eight_operator(self):
        pixels=[0]*(512*512)
        for x in range(8):
            pixels[x]=1600
        s=audit.compute_tile_order_stats(pixels)
        self.assertEqual(s['eight'][0],1600)
        self.assertEqual(s['any'][0],1600)
        self.assertEqual(s['eight'][1],0)

    def test_nonfinite_or_corrupt_pixel_vector_rejected(self):
        pixels=[0]*(512*512)
        pixels[0]=-2
        with self.assertRaisesRegex(ValueError,'nonfinite/negative/out of range'):
            audit.compute_tile_order_stats(pixels)

    def test_bad_shape_rejected(self):
        with self.assertRaisesRegex(ValueError,'512x512'):
            audit.compute_tile_order_stats([1,2,3])

    def test_three_dimensional_six_neighbor_across_source_adjacent_slices(self):
        first=bytearray(audit.TILE_COUNT)
        second=bytearray(audit.TILE_COUNT)
        # Adjacent in physical source Z within ONE source acquisition group.
        first[123]=second[123]=1
        self.assertEqual(audit._component_sizes([first,second]),[2])

    def test_no_wraparound_across_opposite_image_edges(self):
        a=bytearray(audit.TILE_COUNT)
        a[63]=a[64]=1
        self.assertEqual(audit._component_sizes([a]),[1,1])

    def test_diagonal_only_not_six_connected(self):
        a=bytearray(audit.TILE_COUNT)
        a[0]=a[65]=1
        self.assertEqual(audit._component_sizes([a]),[1,1])

    def test_one_slice_in_plane_four_neighbors_connected(self):
        a=bytearray(audit.TILE_COUNT)
        for i in (64,65,66,130):
            a[i]=1
        self.assertEqual(audit._component_sizes([a]),[4])

    def test_reference_comparison_jaccard(self):
        a=[bytearray([1,1,0,0])]
        b=[bytearray([1,0,1,0])]
        self.assertAlmostEqual(audit._jaccard(a,b),1/3)

    def test_empty_masks_are_identically_equal(self):
        a=[bytearray(audit.TILE_COUNT)]
        self.assertEqual(audit._jaccard(a,a),1.0)
        self.assertEqual(audit._component_sizes(a),[])

    def test_threshold_monotonicity_and_component_split(self):
        a=blank()
        b=blank()
        set_tile(a,10,1550)
        set_tile(a,11,1200)
        set_tile(b,10,1550)
        set_tile(b,11,1200)
        r=audit.evaluate_group([a,b],'eight')
        q={x['raw_stored_PNG_scalar_cutoff']:x for x in r['results']}
        self.assertEqual(q[900]['active_8x8x_slice_blocks'],4)
        self.assertEqual(q[1200]['active_8x8x_slice_blocks'],4)
        self.assertEqual(q[1500]['active_8x8x_slice_blocks'],2)
        self.assertEqual(q[1800]['active_8x8x_slice_blocks'],0)
        self.assertEqual(q[1200]['component_count_6_neighbor'],1)
        self.assertEqual(q[1500]['component_count_6_neighbor'],1)
        self.assertAlmostEqual(q[1500]['jaccard_to_same_operator_raw_1200'],.5)
        self.assertTrue(r['occupancy_monotone_nonincreasing_with_threshold'])
        self.assertFalse(r['bone_threshold_supported_by_anatomy'])

    def test_all_thresholds_expressed_as_raw_not_HU(self):
        self.assertEqual(audit.THRESHOLDS,(900,1050,1200,1350,1500,1800))
        a=blank()
        r=audit.evaluate_group([a,a],'any')
        self.assertTrue(all(x['not_a_bone_mask_or_HU_threshold'] for x in r['results']))

    def test_bad_operator_rejected(self):
        with self.assertRaisesRegex(ValueError,'invalid source tile'):
            audit.evaluate_group([blank(),blank()],'approved_bone')

    def test_short_tile_order_stat_vector_rejected(self):
        a=blank()
        a['eight']=[1000]
        with self.assertRaisesRegex(ValueError,'missing source tile'):
            audit.evaluate_group([a,a],'eight')

    def test_threshold_list_changed_without_review_rejected(self):
        with self.assertRaisesRegex(ValueError,'fixed stored scalar thresholds'):
            audit.evaluate_group([blank(),blank()],'eight',(1000,))

    def test_synthetic_72_frame_bundle_no_CTs_downloaded_or_promoted(self):
        before=json.dumps(self.bundle,sort_keys=True)
        def fake(row):
            v=blank()
            v['any'][101]=1600
            v['eight'][101]=1600
            return row['source_id'],v
        result=audit.analyze(self.bundle,fake)
        self.assertEqual(result['source_slices_verified'],72)
        self.assertEqual(result['source_groups_evaluated_separately'],2)
        self.assertTrue(result['thresholds_are_original_PNG_stored_scalars_not_HU'])
        self.assertTrue(result['comparison_is_not_original_Blender_occupancy_implementation'])
        for key in ('provisional_image_intensity_to_HU_conversion_verified',
                    'cortical_or_cancellous_bone_label_independently_verified',
                    'individual_bones_separated_from_artifacts_or_nonbone',
                    '3d_bone_surface_extracted','canonical_promotion_allowed'):
            self.assertFalse(result[key])
        self.assertEqual(json.dumps(self.bundle,sort_keys=True),before)

    def test_executed_original_NLM_source_results_are_pinned(self):
        source=(HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/'
                'nlm_ct_raw_threshold_sensitivity_verified_20261009.json')
        result=json.loads(source.read_text())
        self.assertEqual(result['source_slices_verified'],72)
        self.assertEqual(result['source_groups_evaluated_separately'],2)
        self.assertTrue(result['original_NLM_PNG_sha256_verified_for_each_image'])
        self.assertFalse(result['canonical_promotion_allowed'])
        self.assertFalse(result['cortical_or_cancellous_bone_label_independently_verified'])
        self.assertFalse(result['provisional_image_intensity_to_HU_conversion_verified'])
        self.assertTrue(result['published_threshold_sweep_only_not_raw_medical_images'])

    def test_real_72_frame_threshold_1200_to_1800_is_topologically_unstable(self):
        source=(HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/'
                'nlm_ct_raw_threshold_sensitivity_verified_20261009.json')
        record=json.loads(source.read_text())
        expected=[(10452,3704),(7311,2798)]
        for group,(before,after) in zip(record['group_reports'],expected):
            op=next(x for x in group['operators'] if x['operator']=='any')
            r={x['raw_stored_PNG_scalar_cutoff']:x for x in op['results']}
            self.assertEqual(r[1200]['active_8x8x_slice_blocks'],before)
            self.assertEqual(r[1800]['active_8x8x_slice_blocks'],after)
            self.assertGreater((before-after)/before,.60)
            self.assertLess(r[1800]['jaccard_to_same_operator_raw_1200'],.40)
            self.assertGreater(r[1200]['largest_component_block_fraction'],
                               r[1800]['largest_component_block_fraction'])

    def test_real_72_frame_source_groups_remain_separate(self):
        source=(HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/'
                'nlm_ct_raw_threshold_sensitivity_verified_20261009.json')
        data=json.loads(source.read_text())
        self.assertEqual([g['individual_group_original_pinned_source_count']
                          for g in data['group_reports']],[37,35])
        self.assertTrue(all(g['no_3d_components_connected_to_other_scanner_group']
                            for g in data['group_reports']))

    def test_missing_source_record_fails_closed(self):
        def bad(row):
            return 'not-the-same-id',blank()
        with self.assertRaisesRegex(ValueError,'duplicate or missing CT'):
            audit.analyze(self.bundle,bad)


if __name__=='__main__':
    unittest.main()
