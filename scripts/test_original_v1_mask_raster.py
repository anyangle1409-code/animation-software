"""First-party QA mask rasterizer tests."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

import original_v1_mask_raster as r


class MaskRasterTests(unittest.TestCase):
    def test_triangle_fills_role(self):
        result=r.rasterize([{"points":[[1,1,2],[6,1,2],[1,6,2]],"roles":["subject","body"]}],8,8)
        self.assertGreater(sum(v>0 for v in result["masks"]["body"]),0)
        self.assertEqual(result["masks"]["body"],result["masks"]["subject"])

    def test_front_triangle_occludes_back_role(self):
        tris=[
            {"points":[[1,1,4],[6,1,4],[1,6,4]],"roles":["body"]},
            {"points":[[1,1,2],[6,1,2],[1,6,2]],"roles":["garment"]},
        ]
        result=r.rasterize(tris,8,8)
        self.assertGreater(sum(v>0 for v in result["masks"]["garment"]),0)
        self.assertEqual(sum(v>0 for v in result["masks"]["body"]),0)

    def test_equal_depth_merges_roles_deterministically(self):
        tris=[
            {"points":[[1,1,2],[6,1,2],[1,6,2]],"roles":["body"]},
            {"points":[[1,1,2],[6,1,2],[1,6,2]],"roles":["hand_l"]},
        ]
        result=r.rasterize(tris,8,8)
        self.assertEqual(result["masks"]["body"],result["masks"]["hand_l"])

    def test_invalid_depth_refused(self):
        with self.assertRaisesRegex(ValueError,"positive depth"):
            r.rasterize([{"points":[[1,1,-1],[2,1,1],[1,2,1]],"roles":["body"]}],4,4)

    def test_p5_write_is_collision_safe(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"m.pgm";r.write_p5(p,2,2,bytearray([0,255,0,255]))
            self.assertTrue(p.read_bytes().startswith(b"P5\n2 2\n255\n"))
            with self.assertRaisesRegex(ValueError,"collision"):r.write_p5(p,2,2,bytearray(4))


if __name__=="__main__":
    unittest.main()
