"""Protect NLM 72-slice volume against rotated / mirrored in-plane CT frames."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE / "anatomy_fit"))
import nlm_ct_72_header_orientation_audit as audit

BUNDLE=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
        "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json")


def source_case():
    bundle=json.loads(BUNDLE.read_text())
    headers={}
    for group in bundle["series"]:
        for row in group["slices"]:
            cx,cy,z=row["scanner_centre_RAS_mm"]
            half_x=row["scanner_grid"][0]*row["pixel_spacing_mm"][0]/2
            half_y=row["scanner_grid"][1]*row["pixel_spacing_mm"][1]/2
            # 0.898438*512 = 460.000256 mm, matching source GE FOV.
            safe={
                "image_dimensions":list(row["scanner_grid"]),
                "pixel_spacing_mm":list(row["pixel_spacing_mm"]),
                "slice_thickness_mm":row["slice_thickness_mm"],
                "reported_plane_centre_RAS_mm":[cx,cy,z],
                "plane_TL_RAS_mm":[cx+half_x,cy+half_y,z],
                "plane_TR_RAS_mm":[cx-half_x,cy+half_y,z],
                "plane_BR_RAS_mm":[cx-half_x,cy-half_y,z],
                "normal_RAS":list(row["slice_normal_RAS"]),
            }
            headers[row["source_id"]]={
                "source_header_sha256":row["source_header_sha256"],
                "safe_scanner_geometry":safe}
    return bundle,headers


def selected(case,number=20):
    rows=[r for group in case[0]["series"] for r in group["slices"]]
    return case[1][rows[number]["source_id"]]


class OriginalOrientationTests(unittest.TestCase):
    def test_source_bundle_has_real_72_slices_two_groups(self):
        b,h=source_case()
        self.assertEqual(sum(len(g["slices"]) for g in b["series"]),72)
        self.assertEqual(len(h),72)

    def test_valid_synthetic_source_header_geometry_is_noncanonical(self):
        b,h=source_case()
        r=audit.verify_72_original_headers(b,h)
        self.assertEqual(r["source_header_count_verified"],72)
        self.assertEqual(len(r["source_groups"]),2)
        self.assertTrue(r["cross_group_image_axes_aligned"])
        self.assertFalse(r["canonical_promotion_allowed"])
        self.assertFalse(r["independent_clinical_bone_surfaces_verified"])

    def test_original_image_orientation_axes_match_expected_RAS(self):
        b,h=source_case()
        r=audit.verify_72_original_headers(b,h)
        for group in r["source_groups"]:
            self.assertEqual(group["pixel_column_increasing_RAS_unit"],[-1,0,0])
            self.assertEqual(group["pixel_row_increasing_RAS_unit"],[0,-1,0])
            self.assertEqual(group["header_normal_RAS_unit"],[0,0,1])

    def test_one_frame_rotated_180_deg_same_normal_rejected(self):
        b,h=source_case()
        # A source bitmap rotated 180 degrees can retain same centre,
        # same pixel spacing and same axial normal; prior manifest
        # couldn't catch this.
        one=selected((b,h))["safe_scanner_geometry"]
        cx,cy,z=one["reported_plane_centre_RAS_mm"]
        half=256*one["pixel_spacing_mm"][0]
        one["plane_TL_RAS_mm"]=[cx-half,cy-half,z]
        one["plane_TR_RAS_mm"]=[cx+half,cy-half,z]
        one["plane_BR_RAS_mm"]=[cx+half,cy+half,z]
        with self.assertRaisesRegex(ValueError,"axis changed within scan group"):
            audit.verify_72_original_headers(b,h)

    def test_one_frame_rotated_90_deg_same_normal_rejected(self):
        b,h=source_case()
        one=selected((b,h))["safe_scanner_geometry"]
        cx,cy,z=one["reported_plane_centre_RAS_mm"]
        half=256*one["pixel_spacing_mm"][0]
        one["plane_TL_RAS_mm"]=[cx-half,cy+half,z]
        one["plane_TR_RAS_mm"]=[cx-half,cy-half,z]
        one["plane_BR_RAS_mm"]=[cx+half,cy-half,z]
        with self.assertRaisesRegex(ValueError,"axis changed within scan group"):
            audit.verify_72_original_headers(b,h)

    def test_one_frame_mirrored_about_column_axis_rejected(self):
        b,h=source_case()
        one=selected((b,h))["safe_scanner_geometry"]
        one["plane_TL_RAS_mm"],one["plane_TR_RAS_mm"]=(
            one["plane_TR_RAS_mm"],one["plane_TL_RAS_mm"])
        with self.assertRaisesRegex(ValueError,"not right-handed"):
            audit.verify_72_original_headers(b,h)

    def test_second_group_rotated_180_rejected_without_registered_transform(self):
        b,h=source_case()
        for row in b["series"][1]["slices"]:
            one=h[row["source_id"]]["safe_scanner_geometry"]
            cx,cy,z=one["reported_plane_centre_RAS_mm"]
            a=one["pixel_spacing_mm"][0]*256
            one["plane_TL_RAS_mm"]=[cx-a,cy-a,z]
            one["plane_TR_RAS_mm"]=[cx+a,cy-a,z]
            one["plane_BR_RAS_mm"]=[cx+a,cy+a,z]
        with self.assertRaisesRegex(ValueError,"unregistered image axis mismatch across scan groups"):
            audit.verify_72_original_headers(b,h)

    def test_unrelated_original_header_sha_rejected(self):
        b,h=source_case()
        selected((b,h))["source_header_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"header byte SHA changed"):
            audit.verify_72_original_headers(b,h)

    def test_missing_one_original_header_rejected(self):
        b,h=source_case()
        del h[next(iter(h))]
        with self.assertRaisesRegex(ValueError,"every pinned original header"):
            audit.verify_72_original_headers(b,h)

    def test_shifted_source_physical_centre_rejected(self):
        b,h=source_case()
        selected((b,h))["safe_scanner_geometry"]["reported_plane_centre_RAS_mm"][1]+=3
        with self.assertRaisesRegex(ValueError,"RAS centre differs"):
            audit.verify_72_original_headers(b,h)

    def test_wrong_source_pixel_spacing_rejected(self):
        b,h=source_case()
        selected((b,h))["safe_scanner_geometry"]["pixel_spacing_mm"]=[.5,.5]
        with self.assertRaisesRegex(ValueError,"in-plane spacing differs"):
            audit.verify_72_original_headers(b,h)

    def test_wrong_source_normal_rejected(self):
        b,h=source_case()
        selected((b,h))["safe_scanner_geometry"]["normal_RAS"]=[0,0,-1]
        with self.assertRaisesRegex(ValueError,"scanner normal differs"):
            audit.verify_72_original_headers(b,h)

    def test_same_source_bone_remains_unverified_even_after_all_72_checks(self):
        b,h=source_case()
        r=audit.verify_72_original_headers(b,h)
        for f in ("image_pixels_downloaded_or_committed",
                  "index_zero_pixel_centre_vs_outer_edge_convention_verified",
                  "original_PNG_stored_scalars_calibrated_as_HU",
                  "candidate_bone_regions_independently_labelled",
                  "scanner_patient_RAS_to_HGPT_world_verified",
                  "skeleton_or_mesh_modified"):
            self.assertFalse(r[f])

    def test_source_bundle_input_and_parsed_headers_immutable(self):
        b,h=source_case()
        raw=json.dumps([b,h],sort_keys=True)
        audit.verify_72_original_headers(b,h)
        self.assertEqual(json.dumps([b,h],sort_keys=True),raw)

    def test_network_source_name_must_be_pinned_four_digits(self):
        with self.assertRaisesRegex(ValueError,"unsafe NLM"):
            audit._fetch_one("../other")
        with self.assertRaisesRegex(ValueError,"unsafe NLM"):
            audit._fetch_one("cvm1734f.txt")


if __name__=="__main__":
    unittest.main()
