#!/usr/bin/env python3
"""Independent 3D RIB/CARTILAGE-CORRIDOR correspondence audit for P004/P005.

Mechanical regression diagnostic only. A marker-to-control vector, rib
head-to-vertebral-level vector or rib-stick-to-sternocostal-marker corridor
is NOT a bone surface, anatomical contact/clearance, nor cartilage length.
Always refuse anatomical or production acceptance.

Unlike coupled_trunk_preflight.py's historical Z-level guard, this uses all
three axes and explicitly checks both costovertebral and costotransverse
marker offsets for 24 ribs, and the rib-to-sternum endpoint proxy for the
first seven rib pairs. Values are compared to the frozen baseline, NOT to
fabricated clinical norms. 5mm is only an engineering change review trigger.

Do not rely on proposer-set metadata to claim that marks 'follow' a bone:
the geometric changes are derived independently from the actual coordinates.
"""
import argparse
import json
import math
from pathlib import Path

REFERENCE_CHANGE_GUARD_MM = 5.0
RIB_LENGTH_CHANGE_GUARD_MM = 1.0  # engineering, NOT biological variation


def _vec(v):
    return isinstance(v, list) and len(v) == 3 and all(
        type(x) in (int, float) and math.isfinite(x) for x in v)


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _norm_mm(v):
    return math.sqrt(sum(x*x for x in v)) * 1000


def _centre(b):
    return [(x + y)/2 for x, y in zip(b['head_m'], b['tail_m'])]


def level(bones, i):
    """Independent implementation of documented project costovertebral map."""
    if i == 1 or i >= 10:
        return _centre(bones[f't{i}'])
    lower, upper = bones[f't{i}'], bones[f't{i-1}']
    return [(a+b)/2 for a,b in zip(lower['tail_m'], upper['head_m'])]


def measured(record):
    bones = record.get('bones')
    markers = record.get('joint_markers')
    if not isinstance(bones, dict) or not isinstance(markers, dict):
        raise ValueError('bones and joint_markers dictionaries required')
    rows = {}
    for i in range(1, 13):
        anchor = level(bones, i)
        if not _vec(anchor):
            raise ValueError('invalid rib vertebral attachment level')
        for side in ('left', 'right'):
            bid = f'rib_{i:02d}_{side}'
            rib = bones[bid]
            h, t = rib['head_m'], rib['tail_m']
            if not _vec(h) or not _vec(t):
                raise ValueError(f'invalid rib endpoints {bid}')
            row = {
                'rib_head_minus_vertebral_level_m': _sub(h, anchor),
                'rib_length_mm': _norm_mm(_sub(t, h)),
                'marker_minus_rib_head_m': {},
            }
            for kind in ('costovertebral', 'costotransverse'):
                jid = f'{kind}_{i:02d}_{side}'
                m = markers[jid]
                pos = m.get('centre_m')
                if not _vec(pos):
                    raise ValueError(f'invalid {jid} centre')
                if m.get('frame_bone') != bid:
                    raise ValueError(f'incorrect {jid} frame bone')
                row['marker_minus_rib_head_m'][kind] = _sub(pos, h)
            if i <= 7:
                jid = f'sternocostal_{i:02d}_{side}'
                m = markers[jid]
                pos = m.get('centre_m')
                if not _vec(pos) or m.get('frame_bone') != 'sternum':
                    raise ValueError(f'{jid} does not reference sternum or has invalid centre')
                # Diagnostic rib-stick endpoint to recorded sternal marker
                # vector, NOT anatomical cartilage shape or real cartilage.
                row['rib_tail_to_sternocostal_marker_vector_m'] = _sub(pos, t)
                row['rib_tail_to_sternocostal_marker_distance_mm'] = _norm_mm(_sub(pos, t))
            rows[bid] = row
    return rows


