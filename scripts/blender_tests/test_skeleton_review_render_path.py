"""Real Blender render-path regression; the scene is NOT anatomical evidence.

Run with Blender --background --factory-startup --python-exit-code 1 --python THIS.
This tests the native render boundary using a temporary, empty review scene.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "anatomy_fit"))
from render_skeleton_only_review import setup_scene, shoot


class NativeRenderPath(unittest.TestCase):
    def test_relative_render_is_written_beside_python_manifest(self):
        # A relative path passed unchanged to Blender can use a different base
        # directory than Python's cwd. Removing absolute normalization must fail.
        initial_cwd = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="hgpt-render-path-") as td:
            try:
                os.chdir(td)
                sc = bpy.context.scene
                for obj in list(bpy.data.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                camera = setup_scene(sc)
                sc.render.resolution_x = sc.render.resolution_y = 32
                output = Path(Path(td).name)
                output.mkdir()
                image = output / "neutral.png"
                shoot(sc, camera, (0, -1, 0), (0, 0, 1), Vector((0, 0, 0)), 2.05, image)
                self.assertTrue(image.is_file(), "Native render escaped the Python review directory")
                self.assertTrue(Path(sc.render.filepath).is_absolute())
                self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual([p.name for p in output.glob("*.png")], ["neutral.png"])
            finally:
                os.chdir(initial_cwd)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeRenderPath)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Native Blender render-path regression failed")
