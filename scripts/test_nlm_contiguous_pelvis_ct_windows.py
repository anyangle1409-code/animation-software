"""Original CT 3-slice physical windows; mock real byte/image geometry only."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_contiguous_pelvis_ct_windows as windows
import nlm_ct_scanner_geometry_header as hdr
from test_nlm_pelvis_region_scout import png


def rows():
    out=[]
    for triplet in windows.TRIPLETS:
        block=[]
        # Physical superior positions are source headers, not filename arithmetic.
        centre= -360 if triplet[1]==1752 else -408
        for i,num in enumerate(triplet):
            block.append({
                "source_id":num,
                "source_png_sha256":"a"*64,
                "source_header_sha256":"b"*64,
                "source_bytes_verified":True,
                "physical_scanner_S_mm":centre + (1-i)*3,
                "scanner_grid":[512,512],
                "pixel_spacing_mm":[.898438,.898438],
                "slice_thickness_mm":3.,
                "nominal_slice_spacing_mm":3.,
                "candidate_anatomical_label_approved":False
            })
        out.append(block)
    return out


def header_text(z):
    v={
        "width_pixels":512,"height_pixels":512,
        "pixel_spacing_x_mm":.898438,"pixel_spacing_y_mm":.898438,
        "slice_thickness_mm":3,"series_nominal_slice_spacing_mm":3,
        "image_location_mm":z,
        "scanner_R_centre_mm":-2,"scanner_A_centre_mm":61,
        "scanner_S_centre_mm":z,
        "R_TL_mm":228,"A_TL_mm":291,"S_TL_mm":z,
        "R_TR_mm":-232,"A_TR_mm":291,"S_TR_mm":z,
        "R_BR_mm":-232,"A_BR_mm":-169,"S_BR_mm":z,
        "normal_R":0,"normal_A":0,"normal_S":1
    }
    s="Patient Name..........................: NEVER-ECHO-THIS\n"
    for key,alias in hdr.KEYS.items():
        s+=key+"."*(45-len(key))+": "+str(v[alias])+"\n"
    return s.encode()


class OriginalCTTriplets(unittest.TestCase):
    def test_two_original_windows_have_three_images_each(self):
        self.assertEqual(windows.TRIPLETS,((1749,1752,1755),(1797,1800,1803)))

    def test_valid_physical_contiguous_triplets_are_not_anatomy(self):
        v=windows.validate_windows(rows())
        self.assertEqual(len(v),2)
        self.assertEqual(v[0]["measured_step_between_centres_mm"],[3,3])
        self.assertFalse(v[0]["any_bony_feature_independently_labelled"])
        self.assertEqual(v[0]["scan_window_extents_including_half_slice_mm"],[-364.5,-355.5])

    def test_filename_3step_with_wrong_physical_4mm_gap_rejected(self):
        a=rows()
        a[0][1]["physical_scanner_S_mm"] -= 1
        with self.assertRaisesRegex(ValueError,"not contiguous"):
            windows.validate_windows(a)

    def test_wrong_source_id_or_missing_slice_rejected(self):
        a=rows()
        a[1].pop()
        with self.assertRaisesRegex(ValueError,"exact two reviewed"):
            windows.validate_windows(a)

    def test_source_anatomical_acceptance_claim_rejected(self):
        a=rows()
        a[0][2]["candidate_anatomical_label_approved"]=True
        with self.assertRaisesRegex(ValueError,"anatomy evidence status"):
            windows.validate_windows(a)

    def test_no_source_byte_verification_rejected(self):
        a=rows()
        a[0][1]["source_bytes_verified"]=False
        with self.assertRaisesRegex(ValueError,"source identity"):
            windows.validate_windows(a)

    def test_different_slice_thickness_fails_closed(self):
        a=rows()
        a[1][0]["slice_thickness_mm"]=1
        with self.assertRaisesRegex(ValueError,"physical slice thickness"):
            windows.validate_windows(a)

    def test_mock_original_png_and_headers_validate_true_adjacent_ct_geometry(self):
        image=png((0,))
        def loader(url,limit):
            if url.endswith(".png"):
                return image
            i=int(url.rsplit("cvm",1)[-1].split("f.txt")[0])
            if i in (1749,1752,1755):
                z=-360+(1752-i)
            elif i in (1797,1800,1803):
                z=-408+(1800-i)
            else:
                raise ValueError("untrusted source")
            return header_text(z)
        r=windows.scout_windows(loader)
        self.assertEqual(r["number_of_original_CT_images"],6)
        self.assertEqual(r["physical_contiguous_window_evidence"][0]["physical_scanner_Z_mm"],
                         [-357,-360,-363])
        self.assertEqual(r["physical_contiguous_window_evidence"][1]["physical_scanner_Z_mm"],
                         [-405,-408,-411])
        self.assertFalse(r["anatomical_reference_landmarks_verified"])
        self.assertFalse(r["source_HU_calibration_verified"])
        self.assertFalse(r["canonical_promotion_allowed"])
        self.assertNotIn("NEVER-ECHO-THIS",json.dumps(r))

    def test_pinned_source_manifest_unique_complete_and_noncanonical(self):
        path=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
              "nlm_contiguous_ct_windows_pinned_20261009.json")
        m=json.loads(path.read_text())
        self.assertFalse(m["canonical_promotion_allowed"])
        self.assertFalse(m["anatomical_features_identified"])
        self.assertEqual(set(row["source_id"] for row in m["exact_png_and_scanner_header_sha256"]),
                         {1749,1752,1755,1797,1800,1803})
        self.assertEqual(m["pixel_spacing_xy_mm"],[.898438,.898438])

    def test_pin_verifier_checks_every_source_coordinate_and_SHA(self):
        path=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
              "nlm_contiguous_ct_windows_pinned_20261009.json")
        m=json.loads(path.read_text())
        p={r["source_id"]:r for r in m["exact_png_and_scanner_header_sha256"]}
        rows0=rows()
        for group in rows0:
            for r in group:
                d=p[r["source_id"]]
                r["source_png_sha256"]=d["png_sha256"]
                r["source_header_sha256"]=d["scanner_header_sha256"]
                r["source_PNG_byte_count"]=d["png_bytes"]
        a=windows.check_pinned_source({"source_image_rows":rows0},m)
        self.assertTrue(a["all_six_source_png_header_sha_and_scanner_positions_match"])
        self.assertFalse(a["canonical_promotion_allowed"])
        rows0[0][0]["source_header_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"source-byte identity mismatch"):
            windows.check_pinned_source({"source_image_rows":rows0},m)

    def test_pin_verifier_rejects_claimed_anatomical_promotion(self):
        path=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
              "nlm_contiguous_ct_windows_pinned_20261009.json")
        m=json.loads(path.read_text())
        m["anatomical_features_identified"]=True
        with self.assertRaisesRegex(ValueError,"unsupported anatomy"):
            windows.check_pinned_source({"source_image_rows":[]},m)

    def test_proper_real_source_https_only(self):
        self.assertTrue(windows.scout.INDEX_BASE.startswith("https://data.lhncbc.nlm.nih.gov/"))
        self.assertTrue(windows.hdr.ROOT.startswith("https://data.lhncbc.nlm.nih.gov/"))


if __name__=="__main__":
    unittest.main()
