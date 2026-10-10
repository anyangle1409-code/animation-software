"""Synthetic unsigned16 grids test pixel reads, never HU/anatomical validity."""
import gzip
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent/'anatomy_fit'))


def image(endian='<',values=(0,1,2,3,4,5,6,65535),slope=1,intercept=0):
    h=bytearray(352)
    struct.pack_into(endian+'i',h,0,348)
    struct.pack_into(endian+'8h',h,40,3,2,2,2,1,1,1,1)
    struct.pack_into(endian+'2h',h,70,512,16)
    struct.pack_into(endian+'8f',h,76,1,1,1,1,0,0,0,0)
    struct.pack_into(endian+'3f',h,108,352,slope,intercept)
    h[123]=2;h[344:348]=b'n+1\0'
    return gzip.compress(bytes(h)+struct.pack(endian+str(len(values))+'H',*values),mtime=0)


class Pixels(unittest.TestCase):
    def run_sample(self,raw,queries,sha=None,**kwargs):
        self.assertIsNotNone(importlib.util.find_spec('source_nifti_pixel_stream'))
        import source_nifti_pixel_stream as m
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'image.nii.gz';p.write_bytes(raw)
            r=m.sample(p,sha or hashlib.sha256(raw).hexdigest(),queries,**kwargs)
            self.assertEqual(p.read_bytes(),raw)
            return r

    def test_unsigned_values_xyz_order_and_duplicate_requests(self):
        r=self.run_sample(image(),[(1,1,1),(0,0,0),(1,0,0),(1,1,1)])
        self.assertEqual(r['stored_values'],[65535,0,1,65535])
        self.assertFalse(r['hounsfield_units_verified'])
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertEqual(r['decoded_pixel_bytes_verified'],16)

    def test_big_endian_pixels_and_declared_scalar_scaling(self):
        r=self.run_sample(image('>',slope=2,intercept=-10),[(1,0,0),(1,1,1)])
        self.assertEqual(r['stored_values'],[1,65535])
        self.assertEqual(r['header_scaled_values'],[-8,131060])

    def test_zero_slope_means_no_scaling_and_ignores_intercept(self):
        r=self.run_sample(image(slope=0,intercept=-1000),[(1,0,0)])
        self.assertEqual(r['header_scaled_values'],[1])

    def test_bad_source_hash_is_refused(self):
        with self.assertRaises(ValueError):
            self.run_sample(image(),[(0,0,0)],sha='0'*64)

    def test_truncated_extra_pixels_and_bad_trailer_are_refused(self):
        good=image();bad=bytearray(good);bad[-8]^=1
        for raw in (image(values=tuple(range(7))),image(values=tuple(range(9))),good[:-4],bytes(bad)):
            with self.assertRaises(ValueError):
                self.run_sample(raw,[(0,0,0)])

    def test_nonfinite_scaling_wrong_magic_or_datatype_refused(self):
        good=bytearray(gzip.decompress(image()))
        variants=[]
        for offset,value in ((344,b'bad\0'),(70,struct.pack('<h',4)),(112,struct.pack('<f',float('nan')))):
            h=bytearray(good);h[offset:offset+len(value)]=value;variants.append(gzip.compress(h,mtime=0))
        for raw in variants:
            with self.assertRaises(ValueError):
                self.run_sample(raw,[(0,0,0)])

    def test_invalid_indices_and_chunk_alignment_refused(self):
        for q in ((2,0,0),(-1,0,0),(0.5,0,0),(True,0,0),7):
            with self.assertRaises(ValueError):
                self.run_sample(image(),[q])
        with self.assertRaises(ValueError):
            self.run_sample(image(),[(0,0,0)],chunk_bytes=3)


if __name__=='__main__':
    unittest.main()
