#!/usr/bin/env python3
"""Adversarial original-source CT review tests, no anatomical acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from nlm_ct_private_annotation_capture import (
    make_offline_annotation_html, packet_template, validate_packet,
    recheck_source_HU,
)
from nlm_ct_private_slice_review_plate import private_ct_plate

AUDIT=ROOT/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
BUNDLE=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json").read_text())
CAL=json.loads((AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json").read_text())
REVIEW=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json").read_text())


def loader(_root,row):
    s=row["scanner_centre_RAS_mm"][2]
    p=[1100]*(512*512)
    for pt in REVIEW["observations"]:
        if pt["source_id"]==row["source_id"]:
            r,c=pt["pixel"]["row"],pt["pixel"]["column"]
            p[r*512+c]=1400
    return {
        "plane_TL_RAS_mm":[230,230,s],
        "plane_TR_RAS_mm":[-230,230,s],
        "plane_BR_RAS_mm":[-230,-230,s],
        "scanner_S_mm":s,
    },p


class OriginalCTReviewerAnnotator(unittest.TestCase):
    def report(self):
        packet=packet_template(BUNDLE,REVIEW,"cvm1873f")
        packet["reviewer_alias"]="reviewer_01"
        return packet

    def test_all_four_original_source_hip_points_immutable_and_unapproved(self):
        p=self.report()
        self.assertEqual(p["centre_source_id"],"cvm1873f")
        self.assertEqual(len(p["observations"]),4)
        self.assertEqual([x["original_pixel"] for x in p["observations"]],[
            {"row":270,"column":175},{"row":270,"column":342},
            {"row":257,"column":151},{"row":257,"column":366}])
        self.assertFalse(p["bone_identity_independently_verified"])
        self.assertFalse(p["canonical_promotion_allowed"])
        self.assertEqual(validate_packet(p,BUNDLE,REVIEW),(2,"cvm1873f"))

    def test_browser_review_has_source_pinned_six_images_and_no_network(self):
        plate,evidence=private_ct_plate(
            BUNDLE,CAL,REVIEW,2,"cvm1873f","/private/nlm",loader=loader)
        html=make_offline_annotation_html(
            plate,evidence,BUNDLE,REVIEW,"cvm1873f")
        self.assertEqual(html.count("data:image/png;base64,"),6)
        self.assertIn("Content-Security-Policy",html)
        self.assertIn("connect-src 'none'",html)
        self.assertIn("getScreenCTM()",html)
        self.assertIn("matrixTransform(matrix.inverse())",html)
        self.assertIn("canonical_promotion_allowed",html)
        self.assertIn("bone_identity_independently_verified",html)
        self.assertIn("Reject original hypothesis",html)
        self.assertIn("Tentative pixel",html)
        self.assertIn("source-packet",html)
        self.assertNotIn("fetch(",html)
        self.assertNotIn("XMLHttpRequest",html)
        self.assertNotIn("<script",plate)
        self.assertIn("cvm1873f",html)

    def test_manual_tentative_corrected_pixel_is_rechecked_on_original_HU(self):
        p=self.report()
        p["observations"][0]["review_status"]="tentative_reviewer_pixel"
        p["observations"][0]["tentative_pixel"]={"row":269,"column":175}
        p["observations"][0]["evidence_note"]="Tentative source feature; boundary not proven."
        p["observations"][1]["review_status"]="rejected_original_point"
        self.assertEqual(validate_packet(p,BUNDLE,REVIEW),(2,"cvm1873f"))
        result=recheck_source_HU(p,BUNDLE,CAL,REVIEW,"/private/nlm",loader=loader)
        self.assertEqual(result["observations"][0]["source_original_HU_confirmed"],376)
        self.assertEqual(result["observations"][0]["tentative_HU_confirmed_if_selected"],76)
        self.assertEqual(result["observations"][1]["review_status"],"rejected_original_point")
        self.assertIsNone(result["observations"][1]["tentative_HU_confirmed_if_selected"])
        self.assertEqual(result["accepted_true_pelvic_bony_landmarks"],0)
        self.assertFalse(result["canonical_promotion_allowed"])

    def test_rejects_false_anatomical_promotion(self):
        for key in ("canonical_promotion_allowed","bone_identity_independently_verified",
                    "scanner_to_HGPT_skeleton_registered","scanner_pixel_origin_verified"):
            p=self.report();p[key]=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"promoted"):
                validate_packet(p,BUNDLE,REVIEW)
        p=self.report();p["observations"][0]["canonical_promotion_allowed"]=True
        with self.assertRaisesRegex(ValueError,"promotion"):
            validate_packet(p,BUNDLE,REVIEW)

    def test_original_identity_and_hash_can_never_change(self):
        for key,value in (
            ("source_png_sha256","0"*64),("source_group",1),
            ("source_header_sha256","0"*64),("source_scanner_S_mm",0)):
            p=self.report();p[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"provenance"):
                validate_packet(p,BUNDLE,REVIEW)
        p=self.report();p["observations"][0]["original_pixel"]["column"]+=1
        with self.assertRaisesRegex(ValueError,"original observation"):
            validate_packet(p,BUNDLE,REVIEW)
        p=self.report();p["observations"].reverse()
        with self.assertRaisesRegex(ValueError,"original observation"):
            validate_packet(p,BUNDLE,REVIEW)

    def test_tentative_pixel_requires_exact_integer_bounds_and_status(self):
        for pixel in ({"row":0,"column":512},{"row":True,"column":7},
                      {"row":8,"column":"10"},{"row":8},None):
            p=self.report()
            p["observations"][0]["review_status"]="tentative_reviewer_pixel"
            p["observations"][0]["tentative_pixel"]=pixel
            with self.subTest(pixel=pixel),self.assertRaisesRegex(ValueError,"tentative pixel"):
                validate_packet(p,BUNDLE,REVIEW)
        p=self.report()
        p["observations"][0]["tentative_pixel"]={"row":270,"column":175}
        with self.assertRaisesRegex(ValueError,"silently"):
            validate_packet(p,BUNDLE,REVIEW)

    def test_rejects_invalid_reviewer_alias_and_status(self):
        for alias in ("","one two","<script>","a","x"*33):
            p=self.report();p["reviewer_alias"]=alias
            with self.subTest(alias=alias),self.assertRaisesRegex(ValueError,"alias"):
                validate_packet(p,BUNDLE,REVIEW)
        p=self.report();p["observations"][0]["review_status"]="certified_femoral_head"
        with self.assertRaisesRegex(ValueError,"status"):
            validate_packet(p,BUNDLE,REVIEW)
        p=self.report();p["observations"][0]["evidence_note"]="x"*2001
        with self.assertRaisesRegex(ValueError,"note"):
            validate_packet(p,BUNDLE,REVIEW)

    def test_private_plate_tampering_rejected_before_html_generation(self):
        plate,evidence=private_ct_plate(
            BUNDLE,CAL,REVIEW,2,"cvm1873f","/private/nlm",loader=loader)
        changed=json.loads(json.dumps(evidence))
        changed["source_sha256"][1]="0"*64
        with self.assertRaisesRegex(ValueError,"provenance"):
            make_offline_annotation_html(plate,changed,BUNDLE,REVIEW,"cvm1873f")
        with self.assertRaisesRegex(ValueError,"executable SVG"):
            make_offline_annotation_html(plate+"<script>alert(1)</script>",
                                        evidence,BUNDLE,REVIEW,"cvm1873f")

    def test_recheck_rejects_incorrect_scanner_frame(self):
        p=self.report()
        def misread(_source,row):
            geo,pixels=loader(_source,row)
            geo["scanner_S_mm"]+=3
            return geo,pixels
        with self.assertRaisesRegex(ValueError,"scanner"):
            recheck_source_HU(p,BUNDLE,CAL,REVIEW,"/private/nlm",loader=misread)


if __name__=="__main__":
    unittest.main()
