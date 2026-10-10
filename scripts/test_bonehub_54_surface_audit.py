"""Adversarial no-network tests for frozen 54-bone raw provenance and mesh topology."""
import copy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from anatomy_fit.bonehub_region_source_index import MALE_ROOT, EXPECTED_SAMPLE_PINS
from anatomy_fit.bonehub_54_surface_audit import (
    FROZEN_UPSTREAM_REV, mesh_diagnostics, select_bones, source_url, verify_bytes,
    scan, get_bytes, main,
)

CARPAL = ("SCAPHOID", "LUNATE", "TRIQUETRUM", "PISIFORM",
          "TRAPEZIUM", "TRAPEZOID", "CAPITATE", "HAMATE")
TARSAL = ("TALUS", "CALCANEUS", "NAVICULAR", "CUBOID",
          "CUNEIFORM_MEDIAL", "CUNEIFORM_INTERMEDIATE", "CUNEIFORM_LATERAL")


def tetra_stl(triangles=None):
    vertices = [
        (0., 0., 0.), (1., 0., 0.), (0., 1., 0.), (0., 0., 1.)
    ]
    faces = triangles if triangles is not None else [
        (0,2,1), (0,1,3), (0,3,2), (1,2,3)]
    data = bytearray(b"HGPT geometry unit-test".ljust(80, b"\x00") +
                     struct.pack("<I", len(faces)))
    for a,b,c in faces:
        data.extend(struct.pack("<12fH",
                   0,0,0,*vertices[a],*vertices[b],*vertices[c],0))
    return bytes(data)


def make_index():
    entries = []
    for side in ("LEFT", "RIGHT"):
        for name in CARPAL:
            entries.append(("carpus_file_candidate", f"HAND_{side}/{name}_{side}.stl"))
        for name in TARSAL:
            entries.append(("tarsus_file_candidate", f"FOOT_{side}/{name}_{side}.stl"))
        for number in range(1,13):
            entries.append(("rib_file_candidate", f"THORAX/RIB_{number}_{side}.stl"))
    raw = tetra_stl()
    sha = hashlib.sha256(raw).hexdigest()
    return {
        "source_revision": FROZEN_UPSTREAM_REV,
        "cp1_anatomical_acceptance": False,
        "canonical_geometry_modified": False,
        "source_subject_independent_of_existing_CT": False,
        "source_file_candidates": [
            {"category": category, "source_relpath": rel,
             "size_bytes": len(raw),
             "lfs_sha256_metadata": EXPECTED_SAMPLE_PINS.get(rel, sha)}
            for category, rel in entries
        ],
    }


