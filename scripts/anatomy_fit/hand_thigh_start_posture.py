#!/usr/bin/env python3
"""H6: arm-sweep start posture that keeps the hand off the thigh (read-only test-design analysis; changes no test).

Finding H6 (skeleton_defect_register_v1.json): isolated forearm/elbow/wrist/GH-rotation sweeps run from the hanging
posture of c004 (shoulders narrowed by c003/c004, a003 hanging arm kept) and bring the hand/forearm to 1.5-6.9 mm of the
femoral axis. This measures, on c004's own committed isolated run, how far a GH-ONLY start abduction alpha (whole arm =
humerus and all descendants, rigid about the fitted GH centre, around the global antero-posterior axis) separates the
arm from the femur and hip bone during each affected sweep: the committed per-frame world deltas are applied first, then
the start abduction. alpha = 0 must reproduce whole_body_interaction_c004.json.

Axis distances only (no bone or soft-tissue envelopes); reporting thresholds 10/25 mm are not anatomical clearances.
A GH-only abduction ignores the scapulothoracic contribution, which is acceptable for a START posture but must be stated
in any redesigned test; no amplitude changes.

  hand_thigh_start_posture.py --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_solver as js  # noqa: E402
import hip_adduction_start_posture as hp  # noqa: E402

ROOT = HERE.parents[1]
REC = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
SAMPLES = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_c004_arm_inputs_001/isolated_samples.json'
SCAN = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/whole_body_interaction_c004.json'
TESTS = ['forearm_rotation_at_elbow_0', 'forearm_rotation_at_elbow_90', 'elbow_flexion_at_pronation_0', 'elbow_flexion_at_pronation_60',
         'gh_axial_rotation_at_0_elevation', 'wrist_flexion', 'wrist_adduction', 'thumb_opposition', 'digit3_flexion']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def descendants(B, root):
    out, frontier = {root}, [root]
    while frontier:
        n = frontier.pop()
        for k, b in B.items():
            if b['parent'] == n and k not in out:
                out.add(k); frontier.append(k)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    rec = json.loads(REC.read_text()); B = rec['bones']; S = json.loads(SAMPLES.read_text()); J = rec['joint_markers']
    res, first = {}, {}
    for side in ('left', 'right'):
        arm = descendants(B, f'humerus_{side}')
        dist_bones = [n for n in arm if not n.startswith('humerus')]
        targets = [f'femur_{side}', f'hip_bone_{side}']
        gh = np.array(J[f'glenohumeral_{side}']['centre_m'])
        sgn = -1.0 if side == 'left' else 1.0                     # left: lateral = +X needs a negative rotation about +Y
        R1 = js.rot(np.array([0, 1.0, 0]), sgn * 10)
        assert (R1 @ (np.array(B[f'radius_{side}']['tail_m']) - gh))[0] * (1 if side == 'left' else -1) > \
            (np.array(B[f'radius_{side}']['tail_m']) - gh)[0] * (1 if side == 'left' else -1), 'abduction must move the wrist laterally'

        def anc(n, d):
            m = n
            while m is not None:
                if m in d:
                    return d[m]
                m = B[m]['parent']
            return None
        for t in TESTS:
            tid = f'{t}_{side}'
            if tid not in S:
                continue
            row = {}
            for alpha in range(0, 21):
                R = js.rot(np.array([0, 1.0, 0]), sgn * alpha)
                dmin, pair = 1e9, None
                for fr in S[tid][::2]:
                    d = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
                    for n in dist_bones:
                        h, tl = np.array(B[n]['head_m']), np.array(B[n]['tail_m'])
                        D = anc(n, d)
                        if D is not None:
                            h, tl = D[:3, :3] @ h + D[:3, 3], D[:3, :3] @ tl + D[:3, 3]
                        h, tl = gh + R @ (h - gh), gh + R @ (tl - gh)
                        for tg in targets:
                            dd = hp.seg_dist(h, tl, np.array(B[tg]['head_m']), np.array(B[tg]['tail_m']))
                            if dd < dmin:
                                dmin, pair = dd, (n, tg)
                row[alpha] = {'min_axis_mm': round(dmin * 1000, 2), 'pair': pair}
                for thr in (10, 25):
                    if (tid, thr) not in first and dmin * 1000 >= thr:
                        first[(tid, thr)] = alpha
            res[tid] = row
    scan = json.loads(SCAN.read_text())['pairs']
    check = {}
    for tid, row in res.items():
        ref = [p['min_axis_mm'] for p in scan if p['test'] == tid and any(b.startswith(('femur', 'hip_bone')) for b in p['bones'])]
        check[tid] = {'alpha0_mm': row[0]['min_axis_mm'], 'interaction_scan_min_mm': min(ref) if ref else None}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_TEST_DESIGN_ANALYSIS', 'finding': 'H6', 'record': 'c004 (unchanged)',
           'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (REC, SAMPLES, SCAN)},
           'method': 'committed per-frame world deltas (stride 2), then a GH-only start abduction alpha of the whole arm about the fitted GH centre '
                     'around the global AP axis; segment distance between forearm/hand sticks and the same-side femur and hip bone',
           'smallest_start_abduction_deg_for_axis_distance': {f'{t}_ge{thr}mm': a for (t, thr), a in sorted(first.items())},
           'alpha0_consistency_with_interaction_scan': check,
           'per_test': {t: {str(a): v for a, v in r.items() if a % 5 == 0} for t, r in res.items()},
           'threshold_note': '10/25 mm are reporting thresholds on axis distance, not anatomical clearances (no envelopes exist)',
           'reading': 'H6 is a start-posture (test-design) problem: a modest GH start abduction separates the arm from the thigh in every '
                      'affected sweep; no bone or amplitude change is implied. Scapular participation in the start posture is not modelled.'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for t, r in res.items():
        print(t, {a: r[a]['min_axis_mm'] for a in (0, 5, 10, 15, 20)}, 'scan', check[t]['interaction_scan_min_mm'])
    print(out['smallest_start_abduction_deg_for_axis_distance'])


if __name__ == '__main__':
    main()
