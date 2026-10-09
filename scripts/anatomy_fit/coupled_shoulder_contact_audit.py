#!/usr/bin/env python3
"""Read-only relative-joint and scapulothoracic proxy audit for trunk proposals.

Checks preservation of already-present SC/AC/GH marker control relationships.
Only *relative changes* from c004 are checked, not anatomical truth.
Scapulothoracic proxy distance is from a marker to the 1–8 rib CONTROL
CHORDS, not an anatomical thorax surface and therefore is measurement-only.
"""
import argparse
import json
import math
from pathlib import Path


def _sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def _dist_mm(a, b):
    return 1000.0 * math.dist(a, b)


def _segment_dist(point, a, b):
    d = _sub(b, a)
    denom = sum(x*x for x in d)
    if denom < 1e-12:
        raise ValueError('zero-length rib control chord')
    projection = sum((point[k] - a[k]) * d[k] for k in range(3)) / denom
    t = max(0.0, min(1.0, projection))
    closest = [a[k] + t * d[k] for k in range(3)]
    return _dist_mm(point, closest)


def _rib_proxy(rec, side):
    marker = rec['joint_markers'][f'scapulothoracic_{side}']['centre_m']
    return min((_segment_dist(marker,
                              rec['bones'][f'rib_{n:02d}_{side}']['head_m'],
                              rec['bones'][f'rib_{n:02d}_{side}']['tail_m']),
                n)
               for n in range(1, 9))


def _reference_vector(rec, joint, bone, point):
    return _sub(rec['joint_markers'][joint]['centre_m'],
                rec['bones'][bone][f'{point}_m'])


def audit(base, candidate):
    B, P = base, candidate
    if set(B['bones']) != set(P['bones']) or set(B['joint_markers']) != set(P['joint_markers']):
        raise ValueError('bone/joint inventory changed')
    ids = set()
    changes = {}
    for side in ('left', 'right'):
        # Each vector is only a RELATIVE control registration check.
        for contact, bone, anchor in (
                ('sternoclavicular', 'sternum', 'head'),
                ('acromioclavicular', f'clavicle_{side}', 'tail'),
                ('acromioclavicular', f'scapula_{side}', 'head'),
                ('glenohumeral', f'scapula_{side}', 'head'),
                ('glenohumeral', f'humerus_{side}', 'head')):
            jid = f'{contact}_{side}'
            if not all(x in B['joint_markers'] and x in P['joint_markers'] for x in [jid]):
                raise ValueError('joint marker missing')
            label = f'{jid}:{bone}.{anchor}'
            before = _reference_vector(B, jid, bone, anchor)
            after = _reference_vector(P, jid, bone, anchor)
            changes[label] = round(_dist_mm(before, after), 6)
            ids.add(jid)

    # Engineering-only tests: a changed >=5 mm relative vector should
    # not be accidentally reported as an accepted mechanical closure.
    bad_markers = {k: v for k, v in changes.items() if v > 5.0}
    proxies = {}
    for side in ('left', 'right'):
        bdist, bnum = _rib_proxy(B, side)
        pdist, pnum = _rib_proxy(P, side)
        proxies[side] = {
            'baseline_nearest_rib_control': bnum,
            'candidate_nearest_rib_control': pnum,
            'baseline_marker_to_rib_chord_mm': round(bdist, 4),
            'candidate_marker_to_rib_chord_mm': round(pdist, 4),
            'proxy_distance_change_mm': round(pdist - bdist, 4),
        }

    # Markers alone cannot certify AC/GH/SC anatomy, and a rib chord is
    # not a physical scapulothoracic envelope.
    return {
        'schema_version': 1,
        'kind': 'RELATIVE_SHOULDER_KINEMATICS_DIAGNOSTIC',
        'joint_markers_checked': sorted(ids),
        'joint_reference_vector_change_mm': changes,
        'changes_over_engineering_5mm_guard': bad_markers,
        'scapulothoracic_rib_chord_proxy': proxies,
        'rig_control_closure': 'FAILED' if bad_markers else 'RELATIVE_CONTROL_VECTORS_PRESERVED',
        'anatomical_joint_surface_verified': False,
        'scapulothoracic_surface_verified': False,
        'canonical_promotion_allowed': False,
        'unverified': [
            'Sternum, SC, AC, GH articular surfaces and bone-specific joint frames',
            'Scapular gliding and ribcage curvature (rib control chords are not surfaces)',
            'Muscle lengths and appearance across overhead, pressing and weight-bearing exercises',
            'C7 thorax and living-skin landmark closure for a standing 1.82 m male',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    opts = parser.parse_args()
    r = audit(json.loads(opts.baseline.read_text()), json.loads(opts.proposal.read_text()))
    payload = json.dumps(r, indent=2) + '\n'
    if opts.out:
        with opts.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
