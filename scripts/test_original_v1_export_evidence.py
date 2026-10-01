import importlib
import json
from pathlib import Path
import struct
import tempfile
import unittest


class ExportEvidenceTests(unittest.TestCase):
    def module(self):return importlib.import_module('original_v1_export_evidence')
    def fixture(self,root):
        c=self.module();candidate=root/'candidate_r29.blend';candidate.write_bytes(b'unit-test candidate only')
        manifest=root/'candidate_r29.json';manifest.write_text(json.dumps({'candidate':candidate.name,'candidate_sha256':c.digest(candidate)}))
        return candidate,manifest
    def write_glb(self,path,sha,revision,dressed):
        names=['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']+(['HGPT_ORIGINAL_V1_SHORTS_CANDIDATE'] if dressed else [])
        doc={'asset':{'version':'2.0'},'nodes':[{'name':name,'mesh':i,'extras':{
            'hgpt_export_source_candidate_sha256':sha,'hgpt_export_candidate_revision':revision,
            'hgpt_export_production_approved':False}} for i,name in enumerate(names)]}
        data=json.dumps(doc).encode();data+=b' '*((-len(data))%4)
        path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(data))+struct.pack('<II',len(data),0x4e4f534a)+data)
    def capture_fixture(self,root):
        c=self.module();candidate,manifest=self.fixture(root);out=root/'exports_r29';plan=c.plan(root,candidate,manifest,out,'r29')
        out.mkdir()
        script=root/'scripts/export_original_v1_candidate_glb_blender.py';script.parent.mkdir();script.write_text('unit-test script only')
        for variant,name in plan['files'].items():self.write_glb(out/name,plan['candidate_sha256'],'r29',variant=='dressed')
        record=c.record(root,plan,'test fixture only','b'*40,c.digest(script),c.SETTINGS)
        (out/'CANDIDATE_GLB_EXPORT.json').write_text(json.dumps(record));return out,record
    def test_plan_binds_source_and_uses_revision_names(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);candidate,manifest=self.fixture(root);p=c.plan(root,candidate,manifest,root/'fresh','r29')
            self.assertEqual(set(p['files']),{'bare','dressed'});self.assertTrue(all('r29' in x for x in p['files'].values()))
            self.assertFalse((root/'fresh').exists());self.assertEqual(p['candidate_sha256'],c.digest(candidate))
    def test_no_existing_destination_or_external_source(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);candidate,manifest=self.fixture(root)
            with self.assertRaises(ValueError):c.plan(root,candidate,manifest,root,'r29')
            with self.assertRaises(ValueError):c.plan(root,candidate,manifest,root.parent/'outside','r29')
    def test_source_name_hash_and_revision_must_match(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);candidate,manifest=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'revision'):c.plan(root,candidate,manifest,root/'new','r30')
            candidate.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash'):c.plan(root,candidate,manifest,root/'new','r29')
    def test_record_cannot_claim_approval_or_visual_evidence(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            out,r=self.capture_fixture(Path(td));self.assertFalse(r['production_approved']);self.assertFalse(r['visual_review_available'])
            self.assertEqual(r['export_settings'],c.SETTINGS);self.assertEqual(r['pose_position'],'REST')
            self.assertEqual(set(r['exports']),{'bare','dressed'})
    def test_source_changes_during_capture_are_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out,r=self.capture_fixture(root);(root/'candidate_r29.blend').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'source'):c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')
    def test_glb_metadata_and_bytes_are_bound(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out,r=self.capture_fixture(root);proof=c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')
            self.assertEqual(proof['local_blend_verification'],'VERIFIED');self.assertFalse(proof['production_approved'])
            (out/r['exports']['bare']['file']).write_bytes(b'changed')
            with self.assertRaises(ValueError):c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')
    def test_cloud_verification_does_not_invent_local_blend_check(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out,r=self.capture_fixture(root);(root/'candidate_r29.blend').unlink()
            self.assertEqual(c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')['local_blend_verification'],'UNAVAILABLE')
    def test_old_capture_settings_or_unbound_glb_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out,r=self.capture_fixture(root);r['export_settings']['export_animations']=True
            (out/'CANDIDATE_GLB_EXPORT.json').write_text(json.dumps(r))
            with self.assertRaisesRegex(ValueError,'settings'):c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')
    def test_glb_path_traversal_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out,r=self.capture_fixture(root);r['exports']['bare']['file']='../other.glb'
            (out/'CANDIDATE_GLB_EXPORT.json').write_text(json.dumps(r))
            with self.assertRaises(ValueError):c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')
    def test_blender_driver_selects_only_owned_meshes_and_restores_state(self):
        self.driver_case()
    def test_blender_driver_preserves_partial_files_and_restores_on_failure(self):
        self.driver_case(fail=True)
    def test_blender_driver_refuses_missing_clothing(self):
        self.driver_case(missing_shorts=True)
    def test_capture_receipt_cannot_alias_future_export_files(self):
        import contextlib,io
        from unittest.mock import patch
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'fresh'
            for name in ('CANDIDATE_GLB_EXPORT.json',*c.filenames('r29').values()):
                with patch.object(c,'ROOT',root),patch('sys.argv',['export','r29','--out-dir',str(out),'--capture','--json-out',str(out/name)]),contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(c.main(),2);self.assertIn('aliases',output.getvalue());self.assertFalse(out.exists())
    def driver_case(self,fail=False,missing_shorts=False):
        import contextlib,io,runpy,types
        from unittest.mock import patch
        c=self.module()
        class Object(dict):
            def __init__(self,name,kind,rig=None):
                super().__init__();self.name=name;self.type=kind;self.rig=rig
                self.selected=True;self.hidden=True;self.hide_viewport=True;self.hide_render=True
                self.modifiers={};self.data=types.SimpleNamespace(bones=list(range(63)),pose_position='POSE')
            def find_armature(self):return self.rig
            def select_get(self):return self.selected
            def select_set(self,value):self.selected=value
            def hide_get(self):return self.hidden
            def hide_set(self,value):self.hidden=value
        class Objects(dict):
            def __iter__(self):return iter(self.values())
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source,manifest=self.fixture(root);folder=root/'scripts';folder.mkdir()
            script=folder/'export_original_v1_candidate_glb_blender.py'
            script.write_bytes((Path(__file__).parent/script.name).read_bytes())
            rig=Object('HGPT_CANONICAL_V4_ORIGINAL','ARMATURE');body=Object(c.BODY,'MESH',rig);shorts=Object(c.SHORTS,'MESH',rig)
            unrelated=Object('UNSELECTED_TEST_FIXTURE','MESH',rig)
            mask=types.SimpleNamespace(show_viewport=False,show_render=True);body.modifiers['HGPT_DRESSED_MASK']=mask
            objects=Objects({o.name:o for o in (rig,body,shorts,unrelated)})
            if missing_shorts:del objects[shorts.name]
            calls=[]
            def export(**kwargs):
                meshes=[o for o in objects if o.selected and o.type=='MESH'];calls.append({o.name for o in meshes})
                self.assertEqual(rig.data.pose_position,'REST');self.assertFalse(unrelated.selected)
                self.assertEqual({k:v for k,v in kwargs.items() if k!='filepath'},c.SETTINGS)
                if fail:return {'CANCELLED'}
                doc={'asset':{'version':'2.0'},'nodes':[{'name':o.name,'mesh':i,'extras':dict(o)} for i,o in enumerate(meshes)]}
                data=json.dumps(doc).encode();data+=b' '*((-len(data))%4)
                Path(kwargs['filepath']).write_bytes(struct.pack('<III',0x46546c67,2,20+len(data))+struct.pack('<II',len(data),0x4e4f534a)+data)
                return {'FINISHED'}
            fake=types.SimpleNamespace(data=types.SimpleNamespace(filepath=str(source),objects=objects),
                context=types.SimpleNamespace(scene={'hgpt_not_production':True},view_layer=types.SimpleNamespace(update=lambda:None)),
                app=types.SimpleNamespace(version_string='test fixture only'),ops=types.SimpleNamespace(export_scene=types.SimpleNamespace(gltf=export)))
            state={'current_candidate':'r29','candidate_state':'experimental','last_known_candidate_sha256':c.digest(source)}
            out=root/'fresh';argv=['blender','--','--out-dir',str(out),'--candidate-manifest',str(manifest),'--revision','r29']
            with patch.dict('sys.modules',{'bpy':fake,'addon_utils':types.SimpleNamespace(enable=lambda *a,**k:None)}),patch('sys.argv',argv),patch('sys.path',list(__import__('sys').path)),patch('original_v1_production_control.build',return_value=(state,{})),patch('subprocess.check_output',return_value='b'*40),contextlib.redirect_stdout(io.StringIO()):
                if fail or missing_shorts:
                    with self.assertRaises(ValueError):runpy.run_path(str(script),run_name='__main__')
                else:runpy.run_path(str(script),run_name='__main__')
            self.assertEqual(rig.data.pose_position,'POSE');self.assertEqual((mask.show_viewport,mask.show_render),(False,True))
            for o in objects:
                self.assertTrue(o.selected);self.assertTrue(o.hidden);self.assertTrue(o.hide_viewport);self.assertTrue(o.hide_render)
                self.assertNotIn('hgpt_export_source_candidate_sha256',o)
            self.assertEqual(source.read_bytes(),b'unit-test candidate only')
            if not fail and not missing_shorts:
                self.assertEqual(calls,[{c.BODY},{c.BODY,c.SHORTS}]);self.assertEqual(c.verify(root,out/'CANDIDATE_GLB_EXPORT.json')['local_blend_verification'],'VERIFIED')
            else:self.assertFalse((out/'CANDIDATE_GLB_EXPORT.json').exists())

if __name__=='__main__':unittest.main()
