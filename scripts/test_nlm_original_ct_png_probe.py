"""Synthetic PNG byte-integrity tests; NEVER download external data in unit tests."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"anatomy_fit"))
import nlm_original_ct_png_probe as p


def chunk(tag,payload):
    return (struct.pack(">I",len(payload))+tag+payload+
            struct.pack(">I",zlib.crc32(tag+payload)&0xffffffff))


def sample_png(width=512,height=512,depth=16):
    header=struct.pack(">IIBBBBB",width,height,depth,0,0,0,0)
    row=b"\x00"+b"\x00\x11" * width
    pixels=zlib.compress(row*height)
    return p.MAGIC+chunk(b"IHDR",header)+chunk(b"IDAT",pixels)+chunk(b"IEND",b"")


class CTSourceIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"cvm1012f.png"
        self.path.write_bytes(sample_png())

    def test_valid_synthetic_png_with_original_sized_header(self):
        r=p.probe_file(self.path,"cvm1012f.png")
        self.assertEqual(r["image_header"]["width_pixels"],512)
        self.assertEqual(r["image_header"]["height_pixels"],512)
        self.assertEqual(r["image_header"]["bit_depth"],16)
        self.assertTrue(r["PNG_chunk_CRC32_all_checked"])

    def test_no_anatomical_claim_or_ct_HU_calibration(self):
        r=p.probe_file(self.path)
        for flag in ("CT_Hounsfield_units_verified",
                     "axial_slice_patient_world_transform_verified",
                     "S1_ASIS_pubis_femur_features_identified",
                     "source_3d_geometry_registered","canonical_promotion_allowed"):
            self.assertFalse(r[flag])

    def test_sha256_digests_actual_bytes(self):
        r=p.probe_file(self.path)
        self.assertEqual(r["source_sha256"],hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_invalid_png_signature(self):
        with self.assertRaisesRegex(ValueError,"invalid PNG signature"):
            p.inspect_png(b"JPEG baddata")

    def test_invalid_crc_rejected(self):
        raw=bytearray(self.path.read_bytes())
        raw[20]^=1
        with self.assertRaisesRegex(ValueError,"CRC32"):
            p.inspect_png(bytes(raw))

    def test_truncated_payload_rejected(self):
        with self.assertRaisesRegex(ValueError,"truncated"):
            p.inspect_png(self.path.read_bytes()[:-3])

    def test_duplicate_ihdr_rejected(self):
        raw=self.path.read_bytes()
        ihdr=raw[8:8+12+13]
        bad=raw[:8+12+13]+ihdr+raw[8+12+13:]
        with self.assertRaisesRegex(ValueError,"duplicate PNG IHDR"):
            p.inspect_png(bad)

    def test_unsupported_colour_encoding_rejected(self):
        raw=sample_png(depth=3)
        with self.assertRaisesRegex(ValueError,"invalid PNG image"):
            p.inspect_png(raw)

    def test_ihdr_not_first_rejected(self):
        raw=self.path.read_bytes()
        bad=p.MAGIC+chunk(b"tEXt",b"fake")+raw[8:]
        with self.assertRaisesRegex(ValueError,"missing first IHDR"):
            p.inspect_png(bad)

    def test_late_untrusted_extra_chunk_rejected(self):
        raw=self.path.read_bytes()+chunk(b"tEXt",b"bad")
        with self.assertRaisesRegex(ValueError,"IEND not final"):
            p.inspect_png(raw)

    def test_frame_image_identity_rejected(self):
        with self.assertRaisesRegex(ValueError,"identity mismatch"):
            p.probe_file(self.path,"cvm1013f.png")

    def test_nonallowlisted_download_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError,"not a pinned"):
            p.download_allowlisted("other_slice.png",Path(self.tmp.name)/"out.png")

    def test_exclusive_output_does_not_overwrite_existing_file(self):
        # No network initiated if output already exists.
        with self.assertRaisesRegex(ValueError,"refuse to replace"):
            p.download_allowlisted("cvm1012f.png",self.path)

    def test_source_URL_is_NLM_custodian(self):
        self.assertTrue(p.BASE.startswith("https://data.lhncbc.nlm.nih.gov/"))
        self.assertEqual(p.ALLOWED,("cvm1012f.png","cvm1013f.png"))


if __name__=="__main__":
    unittest.main()
