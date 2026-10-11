"""Hand-derived tetrahedra test mathematical source QA, never anatomical truth."""
import hashlib
import importlib.util
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))


def tetra(offset=(0, 0, 0), scale=1):
    points = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    v = [tuple(offset[j] + scale*p[j] for j in range(3)) for p in points]
    return [tuple(v[i] for i in face) for face in
            [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]]


def binary(faces):
    return b'x'*80 + struct.pack('<I', len(faces)) + b''.join(
        struct.pack('<12fH', 0, 0, 0, *[x for v in face for x in v], 0)
        for face in faces)


class Components(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec('source_surface_component_geometry') is None:
            raise AssertionError('Missing source component QA implementation')
        import source_surface_component_geometry
        cls.m = source_surface_component_geometry

    def test_closed_tetra_area_volume_centres(self):
        r = self.m.analyze(binary(tetra()))
        c = r['components'][0]
        self.assertEqual(c['nondegenerate_faces'], 4)
        self.assertAlmostEqual(c['surface_area_source_units_squared'], (3+math.sqrt(3))/2)
        self.assertAlmostEqual(c['signed_algebraic_volume_source_units_cubed'], 1/6)
        self.assertEqual(c['algebraic_volume_centroid_source_units'], [.25]*3)
        want = (2+math.sqrt(3))/(3*(3+math.sqrt(3)))
        for x in c['surface_area_centroid_source_units']:
            self.assertAlmostEqual(x, want)
        self.assertFalse(r['source_units_or_frame_verified'])
        self.assertFalse(r['anatomical_centroids_accepted'])
        self.assertFalse(r['canonical_promotion_allowed'])

    def test_translation_stable_volume_not_origin_dependent(self):
        c = self.m.analyze(binary(tetra((1000000, -1000000, 2000000))))['components'][0]
        self.assertAlmostEqual(c['signed_algebraic_volume_source_units_cubed'], 1/6)
        self.assertEqual(c['algebraic_volume_centroid_source_units'], [1000000.25, -999999.75, 2000000.25])

    def test_two_shells_keep_small_island_and_individual_bounds(self):
        r = self.m.analyze(binary(tetra()+tetra((10, 20, 30), 2)))
        self.assertEqual(len(r['components']), 2)
        centres = sorted(c['algebraic_volume_centroid_source_units'] for c in r['components'])
        self.assertEqual(centres, [[.25]*3, [10.5, 20.5, 30.5]])
        self.assertEqual(sorted(c['bbox_extent_source_units'] for c in r['components']), [[1]*3, [2]*3])

    def test_degenerate_face_does_not_become_surface_island(self):
        r = self.m.analyze(binary(tetra()+[((5, 5, 5),)*3]))
        self.assertEqual(r['degenerate_faces'], 1)
        self.assertEqual(len(r['components']), 1)
        self.assertEqual(r['components'][0]['bbox_max_source_units'], [1]*3)

    def test_open_shell_refuses_volume(self):
        c = self.m.analyze(binary(tetra()[:-1]))['components'][0]
        self.assertEqual(c['boundary_edges'], 3)
        self.assertIsNone(c['signed_algebraic_volume_source_units_cubed'])
        self.assertIsNone(c['algebraic_volume_centroid_source_units'])

    def test_closed_flat_double_triangle_has_no_volume_centroid(self):
        f = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        c = self.m.analyze(binary([f, f[::-1]]))['components'][0]
        self.assertEqual(c['boundary_edges'], 0)
        self.assertEqual(c['same_direction_paired_edges'], 0)
        self.assertIsNone(c['algebraic_volume_centroid_source_units'])

    def test_triangle_order_does_not_change_mathematical_centres(self):
        a = self.m.analyze(binary(tetra()))['components'][0]
        b = self.m.analyze(binary(tetra()[::-1]))['components'][0]
        for key in ('surface_area_centroid_source_units', 'algebraic_volume_centroid_source_units'):
            for x, y in zip(a[key], b[key]):
                self.assertAlmostEqual(x, y)

    def test_one_reversed_face_refuses_volume(self):
        f = tetra()
        f[0] = f[0][::-1]
        c = self.m.analyze(binary(f))['components'][0]
        self.assertEqual(c['same_direction_paired_edges'], 3)
        self.assertIsNone(c['algebraic_volume_centroid_source_units'])

    def test_global_reversal_changes_volume_sign_not_centroid(self):
        c = self.m.analyze(binary([f[::-1] for f in tetra()]))['components'][0]
        self.assertAlmostEqual(c['signed_algebraic_volume_source_units_cubed'], -1/6)
        self.assertEqual(c['algebraic_volume_centroid_source_units'], [.25]*3)

    def test_duplicate_face_reports_nonmanifold_locations(self):
        f = tetra()
        c = self.m.analyze(binary(f+[f[0]]))['components'][0]
        self.assertEqual(c['nonmanifold_edges'], 3)
        self.assertEqual(len(c['nonmanifold_edge_locations_source_units']), 3)
        self.assertIsNone(c['signed_algebraic_volume_source_units_cubed'])

    def test_untrusted_header_normal_has_no_effect(self):
        raw = bytearray(binary(tetra()))
        struct.pack_into('<3f', raw, 84, float('nan'), float('inf'), -100)
        c = self.m.analyze(bytes(raw))['components'][0]
        self.assertAlmostEqual(c['signed_algebraic_volume_source_units_cubed'], 1/6)

    def test_nonfinite_vertices_rejected(self):
        raw = bytearray(binary(tetra()))
        struct.pack_into('<f', raw, 96, float('nan'))
        with self.assertRaises(ValueError):
            self.m.analyze(bytes(raw))

    def test_header_lps_is_a_declaration_not_verified_registration_or_units(self):
        raw=binary(tetra())
        for text,want in [('3D Slicer output. SPACE=LPS','LPS'),
                          ('SPACE=RAS','RAS'),('no declaration','UNSPECIFIED'),
                          ('SPACE=LPS SPACE=RAS','AMBIGUOUS_OR_UNSUPPORTED'),
                          ('SPACE=XYZ','AMBIGUOUS_OR_UNSUPPORTED')]:
            r=self.m.analyze(text.encode().ljust(80,b'\0')+raw[80:])
            self.assertEqual(r.get('source_header_coordinate_declaration'),want)
            self.assertFalse(r['source_frame_registration_verified'])
            self.assertFalse(r['source_units_or_frame_verified'])

    def test_truncation_count_mismatch_and_extra_bytes_rejected(self):
        raw = binary(tetra())
        for bad in (b'', raw[:-1], raw+b'x', raw[:80]+struct.pack('<I', 999999999)+raw[84:]):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                self.m.analyze(bad)

    def test_all_degenerate_rejected(self):
        with self.assertRaises(ValueError):
            self.m.analyze(binary([((1, 2, 3),)*3]))

    def test_cli_checks_sha_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src, out = root/'source.stl', root/'report.json'
            raw = binary(tetra())
            src.write_bytes(raw)
            cmd = [sys.executable, self.m.__file__, '--input', str(src), '--sha256', hashlib.sha256(raw).hexdigest(), '--output', str(out)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            saved = out.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(out.read_bytes(), saved)
            self.assertEqual(src.read_bytes(), raw)

    def test_cli_bad_digest_creates_no_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src, out = root/'source.stl', root/'report.json'
            src.write_bytes(binary(tetra()))
            cmd = [sys.executable, self.m.__file__, '--input', str(src), '--sha256', '0'*64, '--output', str(out)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())

    def test_paths_inside_any_other_git_checkout_refused(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)/'other-repo'
            repo.mkdir()
            (repo/'.git').write_text('gitdir: elsewhere')
            with self.assertRaises(ValueError):
                self.m.require_private(repo/'result.json')


if __name__ == '__main__':
    unittest.main()
