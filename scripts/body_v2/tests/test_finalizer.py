import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'finalize_recovery.py'


class Finalizer(unittest.TestCase):
    def module(self):
        self.assertTrue(PATH.exists(), 'artifact finalizer must exist')
        spec = importlib.util.spec_from_file_location('finalize', PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_missing_evidence_cannot_be_reconstructed_or_quality_pass(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.module().collect(Path(td))
            self.assertFalse(result['reconstruction_pass'])
            self.assertFalse(result['movement_quality_pass'])
            self.assertTrue(result['missing'])

    def test_hash_manifest_roundtrip_and_header_inclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'W8').mkdir()
            (root / 'W8/model.blend').write_bytes(b'fixture')
            (root / 'MANIFEST_HEADER.json').write_text('{}')
            self.module().manifest(root)
            import hashlib
            for line in (root / 'MANIFEST.sha256').read_text().splitlines():
                digest, relative = line.split('  ', 1)
                self.assertEqual(hashlib.sha256((root / relative).read_bytes()).hexdigest(), digest)
            self.assertIn('MANIFEST_HEADER.json', (root / 'MANIFEST.sha256').read_text())


class FinalizerTestFailures(unittest.TestCase):
    def test_nonzero_exit_blocks_test_suite_pass(self):
        spec = importlib.util.spec_from_file_location('finalize', PATH)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'tests').mkdir()
            for name in ('vitest', 'typecheck', 'scripts', 'scripts_tests', 'scripts_blender_tests', 'muscles', 'guards'):
                (root / 'tests' / (name + '.exit')).write_text('0')
            (root / 'tests/muscles.exit').write_text('1')
            result = mod.collect(root)
            self.assertFalse(result['test_suites_pass'])
