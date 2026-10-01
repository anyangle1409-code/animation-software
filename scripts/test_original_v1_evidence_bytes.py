"""Evidence byte hashes must survive Git checkout on Windows configurations."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class EvidenceByteTests(unittest.TestCase):
    def test_git_autocrlf_preserves_evidence_and_frozen_rig_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE)
            git('init','-q');git('config','core.autocrlf','true')
            attrs=ROOT/'.gitattributes'
            if attrs.exists():(root/'.gitattributes').write_bytes(attrs.read_bytes())
            paths=('ORIGINAL_V1_PRODUCTION_CONTROL.json',
                   'ORIGINAL_V1_WORK/candidates/repair_checks/hand_r30/pose_test_report.json',
                   'ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r30.json',
                   'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json',
                   'src/rig/canonicalV4Original.ts',
                   'scripts/export_original_v1_candidate_glb_blender.py',
                   'scripts/pose_test_original_v1_o4_candidate_blender.py',
                   'scripts/snapshot_original_v1_model_blender.py',
                   'scripts/original_v1_export_evidence.py')
            for name in paths:
                with self.subTest(path=name):
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                    content=b'{\r\n  "test_only": true\r\n}\r\n'
                    path.write_bytes(content);git('add',name)
                    self.assertEqual(git('show',':'+name),content,'Git changed hashed evidence bytes')
                    path.unlink();git('checkout-index','--',name)
                    self.assertEqual(path.read_bytes(),content)

if __name__=='__main__':unittest.main()
