"""c004 arm-input resync: builder reproducible, causality pinned, baselines untouched, and the skeleton_input guard that
prevents stale input points in future candidate builders (mutation-proven)."""
import copy, hashlib, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import skeleton_input_guard as g  # noqa: E402
import build_candidate_c004_arm_inputs as b4  # noqa: E402

A = ROOT / 'ORIGINAL_V1_WORK/anatomy'
CAND = A / 'audit/candidates'
D4 = CAND / 'shoulder_thorax_c004_arm_inputs'
REC = {'a003': A / 'character_fit_r95_a003.json',
       'c001': CAND / 'shoulder_proposal_c001/candidate_record.json',
       'c002': CAND / 'shoulder_proposal_c002_ansur_height/candidate_record.json',
       'c003': CAND / 'shoulder_thorax_c003_ansur_coupled/candidate_record.json',
       'c004': D4 / 'candidate_record.json'}
L = {k: json.loads(p.read_text()) for k, p in REC.items()}
STALE = ['EJC', 'WJC', 'carpals', 'hand', 'humeroradial', 'humeroulnar', 'radial_styloid_bone', 'ulnar_styloid_bone']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Baselines(unittest.TestCase):
    def test_immutable_inputs(self):
        pins = {REC['a003']: '11712ba3e105aa88', REC['c001']: '08e9f2e1187dbeda', REC['c002']: 'aa344a6819dde763', REC['c003']: '3eb4fa1e2f7d815e',
                CAND / 'shoulder_thorax_c003_ansur_coupled/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend': '3962215043cebbcf'}
        for p, h in pins.items():
            self.assertTrue(sha(p).startswith(h), p)


class Guard(unittest.TestCase):
    def test_baseline_self_consistent(self):
        r = g.check(L['a003'], L['a003'])
        self.assertEqual((r['violations'], r['anchored'], r['consistent']), ([], 240, 240))

    def test_historic_candidates_flagged(self):
        for k in ('c001', 'c002', 'c003'):
            self.assertEqual(g.check(L['a003'], L[k])['violation_keys'], STALE, k)

    def test_c004_only_out_of_scope_residue(self):
        # any NEW stale key in a future derived builder fails here; carpals/hand are the recorded UNRESOLVED residue
        self.assertEqual(g.check(L['a003'], L['c004'])['violation_keys'], ['carpals', 'hand'])

    def test_mutation_stale_point_detected(self):
        c = copy.deepcopy(L['c004']); c['skeleton_input']['sides']['left']['WJC'] = L['a003']['skeleton_input']['sides']['left']['WJC']
        self.assertIn('WJC', g.check(L['a003'], c)['violation_keys'])

    def test_mutation_bone_moved_without_input_detected(self):
        c = copy.deepcopy(L['a003']); c['bones']['femur_left']['head_m'] = (np.array(c['bones']['femur_left']['head_m']) + [0, 0, 0.01]).tolist()
        self.assertEqual(g.check(L['a003'], c)['violation_keys'], ['HJC'])

    def test_consistent_rigid_move_passes(self):
        c = copy.deepcopy(L['a003']); t = np.array([0.0, 0.0, 0.01])
        for n in ('femur_left',):
            for e in ('head_m', 'tail_m'):
                c['bones'][n][e] = (np.array(c['bones'][n][e]) + t).tolist()
        for m in ('hip_left', 'tibiofemoral_left'):
            c['joint_markers'][m]['centre_m'] = (np.array(c['joint_markers'][m]['centre_m']) + t).tolist()
        for k in ('HJC', 'KJC'):
            c['skeleton_input']['sides']['left'][k] = (np.array(c['skeleton_input']['sides']['left'][k]) + t).tolist()
        r = g.check(L['a003'], c)
        # KJC is also the tibia head (not moved): the guard must report exactly that inconsistency and nothing else
        self.assertEqual([v['point'] for v in r['violations']], ['left/KJC'])
        self.assertEqual(list(r['violations'][0]['gap_mm']), ['bone:tibia_left:head'])


