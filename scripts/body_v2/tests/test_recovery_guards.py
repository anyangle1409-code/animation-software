"""Recovery regressions that do not require Blender; no anatomy acceptance inferred."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]


class RecoveryGuards(unittest.TestCase):
    def test_missing_body_and_rig_write_failure_report_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'bpy.py').write_text('''from types import SimpleNamespace as N
ops=N(wm=N(open_mainfile=lambda **kw: None))
data=N(version=(5,2,0), objects={})
app=N(version_string="5.2.0")
''')
            model = root / 'source.blend'
            model.write_bytes(b'fixture only')
            report = root / 'report.json'
            result = subprocess.run([sys.executable, str(HERE / 'verify_body_v2_blend.py'), '--', str(model), 'none', '-', str(report)], env={**os.environ, 'PYTHONPATH': td}, capture_output=True, text=True)
            self.assertEqual(json.loads(report.read_text())['summary']['fail'], 2)
            self.assertNotEqual(result.returncode, 0, 'failed native checks must fail the process')
            self.assertEqual(model.read_bytes(), b'fixture only')

    def test_manifest_header_accepts_multiline_blender_output(self):
        script = (HERE / 'rebuild_w8_v14_verified.sh').read_text()
        fragment = script[script.index('step "hashes + manifest"'):script.index('git -C "$REPO" worktree remove')]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in ['W8', 'V14', 'R120_base', 'R120', 'verify', 'logs']:
                (root / name).mkdir()
            (root / 'verify/blender_version.txt').write_text('bpy 5.2.0\nBlender quit\n')
            env = {**os.environ, 'OUTROOT': td, 'REPO': str(HERE.parents[1]), 'PY': sys.executable, 'R57_COMMIT': 'fixture-commit', 'R41_SHA': 'fixture-sha'}
            result = subprocess.run(['bash', '-eu', '-c', 'step() { :; };\n' + fragment], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            header = json.loads((root / 'MANIFEST_HEADER.json').read_text())
            self.assertIn('5.2.0', header['bpy'])
            self.assertIn('MANIFEST_HEADER.json', (root / 'MANIFEST.sha256').read_text())


    def test_v14_archive_difference_fails_recovery_status(self):
        script = (HERE / 'rebuild_w8_v14_verified.sh').read_text()
        start = script.index('"$PY" -I - "$REPO" "$OUTROOT"')
        fragment = script[start:script.index('\nEOF', start) + 4]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = root / 'review-assets/body_v2/draft_v14b_torso'
            archive.mkdir(parents=True)
            (root / 'V14').mkdir()
            (root / 'verify').mkdir()
            (archive / 'legs_v2_report.json').write_text('{"groups": 77}')
            (root / 'V14/legs_v2_report.json').write_text('{"groups": 76}')
            env = {**os.environ, 'REPO': td, 'OUTROOT': td, 'PY': sys.executable, 'VERIFY_FAILED': '0'}
            result = subprocess.run(['bash', '-eu', '-c', fragment + '\nexit "$VERIFY_FAILED"'], env=env, capture_output=True, text=True)
            self.assertFalse(json.loads((root / 'verify/v14_report_vs_archive.json').read_text())['identical'])
            self.assertNotEqual(result.returncode, 0, 'archive differences must fail aggregate recovery')


if __name__ == '__main__':
    unittest.main()
