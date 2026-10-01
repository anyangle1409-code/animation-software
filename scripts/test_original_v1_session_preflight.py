import importlib
from pathlib import Path
import tempfile
import unittest

class PreflightTests(unittest.TestCase):
    def module(self):
        self.assertTrue((Path(__file__).parent/'original_v1_session_preflight.py').exists(),'session preflight missing')
        return importlib.import_module('original_v1_session_preflight')
    def test_stale_head_and_dirty_tree_stop(self):
        c=self.module()
        issues=c.repository_issues('correct','correct','a','b',' M file')
        self.assertTrue(any('live' in x for x in issues))
        self.assertTrue(any('working tree' in x for x in issues))
    def test_wrong_branch_and_unavailable_remote_stop(self):
        c=self.module()
        self.assertTrue(c.repository_issues('main','correct','a',None,''))
    def test_matching_clean_repository_passes(self):
        c=self.module(); self.assertEqual(c.repository_issues('correct','correct','a','a',''),[])
    def test_collision_refuses_even_empty_output_folder(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/'ORIGINAL_V1_WORK/candidates/repair_checks/hand_r30';p.mkdir(parents=True)
            self.assertTrue(any('collision' in x for x in c.collision_issues(root,'r30','o22.npz')))
    def test_evidence_mode_does_not_require_optimizer_inputs(self):
        from unittest.mock import patch
        import contextlib,io,json
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);candidate=root/c.CAND/'candidate.blend';candidate.parent.mkdir(parents=True);candidate.write_bytes(b'test fixture only')
            state={'current_candidate':'r29','next_action':{'action':'RUN r30'}}
            def read(root,path):return {'branch':'expected'} if str(path)=='ORIGINAL_V1_PRODUCTION_CONTROL.json' else {'candidate':candidate.name,'candidate_sha256':c.digest(candidate)}
            def run(args,*a,**k):return 'expected' if args[:3]==['git','branch','--show-current'] else '' if args[:2]==['git','status'] else 'a'*40
            with patch.object(c,'ROOT',root),patch.object(c,'build',return_value=(state,{})),patch.object(c,'read',side_effect=read),patch.object(c,'run',side_effect=run),patch.object(c,'blender_path',return_value=Path('test.exe')),patch.object(c,'power_info',return_value={'available':False}),patch.object(c,'process_info',return_value={'available':False}),patch.object(c.importlib.util,'find_spec',side_effect=AssertionError('optimizer dependency probe')),patch('sys.argv',['preflight','--evidence-only','--json']),contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(c.main(),0)
                data=json.loads(output.getvalue());self.assertFalse(data['information']['power']['available'])
if __name__=='__main__':unittest.main()
