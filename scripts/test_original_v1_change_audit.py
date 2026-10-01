import copy
import importlib
from pathlib import Path
import unittest

class AuditTests(unittest.TestCase):
    def module(self):
        self.assertTrue((Path(__file__).parent/'audit_original_v1_changes.py').exists(),'change audit missing')
        return importlib.import_module('audit_original_v1_changes')
    def snapshot(self):
        return {'schema_version':1,'candidate_sha256':'a'*64,'vertices':[[-1,0,0],[1,0,0],[0,1,0]],
                'faces':[[0,1,2]],'regions':['hand','hand','torso'],
                'weights':[{'hand_l':1},{'hand_r':1},{'spine_02':1}],
                'mirror_pairs':[[0,1],[2,2]],'left_x_sign':-1}
    def policy(self):return {'allowed_regions':['hand'],'allowed_vertex_ids':[0,1],
                              'allowed_bones':['hand_l','hand_r'],'index_correspondence_confirmed':True}
    def test_distant_mesh_edit_is_exposed(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['candidate_sha256']='b'*64;b['vertices'][2][2]=.01
        r=c.audit(a,b,self.policy())
        self.assertEqual(r['mesh']['unexpected_vertex_ids'],[2])
        self.assertAlmostEqual(r['mesh']['max_displacement_mm'],10)
        self.assertFalse(r['production_approved'])
    def test_weights_are_not_renormalized_to_hide_errors(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['weights'][0]={'hand_r':.6,'hand_l':.6}
        r=c.audit(a,b,self.policy())
        self.assertAlmostEqual(r['weights']['normalization_max_error'],.2)
        self.assertEqual(r['weights']['cross_side_vertex_ids'],[0])
    def test_changed_topology_cannot_claim_index_displacements(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['faces']=[[2,1,0]]
        r=c.audit(a,b,self.policy())
        self.assertTrue(r['mesh']['topology_changed'])
        self.assertIsNone(r['mesh']['max_displacement_mm'])
        self.assertEqual(r['weights']['comparison_status'],'CORRESPONDENCE_REQUIRED')
    def test_missing_correspondence_is_not_assumed(self):
        c=self.module();a=self.snapshot();p=self.policy();p['index_correspondence_confirmed']=False
        self.assertIsNone(c.audit(a,a,p)['mesh']['max_displacement_mm'])
    def test_nonfinite_coordinates_refused(self):
        c=self.module();a=self.snapshot();a['vertices'][0][0]=float('nan')
        with self.assertRaises(ValueError):c.audit(a,a,self.policy())
if __name__=='__main__':unittest.main()
