import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/'package_candidates.py'

class ArtifactAccess(unittest.TestCase):
    def test_packages_exact_bytes_with_hashes_without_approving_candidate(self):
        self.assertTrue(MODULE.exists(), 'per-model artifact packager required')
        spec=importlib.util.spec_from_file_location('access',MODULE)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'source'; out=Path(td)/'access'; root.mkdir()
            for model,relative in mod.MODELS.items():
                file=root/relative; file.parent.mkdir(parents=True,exist_ok=True); file.write_bytes(b'BLENDER-fixture-'+model.encode())
            report=mod.package(root,out)
            self.assertEqual(report['anatomical_approval'],'NOT_GRANTED')
            for model,relative in mod.MODELS.items():
                self.assertEqual((root/relative).read_bytes(),(out/model/Path(relative).name).read_bytes())
                self.assertIn(report['models'][model]['sha256'],(out/model/'SHA256SUMS.txt').read_text())
            with self.assertRaises(FileExistsError): mod.package(root,out)
