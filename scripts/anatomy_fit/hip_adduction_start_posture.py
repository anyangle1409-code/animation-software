#!/usr/bin/env python3
"""Hip adduction test start posture (read-only; changes no test).

Finding L4: the isolated 'hip abduction/adduction' sweep adducts one leg 20 deg from neutral standing while the other
leg stays vertical, so the moving tibia and foot pass through the stationary leg. That is a test-design problem: an
adduction range cannot be expressed from neutral standing without moving the other limb out of the way (clinical
goniometry abducts or flexes the contralateral limb for this reason).

This measures, on c004's own bone sticks (axes only; bone radii and soft tissue are NOT included), the minimum
axis-to-axis distance between the two lower limbs when the moving leg (whole limb rigid about its HJC, adduction about
the global AP axis) is adducted 0-20 deg and the contralateral leg is abducted by 0-20 deg. It reports the smallest
contralateral abduction that keeps the axes apart, plus the clearance margin at each combination, so a redesigned test
can choose its start posture from data. A positive axis distance is necessary, not sufficient: real bones and soft tissue
need more room.

  hip_adduction_start_posture.py --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_solver as js  # noqa: E402

ROOT = HERE.parents[1]
C004 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
LEG = ('femur', 'patella', 'tibia', 'fibula', 'talus', 'calcaneus', 'navicular', 'cuboid', 'cuneiform', 'metatarsal', 'hallux', 'toe', 'digit')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg_dist(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    c, b = d1 @ r, d1 @ d2
    den = a * e - b * b
    s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-18 else 0.0
    t = (b * s + f) / e
    if t < 0:
        t, s = 0.0, np.clip(-c / a, 0, 1)
    elif t > 1:
        t, s = 1.0, np.clip((b - c) / a, 0, 1)
    return float(np.linalg.norm((p1 + s * d1) - (p2 + t * d2)))


def leg_bones(B, side):
    return [k for k in B if k.endswith('_' + side) and any(k.startswith(p) for p in LEG)]


def posed(B, side, hjc, deg):
    """Rigid limb rotation about the global AP (+Y) axis through HJC; positive deg = toward the midline (adduction)."""
    R = js.rot(np.array([0, 1.0, 0]), deg if side == 'left' else -deg)
    out = {}
    for k in leg_bones(B, side):
        out[k] = [hjc + R @ (np.array(B[k][e]) - hjc) for e in ('head_m', 'tail_m')]
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    B = json.loads(C004.read_text())['bones']
    hl, hr = np.array(B['femur_left']['head_m']), np.array(B['femur_right']['head_m'])
    # sign check: adduction of the left leg must move the left ankle toward -X
    t = posed(B, 'left', hl, 10)['tibia_left'][1]
    assert t[0] < B['tibia_left']['tail_m'][0], 'left adduction sign'
    t = posed(B, 'right', hr, -10)['tibia_right'][1]
    assert t[0] < B['tibia_right']['tail_m'][0], 'right abduction sign (moves away from the midline, -X)'
    grid = {}
    first_clear = {}
    for add in (0, 5, 10, 15, 20):
        L = posed(B, 'left', hl, add)
        for abd in range(0, 21, 1):
            Rr = posed(B, 'right', hr, -abd)
            dmin, pair = 1e9, None
            for kl, (a, b) in L.items():
                for kr, (c, d) in Rr.items():
                    dd = seg_dist(a, b, c, d)
                    if dd < dmin:
                        dmin, pair = dd, (kl, kr)
            grid[f'add{add}_contra_abd{abd}'] = {'min_axis_distance_mm': round(dmin * 1000, 2), 'closest_pair': pair}
            for thr in (10, 25, 50):
                if (add, thr) not in first_clear and dmin * 1000 >= thr:
                    first_clear[(add, thr)] = abd
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_TEST_DESIGN_ANALYSIS', 'finding': 'L4',
           'inputs_sha256': {str(C004.relative_to(ROOT)): sha(C004)},
           'method': 'rigid whole-limb rotation about each HJC around the global AP axis; segment-segment distance between all leg '
                     'bone sticks of the two sides; axis distance only (no bone radius, no soft tissue)',
           'neutral_min_axis_distance_mm': grid['add0_contra_abd0']['min_axis_distance_mm'],
           'smallest_contralateral_abduction_deg_for_axis_distance': {f'add{a}_ge{t}mm': v for (a, t), v in sorted(first_clear.items())},
           'threshold_note': '10/25/50 mm are reporting thresholds on axis distance, not anatomical clearances',
           'at_20_deg_adduction': {k: v for k, v in grid.items() if k.startswith('add20_')},
           'grid': grid,
           'reading': 'Axis separation is necessary but not sufficient. The redesigned test should abduct (or flex) the contralateral '
                      'hip by at least the reported angle plus a bone/soft-tissue margin chosen from envelope geometry once the '
                      'lower-limb envelopes exist; no amplitude change is proposed.'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print('neutral', out['neutral_min_axis_distance_mm'], 'first clear', first_clear)
    print({k: (v['min_axis_distance_mm'], v['closest_pair']) for k, v in out['at_20_deg_adduction'].items() if int(k.split('abd')[1]) % 5 == 0})


if __name__ == '__main__':
    main()
