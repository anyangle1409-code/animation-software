#!/usr/bin/env python3
"""c004 correction table, hashes and causality proof (pure Python, read-only).

1. Record diff c003 -> c004: every changed JSON leaf path (must be the 12 corrected points + the 'candidate' block).
2. Derived test frames (isolated_tests.frames): for arm-distal segments (radius, ulna, carpals, metacarpals, phalanges)
   c004 must equal a003 (the arm moved by pure translation, so orientations must match a003) while c003 does not;
   every other segment must be identical between c003 and c004.
3. Test specs (isolated_tests.specs): which tests change c003 -> c004; for wrist tests the centre must now be the
   radiocarpal marker; every other spec must be identical.
4. Visual inputs for the render pack: bones, joint_markers, candidate scapula landmarks and the TS/AA/AI inputs the
   renderer reads are hashed for c003 and c004 (must be identical), plus the reused c003 blend hash.

  c004_causality.py --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isolated_tests as it  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
P = {'a003': ANAT / 'character_fit_r95_a003.json',
     'c003': ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json',
     'c004': ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'}
BLEND = ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'
ARM_DISTAL = ('radius', 'ulna', 'scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate',
              'metacarpal', 'digit', 'thumb')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()


def leaves(x, path=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f'{path}/{k}')
    elif isinstance(x, list) and x and all(isinstance(v, (int, float)) for v in x):
        yield path, x
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f'{path}[{i}]')
    else:
        yield path, x


def frame_angle(A, B):
    R = A.T @ B
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return float(np.degrees(np.arctan2(np.linalg.norm(w) / 2, (np.trace(R) - 1) / 2)))


def run():
    R = {k: json.loads(p.read_text()) for k, p in P.items()}
    atlas = json.loads((ANAT / 'whole_body_movement_atlas.json').read_text())
    l3 = dict(leaves({k: v for k, v in R['c003'].items() if k != 'candidate'}))
    l4 = dict(leaves({k: v for k, v in R['c004'].items() if k != 'candidate'}))
    changed = sorted(p for p in set(l3) | set(l4) if l3.get(p) != l4.get(p))
    F = {k: it.frames(R[k]) for k in R}
    arm = lambda n: any(n.startswith(p) for p in ARM_DISTAL) and n.endswith(('_left', '_right'))
    fr = {'arm_distal_segments': 0, 'c004_vs_a003_max_deg': 0.0, 'c003_vs_a003_max_deg': 0.0, 'other_segments_c003_vs_c004_max_deg': 0.0, 'other_segments': 0}
    worst_c003 = None
    for n in F['a003']:
        if n == 'world':
            continue
        if arm(n):
            fr['arm_distal_segments'] += 1
            fr['c004_vs_a003_max_deg'] = max(fr['c004_vs_a003_max_deg'], frame_angle(F['a003'][n], F['c004'][n]))
            d3 = frame_angle(F['a003'][n], F['c003'][n])
            if d3 > fr['c003_vs_a003_max_deg']:
                fr['c003_vs_a003_max_deg'] = d3; worst_c003 = n
        else:
            fr['other_segments'] += 1
            fr['other_segments_c003_vs_c004_max_deg'] = max(fr['other_segments_c003_vs_c004_max_deg'], frame_angle(F['c003'][n], F['c004'][n]))
    fr['c003_worst_segment'] = worst_c003
    S = {k: {t['id']: t for t in it.specs(R[k], atlas)} for k in ('c003', 'c004')}
    spec_changed = sorted(t for t in S['c003'] if digest(S['c003'][t]) != digest(S['c004'][t]))
    wrist = {}
    for t in spec_changed:
        sp = S['c004'][t]
        if 'centre' in sp and t.startswith('wrist'):
            side = sp['side']; mk = np.asarray(R['c004']['joint_markers'][f'radiocarpal_{side}']['centre_m'])
            wrist[t] = {'c003_centre_to_radiocarpal_mm': round(float(np.linalg.norm(np.asarray(S['c003'][t]['centre']) - mk)) * 1000, 3),
                        'c004_centre_to_radiocarpal_mm': round(float(np.linalg.norm(np.asarray(sp['centre']) - mk)) * 1000, 6)}
    vis = lambda r: {'bones': digest(r['bones']), 'joint_markers': digest(r['joint_markers']),
                     'scapula_landmarks': digest(r['candidate']['scapula_landmarks_world_mm']),
                     'renderer_inputs_TS_AA_AI': digest({s: {k: r['skeleton_input']['sides'][s][k] for k in ('TS', 'AA', 'AI')} for s in ('left', 'right')})}
    v3, v4 = vis(R['c003']), vis(R['c004'])
    return {'hashes': {k: sha(p) for k, p in P.items()}, 'reused_blend': {'path': str(BLEND.relative_to(ROOT)), 'sha256': sha(BLEND)},
            'correction_table': R['c004']['candidate']['arm_input_correction']['table'],
            'record_diff_c003_to_c004_excluding_candidate': changed,
            'derived_frames': fr,
            'specs': {'tests': len(S['c004']), 'changed_c003_to_c004': spec_changed, 'wrist_centres': wrist},
            'visual_inputs': {'c003': v3, 'c004': v4, 'identical': v3 == v4},
            'acceptance_checks_identical_to_c003': digest(R['c003']['candidate']['acceptance_checks']) == digest(R['c004']['candidate']['acceptance_checks'])}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    r = run()
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'CAUSALITY_PROOF_READ_ONLY', **r}, indent=1) + '\n')
    print(json.dumps({k: r[k] for k in ('record_diff_c003_to_c004_excluding_candidate', 'derived_frames', 'specs', 'acceptance_checks_identical_to_c003')}, indent=0)[:3000])
    print('visual identical', r['visual_inputs']['identical'])


if __name__ == '__main__':
    main()
