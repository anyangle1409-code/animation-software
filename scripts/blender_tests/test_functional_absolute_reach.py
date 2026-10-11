import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class AbsoluteReach(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'scripts/build_functional_absolute_reach_blender.py'
        self.assertTrue(script.exists(), 'absolute reach builder missing')
        spec = importlib.util.spec_from_file_location('absolute_reach', script)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.rec = json.loads((ROOT / self.m.context.shoulder.RECORD).read_text())
        self.arm, _ = self.m.context.shoulder.build(self.rec)

    def test_absolute_elevation_and_scapular_plane_in_native_pose(self):
        # A rest-relative rotation or swapping anterior/posterior must fail.
        for angle in (0, 45, 90, 120, 160, 90, 0):
            self.m.pose_absolute(self.arm, self.rec, angle)
            for side, sign in [('left', 1), ('right', -1)]:
                bone = self.arm.pose.bones['humerus_' + side]
                direction = (bone.tail - bone.head).normalized()
                expected = (sign * math.sin(math.radians(angle)) * math.cos(math.radians(40)),
                            -math.sin(math.radians(angle)) * math.sin(math.radians(40)),
                            -math.cos(math.radians(angle)))
                for actual, wanted in zip(direction, expected):
                    self.assertAlmostEqual(actual, wanted, places=5)
                measured = math.degrees(math.acos(max(-1, min(1, -direction.z))))
                self.assertAlmostEqual(measured, angle, places=4)

    def test_source_rest_and_joint_continuity_preserved(self):
        from mathutils import Vector
        before = json.dumps(self.rec, sort_keys=True)
        rest = {b.name: b.matrix_local.copy() for b in self.arm.data.bones}
        for angle in (0, 90, 160):
            self.m.pose_absolute(self.arm, self.rec, angle)
            for side in ('left', 'right'):
                clav = self.arm.pose.bones['clavicle_' + side]
                scap = self.arm.pose.bones['scapula_' + side]
                hum = self.arm.pose.bones['humerus_' + side]
                self.assertLess((clav.tail - scap.head).length, 1e-6)
                # The scapular display tail is the inferior angle, NOT GH.
                source_gh = Vector(self.rec['bones']['humerus_' + side]['head_m'])
                expected_gh = scap.matrix @ self.arm.data.bones[scap.name].matrix_local.inverted() @ source_gh
                self.assertLess((expected_gh - hum.head).length, 1e-6)
                self.assertAlmostEqual(hum.length, self.arm.data.bones[hum.name].length, places=6)
        self.assertEqual(before, json.dumps(self.rec, sort_keys=True))
        for b in self.arm.data.bones:
            self.assertEqual(b.matrix_local, rest[b.name])

    def test_invalid_angle_refused_before_pose_mutation(self):
        self.m.pose_absolute(self.arm, self.rec, 90)
        before = {b.name: b.matrix.copy() for b in self.arm.pose.bones}
        for invalid in (True, '90', -1, 161, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                self.m.pose_absolute(self.arm, self.rec, invalid)
            for b in self.arm.pose.bones:
                self.assertEqual(b.matrix, before[b.name])


if __name__ == '__main__':
    result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(AbsoluteReach))
    if not result.wasSuccessful():
        raise RuntimeError('absolute reach checks failed')
