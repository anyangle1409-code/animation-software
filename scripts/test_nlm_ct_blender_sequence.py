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
    def test_scanner_display_rotation_preserves_handedness_and_mm_scale(self):
        sys.path.insert(0, str(HERE))
        viewer = importlib.import_module("build_nlm_ct_blender_sequence_viewer")
        axes = [viewer._scanner_to_view(point) for point in
                ((1000, 0, 0), (0, 1000, 0), (0, 0, 1000))]
        for actual, expected in zip(axes, ((-1, 0, 0), (0, -1, 0), (0, 0, 1))):
            for coordinate, wanted in zip(actual, expected):
                self.assertAlmostEqual(coordinate, wanted, places=6)
        self.assertAlmostEqual(axes[0].cross(axes[1]).dot(axes[2]), 1.0, places=6)

    @unittest.skipIf(bpy is None, "requires Blender's bundled Python")
    def test_plane_corners_and_uv_keep_source_pixel_orientation(self):
        sys.path.insert(0, str(HERE))
        viewer = importlib.import_module("build_nlm_ct_blender_sequence_viewer")
        geometry = {"plane_TL_RAS_mm": [10, 20, 30],
                    "plane_TR_RAS_mm": [30, 20, 30],
                    "plane_BR_RAS_mm": [30, 0, 30]}
        record = self.module().build_frame_plan(bundle())["frames"][0]
        material = bpy.data.materials.new("TEST_CT_CORNER_MATERIAL")
        obj, corners = viewer._make_plane("TEST_CT_SOURCE_CORNERS", geometry,
                                          material, record)
        mesh = obj.data
        try:
            expected = ((-.01, -.02, .03), (-.03, -.02, .03),
                        (-.03, 0, .03), (-.01, 0, .03))
            for corner, wanted in zip(corners, expected):
                for actual, coordinate in zip(corner, wanted):
                    self.assertAlmostEqual(actual, coordinate, places=6)
            self.assertEqual([tuple(uv.uv) for uv in mesh.uv_layers.active.data],
                             [(0, 1), (1, 1), (1, 0), (0, 0)])
            location, rotation, scale = viewer._camera_pose(corners)
            self.assertAlmostEqual(location.z, 1.03, places=6)
            self.assertAlmostEqual(scale, .0208, places=6)
            self.assertAlmostEqual(rotation.to_matrix().determinant(), 1.0, places=6)
            self.assertFalse(obj["canonical_promotion_allowed"])
        finally:
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(mesh)
            bpy.data.materials.remove(material)

    @unittest.skipIf(bpy is None, "requires Blender's bundled Python")
    def test_image_material_keeps_synthetic_display_external_and_unpacked(self):
        sys.path.insert(0, str(HERE))
        viewer = importlib.import_module("build_nlm_ct_blender_sequence_viewer")
        import ct_pelvis_window_geometry as window
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic-display.png"
            path.write_bytes(window.encode_png_gray8(2, 2, bytes([0, 64, 128, 255])))
            material, image = viewer._material_for_image("TEST_CT_EXTERNAL", path)
            try:
                self.assertIsNone(image.packed_file)
                self.assertEqual(Path(image.filepath).resolve(), path.resolve())
                self.assertEqual(tuple(image.size), (2, 2))
                textures = [node for node in material.node_tree.nodes
                            if node.type == "TEX_IMAGE"]
                self.assertEqual(len(textures), 1)
                self.assertEqual(textures[0].image, image)
                self.assertEqual(textures[0].interpolation, "Closest")
            finally:
                bpy.data.materials.remove(material)
                bpy.data.images.remove(image)

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
