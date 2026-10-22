import math
import unittest
from experiments.anatomical_muscles import kernel as k

I=((1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1))
def translated(x,y,z):
    return ((1,0,0,x),(0,1,0,y),(0,0,1,z),(0,0,0,1))

class KernelTests(unittest.TestCase):
    def test_anchored_path_uses_each_bone(self):
        anchors=[{'bone':'pelvis','local_m':[0,0,0]}, {'bone':'femur','local_m':[0,0,0]}, {'bone':'tibia','local_m':[0,0,0]}]
        p=k.resolve_path(anchors,{'pelvis':I,'femur':translated(0,1,0),'tibia':translated(1,1,0)})
        self.assertEqual(p,[(0,0,0),(0,1,0),(1,1,0)])
        self.assertEqual(k.path_length(p),2)
        with self.assertRaises(ValueError): k.resolve_path(anchors,{'pelvis':I})
    def test_segment_interior_clearance_not_only_endpoints(self):
        self.assertAlmostEqual(k.sphere_clearance([(-2,0,0),(2,0,0)],(0,0,0),1),-1)
        self.assertAlmostEqual(k.sphere_clearance([(-2,2,0),(2,2,0)],(0,0,0),1),1)
    def test_authored_via_points_clear_obstacle(self):
        p=[(-2,0,0),(-1,1.1,0),(1,1.1,0),(2,0,0)]
        self.assertGreater(k.sphere_clearance(p,(0,0,0),1),0)
        self.assertGreater(k.path_length(p),4)
    def test_volume_preserved_across_shortening_and_activation(self):
        for length in (.6,1,1.4):
            for activation in (0,.5,1):
                a,b=k.belly_axes(.01,length,activation,.2)
                self.assertAlmostEqual(math.pi*a*b*length,.01)
    def test_isometric_activation_changes_shape_not_volume(self):
        a,b=k.belly_axes(.01,1,0,.2)
        c,d=k.belly_axes(.01,1,1,.2)
        self.assertGreater(c,a)
        self.assertLess(d,b)
    def test_blend_does_not_double_bulge_and_respects_region(self):
        self.assertEqual(k.skin_delta([(1,(0,0,.01)),(1,(0,0,.01))],1,.02),(0,0,.01))
        self.assertEqual(k.skin_delta([(1,(0,0,.01))],0,.02),(0,0,0))
        self.assertAlmostEqual(k.skin_delta([(1,(0,0,.1))],.5,.02)[2],.02)
    def test_small_influences_fade_without_normalizing_to_full(self):
        self.assertAlmostEqual(k.skin_delta([(.1,(0,0,.01))],1,.02)[2],.001)
    def test_huge_finite_inputs_do_not_false_clear_or_zero_out(self):
        self.assertAlmostEqual(k.sphere_clearance([(-1e200,0,0),(1e200,0,0)],(0,0,0),1),-1)
        self.assertAlmostEqual(k.skin_delta([(1,(1e200,0,0))],1,.02)[0],.02)

    def test_invalid_geometry_rejected(self):
        for v in (float('nan'),float('inf'),-1,0):
            with self.assertRaises(ValueError): k.belly_axes(v,1,0,.2)
        with self.assertRaises(ValueError): k.belly_axes(.01,1,1.1,.2)
        with self.assertRaises(ValueError): k.path_length([(0,0,0),(0,0,0)])
        with self.assertRaises(ValueError): k.skin_delta([(-1,(1,0,0))],1,.01)
        with self.assertRaises(ValueError): k.sphere_clearance([(0,0,0),(1,0,0)],(0,0,0),-1)

if __name__=='__main__': unittest.main()
