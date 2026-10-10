"""Adversarial source and STL tests; require no source downloads or Blender."""
import copy
import io
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anatomy_fit.bonehub_surface_intake import (
    ROOT, digest, download_verified, load_sources, measure_binary_stl,
    private_location,
)


def tetra_stl(header=b"Binary synthetic STL"):
    verts = [
        ((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        ((0, 0, 0), (1, 0, 0), (0, 0, 1)),
        ((0, 0, 0), (0, 1, 0), (0, 0, 1)),
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    ]
    blob = bytearray(header.ljust(80, b" ")[:80] + struct.pack("<I", len(verts)))
    for tri in verts:
        blob.extend(struct.pack("<12fH", 0., 0., 1., *tri[0], *tri[1], *tri[2], 0))
    return bytes(blob)


class SourceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_sources()

    def changed_manifest(self, update):
        obj = copy.deepcopy(self.manifest)
        update(obj)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidate.json"
            path.write_text(json.dumps(obj), encoding="utf-8")
            return load_sources(path)

    def test_exact_pinned_three_blocked_regions(self):
        sources = {s["id"]: s for s in self.manifest["samples"]}
        self.assertEqual(set(sources), {
            "carpus_scaphoid_left", "tarsus_talus_left",
            "tarsus_cuboid_left", "rib_1_left",
        })
        self.assertEqual(sources["carpus_scaphoid_left"]["sha256"],
                         "362d0d42bf1b4475e705846d8c7c48965bb052f875a93355c8e302937ddef762")
        self.assertEqual(sources["tarsus_talus_left"]["sha256"],
                         "b79dcb8037223d2652e300cb42124c9d4e16dfedcc49ff36b4d44ed3fc24602e")
        self.assertEqual(sources["rib_1_left"]["sha256"],
                         "5b5216f2df8cac598aa94b1fe89039ce6734a15e520b9f1f788ddae3a6070295")
        self.assertFalse(self.manifest["acceptance"]["canonical_promoted"])

    def test_reject_forged_acceptance(self):
        with self.assertRaisesRegex(ValueError, "acceptance"):
            self.changed_manifest(lambda v: v["acceptance"].update({"cp1_passed": True}))

    def test_reject_unexpected_subject(self):
        with self.assertRaisesRegex(ValueError, "subject"):
            self.changed_manifest(lambda v: v["subject"].update({"stature_cm": 182}))

    def test_reject_duplicate_id(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.changed_manifest(lambda v: v["samples"][1].update(
                {"id": "carpus_scaphoid_left"}))

    def test_reject_unpinned_digest(self):
        with self.assertRaisesRegex(ValueError, "SHA"):
            self.changed_manifest(lambda v: v["samples"][1].update({"sha256": "0"*63}))

    def test_reject_path_traversal(self):
        with self.assertRaisesRegex(ValueError, "path"):
            self.changed_manifest(lambda v: v["samples"][1].update(
                {"path": "../LEAK.stl"}))

    def test_reject_extra_source(self):
        with self.assertRaisesRegex(ValueError, "four"):
            self.changed_manifest(lambda v: v["samples"].append({
                **v["samples"][0], "id": "extra_source"
            }))

    def test_binary_tetra_geometry(self):
        report = measure_binary_stl(tetra_stl())
        self.assertEqual(report["binary_stl_triangles"], 4)
        self.assertEqual(report["bounds_min_source_units"], [0., 0., 0.])
        self.assertEqual(report["bbox_extent_source_units"], [1., 1., 1.])
        self.assertFalse(report["closed_surface_or_joint_contact_validated"])

    def test_binary_header_may_start_with_solid(self):
        self.assertEqual(measure_binary_stl(tetra_stl(b"solid-but-binary"))[
                         "binary_stl_triangles"], 4)

    def test_reject_truncated_or_ascii(self):
        with self.assertRaises(ValueError):
            measure_binary_stl(tetra_stl()[:-4])
        with self.assertRaises(ValueError):
            measure_binary_stl(b"solid test\nfacet\nendsolid" * 8)

    def test_reject_nonfinite_vertex(self):
        blob = bytearray(tetra_stl())
        struct.pack_into("<f", blob, 84+12, math.nan)
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            measure_binary_stl(bytes(blob))

    def test_reject_degenerate_plane(self):
        blob = bytearray(tetra_stl())
        for i in range(4):
            for offset in (84+50*i+12+8, 84+50*i+12+20, 84+50*i+12+32):
                struct.pack_into("<f", blob, offset, 0.)
        with self.assertRaisesRegex(ValueError, "planar"):
            measure_binary_stl(bytes(blob))

    def test_reject_repository_output(self):
        with self.assertRaisesRegex(ValueError, "OUTSIDE"):
            private_location(ROOT / "work" / "medical_meshes")
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(private_location(Path(root)), Path(root).resolve())

    def test_cached_wrong_digest_is_not_accepted_or_modified(self):
        with tempfile.TemporaryDirectory() as root:
            source = self.manifest["samples"][0]
            file = Path(root) / (source["id"] + ".stl")
            original = tetra_stl()
            file.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "Unverified"):
                download_verified(source, Path(root), False)
            self.assertEqual(file.read_bytes(), original)

    def test_network_not_used_without_flag(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("anatomy_fit.bonehub_surface_intake.urllib.request.urlopen") as mocked:
                with self.assertRaises(FileNotFoundError):
                    download_verified(self.manifest["samples"][0], Path(root), False)
                mocked.assert_not_called()

    def test_hash_check_prior_to_write(self):
        with tempfile.TemporaryDirectory() as root:
            source = dict(self.manifest["samples"][0])
            valid = tetra_stl()
            source["sha256"] = digest(valid)
            path = Path(root) / (source["id"] + ".stl")
            with patch("anatomy_fit.bonehub_surface_intake.urllib.request.urlopen",
                       return_value=io.BytesIO(b"incorrect-data")):
                with self.assertRaisesRegex(ValueError, "SHA256"):
                    download_verified(source, Path(root), True)
            self.assertFalse(path.exists())
            with patch("anatomy_fit.bonehub_surface_intake.urllib.request.urlopen",
                       return_value=io.BytesIO(valid)):
                self.assertEqual(download_verified(source, Path(root), True), valid)
            self.assertEqual(path.read_bytes(), valid)
            with patch("anatomy_fit.bonehub_surface_intake.urllib.request.urlopen") as mocked:
                self.assertEqual(download_verified(source, Path(root), False), valid)
                mocked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
