import copy
import importlib
import json
from pathlib import Path
import unittest

class AuditTests(unittest.TestCase):
    def module(self):
        self.assertTrue((Path(__file__).parent/'audit_original_v1_changes.py').exists(),'change audit missing')
        return importlib.import_module('audit_original_v1_changes')
    def snapshot(self):
        payload=json.loads((Path(__file__).resolve().parents[1]/'ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json').read_text())
        matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        rest=[dict(b,use_deform=(b['name']!='root'),matrix=matrix) for b in payload['bones']]
        deform=[b['name'] for b in rest if b['use_deform']]
        return {'schema_version':2,'scene_unit_scale_length':1.0,'rig_id':'hgpt_canonical_v4_original','coordinate_space':'raw mesh local Blender coordinates in metres',
                'mesh_matrix_world':matrix,
                'rig_matrix_world':matrix,
                'rig_rest_bones':rest,
                'bone_names':deform,'candidate_sha256':'a'*64,'vertices':[[-1,0,0],[1,0,0],[0,1,0]],
                'faces':[[0,1,2]],'regions':['hand','hand','torso'],
                'weights':[{'hand_l':1},{'hand_r':1},{'spine_02':1}],
                'mirror_pairs':[[0,1],[2,2]],'left_x_sign':-1}
    def policy(self):return {'before_candidate_sha256':'a'*64,'candidate_sha256':'a'*64,'allowed_regions':['hand'],'allowed_vertex_ids':[0,1],
                              'allowed_bones':['hand_l','hand_r'],'index_correspondence_confirmed':True}
    def test_stale_63_bone_snapshot_refused(self):
        c=self.module();a=self.snapshot()
        a['rig_rest_bones']=a['rig_rest_bones'][:63]
        a['bone_names']=[b['name'] for b in a['rig_rest_bones'] if b['use_deform']]
        with self.assertRaisesRegex(ValueError,'rev2c'):
            c.validate(a)

    def test_current_snapshot_uses_67_bone_locked_hierarchy(self):
        c=self.module();a=self.snapshot();c.validate(a)
        self.assertEqual(len(a['rig_rest_bones']),67)
        self.assertEqual(len(a['bone_names']),66)

    def test_distant_mesh_edit_is_exposed(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['candidate_sha256']='b'*64;b['vertices'][2][2]=.01
        policy=self.policy();policy['candidate_sha256']='b'*64
        r=c.audit(a,b,policy)
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
    def test_policy_candidate_identity_is_required(self):
        c=self.module();a=self.snapshot();p=self.policy();p['candidate_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'policy candidate'):c.audit(a,a,p)
    def test_transformed_mesh_cannot_report_local_displacements(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['mesh_matrix_world'][0][3]=1
        with self.assertRaisesRegex(ValueError,'coordinate frame'):c.audit(a,b,self.policy())
    def test_changed_rig_rest_is_detected(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['rig_rest_bones'][0]['tail'][2]=1.1
        with self.assertRaisesRegex(ValueError,'frozen rig rest'):c.audit(a,b,self.policy())
    def test_nonfinite_policy_cannot_hide_normalization_errors(self):
        c=self.module();a=self.snapshot();p=self.policy();p['normalization_tolerance']=float('nan')
        with self.assertRaisesRegex(ValueError,'non-finite'):c.audit(a,a,p)
    def test_region_relabelling_cannot_authorize_a_distant_edit(self):
        c=self.module();a=self.snapshot();b=copy.deepcopy(a);b['vertices'][2][2]=.01;b['regions'][2]='hand'
        p=self.policy();p['allowed_vertex_ids']=[0,1,2]
        r=c.audit(a,b,p)
        self.assertEqual(r['mesh']['unexpected_vertex_ids'],[2])
        self.assertEqual(r['mesh']['region_label_changes'],[2])
    def test_unknown_bone_weights_are_rejected(self):
        c=self.module();a=self.snapshot();a['weights'][0]={'unknown_l':1}
        with self.assertRaisesRegex(ValueError,'unknown bone'):c.audit(a,a,self.policy())
    def test_non_metre_scene_units_stop(self):
        c=self.module();a=self.snapshot();a['scene_unit_scale_length']=.01
        with self.assertRaisesRegex(ValueError,'unit scale'):c.audit(a,a,self.policy())
if __name__=='__main__':unittest.main()
