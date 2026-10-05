"""Safety cases for model production control; no Blender required."""
import copy
import importlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ControlTests(unittest.TestCase):
    def module(self):
        self.assertTrue((ROOT/'scripts/original_v1_production_control.py').exists(),
                        'evidence-led production control is not implemented')
        return importlib.import_module('original_v1_production_control')

    def latest(self, c):
        """Live latest complete numbered candidate and the next free revision (derived, never hard-coded)."""
        status, _ = c.build(ROOT)
        rev = status['current_candidate']
        self.assertRegex(rev, r'^r\d+$')
        return rev, 'r%d' % (int(rev[1:]) + 1)

    def test_phase_checkpoint_can_be_inherited_by_direct_descendant(self):
        c=self.module()
        a={"revision":"r100","sha256":"a"*64,"parent_sha256":None}
        b={"revision":"r101","sha256":"b"*64,"parent_sha256":"a"*64}
        info=c.phase_checkpoint_on_lineage({"r100":a,"r101":b},"r101","a"*64)
        self.assertEqual(info,{"revision":"r100","sha256":"a"*64,"depth":1})

    def test_phase_checkpoint_divergent_candidate_is_refused(self):
        c=self.module()
        entries={
            "r100":{"revision":"r100","sha256":"a"*64,"parent_sha256":None},
            "r101":{"revision":"r101","sha256":"b"*64,"parent_sha256":"a"*64},
            "r102":{"revision":"r102","sha256":"c"*64,"parent_sha256":"d"*64},
        }
        with self.assertRaisesRegex(ValueError,"not on current candidate lineage"):
            c.phase_checkpoint_on_lineage(entries,"r102","a"*64)

    def test_duplicate_revision_labels_for_identical_bytes_are_allowed_when_parent_agrees(self):
        c=self.module()
        entries={
            "r100":{"revision":"r100","sha256":"a"*64,"parent_sha256":"b"*64},
            "r101":{"revision":"r101","sha256":"a"*64,"parent_sha256":"b"*64},
            "r99":{"revision":"r99","sha256":"b"*64,"parent_sha256":None},
        }
        info=c.phase_checkpoint_on_lineage(entries,"r101","b"*64)
        self.assertEqual(info["sha256"],"b"*64)
        self.assertEqual(info["depth"],1)

    def test_duplicate_candidate_bytes_with_conflicting_parent_lineage_are_refused(self):
        c=self.module()
        entries={
            "r100":{"revision":"r100","sha256":"a"*64,"parent_sha256":"b"*64},
            "r101":{"revision":"r101","sha256":"a"*64,"parent_sha256":"c"*64},
        }
        with self.assertRaisesRegex(ValueError,"conflicting parent lineage"):
            c.candidate_lineage(entries,"r101")

    def test_phase_checkpoint_cycle_is_refused(self):
        c=self.module()
        entries={
            "r100":{"revision":"r100","sha256":"a"*64,"parent_sha256":"b"*64},
            "r101":{"revision":"r101","sha256":"b"*64,"parent_sha256":"a"*64},
        }
        with self.assertRaisesRegex(ValueError,"lineage cycle"):
            c.phase_checkpoint_on_lineage(entries,"r101","c"*64)

    def test_live_evidence_preserves_tradeoff_and_baseline(self):
        c = self.module()
        status, ledger = c.build(ROOT)
        rows = {x['revision']: x for x in ledger['candidates']}
        rev = status['current_candidate']
        # The live state advanced past r29: the current candidate is the latest complete numbered revision.
        self.assertRegex(rev, r'^r\d+$')
        self.assertGreaterEqual(int(rev[1:]), 29)
        self.assertEqual(status['development_failure_count'], rows[rev]['development_failure_count'])
        self.assertFalse(status['production_approved'])
        self.assertEqual(status['pinned_baseline']['revision'], c.epoch_baseline(ROOT, rev)[0])   # baseline of the candidate's stress-pose epoch
        # Historical evidence is immutable: r29 stays a trade-off with its recorded r28 comparison.
        self.assertEqual(rows['r29']['comparisons']['r28']['regression_count'], 12)
        self.assertEqual(rows['r29']['classification'], 'TRADE-OFF')
        # An advanced state may never silently promote: no production approval and the action is a known repair/diagnostic step.
        self.assertNotIn(status['next_action']['action'], ('VERIFY production promotion packet',))
        self.assertIn(status['phases']['3D']['state'], ('refinement', 'blocked', 'complete'))

    def fixture(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        root = Path(td.name)
        shutil.copytree(ROOT/'ORIGINAL_V1_WORK', root/'ORIGINAL_V1_WORK')
        (root/'src/rig').mkdir(parents=True)
        shutil.copy(ROOT/'src/rig/canonicalV4Original.ts',root/'src/rig/canonicalV4Original.ts')
        (root/'scripts').mkdir()
        shutil.copy(ROOT/'scripts/pose_test_original_v1_o4_candidate_blender.py',root/'scripts/pose_test_original_v1_o4_candidate_blender.py')
        for hist in ROOT.glob('scripts/pose_test_original_v1_o4_candidate_blender_P*_historical.py'): shutil.copy(hist,root/'scripts'/hist.name)
        for p in ROOT.glob('ORIGINAL_V1*.json'): shutil.copy(p, root/p.name)
        return root

    def test_owner_accepted_regression_is_bound_to_exact_candidate_and_values(self):
        c = self.module()
        root = self.fixture()
        cp = root/'ORIGINAL_V1_PRODUCTION_CONTROL.json'
        ctl = json.loads(cp.read_text(encoding='utf-8-sig'))
        acc = ctl.get('owner_accepted_regressions') or []
        self.assertTrue(acc, 'live control carries the owner disposition')
        status, _ = c.build(root)
        # accepted: not unresolved, but still listed with the untouched comparator entry and the strict count before dispositions
        self.assertEqual(status['unresolved_regressions'], [])
        self.assertEqual(len(status['owner_accepted_regressions']), len(acc))
        self.assertEqual(status['strict_regression_count_before_owner_dispositions'], len(acc))
        rec = status['owner_accepted_regressions'][0]
        self.assertEqual(rec['comparator_regression']['name'], acc[0]['pose'])
        self.assertEqual(rec['comparator_regression']['tolerance'], 0.02)           # tolerance untouched
        self.assertEqual(status['pinned_baseline']['revision'], acc[0]['pinned_baseline'])
        self.assertFalse(status['production_approved'])
        # a different candidate hash, a different value or a different baseline leaves the regression unresolved
        for key, bad in (('candidate_sha256', 'f' * 64), ('candidate_value', 0.6701), ('pinned_baseline', 'P2B1'), ('candidate_revision', 'r999')):
            broken = json.loads(json.dumps(ctl)); broken['owner_accepted_regressions'][0][key] = bad
            cp.write_text(json.dumps(broken, indent=2) + '\n', encoding='utf-8')
            s2, _ = c.build(root)
            self.assertEqual(len(s2['unresolved_regressions']), len(acc), key)
            self.assertEqual(s2['owner_accepted_regressions'], [], key)
        # an incomplete entry is refused loudly
        broken = json.loads(json.dumps(ctl)); del broken['owner_accepted_regressions'][0]['owner_statement']
        cp.write_text(json.dumps(broken, indent=2) + '\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            c.build(root)

    def test_partial_new_candidate_cannot_replace_latest_complete(self):
        c = self.module(); root = self.fixture()
        latest, new = self.latest(c)
        cand = root/'ORIGINAL_V1_WORK/candidates'
        man = json.loads((cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{latest}.json').read_text())
        man['candidate'] = man['candidate'].replace(f'{latest}.blend', f'{new}.blend')
        (cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{new}.json').write_text(json.dumps(man))
        status, _ = c.build(root)
        self.assertEqual(status['current_candidate'], latest)
        self.assertEqual(status['next_action']['action'], 'STOP')
        self.assertIn('incomplete', status['next_action']['reason'])

    def test_stale_comparison_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_comparison_vs_R2.json'
        d = json.loads(p.read_text()); d['candidate_failed_checks'] = 0
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError, 'comparison.*disagrees'): c.build(root)

    def test_missing_extended_pose_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_WORK/candidates/repair_checks/full_r29_merged_pose_report.json'
        d = json.loads(p.read_text()); p.write_text(json.dumps([x for x in d if x['pose'] != 'lunge']))
        with self.assertRaisesRegex(ValueError, 'coverage'): c.build(root)

    def test_rejected_history_survives_regeneration(self):
        c = self.module(); root = self.fixture()
        old = {'schema_version':1,'candidates':[{'revision':'r99_rejected','sha256':'a'*64,
               'state':'rejected','reason':'owner rejected silhouette','evidence_location':None}]}
        (root/'ORIGINAL_V1_CANDIDATE_LEDGER.json').write_text(json.dumps(old))
        _, ledger = c.build(root)
        self.assertIn('r99_rejected',[x['revision'] for x in ledger['candidates']])

    def test_frozen_gate_drift_is_refused(self):
        c = self.module(); root = self.fixture()
        p = root/'ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json'
        d = json.loads(p.read_text()); d['profiles']['development_blocker']['grip_max_penetration_mm'] = 6
        p.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'frozen'): c.build(root)

    def test_next_action_requires_both_source_bound_diagnostics(self):
        c=self.module();status,_=c.build(ROOT)
        status['current_candidate']='r30';status['incomplete_candidates']=[]
        status['latest_evidence']=[{'path':c.RC+'/remaining_diagnostics_r30/edge_extremes.json'}]
        control=c.read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
        self.assertEqual(c.next_action(status,control)['action'],'RUN remaining diagnostics')

    def test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery(self):
        c=self.module();status,_=c.build(ROOT)
        status['current_candidate']='r30';status['incomplete_candidates']=[]
        status['latest_evidence']=[{'path':c.RC+'/remaining_diagnostics_r30/'+n} for n in ('edge_extremes.json','grip_penetration.json')]
        # Define the scenario explicitly (hand recovery done; wrist still open, grip and lunge blocked) instead of
        # inheriting whatever the live phases are, so the ORDER wrist -> grip/thumb -> lunge is what is tested.
        status['phases']['3B']['state']='complete'
        status['phases']['3D']['state']='refinement'
        status['phases']['3C']['state']='blocked'
        status['phases']['3E']['state']='blocked'
        control=c.read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
        control['continuation_decisions']['r30']={'candidate_sha256':status['last_known_candidate_sha256']}
        self.assertEqual(c.next_action(status,control)['action'],'REPAIR wrist')
        status['phases']['3D']['state']='complete'
        self.assertEqual(c.next_action(status,control)['action'],'REPAIR grip/thumb')
        status['phases']['3C']['state']='complete'
        self.assertEqual(c.next_action(status,control)['action'],'REPAIR lunge')

    def test_zero_blockers_cannot_hide_inherited_regressions(self):
        c=self.module();status,_=c.build(ROOT)
        status['current_candidate']='r30';status['incomplete_candidates']=[]
        status['latest_evidence']=[{'path':c.RC+'/remaining_diagnostics_r30/'+n} for n in ('edge_extremes.json','grip_penetration.json')]
        for p in ('3B','3C','3D','3E'):status['phases'][p]['state']='complete'
        status['development_failure_count']=0
        control=c.read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
        control['continuation_decisions']['r30']={'candidate_sha256':status['last_known_candidate_sha256']}
        control['active_local_repair']=None
        # premise stated explicitly (the live candidate may carry an owner-accepted disposition): an UNRESOLVED strict regression must block the freeze
        status['unresolved_regressions']=[{'name':'pullup_top','region':'torso','metric':'region_min_ratio','baseline':0.693,'candidate':0.67,'tolerance':0.02}]
        self.assertEqual(c.next_action(status,control)['action'],'RECONCILE freeze regressions')
        # and once none is unresolved (e.g. every strict difference carries a candidate-bound owner disposition) the freeze validation may be entered
        status['unresolved_regressions']=[]
        self.assertEqual(c.next_action(status,control)['action'],'ENTER development freeze validation')

    def test_candidate_bound_local_repair_precedes_freeze_reconciliation(self):
        c=self.module();status,_=c.build(ROOT)
        control=c.read(ROOT,'ORIGINAL_V1_PRODUCTION_CONTROL.json')
        # Isolate the local-repair precedence rule from the newer, deliberately
        # higher-priority owner visual-rejection gate.
        status['visual_rejections']=[]
        # the live control may have closed its repair record (closed_local_repairs); the precedence rule is tested with a synthetic candidate-bound record
        active={'candidate_revision':status['current_candidate'],'candidate_sha256':status['last_known_candidate_sha256'],
                'action':'RUN local axilla repair','reason':'synthetic','command':'RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat '+status['current_candidate'],
                'work_package':'docs/work_packages/PHASE_3A_AXILLA_PIT_LOCAL_REPAIR.md'}
        control['active_local_repair']=active
        action=c.next_action(status,control)
        self.assertEqual(action['action'],active['action'])
        self.assertEqual(action['command'],active['command'])
        self.assertEqual(action['work_package'],active['work_package'])
        # a record bound to another candidate hash must not take precedence
        active2=dict(active,candidate_sha256='0'*64)
        control['active_local_repair']=active2
        self.assertNotEqual(c.next_action(status,control)['action'],active['action'])

    def test_owner_accepted_limitation_is_candidate_bound_visible_and_waives_nothing(self):
        c = self.module()
        status, _ = c.build(ROOT)
        lims = status['owner_accepted_limitations']
        self.assertTrue(lims, 'live control carries the documented limitation')
        self.assertTrue(all(x['not_a_numerical_pass'] is True and x['waives_no_gate'] is True for x in lims))
        self.assertTrue(all(x['candidate_sha256'] == status['last_known_candidate_sha256'] for x in lims))
        self.assertTrue(any(f['id'] == lims[0]['id'] or f['source'].endswith(lims[0]['id']) for f in status['phase5_followups']))
        self.assertFalse(status['production_approved'])
        self.assertEqual(status['development_failure_count'], 0)

    def test_open_owner_visual_rejection_reopens_active_candidate_before_phase5(self):
        c = self.module()
        status, _ = c.build(ROOT)
        self.assertTrue(status['visual_rejections'])
        self.assertTrue(all(x['candidate_revision'] == status['current_candidate'] for x in status['visual_rejections']))
        self.assertTrue(all(x['candidate_sha256'] == status['last_known_candidate_sha256'] for x in status['visual_rejections']))
        self.assertEqual(status['phases']['4']['state'], 'complete')
        self.assertEqual(status['next_action']['action'], 'REOPEN shoulder/axilla foundation')
        self.assertNotIn('Phase 5', status['next_action']['action'])

    def test_visual_rejection_for_different_candidate_does_not_rewrite_history(self):
        c = self.module(); root = self.fixture()
        cp = root/'ORIGINAL_V1_PRODUCTION_CONTROL.json'
        ctl = json.loads(cp.read_text(encoding='utf-8-sig'))
        historical_phase4 = copy.deepcopy(ctl['phase_completion_records']['4'])
        for rejection in ctl['visual_rejections']:
            rejection['candidate_sha256'] = 'f' * 64
        cp.write_text(json.dumps(ctl, indent=2) + '\n', encoding='utf-8')
        status, _ = c.build(root)
        self.assertEqual(status['visual_rejections'], [])
        self.assertEqual(status['phases']['4']['state'], 'complete')
        self.assertEqual(c.read(root, 'ORIGINAL_V1_PRODUCTION_CONTROL.json')['phase_completion_records']['4'], historical_phase4)
        self.assertTrue(status['next_action']['action'].startswith('EXECUTE Phase 5'))

    def test_incomplete_visual_rejection_is_refused(self):
        c = self.module(); root = self.fixture()
        cp = root/'ORIGINAL_V1_PRODUCTION_CONTROL.json'
        ctl = json.loads(cp.read_text(encoding='utf-8-sig'))
        del ctl['visual_rejections'][0]['evidence_paths']
        cp.write_text(json.dumps(ctl, indent=2) + '\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'visual rejection entry incomplete'):
            c.build(root)


    def test_frozen_stress_pose_drift_is_refused(self):
        c=self.module();root=self.fixture()
        p=root/'scripts/pose_test_original_v1_o4_candidate_blender.py'
        p.write_text(p.read_text().replace('ONLY = set(', 'ONLY = frozenset(',1))
        with self.assertRaisesRegex(ValueError,'frozen stress-pose'):c.build(root)

    def test_historical_stress_pose_definition_drift_is_refused(self):
        c=self.module();root=self.fixture()
        p=root/'scripts/pose_test_original_v1_o4_candidate_blender_P1_historical.py'
        p.write_text(p.read_text().replace('ONLY = set(', 'ONLY = frozenset(',1))
        with self.assertRaisesRegex(ValueError,'historical stress-pose'):c.build(root)

    def test_partial_candidate_stays_incomplete_after_ledger_update(self):
        c=self.module();root=self.fixture();cand=root/'ORIGINAL_V1_WORK/candidates'
        latest,new=self.latest(c)
        man=json.loads((cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{latest}.json').read_text())
        man['candidate']=man['candidate'].replace(f'{latest}.blend',f'{new}.blend')
        (cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{new}.json').write_text(json.dumps(man))
        first,ledger=c.build(root)
        (root/'ORIGINAL_V1_CANDIDATE_LEDGER.json').write_text(json.dumps(ledger))
        second,_=c.build(root)
        self.assertEqual(first['incomplete_candidates'],second['incomplete_candidates'])
        self.assertEqual(second['next_action']['action'],'STOP')

    def test_new_full_candidate_requires_source_receipt(self):
        c=self.module();root=self.fixture();cand=root/c.CAND
        latest,new=self.latest(c)
        man=c.read(root,c.CAND+f'/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{latest}.json')
        man['candidate']=man['candidate'].replace(f'{latest}.blend',f'{new}.blend')
        (cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{new}.json').write_text(json.dumps(man))
        shutil.copy(root/c.RC/f'full_{latest}_merged_pose_report.json',root/c.RC/f'full_{new}_merged_pose_report.json')
        pin_latest,pin_new=c.epoch_baseline(root,latest)[0],c.epoch_baseline(root,new)[0]
        shutil.copy(root/c.RC/f'full_{latest}_comparison_vs_{pin_latest}.json',root/c.RC/f'full_{new}_comparison_vs_{pin_new}.json')
        with self.assertRaisesRegex(ValueError,'source receipt'):c.build(root)

    def receipt_fixture(self):
        from test_original_v1_evidence_merge import MergeTests
        import merge_original_v1_repair_group_reports as merger
        helper=MergeTests();root=helper.fixture(merger);self.addCleanup(helper.doCleanups)
        rows,receipt=merger.collect_reports(root,'r29')
        output=root/merger.RC/'full_r29_merged_pose_report.json'
        output.write_text(json.dumps(rows))
        receipt['merged_pose_report_sha256']=merger.sha256(output)
        packet=output.with_name('full_r29_evidence_manifest.json');packet.write_text(json.dumps(receipt))
        return root,packet

    def test_receipt_checks_without_requiring_every_render_on_phone(self):
        c=self.module();root,packet=self.receipt_fixture()
        verified=c.verify_full_receipt(root,'r29')
        self.assertEqual(verified['path'],packet.relative_to(root).as_posix())

    def test_receipt_candidate_mismatch_is_refused(self):
        c=self.module();root,packet=self.receipt_fixture()
        d=json.loads(packet.read_text());d['candidate_sha256']='b'*64;packet.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'candidate'):c.verify_full_receipt(root,'r29')

    def test_receipt_source_tampering_is_refused(self):
        c=self.module();root,packet=self.receipt_fixture()
        path=root/c.RC/'hand_r29/pose_test_report.json';path.write_text('[]')
        with self.assertRaisesRegex(ValueError,'hash'):c.verify_full_receipt(root,'r29')

    def test_receipt_cannot_hide_disagreement_with_merged_metrics(self):
        c=self.module();root,packet=self.receipt_fixture()
        path=root/c.RC/'full_r29_merged_pose_report.json';rows=json.loads(path.read_text())
        rows[0]['volume_ratio']+=.01;path.write_text(json.dumps(rows))
        d=json.loads(packet.read_text());d['merged_pose_report_sha256']=c.digest(path);packet.write_text(json.dumps(d))
        with self.assertRaisesRegex(ValueError,'merged metrics'):c.verify_full_receipt(root,'r29')

    def test_future_candidate_with_verified_sources_is_selected(self):
        import subprocess
        import sys
        import merge_original_v1_repair_group_reports as merger
        c=self.module();root=self.fixture();cand=root/c.CAND
        latest,new=self.latest(c)
        live_status,live_ledger=c.build(ROOT)
        live_row=next(x for x in live_ledger['candidates'] if x['revision']==latest)
        man=c.read(root,c.CAND+f'/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{latest}.json')
        man['candidate']=man['candidate'].replace(f'{latest}.blend',f'{new}.blend')
        (cand/f'HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{new}.json').write_text(json.dumps(man))
        real={x['pose']:x for x in c.read(root,c.RC+f'/full_{latest}_merged_pose_report.json')}
        for group,poses in merger.GROUP_POSES.items():
            directory=root/c.RC/f'{group}_{new}';directory.mkdir()
            report=directory/'pose_test_report.json';report.write_text(json.dumps([real[n] for n in poses]))
            source={'candidate_sha256':man['candidate_sha256'],'pose_report_sha256':c.digest(report),
                    'render_script_sha256':'a'*64,'blender_version':'test fixture only','images':[]}
            (directory/'render_source_manifest.json').write_text(json.dumps(source))
        rows,receipt=merger.collect_reports(root,new)
        merged=root/c.RC/f'full_{new}_merged_pose_report.json';merged.write_text(json.dumps(rows))
        receipt['merged_pose_report_sha256']=c.digest(merged)
        (root/c.RC/f'full_{new}_evidence_manifest.json').write_text(json.dumps(receipt))
        pin,pin_path=c.epoch_baseline(root,new)
        for previous in (pin,latest)+(('r28',) if int(latest[1:])<39 else ()):
            baseline=root/pin_path if previous==pin else root/c.RC/f'full_{previous}_merged_pose_report.json'
            out=root/c.RC/f'full_{new}_comparison_vs_{previous}.json'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/compare_original_v1_deformation_reports.py'),str(baseline),str(merged),
                '--baseline-grip-report',str(baseline),'--candidate-grip-report',str(merged),
                '--profile','development_blocker','--report-only','--json-out',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
        status,ledger=c.build(root)
        # The fixture candidate carries the live latest candidate's own evidence, so it must be selected as the new
        # current candidate with the SAME development failure count and classification, and never production-approved.
        self.assertEqual(status['current_candidate'],new);self.assertEqual(status['development_failure_count'],live_row['development_failure_count'])
        self.assertFalse(status['production_approved'])
        # The fixture compares the copy with its own source (identical reports), so it cannot reproduce a live trade-off versus a
        # predecessor; it must still carry a recognised classification.
        self.assertIn(status['candidate_classification'],('EXPERIMENTAL','TRADE-OFF','STRICT IMPROVEMENT'))
        self.assertTrue(any(x['path'].endswith('evidence_manifest.json') for x in status['latest_evidence']))
        again,again_ledger=c.build(root)
        self.assertEqual(status,again);self.assertEqual(ledger,again_ledger)

if __name__ == '__main__': unittest.main()
