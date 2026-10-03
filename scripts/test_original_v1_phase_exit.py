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

    def phase5_fixture(self):
        c,temp_root,packet=self.fixture(5)
        control={"phase_completion_records":{"4":{"candidate_sha256":"0"*64}}}
        (temp_root/"ORIGINAL_V1_PRODUCTION_CONTROL.json").write_text(json.dumps(control),encoding="utf-8")
        phase5_plan=temp_root/"ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json"
        phase5_plan.write_text(json.dumps({"schema_version":1,"fixture":True}),encoding="utf-8")
        previous_path=None;previous_sha="0"*64
        mapping=[("anatomy_5A_torso","5A"),("anatomy_5B_shoulders","5B"),("anatomy_5C_arms","5C"),
                 ("anatomy_5D_hands","5D"),("anatomy_5E_pelvis_legs","5E"),("anatomy_5F_feet","5F"),
                 ("anatomy_5G_head_neck","5G")]
        for i,(check_id,region) in enumerate(mapping):
            candidate_sha="a"*64 if region=="5G" else format(i+1,"064x")
            prev_ref=None if previous_path is None else {"path":previous_path.name,"sha256":c.digest(previous_path)}
            report={"schema_version":1,"phase":5,"region":region,"status":"REGION_EVIDENCE_COMPLETE",
                    "phase_complete":False,"production_approved":False,
                    "candidate_sha256":candidate_sha,"parent_candidate_sha256":previous_sha,
                    "development_freeze_candidate_sha256":"0"*64,
                    "active_epoch_baseline_revision":"P3B1","active_epoch_baseline_candidate_sha256":"9"*64,
                    "previous_region_receipt":prev_ref}
            report_path=temp_root/f"{region}_report.json";report_path.write_text(json.dumps(report),encoding="utf-8")
            receipt={"schema_version":1,"phase":5,"region":region,"contract_status":"REGION_EVIDENCE_VERIFIED",
                     "phase_complete":False,"production_approved":False,"issues":[],"candidate_sha256":candidate_sha,
                     "region_report":{"path":report_path.name,"sha256":c.digest(report_path)},
                     "plan":{"path":"ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json","sha256":c.digest(phase5_plan)},
                     "source_git_commit":"b"*40}
            receipt_path=temp_root/f"{region}_receipt.json";receipt_path.write_text(json.dumps(receipt),encoding="utf-8")
            check=next(x for x in packet["checks"] if x["id"]==check_id)
            check["evidence"]=[{"path":receipt_path.name,"sha256":c.digest(receipt_path)}]
            previous_path=receipt_path;previous_sha=candidate_sha
        return c,temp_root,packet

    def test_phase5_exit_requires_real_ordered_region_receipts(self):
        c,root,packet=self.phase5_fixture()
        self.assertEqual(c.verify_exit(root,5,packet,"a"*64),[])

    def test_phase5_exit_rejects_broken_region_parent_chain(self):
        c,root,packet=self.phase5_fixture()
        report=root/"5D_report.json";data=json.loads(report.read_text());data["parent_candidate_sha256"]="f"*64
        report.write_text(json.dumps(data))
        receipt=root/"5D_receipt.json";rd=json.loads(receipt.read_text());rd["region_report"]["sha256"]=c.digest(report)
        receipt.write_text(json.dumps(rd))
        check=next(x for x in packet["checks"] if x["id"]=="anatomy_5D_hands")
        check["evidence"][0]["sha256"]=c.digest(receipt)
        issues=c.verify_exit(root,5,packet,"a"*64)
        self.assertTrue(any("parent candidate" in x for x in issues))

    def test_phase5_exit_rejects_wrong_freeze_identity(self):
        c,root,packet=self.phase5_fixture()
        report=root/"5A_report.json";data=json.loads(report.read_text());data["development_freeze_candidate_sha256"]="e"*64
        report.write_text(json.dumps(data))
        receipt=root/"5A_receipt.json";rd=json.loads(receipt.read_text());rd["region_report"]["sha256"]=c.digest(report)
        receipt.write_text(json.dumps(rd))
        check=next(x for x in packet["checks"] if x["id"]=="anatomy_5A_torso")
        check["evidence"][0]["sha256"]=c.digest(receipt)
        issues=c.verify_exit(root,5,packet,"a"*64)
        self.assertTrue(any("freeze SHA differs" in x for x in issues))

    def test_phase5_exit_rejects_receipt_plan_drift(self):
        c,root,packet=self.phase5_fixture()
        receipt=root/"5C_receipt.json";data=json.loads(receipt.read_text());data["plan"]["sha256"]="f"*64
        receipt.write_text(json.dumps(data))
        check=next(x for x in packet["checks"] if x["id"]=="anatomy_5C_arms")
        check["evidence"][0]["sha256"]=c.digest(receipt)
        issues=c.verify_exit(root,5,packet,"a"*64)
        self.assertTrue(any("execution-plan identity differs" in x for x in issues))

    def test_phase5_exit_rejects_missing_receipt_source_commit(self):
        c,root,packet=self.phase5_fixture()
        receipt=root/"5B_receipt.json";data=json.loads(receipt.read_text());data["source_git_commit"]=None
        receipt.write_text(json.dumps(data))
        check=next(x for x in packet["checks"] if x["id"]=="anatomy_5B_shoulders")
        check["evidence"][0]["sha256"]=c.digest(receipt)
        issues=c.verify_exit(root,5,packet,"a"*64)
        self.assertTrue(any("source Git commit" in x for x in issues))

    def test_phase5_exit_rejects_nonfinal_exit_candidate(self):
        c,root,packet=self.phase5_fixture()
        issues=c.verify_exit(root,5,packet,"b"*64)
        self.assertTrue(any("final 5G" in x for x in issues))

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
