import importlib
from pathlib import Path
import tempfile
import unittest

class PromotionTests(unittest.TestCase):
    def module(self):
        self.assertTrue((Path(__file__).parent/'verify_original_v1_production_promotion.py').exists(),'promotion gate missing')
        return importlib.import_module('verify_original_v1_production_promotion')
    def test_empty_packet_cannot_promote(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            issues=c.verify_packet(Path(td),{})
        self.assertTrue(issues);self.assertTrue(any('owner' in x for x in issues))
    def test_boolean_gate_claim_is_not_evidence(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            issues=c.verify_packet(Path(td),{'candidate_sha256':'a'*64,'gates':{g:True for g in c.REQUIRED_GATES}})
        self.assertTrue(any('report reference' in x for x in issues))
    def test_external_or_traversal_evidence_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'outside'):c.safe_path(Path(td),'../foreign.json')
            with self.assertRaisesRegex(ValueError,'outside'):c.safe_path(Path(td),'/tmp/external.json')
    def test_pending_owner_review_cannot_pass(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            issues=c.verify_packet(Path(td),{'candidate_sha256':'a'*64,'owner_acceptance':{'decision':'pending'}})
        self.assertTrue(any('owner' in x for x in issues))
if __name__=='__main__':unittest.main()
