"""Garment receipts expose identity, raw weights and visibility without approval."""
import copy
import importlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

class GarmentEvidenceTests(unittest.TestCase):
    def module(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('original_v1_garment_evidence'),'garment evidence implementation missing')
        return importlib.import_module('original_v1_garment_evidence')
    def pair(self):
        from test_original_v1_change_audit import AuditTests
        import original_v1_locked_rig as locked
        contract=locked.load_locked_rig()
        b=AuditTests().snapshot();g=copy.deepcopy(b)
        matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        rest=[]
        deform=[]
        for i,row in enumerate(contract["bones"]):
            use_deform=i!=0
            rest.append({"name":row["name"],"parent":row["parent"],"head":[0,0,0],"tail":[0,0,1],
                         "matrix":matrix,"use_deform":use_deform})
            if use_deform:deform.append(row["name"])
        for snapshot in (b,g):
            snapshot["rig_id"]=contract["identity"]
            snapshot["rig_rest_bones"]=copy.deepcopy(rest)
            snapshot["bone_names"]=sorted(deform)
            snapshot["locked_rig"]={"revision":contract["revision"],"rig_structure_sha256":contract["rig_structure_sha256"],
                                     "bone_count":contract["bone_count"],"deform_bone_count":contract["deform_bone_count"],
                                     "lock":contract["lock"],"payload":contract["payload"]}
        for s,name,scope in ((b,'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE','body'),(g,'HGPT_ORIGINAL_V1_SHORTS_CANDIDATE','garment')):
            s.update(mesh_object=name,snapshot_scope=scope,source_candidate='candidate_r29.blend',snapshot_script_sha256='c'*64,snapshot_helper_sha256='d'*64,modifiers=[],non_deform_group_weights={},blender_version='5.0')
        g['regions']=['garment']*len(g['vertices']);return b,g
    def test_same_candidate_pair_reports_raw_weight_errors_without_approval(self):
        c=self.module();b,g=self.pair();g['weights'][0]={'hand_l':.6,'hand_r':.6}
        r=c.inspect_pair(b,g)
        self.assertEqual(r['status'],'EVIDENCE_ONLY');self.assertFalse(r['production_approved'])
        self.assertAlmostEqual(r['garment_weights']['normalization_max_error'],.2)
        self.assertEqual(r['garment_weights']['cross_side_vertex_ids'],[0])
        self.assertIn('posed_clearance_and_intersections',r['unresolved_checks'])
    def test_different_candidate_pair_refused(self):
        c=self.module();b,g=self.pair();g['candidate_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'candidate'):c.inspect_pair(b,g)
    def test_changed_rig_rest_between_captures_refused(self):
        c=self.module();b,g=self.pair();g['rig_rest_bones'][0]['tail'][2]+=1
        with self.assertRaisesRegex(ValueError,'rig'):c.inspect_pair(b,g)
    def test_body_disguised_as_garment_refused(self):
        c=self.module();b,g=self.pair();g['mesh_object']=b['mesh_object']
        with self.assertRaisesRegex(ValueError,'mesh identity'):c.inspect_pair(b,g)
    def test_incomplete_modifier_receipt_refused(self):
        c=self.module();b,g=self.pair();b.pop('modifiers')
        with self.assertRaisesRegex(ValueError,'modifier'):c.inspect_pair(b,g)
    def test_mask_receipt_keeps_hidden_skin_weights(self):
        c=self.module();b,g=self.pair();b['modifiers']=[{'name':'HGPT_DRESSED_MASK','type':'MASK','show_viewport':True,'show_render':True,'vertex_group':'covered','invert_vertex_group':False}]
        b['non_deform_group_weights']={'covered':[1,0,.5]}
        r=c.inspect_pair(b,g)
        self.assertEqual(r['body_coverage']['non_deform_group_weights']['covered'],[1,0,.5])
        self.assertEqual(r['body_coverage']['mask_modifiers'][0]['vertex_group'],'covered')
    def test_nonfinite_weights_refused(self):
        c=self.module();b,g=self.pair();g['weights'][0]['hand_l']=float('nan')
        with self.assertRaises(ValueError):c.inspect_pair(b,g)
    def test_helper_version_mismatch_refused(self):
        c=self.module();b,g=self.pair();g['snapshot_helper_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'capture source'):c.inspect_pair(b,g)
    def test_distinct_mesh_world_frames_preserved_without_fake_clearance(self):
        c=self.module();b,g=self.pair();g['mesh_matrix_world'][0][3]=2
        r=c.inspect_pair(b,g)
        self.assertEqual(r['garment_matrix_world'][0][3],2)
        self.assertIsNone(r['garment_weights']['cross_side_vertex_ids'])
        self.assertEqual(r['garment_weights']['cross_side_status'],'UNRESOLVED_COORDINATE_FRAME')
        self.assertNotIn('minimum_clearance_mm',r)
    def test_approval_label_in_raw_snapshot_refused(self):
        c=self.module();b,g=self.pair();g['production_approved']=True
        with self.assertRaisesRegex(ValueError,'approval'):c.inspect_pair(b,g)
    def test_cli_binds_source_files_and_refuses_repeat_output(self):
        from unittest.mock import patch
        import contextlib,io,sys
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);b,g=self.pair()
            for name in (c.SCRIPT,c.HELPER,'scripts/audit_original_v1_changes.py'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('test fixture')
            manifest=root/'candidate_r29.json';manifest.write_text(json.dumps({'candidate':b['source_candidate'],'candidate_sha256':b['candidate_sha256']}))
            for snapshot in (b,g):
                snapshot['snapshot_script_sha256']=c.digest(root/c.SCRIPT);snapshot['snapshot_helper_sha256']=c.digest(root/c.HELPER)
                snapshot['source_candidate_manifest']={'file':manifest.name,'sha256':c.digest(manifest)}
            for name,snapshot in (('body.json',b),('garment.json',g)):(root/name).write_text(json.dumps(snapshot))
            argv=['tool',str(root/'body.json'),str(root/'garment.json'),'--candidate-manifest',str(manifest),'--json-out',str(root/'out.json')]
            with patch.object(c,'ROOT',root),patch.object(sys,'argv',argv),patch.object(c.subprocess,'check_output',return_value='a'*40),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(c.main(),0)
                receipt=json.loads((root/'out.json').read_text());self.assertFalse(receipt['production_approved'])
                self.assertEqual(receipt['local_blend_verification'],'UNAVAILABLE')
                saved=(root/'out.json').read_bytes();self.assertEqual(c.main(),2);self.assertEqual((root/'out.json').read_bytes(),saved)
                (root/'out.json').unlink();manifest.write_text('{}');self.assertEqual(c.main(),2);self.assertFalse((root/'out.json').exists())
    def fake(self,root):
        source=root/'candidate_r29.blend';source.write_bytes(b'test only')
        import hashlib
        source.with_suffix('.json').write_text(json.dumps({'candidate':source.name,'candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}))
        matrix=[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
        class Bones(list):
            def __getitem__(self,key):return next(b for b in self if b.name==key) if isinstance(key,str) else super().__getitem__(key)
        import original_v1_locked_rig as locked
        contract=locked.load_locked_rig()
        by_name={}
        for i,row in enumerate(contract["bones"]):
            by_name[row["name"]]=NS(name=row["name"],parent=None,head_local=Vec([-1,0,0]),
                                    tail_local=[0,0,1],matrix_local=matrix,use_deform=(i!=0))
        for row in contract["bones"]:
            if row["parent"] is not None:by_name[row["name"]].parent=by_name[row["parent"]]
        bones=Bones([by_name[row["name"]] for row in contract["bones"]])
        rig=NS(name=contract["object_name"],type='ARMATURE',data=NS(bones=bones),matrix_world=matrix)
        def mesh(name):
            return NS(name=name,type='MESH',find_armature=lambda:rig,matrix_world=matrix,modifiers=[],vertex_groups=[NS(index=0,name='upperarm_l'),NS(index=1,name='covered')],data=NS(vertices=[NS(co=[-.1,0,0],groups=[NS(group=0,weight=.8),NS(group=1,weight=.5)]),NS(co=[.1,0,0],groups=[NS(group=0,weight=1)])],polygons=[NS(vertices=[0,1,0])],attributes={'hgpt_region':NS(data=[NS(value=0),NS(value=0)])}))
        body=mesh('HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE');shorts=mesh('HGPT_ORIGINAL_V1_SHORTS_CANDIDATE')
        scene=Scene(hgpt_not_production=True,hgpt_region_names='["torso"]');scene.unit_settings=NS(scale_length=1)
        bpy=NS(data=NS(filepath=str(source),objects={'HGPT_CANONICAL_V4_ORIGINAL':rig,body.name:body,shorts.name:shorts}),context=NS(scene=scene),app=NS(version_string='5.0'))
        return bpy,body,shorts
    def test_stale_63_bone_snapshot_is_refused_by_current_lock(self):
        c=self.module();b,g=self.pair()
        import original_v1_locked_rig as locked
        contract=locked.load_locked_rig()
        b["rig_rest_bones"]=b["rig_rest_bones"][:63]
        b["bone_names"]=[r["name"] for r in b["rig_rest_bones"] if r["use_deform"]]
        issues=c.snapshot_locked_rig_issues(b,contract)
        self.assertTrue(any("hierarchy differs" in x or "deform count differs" in x for x in issues))

    def test_current_rev2c_snapshot_matches_shared_lock(self):
        c=self.module();b,g=self.pair()
        import original_v1_locked_rig as locked
        self.assertEqual(c.snapshot_locked_rig_issues(b,locked.load_locked_rig()),[])

    def test_capture_selects_named_garment_and_keeps_raw_non_deform_groups(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            bpy,b,g=self.fake(Path(temp));s=c.capture(bpy,'garment')
            self.assertEqual(s['mesh_object'],g.name);self.assertEqual(s['regions'],['garment','garment'])
            self.assertEqual(s['weights'][0],{'upperarm_l':.8})
            self.assertEqual(s['non_deform_group_weights'],{'covered':[.5,0]})
    def test_capture_body_regions_preserved(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            bpy,b,g=self.fake(Path(temp));s=c.capture(bpy,'body')
            self.assertEqual(s['regions'],['torso','torso']);self.assertEqual(s['mesh_object'],b.name)
    def test_missing_garment_stops_not_body_fallback(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            bpy,b,g=self.fake(Path(temp));del bpy.data.objects[g.name]
            with self.assertRaisesRegex(ValueError,'owned mesh'):c.capture(bpy,'garment')
    def test_blender_wrapper_writes_garment_and_preserves_existing_output(self):
        from unittest.mock import patch
        import runpy,sys,contextlib,io
        self.module()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);bpy,b,g=self.fake(root);out=root/'garment.json';source=Path(bpy.data.filepath);before=source.read_bytes()
            argv=['blender','--',str(out),'--garment']
            script=Path(__file__).parent/'snapshot_original_v1_model_blender.py'
            with patch.dict(sys.modules,{'bpy':bpy}),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(script),run_name='__main__')
                self.assertEqual(json.loads(out.read_text())['snapshot_scope'],'garment')
                saved=out.read_bytes()
                with self.assertRaisesRegex(SystemExit,'already exists'):runpy.run_path(str(script),run_name='__main__')
                self.assertEqual(out.read_bytes(),saved);self.assertEqual(source.read_bytes(),before)
    def test_changed_source_manifest_stops_capture(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            bpy,b,g=self.fake(Path(temp));Path(bpy.data.filepath).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'manifest'):c.capture(bpy,'garment')

class Vec(list):
    @property
    def x(self):return self[0]
class Scene(dict):pass
if __name__=='__main__':unittest.main()
