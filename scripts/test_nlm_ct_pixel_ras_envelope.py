"""Pixel-to-original-scanner-RAS envelope test without anatomical acceptance."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_ct_pixel_ras_envelope as pixel


def source_1300_header_geometry():
    # Actual original GE scanner frame values in NLM original header
    # cvm1300f.txt, not a Home Gym PT anatomical registration.
    return {
        "image_dimensions":[512,512],
        "plane_TL_RAS_mm":[228.,291.,102.],
        "plane_TR_RAS_mm":[-232.,291.,102.],
        "plane_BR_RAS_mm":[-232.,-169.,102.],
        "pixel_spacing_mm":[.898438,.898438],
        "slice_thickness_mm":3.
    }


class PixelRasObservation(unittest.TestCase):
    def test_source_first_pixel_candidate_centre(self):
        r=pixel.place_pixel(source_1300_header_geometry(),0,0)
        self.assertAlmostEqual(r["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][0],
                               228-460/1024,places=9)
        self.assertAlmostEqual(r["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][1],
                               291-460/1024,places=9)
        self.assertAlmostEqual(r["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][2],102)

    def test_last_pixel_also_within_scanner_extent(self):
        r=pixel.place_pixel(source_1300_header_geometry(),511,511)
        a=r["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"]
        self.assertAlmostEqual(a[0],-232+460/1024,places=9)
        self.assertAlmostEqual(a[1],-169+460/1024,places=9)

    def test_slice_thickness_3mm_is_not_hidden(self):
        r=pixel.place_pixel(source_1300_header_geometry(),200,200)
        self.assertEqual(r["source_slab_S_range_mm"],[100.5,103.5])
        self.assertAlmostEqual(r["in_plane_half_pixel_size_mm"][0],.44921875)

    def test_four_corners_bound_edge_origin_pixel(self):
        r=pixel.place_pixel(source_1300_header_geometry(),0,0)
        corners=r["candidate_cell_four_corners_RAS_mm_if_outer_FOV_corners"]
        self.assertEqual(len(corners),4)
        self.assertEqual(corners[0],[228,291,102])
        self.assertAlmostEqual(corners[1][0],228-460/512,places=9)
        self.assertAlmostEqual(corners[2][1],291-460/512,places=9)

    def test_pixel_to_world_numerical_hypothesis_not_verified(self):
        r=pixel.place_pixel(source_1300_header_geometry(),200,200)
        for f in ("voxel_index_to_physical_sample_centre_convention_verified",
                  "original_CT_pixel_HU_verified","anatomical_region_identified",
                  "bone_surface_segmentation_verified","HomeGymPT_world_transform_applied",
                  "canonical_promotion_allowed"):
            self.assertFalse(r[f])

    def test_source_frame_left_right_orientation_not_flipped(self):
        upper_left=pixel.place_pixel(source_1300_header_geometry(),0,0)
        upper_right=pixel.place_pixel(source_1300_header_geometry(),0,511)
        self.assertGreater(upper_left["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][0],
                           upper_right["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][0])

    def test_scanner_origin_translation_does_not_change_size(self):
        g=source_1300_header_geometry()
        ref=pixel.place_pixel(g,17,31)
        h=copy.deepcopy(g)
        for key in ("plane_TL_RAS_mm","plane_TR_RAS_mm","plane_BR_RAS_mm"):
            h[key]=[h[key][i]+(15 if i==1 else 0) for i in range(3)]
        changed=pixel.place_pixel(h,17,31)
        self.assertEqual(ref["source_pixel_in_plane_step_mm"],
                         changed["source_pixel_in_plane_step_mm"])
        self.assertAlmostEqual(
            changed["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][1]-
            ref["candidate_pixel_centre_RAS_mm_if_outer_FOV_corners"][1],15)

    def test_row_outside_image_rejected(self):
        with self.assertRaisesRegex(ValueError,"pixel indices"):
            pixel.place_pixel(source_1300_header_geometry(),512,0)

    def test_negative_column_rejected(self):
        with self.assertRaisesRegex(ValueError,"pixel indices"):
            pixel.place_pixel(source_1300_header_geometry(),0,-1)

    def test_fractional_pixel_index_rejected(self):
        with self.assertRaisesRegex(ValueError,"pixel indices"):
            pixel.place_pixel(source_1300_header_geometry(),0,2.5)

    def test_malformed_scanner_position_rejected(self):
        h=source_1300_header_geometry()
        h["plane_TR_RAS_mm"][2]=float("nan")
        with self.assertRaisesRegex(ValueError,"invalid scanner"):
            pixel.place_pixel(h,0,0)

    def test_untrusted_scale_refused(self):
        h=source_1300_header_geometry()
        h["pixel_spacing_mm"]=[1.,1.]
        with self.assertRaisesRegex(ValueError,"disagrees with source spacing"):
            pixel.place_pixel(h,0,0)

    def test_inaccurate_thickness_refused(self):
        h=source_1300_header_geometry()
        h["slice_thickness_mm"]=-2.
        with self.assertRaisesRegex(ValueError,"invalid CT slice thickness"):
            pixel.place_pixel(h,0,0)

    def test_different_image_size_rejected(self):
        h=source_1300_header_geometry()
        h["image_dimensions"]=[256,256]
        with self.assertRaisesRegex(ValueError,"unknown original scanner"):
            pixel.place_pixel(h,0,0)

    def test_record_is_read_only(self):
        h=source_1300_header_geometry()
        before=json.dumps(h,sort_keys=True)
        pixel.place_pixel(h,255,256)
        self.assertEqual(before,json.dumps(h,sort_keys=True))


if __name__=="__main__":
    unittest.main()
