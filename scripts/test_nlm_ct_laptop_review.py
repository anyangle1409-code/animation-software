#!/usr/bin/env python3
"""One-click laptop original CT preparation: SHA/sidecar/privacy tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_ct_laptop_review as review_runner

AUDIT=ROOT/"ORIGINAL_V1_WORK"/"anatomy"/"audit"
BUNDLE=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_bundle_20261009.json").read_text())
CAL=json.loads((AUDIT/"nlm_pelvic_ct_full_series_hu_calibration_20261009.json").read_text())
REVIEW=json.loads((AUDIT/"nlm_pelvic_ct_full_series_candidate_review_20261009.json").read_text())


class Reply:
    def __init__(self,payload,url=None,code=200):
        self.payload=payload
        self.url=url
        self.status=code
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def read(self,n):
        return self.payload[:n]
    def geturl(self):
        return self.url


class OriginalCTLaptopSetup(unittest.TestCase):
    def test_plan_all_source_observations_and_3_source_planes_each(self):
        selections,unique=review_runner.plan(BUNDLE,REVIEW)
        self.assertEqual(len(selections),5)
        self.assertEqual(len(unique),15)
        self.assertEqual([x[1] for x in selections],[
            "cvm1764f","cvm1794f","cvm1824f","cvm1873f","cvm1903f"])
        self.assertEqual([x[0] for x in selections],[1,1,1,2,2])
        self.assertEqual([r["source_id"] for r in selections[3][2]],
                         ["cvm1870f","cvm1873f","cvm1876f"])
        self.assertEqual(review_runner.plan(
            BUNDLE,REVIEW,["cvm1873f"])[0][0][0],2)

    def test_invalid_or_unpinned_selection_fails_closed(self):
        for sid in ("../../../evil","cvm1843f","cvm1734f","anything"):
            with self.subTest(sid=sid),self.assertRaises(ValueError):
                review_runner.selected_three_neighbours(BUNDLE,REVIEW,sid)
        with self.assertRaisesRegex(ValueError,"repeated"):
            review_runner.plan(BUNDLE,REVIEW,["cvm1873f","cvm1873f"])
        altered=json.loads(json.dumps(REVIEW))
        point=next(x for x in altered["observations"]
                   if x["source_id"]=="cvm1873f")
        point["source_header_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"hash"):
            review_runner.plan(BUNDLE,altered,["cvm1873f"])

    def test_exact_sha_source_pins_exclusive_local_writes_and_cache_reuse(self):
        png=b"fake original scanner compressed bytes"
        hdr=b"fake exact GE scanner header bytes"
        sid="cvm9999f"
        row={
            "source_id":sid,
            "source_png_sha256":hashlib.sha256(png).hexdigest(),
            "source_header_sha256":hashlib.sha256(hdr).hexdigest(),
            "source_png_bytes":len(png),
        }
        mapping={".png":png,".txt":hdr}
        calls=[]
        def opener(request,timeout=45):
            url=request.full_url
            calls.append((url,timeout))
            extension=".png" if url.endswith(".png") else ".txt"
            return Reply(mapping[extension],url)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"raw_NLM"
            self.assertEqual(review_runner.download_original_pinned_pair(
                row,root,opener=opener),(2,0))
            self.assertEqual(len(calls),2)
            self.assertEqual((root/(sid+".png")).read_bytes(),png)
            self.assertEqual((root/(sid+".txt")).read_bytes(),hdr)
            self.assertEqual(review_runner.download_original_pinned_pair(
                row,root,opener=opener),(0,2))
            self.assertEqual(len(calls),2)
            (root/(sid+".png")).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"refusing to replace"):
                review_runner.download_original_pinned_pair(row,root,opener=opener)
            self.assertEqual((root/(sid+".png")).read_bytes(),b"tampered")

    def test_redirect_hash_mismatch_and_symlink_fail_before_any_write(self):
        payload=b"source_data"
        row={
            "source_id":"cvm9999f",
            "source_png_sha256":hashlib.sha256(payload).hexdigest(),
            "source_header_sha256":hashlib.sha256(payload).hexdigest(),
            "source_png_bytes":len(payload),
        }
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"original"
            with self.assertRaisesRegex(ValueError,"redirected"):
                review_runner.download_original_pinned_pair(
                    row,root,opener=lambda req,timeout:Reply(
                        payload,"https://attacker.invalid/source"))
            self.assertFalse((root/"cvm9999f.png").exists())
            with self.assertRaisesRegex(ValueError,"sha256"):
                review_runner.download_original_pinned_pair(
                    row,root,opener=lambda req,timeout:Reply(
                        b"malicious",req.full_url))
            self.assertFalse((root/"cvm9999f.png").exists())
            other=Path(td)/"elsewhere"
            other.mkdir()
            link=Path(td)/"symlink"
            link.symlink_to(other,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"symlink"):
                review_runner.download_original_pinned_pair(row,link)

    def test_prepares_five_private_local_review_plates_without_3p_tools(self):
        lookup={}
        for series in BUNDLE["series"]:
            for row in series["slices"]:
                lookup[row["source_id"]]=row
        def loader(_private,row):
            pixels=[1024]*(512*512)
            for p in REVIEW["observations"]:
                if p["source_id"]==row["source_id"]:
                    r,c=p["pixel"]["row"],p["pixel"]["column"]
                    pixels[r*512+c]=1324
            s=row["scanner_centre_RAS_mm"][2]
            geom={
                "plane_TL_RAS_mm":[230,230,s],
                "plane_TR_RAS_mm":[-230,230,s],
                "plane_BR_RAS_mm":[-230,-230,s],
                "scanner_S_mm":s,
            }
            return geom,pixels
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)/"source_CT_is_private"
            with patch.object(review_runner,"download_original_pinned_pair",
                              return_value=(2,0)) as downloader:
                report=review_runner.run(
                    BUNDLE,CAL,REVIEW,home,source_loader=loader)
                self.assertEqual(downloader.call_count,15)
            self.assertEqual(report["unique_pinned_source_slices"],15)
            self.assertEqual(report["downloaded_new_original_files"],30)
            self.assertEqual(len(report["review_plates"]),5)
            self.assertEqual(sum(x["candidate_points"] for x in report["review_plates"]),10)
            self.assertEqual(report["real_bony_landmarks_anatomically_verified"],0)
            self.assertFalse(report["canonical_promotion_allowed"])
            index=Path(report["index_file"])
            text=index.read_text()
            self.assertIn("cvm1764f_source_review.svg",text)
            self.assertIn("cvm1873f_source_review.svg",text)
            self.assertIn("Not validated anatomy",text)
            self.assertNotIn("<script",text)
            for plate in report["review_plates"]:
                svg=(index.parent/(plate["source_id"]+"_source_review.svg")).read_text()
                self.assertEqual(svg.count("data:image/png;base64,"),6)
                self.assertIn("ANATOMICAL IDENTITY NOT VERIFIED",svg)
            with patch.object(review_runner,"download_original_pinned_pair",
                              return_value=(2,0)) as downloader:
                with self.assertRaisesRegex(ValueError,"refuse overwrite"):
                    review_runner.run(BUNDLE,CAL,REVIEW,home,source_loader=loader)
                self.assertEqual(downloader.call_count,0)


if __name__=="__main__":
    unittest.main()
