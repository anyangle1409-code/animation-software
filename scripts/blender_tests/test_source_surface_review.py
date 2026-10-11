"""Real Blender integration with a synthetic tetrahedron, never anatomy."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'anatomy_fit'))


class NativeSourceReview(unittest.TestCase):
    def test_unsupported_tiny_and_extreme_coordinates_refused_before_output(self):
        import render_source_surface_review as m
        for scale in (1e-8, 1e38):
            p = [(0,0,0), (scale,0,0), (0,scale,0), (0,0,scale)]
            faces = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
            raw=b'x'*80+struct.pack('<I',4)+b''.join(struct.pack('<12fH',0,0,0,*[x for i in f for x in p[i]],0) for f in faces)
            with tempfile.TemporaryDirectory() as td:
                src,out=Path(td)/'source.stl',Path(td)/'review'
                src.write_bytes(raw)
                with self.assertRaises(ValueError):
                    m.review(src,hashlib.sha256(raw).hexdigest(),out,resolution=64)
                self.assertFalse(out.exists())

    def test_private_render_keeps_source_positions_bytes_and_faces(self):
        self.assertIsNotNone(importlib.util.find_spec('render_source_surface_review'))
        import render_source_surface_review as m
        p = [(0,0,0), (1,0,0), (0,1,0), (0,0,1)]
        faces = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
        raw = b'x'*80+struct.pack('<I',4)+b''.join(struct.pack('<12fH',0,0,0,*[x for i in f for x in p[i]],0) for f in faces)
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td)/'source.stl', Path(td)/'review'
            src.write_bytes(raw)
            report = m.review(src, hashlib.sha256(raw).hexdigest(), out, resolution=64)
            self.assertEqual(src.read_bytes(),raw)
            self.assertEqual(report['imported_raw_triangles'],4)
            self.assertEqual(report['imported_raw_vertex_instances'],12)
            self.assertFalse(report['canonical_promotion_allowed'])
            self.assertEqual(len(report['images']),3)
            for r in report['images']:
                data=(out/r['file']).read_bytes()
                self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(hashlib.sha256(data).hexdigest(),r['sha256'])
            with self.assertRaises(ValueError):
                m.review(src,hashlib.sha256(raw).hexdigest(),out)
            with self.assertRaises(ValueError):
                m.review(src,'0'*64,Path(td)/'bad')
            self.assertFalse((Path(td)/'bad').exists())


if __name__=='__main__':
    unittest.main(argv=[sys.argv[0]])
