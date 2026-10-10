#!/usr/bin/env python3
"""Independent private source CT review-plate tests: NO bone acceptance."""
import base64
import json
from pathlib import Path
import re
import struct
import sys
import unittest
from xml.etree import ElementTree
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
from nlm_ct_private_slice_review_plate import (
    private_ct_plate, encode_windowed_gray_png
)

AUDIT=ROOT/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
BUNDLE=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json").read_text())
CAL=json.loads((AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json").read_text())
REVIEW=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json").read_text())


def geometry(s):
    return {
        "plane_TL_RAS_mm":[230,230,s],
        "plane_TR_RAS_mm":[-230,230,s],
        "plane_BR_RAS_mm":[-230,-230,s],
        "scanner_S_mm":s,
    }


class PrivateCTReviewPlate(unittest.TestCase):
    def test_first_party_png_window_clips_and_has_valid_scanlines(self):
        png=encode_windowed_gray_png([824,1024,1324,2624],-200,1600,size=2)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        pos=8
        idat=b""
        while pos<len(png):
            size,=struct.unpack(">I",png[pos:pos+4])
            typ=png[pos+4:pos+8]
            payload=png[pos+8:pos+8+size]
            crc,=struct.unpack(">I",png[pos+8+size:pos+12+size])
            self.assertEqual(zlib.crc32(typ+payload)&0xffffffff,crc)
            if typ==b"IHDR":
                self.assertEqual(struct.unpack(">II",payload[:8]),(2,2))
                self.assertEqual(payload[8:10],b"\x08\x00")
            if typ==b"IDAT":idat+=payload
            pos+=12+size
        raw=zlib.decompress(idat)
        self.assertEqual(list(raw),[0,0,28,0,71,255])

    def test_refuses_invalid_windows_and_image_lengths(self):
        for args in [([0,0,0],-200,1600,2),([0]*4,200,-200,2),
                     ([0]*4,-200,1600,0)]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                encode_windowed_gray_png(*args)

    def test_real_source_ids_and_hypotheses_appear_without_acceptance(self):
        frames=[]
        for idx in range(3):
            layer=[1200]*(512*512)
            layer[(270)*512+175]=1315
            layer[(270)*512+342]=1329
            layer[(257)*512+151]=1462
            layer[(257)*512+366]=1534
            frames.append(layer)
        expected=BUNDLE["series"][1]["slices"][9:12]
        by_id={row["source_id"]:i for i,row in enumerate(expected)}
        def loader(folder,row):
            i=by_id[row["source_id"]]
            return geometry(row["scanner_centre_RAS_mm"][2]),frames[i]
        svg,evidence=private_ct_plate(
            BUNDLE,CAL,REVIEW,2,"cvm1873f","/private/ct-source",
            loader=loader)
        ElementTree.fromstring(svg)
        self.assertEqual(evidence["source_ids"],[x["source_id"] for x in expected])
        self.assertEqual(len(evidence["points"]),4)
        self.assertEqual([x["source_centre_HU"] for x in evidence["points"]],
                         [291,305,438,510])
        self.assertEqual(svg.count('<image '),6)
        self.assertEqual(len(re.findall(r'fill="none" stroke="#[0-9a-f]{6}" stroke-width="2.6"',svg)),8)
        self.assertEqual(svg.count('data:image/png;base64,'),6)
        # Embed derived 8-bit HU window PNGs, never exact original PNG bytes.
        self.assertNotIn("source_header_sha256",svg)
        self.assertNotIn("clinical diagnosis",svg)
        self.assertIn("UNVERIFIED HYPOTHESIS PIXELS",svg)
        self.assertIn("ANATOMICAL IDENTITY NOT VERIFIED",svg)
        self.assertFalse(evidence["canonical_promotion_allowed"])
        self.assertEqual(evidence["reviewer_identified_real_bony_landmarks"],0)
        self.assertFalse(evidence["pixel_centre_convention_verified"])
        self.assertFalse(evidence["raw_CT_or_header_bytes_committed"])

    def test_bad_source_group_annotation_and_header_fail_closed(self):
        base=lambda row: (
            geometry(row["scanner_centre_RAS_mm"][2]),
            [1024]*(512*512))
        with self.assertRaisesRegex(ValueError,"boundary"):
            private_ct_plate(BUNDLE,CAL,REVIEW,2,"cvm1843f",
                             "/private/ct-source",loader=base)
        with self.assertRaisesRegex(ValueError,"no original candidate"):
            private_ct_plate(BUNDLE,CAL,REVIEW,2,"cvm1870f",
                             "/private/ct-source",loader=base)
        changed=json.loads(json.dumps(REVIEW))
        target=next(x for x in changed["observations"]
                    if x["observation_id"]=="obs-1873-right-femoral-head")
        target["source_png_sha256"]="tampered"
        with self.assertRaisesRegex(ValueError,"source reference"):
            private_ct_plate(BUNDLE,CAL,changed,2,"cvm1873f",
                             "/private/ct-source",loader=base)
        with self.assertRaisesRegex(ValueError,"disagree"):
            private_ct_plate(BUNDLE,CAL,REVIEW,2,"cvm1873f",
                             "/private/ct-source",
                             loader=lambda folder,row:(geometry(999),[1024]*(512*512)))


if __name__=="__main__":
    unittest.main()
