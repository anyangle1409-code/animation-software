"""Native checks of authored geometry/rig only, NOT human movement acceptance."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))


class NativePilot(unittest.TestCase):
    def test_rig_and_shapes_follow_same_centres_and_roundtrip(self):
        script = ROOT / 'scripts/build_functional_shoulder_pilot_blender.py'
        self.assertTrue(script.exists(), 'native pilot builder is missing')
        spec = importlib.util.spec_from_file_location('pilot', script)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        import bpy
        rec = json.loads((ROOT / m.RECORD).read_text())
        arm, shapes = m.build(rec)
        self.assertEqual(len(arm.data.bones), 6)
        self.assertEqual(len([x for x in shapes if x.name.startswith('clavicle_shape')]), 2)
        self.assertEqual(len([x for x in shapes if x.name.startswith('scapula_blade')]), 2)
        for ob in shapes:
            self.assertEqual(ob.parent, arm, 'export must have unambiguous armature parent')
        for angle in (0, 45, 90, 135, 160, 90, 0):
            m.pose(arm, rec, angle)
            for side in ('left', 'right'):
                ac = arm.pose.bones['clavicle_' + side].tail
                scap_head = arm.pose.bones['scapula_' + side].head
                self.assertLess((ac - scap_head).length, 1e-6)
                rest = arm.data.bones['humerus_' + side].length
                self.assertAlmostEqual(arm.pose.bones['humerus_' + side].length, rest, places=6)
            deps = bpy.context.evaluated_depsgraph_get()
            for ob in shapes:
                name = ob['anatomical_control']
                palette = arm.pose.bones[name].matrix @ arm.data.bones[name].matrix_local.inverted()
                expected = palette @ ob.data.vertices[0].co
                actual = ob.evaluated_get(deps).data.vertices[0].co
                self.assertLess((actual - expected).length, 2e-6)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'pilot.blend'
            counts = {x.name: len(x.data.vertices) for x in shapes}
            bpy.ops.wm.save_as_mainfile(filepath=str(p))
            bpy.ops.wm.open_mainfile(filepath=str(p))
            self.assertEqual({name: len(bpy.data.objects[name].data.vertices) for name in counts}, counts)
            self.assertFalse(bpy.context.scene['anatomy_approved'])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(NativePilot))
    if not result.wasSuccessful():
        raise RuntimeError('native pilot checks failed')
