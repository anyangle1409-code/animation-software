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
if __name__=='__main__':unittest.main()
