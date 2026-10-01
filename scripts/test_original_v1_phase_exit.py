"""Phase completion needs substantive exit evidence, not a bare PASS marker."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PhaseExitTests(unittest.TestCase):
    def module(self):return importlib.import_module('verify_original_v1_phase_exit')
    def fixture(self,phase=4):
        c=self.module();temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        source=root/'raw.json';source.write_text(json.dumps({'candidate_sha256':'a'*64,'note':'explicit test fixture only'}))
        ref={'path':'raw.json','sha256':c.digest(source)}
        packet={'schema_version':1,'phase':phase,'candidate_sha256':'a'*64,'status':'PASS',
                'production_approved':False,'source_git_commit':'b'*40,'evidence_timestamp':'2026-10-01T09:00:00Z',
                'checks':[{'id':name,'passed':True,'evidence':[ref]} for name in c.REQUIRED_CHECKS[str(phase)]],
                'owner_review':'pending','blocking':False,'command':'test fixture only'}
        return c,root,packet
    def test_bare_pass_marker_is_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as temp:
            issues=c.verify_exit(Path(temp),4,{'status':'PASS','candidate_sha256':'a'*64},'a'*64)
        self.assertTrue(issues);self.assertTrue(any('check' in x for x in issues))
    def test_complete_candidate_bound_contract_allows_pending_review(self):
        c,root,packet=self.fixture();self.assertEqual(c.verify_exit(root,4,packet,'a'*64),[])
        self.assertFalse(packet['production_approved'])
    def test_missing_check_stops(self):
        c,root,packet=self.fixture();packet['checks'].pop()
        self.assertTrue(any('missing' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_failing_check_stops(self):
        c,root,packet=self.fixture();packet['checks'][0]['passed']=False
        self.assertTrue(any('failing' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_changed_underlying_evidence_stops(self):
        c,root,packet=self.fixture();(root/'raw.json').write_text('tampered')
        self.assertTrue(any('hash' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_wrong_candidate_or_phase_stops(self):
        c,root,packet=self.fixture();packet['phase']=5;packet['candidate_sha256']='c'*64
        self.assertTrue(c.verify_exit(root,4,packet,'a'*64))
    def test_each_check_needs_source_evidence(self):
        c,root,packet=self.fixture();packet['checks'][0]['evidence']=[]
        self.assertTrue(any('source evidence' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_duplicate_check_cannot_fill_contract(self):
        c,root,packet=self.fixture();packet['checks'].append(packet['checks'][0])
        self.assertTrue(any('duplicate' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_phase_twelve_cannot_use_intermediate_exit_contract(self):
        c,root,packet=self.fixture();packet['phase']=12
        self.assertTrue(any('Phase 12' in x for x in c.verify_exit(root,12,packet,'a'*64)))
    def test_review_cannot_become_an_approval_gate(self):
        c,root,packet=self.fixture();packet['blocking']=True
        self.assertTrue(any('non-blocking' in x for x in c.verify_exit(root,4,packet,'a'*64)))
    def test_runtime_exit_needs_exact_commit(self):
        c,root,packet=self.fixture(10)
        self.assertTrue(any('runtime commit' in x for x in c.verify_exit(root,10,packet,'a'*64)))
        packet['target_runtime_commit']='c'*40
        self.assertEqual(c.verify_exit(root,10,packet,'a'*64),[])
    def test_core_state_cannot_complete_anatomy_with_bare_pass(self):
        import shutil
        from test_original_v1_production_control import ControlTests
        import original_v1_production_control as control
        helper=ControlTests();root=helper.fixture();self.addCleanup(helper.doCleanups)
        sha=control.build(root)[0]['last_known_candidate_sha256']
        report=root/'empty_exit.json';report.write_text(json.dumps({'status':'PASS','candidate_sha256':sha}))
        rules=json.loads((root/'ORIGINAL_V1_PRODUCTION_CONTROL.json').read_text())
        rules['phase_completion_records']['5']={'candidate_sha256':sha,'evidence':{'path':'empty_exit.json','sha256':control.digest(report)}}
        (root/'ORIGINAL_V1_PRODUCTION_CONTROL.json').write_text(json.dumps(rules))
        with self.assertRaisesRegex(ValueError,'phase exit'):control.build(root)

    def test_templates_never_satisfy_phase_exit(self):
        c=self.module()
        state={'last_known_candidate_sha256':'a'*64,'current_candidate':'r29',
               'development_failure_count':7,'pinned_baseline':{'revision':'R2'},'next_action':{'action':'RUN r30'}}
        for phase in range(4,12):
            packet=c.make_template(phase,state)
            self.assertEqual(packet['status'],'INCOMPLETE');self.assertFalse(packet['production_approved'])
            self.assertTrue(all(x['passed'] is None and not x['evidence'] for x in packet['checks']))
            with tempfile.TemporaryDirectory() as temp:self.assertTrue(c.verify_exit(Path(temp),phase,packet,'a'*64))
    def test_external_check_evidence_is_refused(self):
        c,root,packet=self.fixture();packet['checks'][0]['evidence'][0]['path']='../external.json'
        self.assertTrue(any('outside' in x for x in c.verify_exit(root,4,packet,'a'*64)))
if __name__=='__main__':unittest.main()
