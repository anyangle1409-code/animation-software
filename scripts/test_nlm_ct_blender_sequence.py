"""Behavioral tests for the source-ordered private Blender CT viewer plan."""
import importlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "anatomy_fit"))

try:
    import bpy
except ModuleNotFoundError:
    bpy = None


def bundle():
    def source(source_id, scanner_s, digit):
        return {
            "source_id": source_id,
            "source_png_sha256": digit * 64,
            "source_header_sha256": format(int(digit, 16) + 1, "x") * 64,
            "scanner_centre_RAS_mm": [1.0, 2.0, scanner_s],
        }

    return {
        "schema_version": 1,
        "kind": "CANDIDATE_PELVIC_CT_SERIES_BUNDLE",
        "source_skeleton_governs_geometry": True,
        "canonical_promotion_allowed": False,
        "series": [
            {"slices": [source("superior-a", 6.0, "a"),
                        source("superior-b", 3.0, "b")]},
            {"slices": [source("inferior-a", 1.0, "c"),
                        source("inferior-b", -2.0, "d")]},
        ],
    }


class BlenderSequencePlanTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(
            importlib.util.find_spec("nlm_ct_blender_sequence"),
            "the private Blender sequence planner must be implemented",
        )
        return importlib.import_module("nlm_ct_blender_sequence")

    def test_frame_plan_preserves_series_order_and_group_boundary(self):
        plan = self.module().build_frame_plan(bundle())
        self.assertEqual(
            [(row["frame"], row["group_index"], row["source_id"], row["scanner_S_mm"])
             for row in plan["frames"]],
            [(1, 1, "superior-a", 6.0), (2, 1, "superior-b", 3.0),
             (3, 2, "inferior-a", 1.0), (4, 2, "inferior-b", -2.0)],
        )
        self.assertEqual(
            [(group["frame_start"], group["frame_end"], group["slice_count"])
             for group in plan["groups"]],
            [(1, 2, 2), (3, 4, 2)],
        )
        self.assertEqual(plan["group_boundary_frame"], 3)
        self.assertFalse(plan["canonical_promotion_allowed"])

    def test_duplicate_source_id_fails_closed(self):
        value = bundle()
        value["series"][1]["slices"][0]["source_id"] = "superior-a"
        with self.assertRaisesRegex(ValueError, "duplicate source_id"):
            self.module().build_frame_plan(value)

    def test_missing_hash_fails_closed(self):
        value = bundle()
        del value["series"][0]["slices"][0]["source_header_sha256"]
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.module().build_frame_plan(value)

    def test_private_display_copy_reuses_only_identical_existing_bytes(self):
        planner = self.module()
        writer = getattr(planner, "write_private_display_copy", None)
        self.assertIsNotNone(writer, "safe resume needs verified display-copy reuse")
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "slice-display.png"
            digest = writer(target, b"fixed-display-bytes")
            self.assertEqual(digest, writer(target, b"fixed-display-bytes"))
            with self.assertRaisesRegex(ValueError, "does not match"):
                writer(target, b"different-bytes")
            self.assertEqual(target.read_bytes(), b"fixed-display-bytes")

    @unittest.skipIf(bpy is None, "requires Blender's bundled Python")
    def test_blender_visibility_schedule_is_discrete(self):
        sys.path.insert(0, str(HERE))
        viewer = importlib.import_module("build_nlm_ct_blender_sequence_viewer")
        scene = bpy.context.scene
        obj = bpy.data.objects.new("TEST_CT_FRAME_VISIBILITY", None)
        scene.collection.objects.link(obj)
        try:
            viewer._key_visibility(obj, frame=2, frame_count=4)
            scene.frame_set(1)
            self.assertTrue(obj.hide_render)
            scene.frame_set(2)
            self.assertFalse(obj.hide_render)
            scene.frame_set(3)
            self.assertTrue(obj.hide_render)
        finally:
            bpy.data.objects.remove(obj, do_unlink=True)

    @unittest.skipIf(bpy is None, "requires Blender's bundled Python")
    def test_group_boundary_markers_follow_manifest_frame_ranges(self):
        sys.path.insert(0, str(HERE))
        viewer = importlib.import_module("build_nlm_ct_blender_sequence_viewer")
        scene = bpy.data.scenes.new("TEST_CT_GROUP_MARKERS")
        try:
            add_markers = getattr(viewer, "_add_group_timeline_markers", None)
            self.assertIsNotNone(add_markers, "group boundaries need visible timeline markers")
            plan = self.module().build_frame_plan(bundle())
            markers = add_markers(scene, plan)
            self.assertEqual([(marker.frame, marker.name) for marker in markers],
                             [(1, "SOURCE_GROUP_01_START"),
                              (3, "SOURCE_GROUP_02_START")])
        finally:
            bpy.data.scenes.remove(scene)


if __name__ == "__main__":
    unittest.main()
