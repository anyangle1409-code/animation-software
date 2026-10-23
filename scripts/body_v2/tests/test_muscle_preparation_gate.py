import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'prepare_recovered_muscles.py'


class MusclePreparationGate(unittest.TestCase):
    def test_archive_difference_blocks_experimental_copy(self):
        self.assertTrue(PATH.exists(), 'muscle preparation gate must exist')
        spec = importlib.util.spec_from_file_location('prep', PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'verify').mkdir()
            for name in mod.REQUIRED:
                (root / 'verify' / (name + '.json')).write_text(json.dumps({'summary': {'pass': 3, 'fail': 0}}))
            (root / 'verify/v14_report_vs_archive.json').write_text('{"identical": false}')
            self.assertFalse(mod.ready(root))
            (root / 'verify/v14_report_vs_archive.json').write_text('{"identical": true}')
            self.assertTrue(mod.ready(root))
            (root / 'verify/w8_vs_archive.json').unlink()
            self.assertFalse(mod.ready(root))
