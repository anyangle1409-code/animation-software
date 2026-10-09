#!/usr/bin/env python3
"""Read-only, mesh-independent hand reconstruction probe for a003 -> c004.

This is NOT a new character, an anatomical correction, c005, or a production
builder. It deliberately bypasses `skeleton_fit.contain` ONLY for this isolated
probe to separate inherited pre-containment fingertip stations from the old
a003 skin and test rigid GH correspondence.

No canonical target is selected. The original records, blend files, skin and
motion rigs are never written to or altered. A future canonical builder must
use independently validated hand geometry, not this legacy skin-derived input.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np

import hand_input_source_rebuild_audit as previous

TOL_M = 1e-8
ENDPOINTS = ('head_m', 'tail_m')


def analyse(records=None):
    """Reconstruct a translated hand without mesh containment; verify provenance.

    This DOES NOT establish correct canonical hand proportions. For each of
    108 inputs, it verifies the uncontained reconstructed endpoint differs
    from c004 only by the exact a003 pre-containment offset. This distinguishes
    the 98 determined inputs from the 10 inherited, unvalidated tip stations.
    """
    records = records if records is not None else {
        k: json.loads(p.read_text()) for k, p in previous.P.items()
    }
    a003, c004 = records['a003'], records['c004']
    rows = previous.point_audit(records)
    if len(rows) != 108:
        raise ValueError('Expected 108 baseline carpal and hand input points')
    if not all(r['c004_bone_moved_by_gh_shift'] for r in rows):
        raise ValueError('c004 hand endpoints are not all a rigid GH translation')

    # Starting from c004's skeleton inputs preserves its already-corrected
    # shoulder, arm, WJC and EJC inputs. Translate only the 108 hand/carpal
    # ORIGINAL pre-containment inputs; do not replace them with skin endpoints.
    landmarks = copy.deepcopy(c004['skeleton_input'])
    shifts = {}
    for side in ('left', 'right'):
        shift = previous.gh_shift(c004, a003, side)
        shifts[side] = shift.tolist()
        for group in ('carpals', 'hand'):
            for key, pair in a003['skeleton_input']['sides'][side][group].items():
                landmarks['sides'][side][group][key] = [
                    (np.asarray(point, float) + shift).tolist() for point in pair
                ]

    # The SOURCE builder's mesh-free stage is used unchanged. Critically:
    # no body mesh, containment callback, or production script is invoked.
    built = previous.rebuild(landmarks, None)
    details = []
    for row in rows:
        side, group, key, idx = (row['side'], row['group'],
                                 row['key'], row['index'])
        name, end = row['bone'], ENDPOINTS[idx]
        original_input = np.asarray(
            a003['skeleton_input']['sides'][side][group][key][idx], float)
        original_endpoint = np.asarray(a003['bones'][name][end], float)
        rebuilt_endpoint = np.asarray(built[name][end], float)
        candidate_endpoint = np.asarray(c004['bones'][name][end], float)
        expected_offset = original_input - original_endpoint
        observed_offset = rebuilt_endpoint - candidate_endpoint
        residual = float(np.linalg.norm(observed_offset - expected_offset))
        if residual > TOL_M:
            raise ValueError(
                f'Unexplained endpoint discrepancy {name}:{end}: '
                f'{residual * 1000:.6f} mm')
        classification = row['correction']
        if classification not in ('UNIQUE_EXACT', 'NOT_ENCODED'):
            raise ValueError('Unexpected point correspondence classification')
        if classification == 'UNIQUE_EXACT' and np.linalg.norm(observed_offset) > TOL_M:
            raise ValueError(f'Exact source point did not reconstruct: {name}:{end}')
        details.append({
            'side': side, 'bone': name, 'endpoint': end,
            'classification': classification,
            'difference_from_c004_mm': round(
                float(np.linalg.norm(observed_offset)) * 1000, 6),
            'source_offset_residual_mm': round(residual * 1000, 8),
        })

    exact = sum(p['classification'] == 'UNIQUE_EXACT' for p in details)
    unresolved = sum(p['classification'] == 'NOT_ENCODED' for p in details)
    if (exact, unresolved) != (98, 10):
        raise ValueError(f'Unexpected verified/unresolved partition: {exact}/{unresolved}')
    if not all(p['endpoint'] == 'tail_m' and 'distal_phalanx' in p['bone']
               for p in details if p['classification'] == 'NOT_ENCODED'):
        raise ValueError('Unexpected provisional endpoint outside the ten tips')

    return {
        'schema_version': 1,
        'kind': 'READ_ONLY_MESH_INDEPENDENT_HAND_PROBE',
        'baseline': 'a003',
        'comparison_candidate': 'c004',
        'state': 'DIAGNOSTIC_ONLY_NOT_CANONICAL_NO_C005',
        'contain_applied': False,
        'mesh_geometry_used': False,
        'skeleton_fit_build_used': True,
        'points_checked': len(details),
        'exact_reconstruction_points': exact,
        'inherited_pre_containment_tips': unresolved,
        'gh_translation_mm': {
            s: round(float(np.linalg.norm(v)) * 1000, 6)
            for s, v in shifts.items()},
        'tip_offsets_mm': [
            {k: p[k] for k in ('side', 'bone', 'difference_from_c004_mm')}
            for p in details if p['classification'] == 'NOT_ENCODED'
        ],
        'maximum_source_offset_residual_mm': max(
            p['source_offset_residual_mm'] for p in details),
        'interpretation': (
            '98 input endpoints reconstruct c004 exactly without the a003 skin. '
            'The remaining 10 preserve their old pre-containment fingertip '
            'stations and therefore differ from post-containment c004 by the '
            'inherited adjustment. These 10 stations are NOT canonical targets. '
            'The old mesh must not be used to choose skeletal endpoints.'
        ),
        'promotion_allowed': False,
        'details': details,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, help='Fresh audit JSON path; never overwritten')
    args = p.parse_args()
    report = analyse()
    data = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # Fail rather than overwrite any evidence or a previous audit.
        with args.out.open('x', encoding='utf-8') as f:
            f.write(data)
        print(f'Saved diagnostic report: {args.out}')
    else:
        print(data, end='')


if __name__ == '__main__':
    main()
