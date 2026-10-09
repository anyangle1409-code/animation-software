#!/usr/bin/env python3
"""Read-only nearest-control-axis clearance between distal arms and thighs.

This is a diagnostic for NEUTRAL POSE and the straight rig controls.
It is not a collision checker for anatomical bones, fat, muscles, hands,
equipment or any animated frame. No clinically sourced contact tolerance
is asserted. Zero axis distance means controls cross, not necessarily
that real body surfaces penetrate; positive separation is no guarantee
that soft-tissue surfaces do not intersect.
"""
import argparse
import json
import math
from pathlib import Path


def _sub(a, b):
    return [a[k] - b[k] for k in range(3)]


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def segment_distance_m(p1, q1, p2, q2):
    """Robust clamped segment/segment distance (closest points in [0,1])."""
    u = _sub(q1, p1)
    v = _sub(q2, p2)
    w = _sub(p1, p2)
    a = _dot(u, u)
    b = _dot(u, v)
    c = _dot(v, v)
    d = _dot(u, w)
    e = _dot(v, w)
    determinant = a*c - b*b
    eps = 1e-12
    if a < eps and c < eps:
        return math.dist(p1, p2)
    if a < eps:
        s = 0.0
        t = max(0.0, min(1.0, e/c))
    elif c < eps:
        t = 0.0
        s = max(0.0, min(1.0, -d/a))
    else:
        # Parallel/near-parallel robustly initialized at one endpoint.
        s = max(0.0, min(1.0, (b*e-c*d)/determinant)) if determinant > eps else 0.0
        t = (b*s + e)/c
        if t < 0:
            t = 0.0
            s = max(0.0, min(1.0, -d/a))
        elif t > 1:
            t = 1.0
            s = max(0.0, min(1.0, (b-d)/a))
    closest = _sub([p1[k] + s*u[k] for k in range(3)],
                   [p2[k] + t*v[k] for k in range(3)])
    return math.sqrt(_dot(closest, closest))


def _ids(bones, side):
    # Include true distal-arm control bones, not the shoulder joints.
    candidates = [
        f'ulna_{side}', f'radius_{side}',
        f'metacarpal_1_{side}', f'metacarpal_2_{side}',
        f'metacarpal_3_{side}', f'metacarpal_4_{side}',
        f'metacarpal_5_{side}',
        f'digit2_proximal_phalanx_{side}', f'digit3_proximal_phalanx_{side}',
        f'digit4_proximal_phalanx_{side}', f'digit5_proximal_phalanx_{side}'
    ]
    required = {f'ulna_{side}', f'radius_{side}', f'metacarpal_2_{side}'}
    if not required <= set(bones):
        raise ValueError('missing mandatory forearm/hand controls')
    return [k for k in candidates if k in bones]


def _distance_bones(b1, b2):
    return 1000 * segment_distance_m(
        b1['head_m'], b1['tail_m'], b2['head_m'], b2['tail_m'])


def measure(record):
    bones = record['bones']
    all_rows = []
    for arm_side in ('left', 'right'):
        for arm_bone in _ids(bones, arm_side):
            for thigh_side in ('left', 'right'):
                femur = f'femur_{thigh_side}'
                if femur not in bones:
                    raise ValueError('missing femur control')
                all_rows.append({
                    'arm_bone': arm_bone,
                    'femur': femur,
                    'distance_mm': round(_distance_bones(bones[arm_bone], bones[femur]), 6),
                })
    all_rows.sort(key=lambda r: (r['distance_mm'], r['arm_bone'], r['femur']))
    return {'min_axis_distance_mm': all_rows[0]['distance_mm'],
            'nearest_pair': all_rows[0], 'pairs': all_rows}


def audit(baseline, candidate):
    if set(baseline['bones']) != set(candidate['bones']):
        raise ValueError('bone inventory changed')
    original = measure(baseline)
    proposed = measure(candidate)
    prior = {(r['arm_bone'], r['femur']): r['distance_mm'] for r in original['pairs']}
    changes = []
    for row in proposed['pairs']:
        old = prior[(row['arm_bone'], row['femur'])]
        changes.append({
            **row, 'baseline_distance_mm': old,
            'distance_change_mm': round(row['distance_mm'] - old, 6)
        })
    changes.sort(key=lambda r: (r['distance_change_mm'], r['arm_bone'], r['femur']))
    largest_reduction = changes[0]
    # A reference decrease >10 mm triggers extra review, NOT an anatomical
    # "penetration" diagnosis. Straight bone-control axes do not model skin.
    review_required = largest_reduction['distance_change_mm'] < -10
    return {
        'schema_version': 1,
        'kind': 'NEUTRAL_POSE_ARM_TO_THIGH_CONTROL_AXIS_DIAGNOSTIC',
        'baseline_min_axis_separation_mm': original['min_axis_distance_mm'],
        'candidate_min_axis_separation_mm': proposed['min_axis_distance_mm'],
        'baseline_nearest_pair': original['nearest_pair'],
        'candidate_nearest_pair': proposed['nearest_pair'],
        'largest_clearance_decrease': largest_reduction,
        'clearance_change_over_engineering_10mm_review_guard': review_required,
        'axis_collision_proven': False,
        'anatomical_surface_collision_verified': False,
        'dynamic_motion_verified': False,
        'clinical_clearance_threshold_established': False,
        'canonical_promotion_allowed': False,
        'no_evidence_of_clearance_error_is_not_proof_of_no_collision': True,
        'unverified': [
            'True radius of upper-limb, thigh and hand soft-tissue envelopes',
            'Equipment/ground interactions and active joint poses',
            'Loaded exercise extremes and joint-angle source correctness'
        ]
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--out', type=Path)
    o = p.parse_args()
    r = audit(json.loads(o.baseline.read_text()), json.loads(o.proposal.read_text()))
    result = json.dumps(r, indent=2) + '\n'
    if o.out:
        with o.out.open('x', encoding='utf-8') as f:
            f.write(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
