import importlib
import copy
import json
from pathlib import Path
import tempfile
import unittest

class PromotionTests(unittest.TestCase):
    def fixture(self, root):
        c=self.module();sha='a'*64;assets=[]
        for role in ('bare','dressed'):
            p=root/(role+'.glb');p.write_bytes(('test fixture '+role).encode())
            assets.append({'role':role,'path':p.name,'sha256':c.digest(p),'candidate_sha256':sha})
        raw=root/'raw.txt';raw.write_text('synthetic unit-test evidence, not model evidence')
        ref={'path':raw.name,'sha256':c.digest(raw)}
        packet={'schema_version':1,'candidate_sha256':sha,'target_runtime_commit':'b'*40,'assets':assets,'gates':{}}
        for gate,checks in c.REQUIRED_GATES.items():
            report={'gate_id':gate,'candidate_sha256':sha,'status':'PASS',
                'checks':[{'id':name,'passed':True,'evidence':[ref]} for name in checks],
                'command':'test-only fixture','source_git_commit':'c'*40,
                'evidence_timestamp':'2026-10-01T09:00:00+00:00','source_evidence':[ref],
                'assets':copy.deepcopy(assets),'target_runtime_commit':'b'*40}
            self.report(root,packet,gate,report)
        owner={'decision':'OWNER ACCEPTED','actor':'owner','candidate_sha256':sha,
            'decision_source':'synthetic unit-test decision','evidence_timestamp':'2026-10-01T09:00:00Z',
            'assets':copy.deepcopy(assets)}
        p=root/'owner.json';p.write_text(json.dumps(owner));packet['owner_acceptance']={'path':p.name,'sha256':c.digest(p)}
        return packet
    def report(self,root,packet,gate,report):
        p=root/(gate+'.json');p.write_text(json.dumps(report));packet['gates'][gate]={'path':p.name,'sha256':self.module().digest(p)}
    def mutate_report(self,root,packet,gate,mutation):
        report=json.loads((root/packet['gates'][gate]['path']).read_text());mutation(report);self.report(root,packet,gate,report)
    def test_valid_contract_is_eligible_without_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.assertEqual(self.module().verify_packet(root,self.fixture(root)),[])
    def test_duplicate_asset_role_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=self.fixture(root);p['assets'].append(copy.deepcopy(p['assets'][0]))
            self.assertTrue(any('assets' in x for x in self.module().verify_packet(root,p)))
    def test_same_file_for_bare_and_dressed_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=self.fixture(root);p['assets'][1].update(path=p['assets'][0]['path'],sha256=p['assets'][0]['sha256'])
            self.assertTrue(any('distinct' in x for x in self.module().verify_packet(root,p)))
    def test_gate_must_bind_exact_final_exports(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=self.fixture(root)
            self.mutate_report(root,p,'clothing',lambda r:r['assets'][1].update(sha256='d'*64))
            self.assertTrue(any('clothing' in x and 'asset' in x for x in self.module().verify_packet(root,p)))
    def test_owner_must_accept_exact_final_exports(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=self.fixture(root);f=root/'owner.json';r=json.loads(f.read_text());r.pop('assets');f.write_text(json.dumps(r));p['owner_acceptance']['sha256']=self.module().digest(f)
            self.assertTrue(any('owner' in x and 'asset' in x for x in self.module().verify_packet(root,p)))
    def test_duplicate_or_non_string_check_ids_refused(self):
        for replacement in ('duplicate', ['invalid']):
            with self.subTest(replacement=replacement),tempfile.TemporaryDirectory() as td:
                root=Path(td);p=self.fixture(root)
                def change(r):
                    if replacement=='duplicate':r['checks'].append(copy.deepcopy(r['checks'][0]))
                    else:r['checks'][0]['id']=replacement
                self.mutate_report(root,p,'anatomy',change)
                self.assertTrue(any('anatomy' in x for x in self.module().verify_packet(root,p)))
    def test_each_check_requires_bound_raw_evidence(self):
        for refs in ([],[{'path':'raw.txt','sha256':'d'*64}]):
            with self.subTest(refs=refs),tempfile.TemporaryDirectory() as td:
                root=Path(td);p=self.fixture(root)
                self.mutate_report(root,p,'anatomy',lambda r:r['checks'][0].update(evidence=refs))
                self.assertTrue(any('anatomy' in x and 'evidence' in x for x in self.module().verify_packet(root,p)))
    def test_invalid_or_timezone_free_timestamp_refused(self):
        for stamp in ('yesterday','2026-10-01T09:00:00',None):
            with self.subTest(stamp=stamp),tempfile.TemporaryDirectory() as td:
                root=Path(td);p=self.fixture(root)
                self.mutate_report(root,p,'topology',lambda r:r.update(evidence_timestamp=stamp))
                self.assertTrue(any('topology' in x for x in self.module().verify_packet(root,p)))
    def test_malformed_command_and_source_refs_refused(self):
        for field,value in (('command',True),('source_evidence','raw.txt'),('source_evidence',[True])):
            with self.subTest(field=field,value=value),tempfile.TemporaryDirectory() as td:
                root=Path(td);p=self.fixture(root);self.mutate_report(root,p,'topology',lambda r:r.update({field:value}))
                self.assertTrue(any('topology' in x for x in self.module().verify_packet(root,p)))
    def test_template_is_incomplete_and_never_eligible(self):
        c=self.module();state={'last_known_candidate_sha256':'a'*64,'current_candidate':'r29','development_failure_count':7}
        packet=c.make_template(state)
        self.assertEqual(packet['status'],'INCOMPLETE');self.assertFalse(packet['production_approved'])
        self.assertEqual(set(packet['gate_report_templates']),set(c.REQUIRED_GATES))
        self.assertTrue(all(x['passed'] is None for r in packet['gate_report_templates'].values() for x in r['checks']))
        with tempfile.TemporaryDirectory() as td:self.assertTrue(c.verify_packet(Path(td),packet))
    def module(self):
        self.assertTrue((Path(__file__).parent/'verify_original_v1_production_promotion.py').exists(),'promotion gate missing')
        return importlib.import_module('verify_original_v1_production_promotion')
    def test_eligibility_receipt_binds_exact_packet_identity(self):
        c=self.module();packet={'candidate_sha256':'a'*64,'target_runtime_commit':'b'*40}
        identity={'path':'phase12/promotion.json','sha256':'c'*64}
        result=c.eligibility_receipt([],identity,packet)
        self.assertEqual(result['eligibility'],'ALL_REQUIRED_GATES_SATISFIED')
        self.assertEqual(result['promotion_packet'],identity)
        self.assertEqual(result['candidate_sha256'],packet['candidate_sha256'])
        self.assertEqual(result['target_runtime_commit'],packet['target_runtime_commit'])
        self.assertFalse(result['production_approved'])

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
