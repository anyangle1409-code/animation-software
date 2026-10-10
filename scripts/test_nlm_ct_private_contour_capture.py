#!/usr/bin/env python3
"""Test provisional CT contour source physics, adversarial falsification gates."""
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from nlm_ct_private_contour_capture import (
    contour_packet,offline_contour_html,validate_polygon,
    validate_contour_packet,original_source_contour_metrics,
)
from nlm_ct_private_slice_review_plate import private_ct_plate

AUDIT=ROOT/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
BUNDLE=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json").read_text())
CAL=json.loads((AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json").read_text())
REVIEW=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json").read_text())


def geometry(s):
    return {"plane_TL_RAS_mm":[230,230,s],
            "plane_TR_RAS_mm":[-230,230,s],
            "plane_BR_RAS_mm":[-230,-230,s],
            "scanner_S_mm":s}


def loader(_private,row):
    pixels=[1324]*(512*512)
    for col in range(140,151):
        pixels[255*512+col]=1500
    return geometry(row["scanner_centre_RAS_mm"][2]),pixels


def triangle():
    return [{"row":250,"column":140},{"row":250,"column":150},
            {"row":260,"column":140}]


def with_outline():
    original={"source_ids":["cvm1870f","cvm1873f","cvm1876f"],
              "source_sha256":[r["source_png_sha256"] for r in BUNDLE["series"][1]["slices"][9:12]],
              "canonical_promotion_allowed":False}
    packet=contour_packet(BUNDLE,original)
    packet["reviewer_alias"]="reviewer_test"
    packet["outlines"]=[{
        "id":"outline_1","source_id":"cvm1873f",
        "label":"candidate_right_acetabulum","vertices":triangle(),
        "note":"Unknown actual cortex. Tentative only.","closed":True}]
    return original,packet


class CTContourWitnessTests(unittest.TestCase):
    def test_source_pins_and_area_are_never_anatomical_approval(self):
        template,packet=with_outline()
        self.assertEqual(validate_polygon(triangle()),50)
        self.assertEqual(validate_contour_packet(packet,BUNDLE,template)["source_group"],2)
        report=original_source_contour_metrics(
            packet,BUNDLE,CAL,template,"/private/source",loader=loader)
        self.assertEqual(report["contours"][0]["polygon_area_pixel_squared"],50)
        self.assertAlmostEqual(
            report["contours"][0]["physical_in_plane_area_mm_squared"],
            round(50*(460/512)**2,3))
        self.assertEqual(report["contours"][0]["vertex_original_source_HU_min_max"],
                         [300,300])
        self.assertEqual(report["contours"][0]["vertex_count"],3)
        self.assertEqual(report["source_ids"],template["source_ids"])
        self.assertFalse(report["complete_named_bone_3D_surface_verified"])
        self.assertFalse(report["canonical_promotion_allowed"])

    def test_static_original_three_slice_plate_wraps_private_contour_interface(self):
        plate,evidence=private_ct_plate(
            BUNDLE,CAL,REVIEW,2,"cvm1873f","/private/source",loader=loader)
        markup=offline_contour_html(plate,BUNDLE,evidence)
        self.assertEqual(markup.count("data:image/png;base64,"),6)
        self.assertIn("connect-src 'none'",markup)
        self.assertIn("Finish tentative outline",markup)
        self.assertIn("getScreenCTM()",markup)
        self.assertIn("matrixTransform(matrix.inverse())",markup)
        self.assertIn("candidate_left_acetabulum",markup)
        self.assertIn("cvm1870f",markup)
        self.assertIn("cvm1873f",markup)
        self.assertIn("cvm1876f",markup)
        self.assertNotIn("fetch(",markup)
        self.assertNotIn("XMLHttpRequest",markup)
        self.assertIn("bone_identity_verified",markup)
        self.assertIn("canonical_promotion_allowed",markup)

    def test_bow_tie_duplicate_degenerate_and_large_polygons_rejected(self):
        bads=[
            [{"row":10,"column":10},{"row":20,"column":20},
             {"row":10,"column":20},{"row":20,"column":10}],
            [{"row":10,"column":10},{"row":10,"column":20},
             {"row":10,"column":20}],
            [{"row":10,"column":10},{"row":10,"column":12},
             {"row":10,"column":15}],
            [{"row":10,"column":10},{"row":11,"column":10}],
            [{"row":0,"column":0},{"row":0,"column":1},
             {"row":1,"column":512}],
            [{"row":0,"column":0},{"row":0,"column":2},
             {"row":True,"column":2}],
        ]
        for pts in bads:
            with self.subTest(points=pts),self.assertRaises(ValueError):
                validate_polygon(pts)

    def test_contour_metadata_and_false_canonical_acceptance_rejected(self):
        template,packet=with_outline()
        for prop,value in (("canonical_promotion_allowed",True),
                           ("bone_identity_verified",True),
                           ("scanner_to_HGPT_transform_verified",True),
                           ("pixel_centre_origin_verified",True),
                           ("source_group",1)):
            changed=json.loads(json.dumps(packet))
            changed[prop]=value
            with self.subTest(prop=prop),self.assertRaisesRegex(ValueError,"provenance"):
                validate_contour_packet(changed,BUNDLE,template)
        changed=json.loads(json.dumps(packet))
        changed["source_planes"][1]["source_header_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            validate_contour_packet(changed,BUNDLE,template)

    def test_contour_source_slice_and_bone_label_cannot_forge(self):
        template,packet=with_outline()
        for field,value in (("source_id","cvm1843f"),("label","verified_real_acetabulum"),
                            ("closed",False),("id","outline_8"),("note","a"*2001)):
            changed=json.loads(json.dumps(packet))
            changed["outlines"][0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"outline"):
                validate_contour_packet(changed,BUNDLE,template)
        changed=json.loads(json.dumps(packet))
        changed["outlines"][0]["canonical_promotion_allowed"]=True
        with self.assertRaisesRegex(ValueError,"promotion"):
            validate_contour_packet(changed,BUNDLE,template)

    def test_source_boundaries_and_bad_trio_fail_closed(self):
        template,packet=with_outline()
        bad=json.loads(json.dumps(template))
        bad["source_sha256"][0]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            contour_packet(BUNDLE,bad)
        bad=json.loads(json.dumps(template))
        bad["source_ids"]=["cvm1870f","cvm1873f","cvm1903f"]
        with self.assertRaisesRegex(ValueError,"groups|consecutive"):
            contour_packet(BUNDLE,bad)
        bad=json.loads(json.dumps(packet))
        bad["reviewer_alias"]="<script>"
        with self.assertRaisesRegex(ValueError,"alias"):
            validate_contour_packet(bad,BUNDLE,template)

    def test_both_axial_end_planes_supported_without_joining_two_groups(self):
        template,packet=with_outline()
        packet["outlines"].append({
            "id":"outline_2","source_id":"cvm1870f",
            "label":"unknown_dense_structure",
            "vertices":[{"row":300,"column":300},{"row":300,"column":310},
                        {"row":310,"column":300}],"note":"uncertain", "closed":True,
        })
        result=original_source_contour_metrics(
            packet,BUNDLE,CAL,template,"/private/source",loader=loader)
        self.assertEqual([x["source_id"] for x in result["contours"]],
                         ["cvm1873f","cvm1870f"])
        self.assertNotEqual(result["contours"][0]["scanner_S_mm"],
                            result["contours"][1]["scanner_S_mm"])


if __name__=="__main__":
    unittest.main()
