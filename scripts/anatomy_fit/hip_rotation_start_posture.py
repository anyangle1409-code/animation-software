#!/usr/bin/env python3
"""L7: hip-rotation sweep start posture that keeps the moving foot off the stationary foot (read-only test-design analysis).

Finding L7 (skeleton_defect_register_v1.json): hip_rotation_at_0_flexion runs from c004 standing with the feet at their
rest stance; internal rotation swings the moving forefoot medially until its hallux reaches the opposite first metatarsal
(1.40 / 1.74 mm bone-axis distance). This measures, on c004's committed isolated run, how far a contralateral start
ABDUCTION beta (whole stationary limb, rigid about its HJC, around the global antero-posterior axis) separates the two
limbs during each hip-rotation sweep: the moving limb uses the committed per-frame world deltas, the stationary limb is
only rotated by beta. beta = 0 must reproduce whole_body_interaction_c004.json.

Bone-axis distances only (no bone or soft-tissue envelopes); 10/25 mm are reporting thresholds, not anatomical clearances.

  hip_rotation_start_posture.py --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_solver as js  # noqa: E402
import hip_adduction_start_posture as hp  # noqa: E402
import hand_thigh_start_posture as ht  # noqa: E402

ROOT = HERE.parents[1]
REC, SAMPLES, SCAN = ht.REC, ht.SAMPLES, ht.SCAN
TESTS = ['hip_rotation_at_0_flexion', 'hip_rotation_at_90_flexion']


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    rec = json.loads(REC.read_text()); B = rec['bones']; S = json.loads(SAMPLES.read_text())
    res, first = {}, {}
    for side in ('left', 'right'):
        other = 'right' if side == 'left' else 'left'
        mov = ht.descendants(B, f'femur_{side}'); sta = ht.descendants(B, f'femur_{other}')
        hjc = np.array(B[f'femur_{other}']['head_m'])
        sgn = -1.0 if other == 'left' else 1.0                 # abduction of the stationary limb moves its foot laterally
        R1 = js.rot(np.array([0, 1.0, 0]), sgn * 10)
        foot = np.array(B[f'tibia_{other}']['tail_m']) - hjc
        lat = 1.0 if other == 'left' else -1.0
        assert (R1 @ foot)[0] * lat > foot[0] * lat, 'contralateral abduction must move the stationary ankle laterally'

        def anc(n, d):
            m = n
            while m is not None:
                if m in d:
                    return d[m]
                m = B[m]['parent']
            return None
        for t in TESTS:
            tid = f'{t}_{side}'
            row = {}
            for beta in range(0, 21):
                R = js.rot(np.array([0, 1.0, 0]), sgn * beta)
                st = {n: (hjc + R @ (np.array(B[n]['head_m']) - hjc), hjc + R @ (np.array(B[n]['tail_m']) - hjc)) for n in sta}
                dmin, pair = 1e9, None
                for fr in S[tid][::2]:
                    d = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
                    for n in mov:
                        h, tl = np.array(B[n]['head_m']), np.array(B[n]['tail_m'])
                        D = anc(n, d)
                        if D is not None:
                            h, tl = D[:3, :3] @ h + D[:3, 3], D[:3, :3] @ tl + D[:3, 3]
                        for m, (a, b) in st.items():
                            dd = hp.seg_dist(h, tl, a, b)
                            if dd < dmin:
                                dmin, pair = dd, (n, m)
                row[beta] = {'min_axis_mm': round(dmin * 1000, 2), 'pair': pair}
                for thr in (10, 25):
                    if (tid, thr) not in first and dmin * 1000 >= thr:
                        first[(tid, thr)] = beta
            res[tid] = row
    scan = json.loads(SCAN.read_text())['pairs']
    check = {}
    for tid, row in res.items():
        side = tid.rsplit('_', 1)[1]; other = 'right' if side == 'left' else 'left'
        ref = [p['min_axis_mm'] for p in scan if p['test'] == tid and any(b.endswith('_' + other) for b in p['bones'])
               and any(b.endswith('_' + side) for b in p['bones'])]
        check[tid] = {'beta0_mm': row[0]['min_axis_mm'], 'interaction_scan_min_mm': min(ref) if ref else None}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_TEST_DESIGN_ANALYSIS', 'finding': 'L7', 'record': 'c004 (unchanged)',
           'inputs_sha256': {str(p.relative_to(ROOT)): ht.sha(p) for p in (REC, SAMPLES, SCAN)},
           'method': 'moving limb: committed per-frame world deltas (stride 2); stationary limb: rigid start abduction beta about its HJC around the '
                     'global AP axis; segment distance between all bone sticks of the two limbs',
           'smallest_contralateral_abduction_deg_for_axis_distance': {f'{t}_ge{thr}mm': b for (t, thr), b in sorted(first.items())},
           'beta0_consistency_with_interaction_scan': check,
           'per_test': {t: {str(b): v for b, v in r.items() if b % 5 == 0} for t, r in res.items()},
           'threshold_note': '10/25 mm are reporting thresholds on bone-axis distance, not anatomical clearances (no envelopes exist)',
           'reading': 'L7 is a start-posture (test-design) problem of the feet-at-rest stance: a contralateral start abduction separates the feet '
                      'during internal rotation; no bone or amplitude change is implied. A wider stance is an alternative not evaluated here.'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for t, r in res.items():
        print(t, {b: r[b]['min_axis_mm'] for b in (0, 5, 10, 15, 20)}, 'scan', check[t]['interaction_scan_min_mm'], r[0]['pair'])
    print(out['smallest_contralateral_abduction_deg_for_axis_distance'])


if __name__ == '__main__':
    main()
