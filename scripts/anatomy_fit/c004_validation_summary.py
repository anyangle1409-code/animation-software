#!/usr/bin/env python3
"""c004 acceptance of the arm-input resync against the requested criteria (read-only; aggregates committed evidence).

Each criterion is computed from repository files, never asserted:
  wrist_centre_gaps_closed      skeleton_input WJC == radiocarpal marker (both sides) and no radiocarpal opening in the
                                v2 attachment scan (c003 opened it 16.7 mm in the wrist sweeps);
  hand_thumb_axes_a003_convention  joint_frame_audit: every single-channel test's followed axis and alignment equal a003's
                                (|d alignment| <= 1e-3 deg), and every c004 test that differs from c003 reproduces a003
                                rotations/angles (run_comparison);
  shoulder_ansur_sc_unharmed    bones, joint markers, landmarks and acceptance_checks identical to c003;
  unrelated_outputs_unchanged   111 of 135 test sample sets identical to c003; mirror / collision / all-pairs / continuity /
                                state-restoration / v2-attachment results equal c003's apart from the wrist correction;
  solver_agreement              AGREE; round_trip PASS and report equal to c003's; sources preserved (hashes);
  guard                         stale skeleton_input residue limited to the out-of-scope carpals/hand dicts.

  c004_validation_summary.py --out JSON
"""
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / 'ORIGINAL_V1_WORK/anatomy'; AU = A / 'audit'
C3 = AU / 'candidates/shoulder_thorax_c003_ansur_coupled'; C4 = AU / 'candidates/shoulder_thorax_c004_arm_inputs'
BLEND = C3 / 'HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'
VOLATILE = {'label', 'inputs_sha256', 'created'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def J(p):
    return json.loads(Path(p).read_text())


def same_scan(kind, a='c003_isolated_001', b='c004_isolated_001'):
    x, y = J(AU / kind / f'{a}.json'), J(AU / kind / f'{b}.json')
    return sorted(k for k in set(x) | set(y) if k not in VOLATILE and x.get(k) != y.get(k))


def run():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import skeleton_input_guard as g
    r3, r4, ra = J(C3 / 'candidate_record.json'), J(C4 / 'candidate_record.json'), J(A / 'character_fit_r95_a003.json')
    out = {}
    gaps = {s: r4['skeleton_input']['sides'][s]['WJC'] == r4['joint_markers'][f'radiocarpal_{s}']['centre_m'] for s in ('left', 'right')}
    v2 = {k: J(AU / f'joint_attachment_scan/{k}_v2.json')['opened'] for k in ('a003_isolated_014', 'c003_isolated_001', 'c004_isolated_001')}
    rc = {k: {s: v.get(f'radiocarpal_{s}', {}).get('max_opening_mm', 0.0) for s in ('left', 'right')} for k, v in v2.items()}
    out['wrist_centre_gaps_closed'] = {'wjc_equals_radiocarpal_marker': gaps, 'radiocarpal_opening_mm': rc,
                                       'pass': all(gaps.values()) and all(x == 0.0 for x in rc['c004_isolated_001'].values()) and any(x > 1 for x in rc['c003_isolated_001'].values())}
    ja = {k: J(AU / f'joint_frame_audit/{k}.json')['motion']['tests'] for k in ('a003_isolated_014', 'c003_isolated_001', 'c004_isolated_001')}
    worst, mism, c3diff = 0.0, [], 0
    for t, v in ja['a003_isolated_014'].items():
        for j, x in v['joints_moving'].items():
            y = ja['c004_isolated_001'][t]['joints_moving'].get(j, {}); z = ja['c003_isolated_001'][t]['joints_moving'].get(j, {})
            if 'alignment_deg' in x:
                d = abs(x['alignment_deg'] - y.get('alignment_deg', 1e9)); worst = max(worst, d)
                if d > 1e-3 or x['follows_joint_axis'] != y.get('follows_joint_axis'):
                    mism.append([t, j])
                if abs(x['alignment_deg'] - z.get('alignment_deg', 1e9)) > 1e-3:
                    c3diff += 1
    rcmp = J(C4 / 'run_comparison.json')
    out['hand_thumb_axes_a003_convention'] = {'c004_vs_a003_worst_alignment_diff_deg': worst, 'mismatches': mism, 'c003_entries_differing_from_a003': c3diff,
                                              'changed_tests_reproducing_a003': len(rcmp['changed_vs_c003']) - len(rcmp['changed_not_reproducing_a003']),
                                              'changed_tests': len(rcmp['changed_vs_c003']),
                                              'pass': not mism and not rcmp['changed_not_reproducing_a003'] and c3diff > 0}
    keys = ('bones', 'joint_markers', 'landmarks_and_joint_centres', 'checks')
    out['shoulder_ansur_sc_unharmed'] = {'identical_to_c003': {k: r3[k] == r4[k] for k in keys},
                                         'acceptance_checks_identical': r3['candidate']['acceptance_checks'] == r4['candidate']['acceptance_checks'],
                                         'acceptance_summary': r4['candidate']['acceptance_checks'].get('summary')}
    out['shoulder_ansur_sc_unharmed']['pass'] = all(out['shoulder_ansur_sc_unharmed']['identical_to_c003'].values()) and out['shoulder_ansur_sc_unharmed']['acceptance_checks_identical']
    changed = set(rcmp['changed_vs_c003']); changed_pairs = {t.rsplit('_', 1)[0] for t in changed}
    J3 = lambda k: J(AU / k / 'c003_isolated_001.json'); J4 = lambda k: J(AU / k / 'c004_isolated_001.json'); JA = lambda k: J(AU / k / 'a003_isolated_014.json')
    num = lambda d: {k: v for k, v in d.items() if not k.startswith('worst_')}      # worst_* bone labels are tie-break names
    m3, m4 = J3('mirror_parity_scan'), J4('mirror_parity_scan')
    mirror_diff = sorted(p for p in m3['pairs'] if num(m3['pairs'][p]) != num(m4['pairs'][p]))
    mirror_label_only = sorted(p for p in m3['pairs'] if num(m3['pairs'][p]) == num(m4['pairs'][p]) and m3['pairs'][p] != m4['pairs'][p])
    f3, f4 = J3('frame_continuity_scan'), J4('frame_continuity_scan')
    cont_diff = sorted(t for t in f3['tests'] if f3['tests'][t] != f4['tests'][t])
    near = lambda d: {(n['test'], tuple(n['bones'])): n['min_mm'] for n in d['near_approaches_below_3mm_info_only']}
    n3, n4, na = near(J3('all_pairs_crossing_scan')), near(J4('all_pairs_crossing_scan')), near(JA('all_pairs_crossing_scan'))
    near_diff = sorted(k for k in set(n3) | set(n4) if n3.get(k) != n4.get(k))
    ap3, ap4 = J3('all_pairs_crossing_scan'), J4('all_pairs_crossing_scan')
    ap_other = sorted(k for k in set(ap3) | set(ap4) if k not in VOLATILE | {'near_approaches_below_3mm_info_only'} and ap3.get(k) != ap4.get(k))
    a1 = same_scan('joint_attachment_scan'); col = same_scan('movement_collision_scan')
    v2diff = sorted(j for j in set(v2['c003_isolated_001']) | set(v2['c004_isolated_001'])
                    if v2['c003_isolated_001'].get(j, {}).get('max_opening_mm') != v2['c004_isolated_001'].get(j, {}).get('max_opening_mm'))
    sr3, sr4 = J(AU / 'state_restoration_audit/c003.json'), J(AU / 'state_restoration_audit/c004.json')
    srk = lambda s: {n: {k: v for k, v in sc.items() if not k.endswith('sha256') and k != 'observed'} for n, sc in s['scenarios'].items()}
    out['unrelated_outputs_unchanged'] = {
        'tests_identical_to_c003': rcmp['identical_to_c003'], 'tests': rcmp['tests'],
        'mirror_pairs_numerically_differing': mirror_diff, 'mirror_pairs_differing_only_in_tie_label': mirror_label_only,
        'mirror_failures_c004': m4['pairs_failed'], 'mirror_rest_asymmetry_only_equal': m3['pairs_rest_asymmetry_only'] == m4['pairs_rest_asymmetry_only'],
        'continuity_tests_differing': cont_diff, 'continuity_issues_c004': f4['summary']['tests_with_issues'],
        'near_approaches_differing': [[k[0], list(k[1]), n3.get(k), n4.get(k), na.get(k)] for k in near_diff],
        'near_approaches_c004_equal_a003_where_changed': all(n4.get(k) == na.get(k) for k in near_diff),
        'all_pairs_other_keys_differing': ap_other, 'collision_keys_differing': col, 'attachment_v1_keys_differing': a1,
        'attachment_v2_articulations_differing': v2diff, 'state_restoration_equal_to_c003': srk(sr3) == srk(sr4)}
    u = out['unrelated_outputs_unchanged']
    u['pass'] = (u['tests_identical_to_c003'] == 111 and set(mirror_diff) <= changed_pairs and not m4['pairs_failed'] and u['mirror_rest_asymmetry_only_equal']
                 and set(cont_diff) <= changed and not f4['summary']['tests_with_issues'] and {k[0] for k in near_diff} <= changed
                 and u['near_approaches_c004_equal_a003_where_changed'] and not ap_other and not col and not a1
                 and set(v2diff) <= {'radiocarpal_left', 'radiocarpal_right'} and u['state_restoration_equal_to_c003'])
    sb = J(AU / 'solver_blender_agreement/c004_isolated_001.json')
    rt3, rt4 = J(C3 / 'roundtrip_report.json'), J(C4 / 'roundtrip_report.json')
    pins = {'a003_record': (A / 'character_fit_r95_a003.json', '11712ba3e105aa88'), 'a003_blend': (AU / 'HGPT_ANATOMICAL_AUDIT_r95_a003.blend', '670a37bfd206d702'),
            'c003_record': (C3 / 'candidate_record.json', '3eb4fa1e2f7d815e'), 'c003_blend': (BLEND, '3962215043cebbcf'),
            'c001_record': (AU / 'candidates/shoulder_proposal_c001/candidate_record.json', '08e9f2e1187dbeda'),
            'c002_record': (AU / 'candidates/shoulder_proposal_c002_ansur_height/candidate_record.json', 'aa344a6819dde763')}
    out['integrity'] = {'solver_agreement': sb['status'], 'round_trip_pass': rt4['roundtrip']['roundtrip_pass'], 'round_trip_equal_to_c003': rt3['roundtrip'] == rt4['roundtrip'],
                        'state_restoration_source_unchanged': all(s['source_sha256_unchanged'] for s in sr4['scenarios'].values()),
                        'sources_preserved': {k: sha(p).startswith(h) for k, (p, h) in pins.items()},
                        'isolated_counts': J(AU / 'runs/isolated_bone_only_c004_arm_inputs_001/isolated_report.json')['counts']}
    i = out['integrity']
    i['pass'] = i['solver_agreement'] == 'AGREE' and i['round_trip_pass'] and i['round_trip_equal_to_c003'] and i['state_restoration_source_unchanged'] and all(i['sources_preserved'].values())
    gr = g.check(ra, r4)
    out['guard'] = {'violation_keys': gr['violation_keys'], 'pass_in_scope': set(gr['violation_keys']) <= {'carpals', 'hand'},
                    'unresolved': 'carpals/hand skeleton_input points remain at a003 values (outside the six-point scope; read only by skeleton_fit.py)'}
    out['overall'] = 'C004_ARM_INPUT_RESYNC_CRITERIA_MET' if all(out[k]['pass'] for k in ('wrist_centre_gaps_closed', 'hand_thumb_axes_a003_convention', 'shoulder_ansur_sc_unharmed', 'unrelated_outputs_unchanged', 'integrity')) and out['guard']['pass_in_scope'] else 'C004_CRITERIA_NOT_MET'
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    r = run()
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'CANDIDATE_VALIDATION_SUMMARY_NOT_ACCEPTANCE',
                                       'candidate_status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED', **r}, indent=1) + '\n')
    print(json.dumps({k: (v.get('pass', v.get('pass_in_scope')) if isinstance(v, dict) else v) for k, v in r.items()}))
    print(json.dumps(r['unrelated_outputs_unchanged'])[:1500]); print(json.dumps(r['hand_thumb_axes_a003_convention'])[:400])


if __name__ == '__main__':
    main()
