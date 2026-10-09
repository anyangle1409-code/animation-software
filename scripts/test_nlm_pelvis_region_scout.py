"""First-party 16bit CT image unfilter tests; safe source-region atlas no anatomy."""
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_pelvis_region_scout as scout
import nlm_ct_scanner_geometry_header as headers
import nlm_original_ct_png_probe as pngprobe


def chunk(name,data):
    return (struct.pack(">I",len(data))+name+data+
            struct.pack(">I",zlib.crc32(name+data)&0xffffffff))


def source_values():
    # Fixed known stored source scalar pattern, NOT calibrated CT HUs.
    return [1000+(i%127)*13 for i in range(512)]


def png(filter_modes=(0,)):
    values=source_values()
    pixels=b"".join(struct.pack(">H",v) for v in values)
    prev=b"\0"*1024
    scan=b""
    for k in range(512):
        f=filter_modes[k%len(filter_modes)]
        src=bytearray(1024)
        for idx,actual in enumerate(pixels):
            left=pixels[idx-2] if idx>=2 else 0
            above=prev[idx]
            upleft=prev[idx-2] if idx>=2 else 0
            if f==0:
                predicted=0
            elif f==1:
                predicted=left
            elif f==2:
                predicted=above
            elif f==3:
                predicted=(left+above)//2
            elif f==4:
                predicted=scout._paeth(left,above,upleft)
            src[idx]=(actual-predicted)&255
        scan+=bytes((f,))+src
        prev=pixels
    ihdr=struct.pack(">IIBBBBB",512,512,16,0,0,0,0)
    return pngprobe.MAGIC+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(scan))+chunk(b"IEND",b"")


def valid_header(z_mm=102):
    vals={
       "width_pixels":512,"height_pixels":512,
       "pixel_spacing_x_mm":.488281,"pixel_spacing_y_mm":.488281,
       "slice_thickness_mm":3,"series_nominal_slice_spacing_mm":3,
       "image_location_mm":z_mm,"scanner_R_centre_mm":-2,
       "scanner_A_centre_mm":0,"scanner_S_centre_mm":z_mm,
       "R_TL_mm":123,"A_TL_mm":125,"S_TL_mm":z_mm,
       "R_TR_mm":-127,"A_TR_mm":125,"S_TR_mm":z_mm,
       "R_BR_mm":-127,"A_BR_mm":-125,"S_BR_mm":z_mm,
       "normal_R":0,"normal_A":0,"normal_S":1,
    }
    s="Patient Name..........................: SECRET PATIENT SHOULD NEVER BE PRINTED\n"
    s+="Patient ID............................: REDACT-ME\n"
    for k,v in headers.KEYS.items():
        s+=k+"."*(46-len(k))+": "+str(vals[v])+"\n"
    return s.encode()


class SourceScoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values=source_values()
        cls.clear_png=png((0,))

    def test_decodes_unfiltered_png16_be(self):
        v=scout.decode_grayscale_png16(self.clear_png)
        self.assertEqual(len(v),512*512)
        self.assertEqual(v[:512],self.values)
        self.assertEqual(v[-512:],self.values)

    def test_decodes_sub_filter(self):
        v=scout.decode_grayscale_png16(png((1,)))
        self.assertEqual(v[512:1024],self.values)

    def test_decodes_up_filter(self):
        v=scout.decode_grayscale_png16(png((2,)))
        self.assertEqual(v[:512],self.values)
        self.assertEqual(v[512:1024],self.values)

    def test_decodes_average_filter(self):
        v=scout.decode_grayscale_png16(png((3,)))
        self.assertEqual(v[-512:],self.values)

    def test_decodes_paeth_filter(self):
        v=scout.decode_grayscale_png16(png((4,)))
        self.assertEqual(v[-512:],self.values)

    def test_combined_png_row_filters(self):
        v=scout.decode_grayscale_png16(png((0,1,2,3,4)))
        self.assertEqual(v[256*512:257*512],self.values)

    def test_raw_statistics_not_hu(self):
        r=scout.raw_statistics(self.values)
        self.assertFalse(r["original_CT_HU_rescale_verified"])
        self.assertFalse(r["anatomical_bone_segmentation_performed"])
        self.assertEqual(r["stored_png_scalar_range"][0],1000)

    def test_out_of_range_pixel_rejected(self):
        with self.assertRaisesRegex(ValueError,"out of 16-bit"):
            scout.raw_statistics([65536,4])

    def test_grayscale_only_input_enforced(self):
        ihdr=struct.pack(">IIBBBBB",512,512,8,0,0,0,0)
        raw=pngprobe.MAGIC+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(b"\0"*512))+chunk(b"IEND",b"")
        with self.assertRaisesRegex(ValueError,"16-bit grayscale"):
            scout.decode_grayscale_png16(raw)

    def test_corrupt_deflate_data_rejected(self):
        raw=bytearray(self.clear_png)
        pos=8+25
        n=struct.unpack_from(">I",raw,pos)[0]
        idat=b"broken"
        blob=bytes(raw[:pos])+chunk(b"IDAT",idat)+chunk(b"IEND",b"")
        with self.assertRaises((ValueError,zlib.error)):
            scout.decode_grayscale_png16(blob)

    def test_geometry_only_excludes_personal_identifiers(self):
        rec=scout.geometry_only(valid_header())
        s=json.dumps(rec)
        self.assertNotIn("REDACT-ME",s)
        self.assertNotIn("SECRET PATIENT",s)
        self.assertTrue(rec["safe_geometry_parser_PIIs_excluded"])
        self.assertFalse(rec.get("HU_calibrated",False))

    def test_atlas_safe_loader_does_not_export_png_bytes(self):
        content=self.clear_png
        def loader(url,maximum):
            if url.endswith(".png"):
                return content
            if "cvm1300f.txt" in url:
                return valid_header(102)
            if "cvm1399f.txt" in url:
                return valid_header(3)
            raise ValueError("unknown source")
        r=scout.atlas([1399,1300],loader)
        self.assertEqual(r["slice_count"],2)
        self.assertEqual([s["scanner_RAS_image_location_superior_mm"] for s in r["slices"]],[102,3])
        self.assertTrue(r["stored_PNG_scalars_not_verified_Hounsfield_units"])
        self.assertFalse(r["anatomical_landmarks_verified"])
        self.assertFalse(r["canonical_promotion_allowed"])
        self.assertNotIn("SECRET PATIENT",json.dumps(r))
        self.assertNotIn("REDACT-ME",json.dumps(r))

    def test_pinned_real_source_inventory_is_complete_and_still_not_anatomy(self):
        p=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
           "nlm_pelvis_scout_pinned_source_positions_20261009.json")
        data=json.loads(p.read_text())
        self.assertFalse(data["canonical_promotion_allowed"])
        self.assertFalse(data["anatomical_pelvic_slice_confirmed"])
        self.assertEqual(len(data["slices"]),12)
        self.assertEqual(set(x["id"] for x in data["slices"]),set(scout.SCOUT_IDS))
        self.assertEqual(set(x["thickness_mm"] for x in data["slices"]),{3})
        self.assertEqual({tuple(x["pixel_spacing_mm"]) for x in data["slices"]},
                         {(.898438,.898438)})

    def test_gaps_in_filename_are_not_physical_offsets(self):
        p=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
           "nlm_pelvis_scout_pinned_source_positions_20261009.json")
        index={x["id"]:x["scanner_superior_mm"] for x in json.loads(p.read_text())["slices"]}
        self.assertEqual(index[1399]-index[1451],57)
        self.assertEqual(1451-1399,52)
        self.assertNotEqual(index[1399]-index[1451],1451-1399)
        self.assertEqual(index[1948],-556)

    def test_pinned_source_changes_fail_closed(self):
        p=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
           "nlm_pelvis_scout_pinned_source_positions_20261009.json")
        data=json.loads(p.read_text())
        rows=[{
            "slice_id":x["id"],"filename":x["source_png_name"],
            "source_png_sha256":x["source_png_sha256"],
            "source_header_sha256":x["source_header_sha256"],
            "scanner_RAS_image_location_superior_mm":x["scanner_superior_mm"],
            "in_plane_mm_per_pixel":x["pixel_spacing_mm"],
            "slice_thickness_mm":x["thickness_mm"]
        } for x in data["slices"]]
        good=scout.verify_pinned_manifest({"slices":rows},data)
        self.assertEqual(good["source_slices_checked"],12)
        self.assertFalse(good["anatomical_image_landmarks_verified"])
        altered=json.loads(json.dumps(rows))
        altered[0]["source_png_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"SHA changed"):
            scout.verify_pinned_manifest({"slices":altered},data)

    def test_invented_scanner_z_rejected_even_when_filename_and_hash_match(self):
        p=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
           "nlm_pelvis_scout_pinned_source_positions_20261009.json")
        data=json.loads(p.read_text())
        rows=[{
            "slice_id":x["id"],"filename":x["source_png_name"],
            "source_png_sha256":x["source_png_sha256"],
            "source_header_sha256":x["source_header_sha256"],
            "scanner_RAS_image_location_superior_mm":x["scanner_superior_mm"],
            "in_plane_mm_per_pixel":x["pixel_spacing_mm"],
            "slice_thickness_mm":x["thickness_mm"]
        } for x in data["slices"]]
        rows[-1]["scanner_RAS_image_location_superior_mm"] += 5
        with self.assertRaisesRegex(ValueError,"scanner coordinates"):
            scout.verify_pinned_manifest({"slices":rows},data)

    def test_do_not_allow_manifest_to_claim_pelvis_anatomy(self):
        p=(HERE.parent/"ORIGINAL_V1_WORK/anatomy/audit/"
           "nlm_pelvis_scout_pinned_source_positions_20261009.json")
        data=json.loads(p.read_text())
        data["anatomical_pelvic_slice_confirmed"]=True
        with self.assertRaisesRegex(ValueError,"improperly claims"):
            scout.verify_pinned_manifest({"slices":[]},data)

    def test_disallow_unreviewed_image_number(self):
        with self.assertRaisesRegex(ValueError,"allowlist"):
            scout.atlas([9999],lambda url,limit: b"bad")

    def test_duplicate_slice_ids_rejected(self):
        with self.assertRaisesRegex(ValueError,"allowlist"):
            scout.atlas([1399,1399],lambda url,limit:b"bad")

    def test_no_actual_pelvic_label_after_scanning(self):
        name="cvm1948f.png"
        r=scout.record(name,self.clear_png,valid_header(-546))
        self.assertFalse(r["bone_region_identified_by_anatomical_review"])
        self.assertIn("upper thigh",r["sample_reference_region_only"])
        self.assertTrue(r["no_source_image_or_identifier_committed"])

    def test_pinned_source_scout_ids_from_index(self):
        self.assertEqual(scout.SCOUT_IDS,
                         (1300,1399,1451,1500,1551,1602,1650,1701,1752,1800,1906,1948))
        self.assertTrue(scout.INDEX_BASE.startswith("https://data.lhncbc.nlm.nih.gov/"))


if __name__=="__main__":
    unittest.main()
