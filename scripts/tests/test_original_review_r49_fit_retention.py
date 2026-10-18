"""Timeout reporting must preserve accepted work without claiming completion."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from retain_original_review_r49 import retain

class FitRetention(unittest.TestCase):
    def test_timeout_retains_preflight_and_reports_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/'preflight.npz').write_bytes(b'accepted preflight fixture')
            report=retain(directory,124)
            self.assertEqual((p/'solved.npz').read_bytes(),b'accepted preflight fixture')
            self.assertEqual(report['state_source'],'accepted_preflight_only')
            self.assertFalse(report['fit_completed']);self.assertFalse(report['model_saved'])
            self.assertEqual(report['fit_exit_code'],124)

    def test_missing_accepted_state_records_blocker_before_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            with self.assertRaises(RuntimeError):retain(directory,124)
            report=json.loads((p/'fit_status.json').read_text())
            self.assertFalse(report['has_accepted_state'])
            self.assertFalse((p/'solved.npz').exists())

if __name__=='__main__':unittest.main()