def audit(baseline, proposed):
    if set(baseline['bones']) != set(proposed['bones']):
        raise ValueError('bone inventory differs')
    if set(baseline['joint_markers']) != set(proposed['joint_markers']):
        raise ValueError('joint marker inventory differs')
    original, new = measured(baseline), measured(proposed)
    rib_changes, marker_changes, sternocostal_changes, rib_length_changes = {}, {}, {}, {}
    for bid, b in original.items():
        p = new[bid]
        rib_changes[bid] = round(_norm_mm(_sub(
            p['rib_head_minus_vertebral_level_m'],
            b['rib_head_minus_vertebral_level_m'])), 6)
        rib_length_changes[bid] = round(abs(p['rib_length_mm'] - b['rib_length_mm']), 6)
        for kind, bvec in b['marker_minus_rib_head_m'].items():
            pvec = p['marker_minus_rib_head_m'][kind]
            marker_changes[f'{kind}:{bid}'] = round(_norm_mm(_sub(pvec, bvec)), 6)
        if 'rib_tail_to_sternocostal_marker_vector_m' in b:
            sternocostal_changes[bid] = {
                'vector_change_mm': round(_norm_mm(_sub(
                    p['rib_tail_to_sternocostal_marker_vector_m'],
                    b['rib_tail_to_sternocostal_marker_vector_m'])), 6),
                'length_proxy_change_mm': round(
                    p['rib_tail_to_sternocostal_marker_distance_mm'] -
                    b['rib_tail_to_sternocostal_marker_distance_mm'], 6),
            }
    rib_review = {k: v for k,v in rib_changes.items() if v > REFERENCE_CHANGE_GUARD_MM}
    marker_review = {k: v for k,v in marker_changes.items() if v > REFERENCE_CHANGE_GUARD_MM}
    sternum_review = {k: v for k,v in sternocostal_changes.items()
                      if v['vector_change_mm'] > REFERENCE_CHANGE_GUARD_MM}
    length_review = {k: v for k,v in rib_length_changes.items()
                     if v > RIB_LENGTH_CHANGE_GUARD_MM}
    blockers = []
    if rib_review:
        blockers.append('RIB_VERTEBRAL_ANCHOR_3D_VECTOR_CHANGED')
    if marker_review:
        blockers.append('RIB_COSTOVERTEBRAL_TRANSVERSE_MARKER_DRIFT')
    if sternum_review:
        blockers.append('STERNOCOSTAL_CORRIDOR_VECTOR_CHANGED')
    if length_review:
        blockers.append('RIB_CONTROL_LENGTH_CHANGED')
    return {
        'schema_version': 1,
        'kind': 'RIB_AND_STERNOCOSTAL_3D_RELATIVE_VECTOR_AUDIT',
        'status': 'REJECTED_DIAGNOSTIC_COUPLING' if blockers else
                  'NO_RELATIVE_VECTOR_REGRESSION_ANATOMY_UNVERIFIED',
        'blockers': blockers,
        'ribs_checked': len(rib_changes),
        'rib_joint_markers_checked': len(marker_changes),
        'sternocostal_corridors_checked': len(sternocostal_changes),
        'rib_level_3d_vector_delta_mm': rib_changes,
        'costovertebral_costotransverse_marker_vector_delta_mm': marker_changes,
        'sternocostal_control_corridor': sternocostal_changes,
        'rib_length_change_mm': rib_length_changes,
        'engineering_change_review_mm': REFERENCE_CHANGE_GUARD_MM,
        'rib_length_engineering_change_review_mm': RIB_LENGTH_CHANGE_GUARD_MM,
        'rib_level_review_over_5mm': rib_review,
        'joint_marker_review_over_5mm': marker_review,
        'sternocostal_review_over_5mm': sternum_review,
        'rib_length_review_over_1mm': length_review,
        'contact_surfaces_verified': False,
        'costal_cartilage_modelled': False,
        'dynamic_exercise_validated': False,
        'canonical_promotion_allowed': False,
        'unverified': [
            'Independent world-frame position and curved 3D rib shape',
            'Costovertebral and costotransverse surface contacts and frames',
            'Sternocostal cartilage, floating ribs and breathing coupling',
            'Thorax-depth, ribcage/scapular soft tissue and shoulder anatomy',
            'Any physical clinical tolerance: all guard levels are engineering changes only'
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = audit(json.loads(a.baseline.read_text()), json.loads(a.proposal.read_text()))
    payload = json.dumps(result, indent=2) + '\n'
    if a.out:
        with a.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
