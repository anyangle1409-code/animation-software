#!/usr/bin/env python3
"""Compare the c004 Phase 9 run with c003 (same geometry) and a003 (same arm orientation) per test (read-only).

Per test: whether every recorded value is IDENTICAL to c003 (exact equality, the expectation for tests whose spec did not
change); for changed tests, the max rotation-part difference of every commanded-bone delta and of every measured angle
channel against c003 and against a003. The arm moved by a pure translation from a003, so for arm tests c004's rotations and
measured angles should reproduce a003's (float32 bound 1e-5 for matrices, 1.7e-3 deg for angles, as in
solver_blender_agreement); translations legitimately differ (pivot moved with the arm).

  c004_run_comparison.py --out JSON
"""
import argparse, hashlib, json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
S = {'a003': RUNS / 'isolated_bone_only_014/isolated_samples.json', 'c003': RUNS / 'isolated_bone_only_c003_shoulder_thorax_001/isolated_samples.json',
     'c004': RUNS / 'isolated_bone_only_c004_arm_inputs_001/isolated_samples.json'}
REP = {k: p.parent / 'isolated_report.json' for k, p in S.items()}
T_BOUND, A_BOUND = 1e-5, math.degrees(3e-5)
SKIP = {'frame', 'time_s', 'commanded', 'moving_deltas', 'moving_delta'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def compare(x, y):
    rot = ang = 0.0
    for fx, fy in zip(x, y):
        for b, M in fx['moving_deltas'].items():
            rot = max(rot, float(np.abs(np.asarray(M)[:3, :3] - np.asarray(fy['moving_deltas'][b])[:3, :3]).max()))
        for k, v in fx.items():
            if k in SKIP or k.endswith('_m') or isinstance(v, bool) or not isinstance(v, (int, float)) or not isinstance(fy.get(k), (int, float)):
                continue
            if k in ('plane_of_elevation', 'gh_plane') and fx.get('elevation', 90) < 1:
                continue
            ang = max(ang, abs(v - fy[k]))
    return rot, ang


def run():
    D = {k: json.loads(p.read_text()) for k, p in S.items()}
    tests, same, changed = {}, [], []
    for t in sorted(D['c004']):
        if D['c004'][t] == D['c003'][t]:
            same.append(t); continue
        r3, a3 = compare(D['c004'][t], D['c003'][t]); ra, aa = compare(D['c004'][t], D['a003'][t])
        tests[t] = {'vs_c003': {'rotation_max_abs': r3, 'angle_max_deg': a3}, 'vs_a003': {'rotation_max_abs': ra, 'angle_max_deg': aa},
                    'reproduces_a003_rotations_and_angles': ra <= T_BOUND and aa <= A_BOUND}
        changed.append(t)
    reps = {k: json.loads(p.read_text()) for k, p in REP.items()}
    summ = {k: {'counts': reps[k]['counts'], 'mirror_pass': [m for m, v in reps[k]['mirror'].items() if isinstance(v, dict) and v.get('status') == 'PASS'].__len__()} for k in reps}
    return {'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in list(S.values()) + list(REP.values())},
            'tests': len(D['c004']), 'identical_to_c003': len(same), 'changed_vs_c003': changed, 'changed_detail': tests,
            'changed_not_reproducing_a003': sorted(t for t, v in tests.items() if not v['reproduces_a003_rotations_and_angles']),
            'report_counts': summ}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    r = run()
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'RUN_COMPARISON_READ_ONLY', **r}, indent=1) + '\n')
    print({k: r[k] for k in ('tests', 'identical_to_c003', 'changed_not_reproducing_a003', 'report_counts')})
    for t, v in r['changed_detail'].items():
        print(' ', t, {k: {kk: float(f'{vv:.3g}') for kk, vv in x.items()} for k, x in v.items() if isinstance(x, dict)})


if __name__ == '__main__':
    main()
