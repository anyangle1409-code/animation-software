import importlib
import json
from pathlib import Path
import tempfile
import unittest


class RepairPreparationTests(unittest.TestCase):
    def module(self):return importlib.import_module('prepare_original_v1_repair_policy')
    def state(self):return {'current_candidate':'r29','candidate_state':'experimental','last_known_candidate_sha256':'a'*64,
                             'pinned_baseline':{'revision':'P3B1','candidate_sha256':'b'*64},'latest_evidence':[]}
    def root(self,path):
        import original_v1_production_control as c
        root=Path(path);manifest=root/c.CAND/'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r29.json'
        manifest.parent.mkdir(parents=True);manifest.write_text(json.dumps({'candidate_sha256':'a'*64}))
        for name in ('ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json','ORIGINAL_V1_PRODUCTION_CONTROL.json'):
            (root/name).write_text('{}')
        for name in ('ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json',
                     'ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json'):
            src=c.ROOT/name;dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
        return root
    def test_empty_permissions_and_unknown_child_remain_incomplete(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);result=c.prepare(root,'3D',self.state())
            p=result['audit_policy_template.json']
            self.assertEqual(p['before_candidate_sha256'],'a'*64);self.assertIsNone(p['candidate_sha256'])
            self.assertEqual(p['allowed_vertex_ids'],[]);self.assertEqual(p['allowed_bones'],[]);self.assertEqual(p['allowed_regions'],[])
            self.assertFalse(p['index_correspondence_confirmed'])
            self.assertEqual(result['inspection_context.json']['diagnostics_state'],'AWAITING_PROBES')
            self.assertFalse(result['edit_intent_template.json']['production_approved'])
    def test_repair_packet_uses_active_epoch_and_rev2c_lock(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);result=c.prepare(root,'3D',self.state())
            context=result['inspection_context.json'];intent=result['edit_intent_template.json']
            self.assertEqual(context['active_epoch_baseline']['revision'],'P3B1')
            self.assertEqual(context['locked_rig']['bone_count'],67)
            self.assertTrue(any('P3B1' in x for x in intent['frozen_constraints']))
            self.assertTrue(any('67 bones' in x for x in intent['frozen_constraints']))

    def test_deterministic_without_probes(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);self.assertEqual(c.prepare(root,'3C',self.state()),c.prepare(root,'3C',self.state()))
    def test_unknown_package_or_rejected_candidate_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td)
            with self.assertRaises(ValueError):c.prepare(root,'5A',self.state())
            state=self.state();state['candidate_state']='rejected'
            with self.assertRaises(ValueError):c.prepare(root,'3C',state)
    def test_parent_manifest_mismatch_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);state=self.state();state['last_known_candidate_sha256']='b'*64
            with self.assertRaisesRegex(ValueError,'parent'):c.prepare(root,'3D',state)
    def test_partial_probe_pair_refused(self):
        c=self.module();import original_v1_production_control as pc
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);folder=root/pc.RC/'remaining_diagnostics_r29';folder.mkdir(parents=True)
            (folder/'edge_extremes.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'partial'):c.prepare(root,'3E',self.state())
    def test_probe_ids_never_become_permissions(self):
        from test_original_v1_diagnostic_brief import DiagnosticBriefTests
        from unittest.mock import patch
        c=self.module();module,grip,edges,primary,profile=DiagnosticBriefTests().fixture()
        import original_v1_production_control as pc
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);folder=root/pc.RC/'remaining_diagnostics_r29';folder.mkdir(parents=True)
            (folder/'grip_penetration.json').write_text(json.dumps(grip));(folder/'edge_extremes.json').write_text(json.dumps(edges))
            summary=module.summarize(grip,edges,primary,'a'*64,'b'*64,profile)
            with patch.object(c,'verified_diagnostics',return_value=(summary,[])):
                result=c.prepare(root,'3D',self.state())
            self.assertEqual(result['inspection_context.json']['inspection_vertex_ids'],[10,11])
            self.assertEqual(result['audit_policy_template.json']['allowed_vertex_ids'],[])
    def test_existing_output_folder_is_preserved(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);folder=root/'existing';folder.mkdir();(folder/'keep').write_text('preserve')
            with self.assertRaisesRegex(ValueError,'exists'):c.publish(root,folder,c.prepare(root,'3C',self.state()))
            self.assertEqual((folder/'keep').read_text(),'preserve')
    def test_output_outside_repo_refused(self):
        c=self.module()
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td)
            with self.assertRaisesRegex(ValueError,'repository'):c.publish(root,root.parent/'outside',c.prepare(root,'3C',self.state()))
    def test_receipt_binds_written_templates(self):
        c=self.module();import original_v1_production_control as pc
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);folder=root/'packet';c.publish(root,folder,c.prepare(root,'3E',self.state()))
            receipt=json.loads((folder/'preparation_manifest.json').read_text())
            self.assertFalse(receipt['production_approved']);self.assertEqual(receipt['state'],'PREPARATION_ONLY')
            for ref in receipt['outputs']:self.assertEqual(pc.digest(root/ref['path']),ref['sha256'])
    def test_draft_cannot_be_used_as_completed_audit_policy(self):
        from test_original_v1_change_audit import AuditTests
        import audit_original_v1_changes as audit
        with tempfile.TemporaryDirectory() as td:
            root=self.root(td);p=self.module().prepare(root,'3D',self.state())['audit_policy_template.json']
            snapshot=AuditTests().snapshot()
            with self.assertRaisesRegex(ValueError,'candidate hashes'):audit.audit(snapshot,snapshot,p)

if __name__=='__main__':unittest.main()
