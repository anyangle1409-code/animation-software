import importlib.util
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class NativeBowl(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'scripts/build_functional_scapula_bowl_blender.py'
        self.assertTrue(path.exists(), 'native curved blade builder missing')
        spec = importlib.util.spec_from_file_location('bowl', path)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.rec = json.loads((ROOT / self.m.reach.context.shoulder.RECORD).read_text())

    def test_only_blade_geometry_changes_and_record_rest_are_preserved(self):
        shoulder = self.m.reach.context.shoulder
        baseline, shapes = shoulder.build(self.rec)
        rest = {b.name: b.matrix_local.copy() for b in baseline.data.bones}
        vertices = {ob.name.split('.')[0]: [tuple(v.co) for v in ob.data.vertices] for ob in shapes}
        source = json.dumps(self.rec, sort_keys=True)
        arm, shapes = self.m.build(self.rec)
        self.assertEqual(json.dumps(self.rec, sort_keys=True), source)
        for b in arm.data.bones:
            self.assertEqual(b.matrix_local, rest[b.name])
        for ob in shapes:
            key = ob.name.split('.')[0]
            actual = [tuple(v.co) for v in ob.data.vertices]
            if ob.name.startswith('scapula_blade_'):
                self.assertGreater(len(actual), len(vertices[key]))
                self.assertEqual(len(actual), 106)
                self.assertFalse(ob['anatomy_approved'])
            else:
                self.assertEqual(actual, vertices[key])

    def test_blade_vertices_follow_scapula_rigid_palette_in_three_poses(self):
        import bpy
        arm, shapes = self.m.build(self.rec)
        for angle in (0,90,160):
            self.m.reach.pose_absolute(arm,self.rec,angle)
            deps = bpy.context.evaluated_depsgraph_get()
            for ob in shapes:
                if not ob.name.startswith('scapula_blade_'):
                    continue
                name = ob['anatomical_control']
                delta = arm.pose.bones[name].matrix @ arm.data.bones[name].matrix_local.inverted()
                posed = ob.evaluated_get(deps)
                for a,b in zip(ob.data.vertices,posed.data.vertices):
                    self.assertLess((delta @ a.co - posed.matrix_world @ b.co).length, 1e-6)


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeBowl))
    if not result.wasSuccessful():
        raise RuntimeError('native curved blade tests failed')
