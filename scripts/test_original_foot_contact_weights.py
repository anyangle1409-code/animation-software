import unittest
import original_foot_contact_weights as contact

class FootContactWeightsTests(unittest.TestCase):
 def test_proximal_to_pivot_toe_weight_transfers_to_foot_without_touching_other_groups(self):
  r=contact.redistribute({'toe':.3,'foot':.5,'shin':.2},'toe','foot',.16,.18,.03)
  self.assertEqual(r,{'toe':0,'foot':.8,'shin':.2})
 def test_distal_to_blend_region_keeps_authored_weights(self):
  w={'toe':.7,'foot':.3}
  self.assertEqual(contact.redistribute(w,'toe','foot',.23,.18,.03),w)
 def test_smooth_transition_preserves_sum_and_input(self):
  w={'toe':.6,'foot':.4};r=contact.redistribute(w,'toe','foot',.195,.18,.03)
  self.assertAlmostEqual(r['toe'],.3)
  self.assertAlmostEqual(sum(r.values()),sum(w.values()))
  self.assertEqual(w,{'toe':.6,'foot':.4})
 def test_invalid_weights_or_coordinates_refused(self):
  for w,f,p,width in [({'toe':float('nan')},.2,.18,.03),({'toe':-.2},.2,.18,.03),({'toe':.4},float('inf'),.18,.03),({'toe':.4},.2,.18,0)]:
   with self.subTest(w=w),self.assertRaises(ValueError):contact.redistribute(w,'toe','foot',f,p,width)
 def test_no_toe_influence_is_unchanged(self):
  w={'foot':.4,'shin':.6}
  self.assertEqual(contact.redistribute(w,'toe','foot',.1,.18,.03),w)

if __name__=='__main__':unittest.main()
