import unittest
import original_foot_candidate_gate as gate

class FootCandidateGateTests(unittest.TestCase):
 def test_28cm_trial_refused_when_unchanged_source_tips_extend_beyond_skin(self):
  r=gate.assess(.03973662,[.26043716,.2644],.280,True)
  self.assertFalse(r['mesh_only_candidate_allowed'])
  self.assertGreater(r['reference_protrusion_m'],.02)
 def test_numeric_fit_alone_does_not_clear_unresolved_landmark_semantics(self):
  r=gate.assess(.04,[.23],.280,False)
  self.assertFalse(r['mesh_only_candidate_allowed'])
  self.assertIn('UNRESOLVED_REFERENCE_STATION_SEMANTICS',r['blockers'])
 def test_compatible_resolved_trial_can_pass_without_skeleton_edit(self):
  r=gate.assess(.04,[.23],.280,True)
  self.assertTrue(r['mesh_only_candidate_allowed'])
  self.assertEqual(r['skeleton_changes_required'],False)
 def test_nonfinite_empty_negative_or_bool_inputs_are_refused(self):
  for args in [(.04,[],.28,True),(-.1,[.2],.28,True),(.04,[float('nan')],.28,True),(.04,[.2],True,True),(.04,[.2],.28,'yes')]:
   with self.subTest(args=args),self.assertRaises(ValueError):gate.assess(*args)
 def test_preserves_input_stations_and_trial_is_not_production_approval(self):
  points=[.22,.23];old=list(points)
  r=gate.assess(.04,points,.28,True)
  self.assertEqual(points,old)
  self.assertFalse(r['production_approved'])

if __name__=='__main__':unittest.main()
