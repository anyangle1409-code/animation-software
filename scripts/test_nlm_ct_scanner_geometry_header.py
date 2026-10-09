"""Sanitized GE scanner geometry parser tests: no historical identifiers emitted."""
import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_ct_scanner_geometry_header as h


def fixture(location=389.):
    v={
        "width_pixels":512,"height_pixels":512,
        "pixel_spacing_x_mm":.488281,"pixel_spacing_y_mm":.488281,
        "slice_thickness_mm":1.,"series_nominal_slice_spacing_mm":1.,
        "image_location_mm":location,
        "scanner_R_centre_mm":-2.,"scanner_A_centre_mm":0.,
        "scanner_S_centre_mm":location,
        "R_TL_mm":123.,"A_TL_mm":125.,"S_TL_mm":location,
        "R_TR_mm":-127.,"A_TR_mm":125.,"S_TR_mm":location,
        "R_BR_mm":-127.,"A_BR_mm":-125.,"S_BR_mm":location,
        "normal_R":0.,"normal_A":0.,"normal_S":1.
    }
    s="Reading file: /redacted/originalCT\n"
    s+="Patient ID............................: SECRET-DO-NOT-ECHO\n"
    s+="Patient Name..........................: PRIVATE-SOURCE-PLACEHOLDER\n"
    s+="Operator..............................: OTHER-SECRET\n"
    for key,alias in h.KEYS.items():
        s+=key+"."*(44-len(key))+": "+str(v[alias])+"\n"
    return s


class OriginalScannerHeaders(unittest.TestCase):
    def test_safe_geometry_extracts_physical_coordinates(self):
        r=h.scanner_geometry_from_text(fixture())
        self.assertEqual(r["image_dimensions"],[512,512])
        self.assertEqual(r["pixel_spacing_mm"],[.488281,.488281])
        self.assertEqual(r["plane_TL_RAS_mm"],[123,125,389])
        self.assertEqual(r["plane_TR_RAS_mm"],[-127,125,389])
        self.assertEqual(r["plane_BR_RAS_mm"],[-127,-125,389])
        self.assertAlmostEqual(r["scanner_corner_range_x_mm"],250)
        self.assertFalse(r["canonical_promotion_allowed"])

    def test_patient_fields_not_returned_anywhere(self):
        r=h.scanner_geometry_from_text(fixture())
        dump=json.dumps(r)
        for secret in ("SECRET-DO-NOT-ECHO","PRIVATE-SOURCE-PLACEHOLDER",
                       "OTHER-SECRET","Patient"):
            self.assertNotIn(secret,dump)
        self.assertTrue(r["patient_identifiers_excluded_by_allowlist"])

    def test_adjacent_superior_coordinate_one_mm(self):
        a=h.scanner_geometry_from_text(fixture(389))
        b=h.scanner_geometry_from_text(fixture(388))
        r=h.pair_consistency(a,b)
        self.assertAlmostEqual(r["slice_spacing_measured_mm"],1)
        self.assertFalse(r["scanner_to_HGPT_world_registration_verified"])

    def test_nonadjacent_slice_pair_rejected(self):
        a=h.scanner_geometry_from_text(fixture(389))
        b=h.scanner_geometry_from_text(fixture(385))
        with self.assertRaisesRegex(ValueError,"not nominally adjacent"):
            h.pair_consistency(a,b)

    def test_bad_pixel_spacing_rejected(self):
        s=fixture().replace("0.488281","2.8",1)
        with self.assertRaisesRegex(ValueError,"invalid pixel spacing|inconsistent"):
            h.scanner_geometry_from_text(s)

    def test_nonorthogonal_scanner_corner_grid_rejected(self):
        s=fixture().replace("A Coord of Bottom Right Hand Corner"+"."*
            (44-len("A Coord of Bottom Right Hand Corner"))+": -125.0",
            "A Coord of Bottom Right Hand Corner"+"."*
            (44-len("A Coord of Bottom Right Hand Corner"))+": 125.0")
        with self.assertRaisesRegex(ValueError,"inconsistent|not orthogonal"):
            h.scanner_geometry_from_text(s)

    def test_missing_required_field_rejected(self):
        s="\n".join(line for line in fixture().splitlines()
                    if "Image pixel size - Y" not in line)
        with self.assertRaisesRegex(ValueError,"fields absent"):
            h.scanner_geometry_from_text(s)

    def test_duplicate_registered_field_rejected(self):
        key="Image location"
        s=fixture()+key+"."*(44-len(key))+": 389\n"
        with self.assertRaisesRegex(ValueError,"duplicate registered"):
            h.scanner_geometry_from_text(s)

    def test_supine_source_does_not_assume_standing_world(self):
        r=h.scanner_geometry_from_text(fixture())
        self.assertEqual(r["scanner_frame"],"GE_RAS_MM_NOT_HOMEGYMPT_WORLD")
        self.assertFalse(r["patient_to_HGPT_frame_registered"])
        self.assertFalse(r["HU_conversion_from_png_verified"])

    def test_non_axial_slice_plane_fails_closed(self):
        name="S Coord of Top Left Hand Corner"
        old=name+"."*(44-len(name))+": 389.0"
        new=name+"."*(44-len(name))+": 385"
        with self.assertRaisesRegex(ValueError,"nonaxial CT slice"):
            h.scanner_geometry_from_text(fixture().replace(old,new))

    def test_incorrect_location_vs_scanner_centre_rejected(self):
        name="Image location"
        old=name+"."*(44-len(name))+": 389.0"
        new=name+"."*(44-len(name))+": 400"
        with self.assertRaisesRegex(ValueError,"image-location"):
            h.scanner_geometry_from_text(fixture().replace(old,new))

    def test_largest_header_input_rejected(self):
        with self.assertRaisesRegex(ValueError,"too large"):
            h.scanner_geometry_from_text(fixture()+"#"*(h.MAX_TEXT_BYTES+1))

    def test_never_allow_unpinned_source_retrieval(self):
        with self.assertRaisesRegex(ValueError,"not an allowlisted"):
            h.fetch_header("unlisted_patient_header.txt")

    def test_exact_two_pinned_headers(self):
        self.assertEqual(h.ALLOWED,("cvm1013f.txt","cvm1014f.txt"))
        self.assertTrue(h.ROOT.startswith("https://data.lhncbc.nlm.nih.gov/"))

    def test_no_raw_patient_identifiers_in_exception(self):
        bad=fixture().replace("Image location", "OTHER",1)
        try:
            h.scanner_geometry_from_text(bad)
        except ValueError as exc:
            self.assertNotIn("PRIVATE-SOURCE-PLACEHOLDER",str(exc))
        else:
            self.fail("expected a missing-field rejection")


if __name__=="__main__":
    unittest.main()