class WholeRegionSurfaceTests(unittest.TestCase):
    def test_exact_54_candidates_both_sides(self):
        x = select_bones(make_index())
        self.assertEqual(len(x), 54)
        self.assertEqual(sum(i["category"] == "carpus_file_candidate" for i in x), 16)
        self.assertEqual(sum(i["category"] == "tarsus_file_candidate" for i in x), 14)
        self.assertEqual(sum(i["category"] == "rib_file_candidate" for i in x), 24)
        self.assertTrue(all(i["selected_verified_pin"] for i in x))

    def test_revision_mutation_rejected(self):
        x = make_index()
        x["source_revision"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "revision"):
            select_bones(x)

    def test_claimed_acceptance_rejected(self):
        x = make_index()
        x["cp1_anatomical_acceptance"] = True
        with self.assertRaisesRegex(ValueError, "flags"):
            select_bones(x)

    def test_missing_region_file_rejected(self):
        x = make_index()
        x["source_file_candidates"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            select_bones(x)

    def test_duplicate_file_rejected(self):
        x = make_index()
        x["source_file_candidates"][1] = copy.deepcopy(x["source_file_candidates"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            select_bones(x)

    def test_opposite_side_filename_rejected(self):
        x = make_index()
        x["source_file_candidates"][0]["source_relpath"] = "HAND_LEFT/SCAPHOID_RIGHT.stl"
        with self.assertRaisesRegex(ValueError, "side"):
            select_bones(x)

    def test_missing_independent_hash_rejected(self):
        x = make_index()
        x["source_file_candidates"][5]["lfs_sha256_metadata"] = None
        with self.assertRaisesRegex(ValueError, "SHA256"):
            select_bones(x)

    def test_historical_pin_mutation_rejected(self):
        x = make_index()
        item = next(i for i in x["source_file_candidates"]
                    if i["source_relpath"] == "HAND_LEFT/SCAPHOID_LEFT.stl")
        item["lfs_sha256_metadata"] = "f"*64
        with self.assertRaisesRegex(ValueError, "Historic"):
            select_bones(x)

    def test_source_url_is_frozen(self):
        path = "THORAX/RIB_1_RIGHT.stl"
        self.assertIn("/resolve/"+FROZEN_UPSTREAM_REV+"/", source_url(FROZEN_UPSTREAM_REV, path))
        for rel in ("../unsafe.stl", "/tmp/x.stl", "FOOT_LEFT/../x.stl"):
            with self.assertRaises(ValueError):
                source_url(FROZEN_UPSTREAM_REV, rel)
        with self.assertRaises(ValueError):
            source_url("main", path)

    def test_source_stl_header_declares_lps_or_ras_without_auto_registration(self):
        raw = tetra_stl()
        for frame in ("LPS", "RAS"):
            header = ("3D Slicer output. SPACE="+frame).encode("ascii").ljust(80, b" ")
            result = mesh_diagnostics(header + raw[80:])
            self.assertEqual(result["source_stl_header_explicit_coordinate_system"], frame)
            self.assertFalse(result["source_stl_header_field_verified_as_origin"])
            self.assertFalse(result["source_to_HGPT_registration_verified"])
        self.assertIsNone(mesh_diagnostics(raw)["source_stl_header_explicit_coordinate_system"])

    def test_conflicting_explicit_stl_coordinate_headers_rejected(self):
        raw = tetra_stl()
        header = b"Slicer SPACE=RAS then SPACE=LPS".ljust(80, b" ")
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            mesh_diagnostics(header + raw[80:])

    def test_closed_oriented_tetra_is_diagnostic_only(self):
        r = mesh_diagnostics(tetra_stl())
        self.assertEqual(r["raw_triangle_count"], 4)
        self.assertEqual(r["exact_weld_unique_vertices"], 4)
        self.assertEqual(r["degenerate_triangles"], 0)
        self.assertEqual(r["boundary_edges_exact_weld"], 0)
        self.assertEqual(r["nonmanifold_edges_over_two_faces"], 0)
        self.assertEqual(r["same_direction_two_face_edges"], 0)
        self.assertEqual(r["vertex_connected_components_exact_weld"], 1)
        self.assertTrue(r["watertight_candidate_exact_weld_only"])
        self.assertFalse(r["anatomical_joint_centres_accepted"])

    def test_valid_shell_and_orphan_degenerate_vertex_are_distinct(self):
        original = bytearray(tetra_stl())
        struct.pack_into("<I", original, 80, 5)
        original.extend(struct.pack("<12fH", 0,0,0,
                                  10,10,10, 10,10,10, 10,10,10, 0))
        r = mesh_diagnostics(bytes(original))
        self.assertEqual(r["degenerate_triangles"], 1)
        self.assertEqual(r["vertex_connected_components_exact_weld"], 2)
        self.assertEqual(r["nondegenerate_face_component_counts_desc"], [4])
        self.assertEqual(r["isolated_vertex_only_components_no_valid_faces"], 1)
        self.assertFalse(r["watertight_candidate_exact_weld_only"])

    def test_two_separate_closed_shells_both_contain_faces(self):
        one = tetra_stl()
        second = bytearray()
        for i in range(4):
            record = list(struct.unpack_from("<12fH", one, 84 + i*50))
            for j in range(3, 12):
                record[j] += 10
            second.extend(struct.pack("<12fH", *record))
        raw = one[:80] + struct.pack("<I", 8) + one[84:] + second
        r = mesh_diagnostics(raw)
        self.assertEqual(r["degenerate_triangles"], 0)
        self.assertEqual(r["vertex_connected_components_exact_weld"], 2)
        self.assertEqual(r["nondegenerate_face_component_counts_desc"], [4, 4])
        self.assertEqual(r["isolated_vertex_only_components_no_valid_faces"], 0)
        self.assertFalse(r["watertight_candidate_exact_weld_only"])

    def test_missing_face_opens_boundary(self):
        r = mesh_diagnostics(tetra_stl()[:-50][:80] +
                             struct.pack("<I", 3) + tetra_stl()[84:-50])
        self.assertEqual(r["raw_triangle_count"], 3)
        self.assertGreater(r["boundary_edges_exact_weld"], 0)
        self.assertFalse(r["watertight_candidate_exact_weld_only"])

    def test_same_orientation_edge_detected(self):
        faces = [(0,1,2), (0,1,3)]
        r = mesh_diagnostics(tetra_stl(faces))
        self.assertGreater(r["same_direction_two_face_edges"], 0)

    def test_overused_edge_detected(self):
        faces = [(0,1,2), (0,1,3), (1,0,2)]
        r = mesh_diagnostics(tetra_stl(faces))
        self.assertGreater(r["nonmanifold_edges_over_two_faces"], 0)

    def test_degenerate_face_detected(self):
        faces = [(0,2,1), (0,1,3), (0,3,2), (1,2,3), (0,0,1)]
        r = mesh_diagnostics(tetra_stl(faces))
        self.assertEqual(r["degenerate_triangles"], 1)
        self.assertFalse(r["watertight_candidate_exact_weld_only"])

    def test_truncation_rejected(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            mesh_diagnostics(tetra_stl()[:-8])

    def test_nonfinite_rejected(self):
        blob = bytearray(tetra_stl())
        struct.pack_into("<f", blob, 84 + 12, float("nan"))
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            mesh_diagnostics(bytes(blob))

    def test_size_and_sha_checked_before_cache_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            x = select_bones(make_index())
            nonhistorical = next(item for item in x
                                 if item["source_relpath"] == "HAND_LEFT/LUNATE_LEFT.stl")
            dest = Path(temp) / "HAND_LEFT__LUNATE_LEFT.stl"
            raw = tetra_stl()
            dest.write_bytes(raw)
            self.assertEqual(get_bytes(nonhistorical, Path(temp), False), raw)
            dest.write_bytes(raw+b"corrupted")
            with self.assertRaisesRegex(ValueError, "length"):
                get_bytes(nonhistorical, Path(temp), False)
            self.assertEqual(dest.read_bytes(), raw+b"corrupted")

    def test_no_network_without_download_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            x = select_bones(make_index())
            with patch("anatomy_fit.bonehub_54_surface_audit.urllib.request.urlopen") as net:
                with self.assertRaisesRegex(ValueError, "download"):
                    get_bytes(x[0], Path(temp), False)
                net.assert_not_called()

    def test_54_no_source_claims_on_synthetic_meshes(self):
        index = make_index()
        raw = tetra_stl()
        with tempfile.TemporaryDirectory() as temp:
            with patch("anatomy_fit.bonehub_54_surface_audit.get_bytes", return_value=raw):
                with patch("anatomy_fit.bonehub_54_surface_audit.verify_bytes",
                           return_value="synthetic"):
                    result = scan(index, Path(temp), False)
            self.assertEqual(len(result["items"]), 54)
            self.assertFalse(result["cp1_gate6_approved"])
            self.assertFalse(result["stl_physical_units_and_axes_confirmed"])

    def test_cli_refuses_existing_report(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/"existing.json"
            out.write_text("unchanged", encoding="utf-8")
            with patch("sys.argv", ["audit","--private-dir",temp,"--output",str(out)]):
                self.assertEqual(main(), 2)
            self.assertEqual(out.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()
