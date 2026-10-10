#!/usr/bin/env python3
"""Independent synthetic geometry and source-gating checks; NOT anatomy tests."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import nlm_ct_provisional_surface as surface

AUDIT = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
BUNDLE = AUDIT / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
CALIBRATION = AUDIT / "nlm_pelvic_ct_full_series_hu_calibration_20261009.json"


def geom(s=-342):
    # Source-verified image axis directions: increasing column -R, row -A.
    return {
        "plane_TL_RAS_mm": [230, 230, s],
        "plane_TR_RAS_mm": [-230, 230, s],
        "plane_BR_RAS_mm": [-230, -230, s],
    }


class ProvisionalSurface(unittest.TestCase):
    def test_one_voxel_has_six_outward_boundary_faces(self):
        verts, faces = surface.make_surface({(0, 10, 20)}, geom(), -342)
        self.assertEqual(len(verts), 8)
        self.assertEqual(len(faces), 6)
        self.assertEqual({len(face) for face in faces}, {4})
        centre = [sum(p[i] for p in verts) / len(verts) for i in range(3)]
        for face in faces:
            p = [verts[i - 1] for i in face]
            a = surface._sub(p[1], p[0])
            b = surface._sub(p[2], p[0])
            normal = surface._cross(a, b)
            mid = [sum(q[i] for q in p) / 4 for i in range(3)]
            self.assertGreater(surface._dot(normal, surface._sub(mid, centre)), 0)

    def test_adjacent_voxels_share_faces_and_vertices_in_xy_and_z(self):
        for pair in ({(0, 1, 1), (0, 1, 2)},
                     {(0, 1, 1), (0, 2, 1)},
                     {(0, 1, 1), (1, 1, 1)}):
            with self.subTest(pair=pair):
                verts, faces = surface.make_surface(pair, geom(), -342)
                self.assertEqual(len(verts), 12)
                self.assertEqual(len(faces), 10)
                self.assertEqual(surface.component_sizes(pair), [2])

    def test_disconnected_threshold_islands_are_preserved(self):
        self.assertEqual(surface.component_sizes({(0, 2, 2), (1, 40, 40)}),
                         [1, 1])

    def test_pixel_origin_uncertainty_remains_explicit(self):
        vox = {(0, 2, 2)}
        outer, _ = surface.make_surface(vox, geom(), -342, pixel_origin="outer_edge")
        centre, _ = surface.make_surface(vox, geom(), -342,
                                         pixel_origin="first_pixel_centre")
        delta = 230 * 2 / 512 / 2
        for a, b in zip(outer, centre):
            self.assertAlmostEqual(b[0] - a[0], delta)
            self.assertAlmostEqual(b[1] - a[1], delta)
            self.assertAlmostEqual(b[2], a[2])

    def test_invalid_or_oversized_geometry_rejected(self):
        for pixels in (set(), {(0, 0, -1)}, {(0, -1, 0)}):
            with self.subTest(pixels=pixels), self.assertRaises(ValueError):
                surface.make_surface(pixels, geom(), -342)
        with self.assertRaisesRegex(ValueError, "pixel origin"):
            surface.make_surface({(0, 0, 0)}, geom(), -342, pixel_origin="guess")
        with self.assertRaisesRegex(ValueError, "axial"):
            tilted = geom()
            tilted["plane_BR_RAS_mm"][2] = -340
            surface.make_surface({(0, 0, 0)}, tilted, -342)

    def test_private_source_pin_mismatch_rejected(self):
        source_row = json.loads(BUNDLE.read_text())["series"][0]["slices"][0]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / (source_row["source_id"] + ".png")).write_bytes(b"not the original")
            (p / (source_row["source_id"] + ".txt")).write_bytes(b"fake")
            with self.assertRaisesRegex(ValueError, "pin"):
                surface._private_source_slice(p, source_row)

    def test_full_group_is_not_silently_welded_and_output_is_private(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            args = SimpleNamespace(
                ct_dir=str(path / "source"), out=str(path / "candidate.obj"),
                bundle=str(BUNDLE), calibration=str(CALIBRATION),
                group=1, start=0, count=2, roi=[2, 3, 2, 3], hu_min=300,
                pixel_origin="outer_edge")
            original = [0] * (512 * 512)
            original[2 * 512 + 2] = 1400

            def staged(_folder, row):
                return geom(row["scanner_centre_RAS_mm"][2]), original

            with patch.object(surface, "_private_source_slice", side_effect=staged):
                report = surface.extract(args)
            self.assertEqual(report["voxel_count"], 2)
            self.assertEqual(report["connected_components_6_neighbour"], [2])
            self.assertEqual(report["boundary_quads"], 10)
            self.assertEqual(report["source_ids"], ["cvm1734f", "cvm1737f"])
            self.assertFalse(report["bone_identity_or_surface_verified"])
            self.assertFalse(report["canonical_promotion_allowed"])
            self.assertTrue((path / "candidate.obj").is_file())
            self.assertTrue((path / "candidate.obj.json").is_file())
            with patch.object(surface, "_private_source_slice", side_effect=staged):
                with self.assertRaisesRegex(ValueError, "new private"):
                    surface.extract(args)
            args.group = 3
            args.out = str(path / "other.obj")
            with self.assertRaisesRegex(ValueError, "acquisition group"):
                surface.extract(args)

    def test_missing_real_files_cannot_yield_mesh(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)
            args = SimpleNamespace(
                ct_dir=str(path), out=str(path / "candidate.obj"),
                bundle=str(BUNDLE), calibration=str(CALIBRATION),
                group=1, start=0, count=2, roi=[2, 3, 2, 3], hu_min=300,
                pixel_origin="outer_edge")
            with self.assertRaises(OSError):
                surface.extract(args)
            self.assertFalse((path / "candidate.obj").exists())


if __name__ == "__main__":
    unittest.main()
