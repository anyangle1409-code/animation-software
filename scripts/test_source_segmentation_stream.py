"""Hand-written tiny label grids exercise layer order and gzip validation."""
import gzip
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent/'anatomy_fit'))


def nrrd(payload, layered=False, extras=''):
    header=('NRRD0004\ntype: unsigned char\ndimension: '+('4' if layered else '3')+
            '\nspace: left-posterior-superior\nsizes: '+('2 2 2 2' if layered else '2 2 2')+
            '\nspace directions: '+('none ' if layered else '')+
            '(1,0,0) (0,1,0) (0,0,1)\nkinds: '+('list ' if layered else '')+
            'domain domain domain\nencoding: gzip\nspace origin: (0,0,0)\n'+extras+'\n')
    return header.encode()+gzip.compress(payload,mtime=0)


class Stream(unittest.TestCase):
    def sample(self,raw,queries,**kwargs):
        self.assertIsNotNone(importlib.util.find_spec('source_segmentation_stream'))
        import source_segmentation_stream as m
        return m.sample(raw,queries,**kwargs)

    def test_xyz_order_and_duplicate_queries_keep_requested_order(self):
        r=self.sample(nrrd(bytes(range(8))),[(1,1,1,0),(0,0,0,0),(1,0,0,0),(1,1,1,0)])
        self.assertEqual(r['label_values'],[7,0,1,7])
        self.assertEqual(r['decoded_bytes_verified'],8)
        self.assertFalse(r['anatomical_identity_accepted'])

    def test_layer_is_fastest_axis_not_whole_volume_layer_blocks(self):
        r=self.sample(nrrd(bytes(range(16)),True),[(0,0,0,1),(1,0,0,0),(1,1,1,1)])
        self.assertEqual(r['label_values'],[1,2,15])

    def test_small_stream_chunks_can_split_sample_positions(self):
        r=self.sample(nrrd(bytes(range(16)),True),[(1,1,1,1),(1,0,0,0)],chunk_bytes=3)
        self.assertEqual(r['label_values'],[15,2])

    def test_exact_decoded_size_required(self):
        for payload in (bytes(7),bytes(9)):
            with self.assertRaises(ValueError):
                self.sample(nrrd(payload),[(0,0,0,0)])

    def test_corrupt_or_truncated_gzip_is_rejected_after_sample_found(self):
        good=nrrd(bytes(range(8)))
        bad=bytearray(good);bad[-8]^=1
        for raw in (bytes(bad),good[:-4]):
            with self.assertRaises(ValueError):
                self.sample(raw,[(0,0,0,0)])

    def test_unknown_frame_type_encoding_duplicate_fields_refused(self):
        good=nrrd(bytes(8))
        for raw in (good.replace(b'left-posterior-superior',b'right-anterior-superior'),
                    good.replace(b'unsigned char',b'float'),
                    good.replace(b'encoding: gzip',b'encoding: raw'),
                    nrrd(bytes(8),extras='sizes: 2 2 2\n')):
            with self.assertRaises(ValueError):
                self.sample(raw,[(0,0,0,0)])

    def test_invalid_layer_negative_fractional_and_outside_queries_refused(self):
        for q in ((0,0,0,1),(-1,0,0,0),(2,0,0,0),(0.5,0,0,0),(True,0,0,0)):
            with self.assertRaises(ValueError):
                self.sample(nrrd(bytes(8)),[q])

    def test_oversized_declared_grid_is_refused_before_inflation(self):
        raw=nrrd(bytes(8)).replace(b'sizes: 2 2 2',b'sizes: 20000 20000 20000')
        with self.assertRaises(ValueError):
            self.sample(raw,[(0,0,0,0)])

    def test_detached_data_or_payload_skip_instructions_are_not_silently_ignored(self):
        for extra in ('data file: elsewhere.gz\n','datafile: elsewhere.gz\n',
                      'byte skip: 1\n','line skip: 1\n'):
            with self.assertRaises(ValueError):
                self.sample(nrrd(bytes(range(8)),extras=extra),[(0,0,0,0)])

    def test_nonsequence_query_is_cleanly_refused(self):
        with self.assertRaises(ValueError):
            self.sample(nrrd(bytes(8)),[7])

    def test_spatial_field_junk_and_missing_origin_parentheses_are_refused(self):
        good=nrrd(bytes(8))
        for raw in (good.replace(b'space directions: ',b'space directions: ignored-junk '),
                    good.replace(b'space origin: (0,0,0)',b'space origin: 0,0,0')):
            with self.assertRaises(ValueError):
                self.sample(raw,[(0,0,0,0)])


if __name__=='__main__':
    unittest.main()
