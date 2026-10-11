import importlib.util
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

class NativeThorax(unittest.TestCase):
    def test_missing_extra_ribs_refused_before_scene_mutation(self):
        import bpy
        spec = importlib.util.spec_from_file_location('thorax_context', ROOT / 'scripts/build_functional_thorax_context_blender.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        rec = json.loads((ROOT / m.shoulder.RECORD).read_text())
        m.shoulder.build(rec)
        for extra in (False, True):
            altered = json.loads(json.dumps(rec))
            if extra:
                altered['bones']['rib_13_left'] = altered['bones']['rib_12_left']
            else:
                del altered['bones']['rib_01_left']
            before = set(bpy.data.objects.keys())
            with self.assertRaises(ValueError):
                m.add_context(altered)
            self.assertEqual(set(bpy.data.objects.keys()), before)

    def test_context_preserves_record_and_control_centres(self):
        script = ROOT / 'scripts/build_functional_thorax_context_blender.py'
        self.assertTrue(script.exists(), 'thorax builder missing')
        spec = importlib.util.spec_from_file_location('thorax_context', script)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        rec = json.loads((ROOT / m.shoulder.RECORD).read_text())
        original = json.dumps(rec, sort_keys=True)
        arm, shapes = m.shoulder.build(rec)
        before = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        context = m.add_context(rec)
        self.assertEqual(len(context), 25)
        self.assertEqual(json.dumps(rec, sort_keys=True), original)
        for b in arm.data.bones:
            self.assertEqual(b.matrix_local, before[b.name])
        for ob in context:
            self.assertFalse(ob['anatomy_approved'])
            self.assertGreater(len(ob.data.vertices), 0)
        for angle in (0, 90, 160):
            m.shoulder.pose(arm, rec, angle)
            for side in ('left', 'right'):
                self.assertLess((arm.pose.bones['clavicle_' + side].tail - arm.pose.bones['scapula_' + side].head).length, 1e-6)

if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeThorax))
    if not result.wasSuccessful():
        raise RuntimeError('thorax context checks failed')