class C004(unittest.TestCase):
    def test_builder_reproduces_committed_record(self):
        out, table = b4.build()
        self.assertEqual(json.loads(json.dumps(out)), L['c004'])
        self.assertEqual(len(table), 12)
        self.assertTrue(all(abs(t['shift_norm_mm'] - 38.432) < 1e-3 for t in table))
        self.assertEqual({t['key']: t['target_reference'].split(':')[0] for t in table if t['side'] == 'left'},
                         {'EJC': 'bone', 'WJC': 'marker', 'humeroulnar': 'marker', 'humeroradial': 'marker', 'ulnar_styloid_bone': 'bone', 'radial_styloid_bone': 'bone'})

    def test_only_intended_change(self):
        c3, c4 = L['c003'], L['c004']
        for k in c3:
            if k not in ('skeleton_input', 'candidate'):
                self.assertEqual(c3[k], c4[k], k)
        for s in ('left', 'right'):
            for k, v in c3['skeleton_input']['sides'][s].items():
                if k not in b4.KEYS:
                    self.assertEqual(v, c4['skeleton_input']['sides'][s][k], (s, k))
        self.assertEqual(c3['skeleton_input']['trunk'], c4['skeleton_input']['trunk'])
        self.assertEqual(c4['candidate']['status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        self.assertFalse(c4['candidate']['freeze_ready'])
        self.assertEqual(c3['candidate']['acceptance_checks'], c4['candidate']['acceptance_checks'])

    def test_causality_pinned(self):
        d = json.loads((D4 / 'correction_and_causality.json').read_text())
        self.assertEqual(len(d['record_diff_c003_to_c004_excluding_candidate']), 12)
        f = d['derived_frames']
        self.assertLess(f['c004_vs_a003_max_deg'], 1e-9); self.assertGreater(f['c003_vs_a003_max_deg'], 10)
        self.assertEqual(f['other_segments_c003_vs_c004_max_deg'], 0.0)
        self.assertEqual(len(d['specs']['changed_c003_to_c004']), 16)
        self.assertTrue(all(v['c004_centre_to_radiocarpal_mm'] == 0 and v['c003_centre_to_radiocarpal_mm'] > 38 for v in d['specs']['wrist_centres'].values()))
        self.assertTrue(d['visual_inputs']['identical'] and d['acceptance_checks_identical_to_c003'])



class C004Run(unittest.TestCase):
    """Run-based evidence (Phase 9 rerun on the reused c003 blend) and the scan fixes it exposed."""
    AU = A / 'audit'

    def test_validation_summary(self):
        d = json.loads((D4 / 'validation_summary.json').read_text())
        self.assertEqual(d['overall'], 'C004_ARM_INPUT_RESYNC_CRITERIA_MET')
        self.assertEqual(d['candidate_status'], 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED')
        self.assertEqual(d['wrist_centre_gaps_closed']['radiocarpal_opening_mm']['c003_isolated_001'], {'left': 16.687, 'right': 16.687})
        self.assertEqual(d['wrist_centre_gaps_closed']['radiocarpal_opening_mm']['c004_isolated_001'], {'left': 0.0, 'right': 0.0})
        self.assertEqual((d['hand_thumb_axes_a003_convention']['mismatches'], d['hand_thumb_axes_a003_convention']['changed_tests_reproducing_a003']), ([], 24))
        self.assertEqual(d['unrelated_outputs_unchanged']['tests_identical_to_c003'], 111)
        self.assertEqual(d['integrity']['isolated_counts'], {'tests': 135, 'integrity_pass': 135, 'mirror_pairs': 43, 'mirror_pass': 41, 'mirror_solver_test_only': 2})
        self.assertEqual(d['guard']['violation_keys'], ['carpals', 'hand'])

    def test_run_comparison_and_reuse(self):
        r = json.loads((D4 / 'run_comparison.json').read_text())
        self.assertEqual((r['tests'], r['identical_to_c003'], len(r['changed_vs_c003']), r['changed_not_reproducing_a003']), (135, 111, 24, []))
        u = json.loads((D4 / 'review_reuse.json').read_text())
        self.assertEqual(u['status'], 'REUSED_C003_RENDER_PACK_NO_NEW_RENDERS')
        self.assertTrue(u['visual_input_digests']['identical'])
        self.assertEqual(sha(ROOT / u['reused_manifest']['path']), u['reused_manifest']['sha256'])
        self.assertFalse((D4 / 'review').exists())                                   # no renders claimed

    def test_attachment_v2_detects_what_v1_missed(self):
        import joint_attachment_scan as ja
        smp = {'wrist_flexion_left': json.loads((self.AU / 'runs/isolated_bone_only_c003_shoulder_thorax_001/isolated_samples.json').read_text())['wrist_flexion_left']}
        self.assertNotIn('radiocarpal_left', ja.scan(L['c003'], smp)['opened'])                      # v1 skipped it (TFCC participant)
        v2 = ja.scan(L['c003'], smp, partial=True)
        self.assertAlmostEqual(v2['opened']['radiocarpal_left']['max_opening_mm'], 16.687, places=2)
        self.assertEqual(v2['soft_tissue_participants_dropped']['radiocarpal_left'], ['tfcc_left'])
        smp4 = {'wrist_flexion_left': json.loads((self.AU / 'runs/isolated_bone_only_c004_arm_inputs_001/isolated_samples.json').read_text())['wrist_flexion_left']}
        self.assertNotIn('radiocarpal_left', ja.scan(L['c004'], smp4, partial=True)['opened'])

    def test_mirror_scan_deterministic_under_hash_seed(self):
        import subprocess, os, tempfile
        outs = []
        code = ('import json,sys; sys.path.insert(0,"scripts/anatomy_fit"); import mirror_parity_scan as m; '
                'r=json.load(open("ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json")); '
                'S=json.load(open("ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_014/isolated_samples.json")); '
                'S={k:S[k] for k in ("knee_flexion_extension_left","knee_flexion_extension_right")}; '
                'print(json.dumps(m.scan(r,S)["pairs"], sort_keys=True))')
        for seed in ('1', '2', '3'):
            env = {**os.environ, 'PYTHONHASHSEED': seed}
            outs.append(subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(len(set(outs)), 1)


if __name__ == '__main__':
    unittest.main()
