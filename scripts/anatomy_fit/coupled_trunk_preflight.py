#!/usr/bin/env python3
"""Read-only checks for a PROPOSED, coupled Home Gym PT trunk correction.

This is a mechanical consistency preflight, not a new skeleton candidate or
a validated anatomical reconstruction. Do not allow any report from here to
promote a canonical skeleton: measurements and sagittal anatomy require
independent review. The existing c004 and rejected P003 are never modified.

Usage:
  python scripts/anatomy_fit/coupled_trunk_preflight.py \
    --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
    --proposal /path/to/isolated_trunk_proposal.json
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

SPINE = ['l5', 'l4', 'l3', 'l2', 'l1'] + [f't{i}' for i in range(12, 0, -1)] + [
    'c7', 'c6', 'c5', 'c4', 'c3'
]
RIBS = [f'rib_{i:02d}_{s}' for i in range(1, 13) for s in ('left', 'right')]
MANDATORY = set(SPINE + RIBS + ['sacrum', 'sternum', 'clavicle_left', 'clavicle_right'])
# Conservative diagnostics, explicitly not clinical/anatomical ranges.
MIN_DISC_MM = 1.0
MAX_DISC_MM = 20.0
RIB_LEVEL_WORSENING_FACTOR = 2.0
COMPONENT_MOVE_FLAG_MM = 10.0


def _pt(record, bone, end):
    return record['bones'][bone][f'{end}_m']


def _dmm(a, b):
    return 1000.0 * math.dist(a, b)


def _centre(b):
    return [(x + y) / 2 for x, y in zip(b['head_m'], b['tail_m'])]


def _along_mm(lower, upper):
    lo = lower['head_m']
    hi = lower['tail_m']
    axis = [b - a for a, b in zip(lo, hi)]
    delta = [b - a for a, b in zip(hi, upper['head_m'])]
    norm = math.sqrt(sum(x*x for x in axis))
    if norm < 1e-8:
        raise ValueError('zero-length spine bone')
    return 1000 * sum(a*b for a, b in zip(axis, delta)) / norm


def _rib_level(bones, index):
    # Same explicit costovertebral level mapping as the existing P003 audit:
    # rib 1 = T1 centre; 2–9 = corresponding disc midpoint; 10–12 = own body.
    # This is a Z-level diagnostic, not full cartilage/facet congruence.
    if index == 1 or index >= 10:
        return _centre(bones[f't{index}'])[2]
    lower, upper = bones[f't{index}'], bones[f't{index-1}']
    return (lower['tail_m'][2] + upper['head_m'][2]) / 2


def rib_offsets(bones):
    result = {}
    for i in range(1, 13):
        z = _rib_level(bones, i)
        for side in ('left', 'right'):
            key = f'rib_{i:02d}_{side}'
            result[key] = round(1000 * (bones[key]['head_m'][2] - z), 6)
    return result


def _changed_mm(b1, b2):
    return max(_dmm(b1[k], b2[k]) for k in ('head_m', 'tail_m'))


def examine(base, proposal):
    if not isinstance(base.get('bones'), dict) or not isinstance(proposal.get('bones'), dict):
        raise ValueError('both inputs need bones')
    B, P = base['bones'], proposal['bones']
    if set(P) != set(B):
        raise ValueError('proposal must preserve exactly the same bone inventory')
    if not MANDATORY <= set(B):
        raise ValueError('missing spine, rib or trunk/shoulder bone')
    for k in MANDATORY:
        for end in ('head_m', 'tail_m'):
            for record in (B, P):
                x = record[k].get(end)
                if (not isinstance(x, list) or len(x) != 3 or
                        any(type(v) not in (int, float) or not math.isfinite(v) for v in x)):
                    raise ValueError(f'non-finite or invalid coordinates for {k}.{end}')
    disc_gaps = {}
    for lower, upper in zip(SPINE, SPINE[1:]):
        # This check reports only the component along the lower vertebra
        # control axis. A real disc model also needs endplates and wedging.
        disc_gaps[f'{lower}/{upper}'] = round(_along_mm(P[lower], P[upper]), 6)
    nonpositive = {k: v for k, v in disc_gaps.items() if v < MIN_DISC_MM}
    too_large = {k: v for k, v in disc_gaps.items() if v > MAX_DISC_MM}

    baseline_offsets = rib_offsets(B)
    proposal_offsets = rib_offsets(P)
    baseline_max = max(abs(v) for v in baseline_offsets.values())
    proposed_max = max(abs(v) for v in proposal_offsets.values())
    # Historical P003 acceptance: do not more than double c004's worst
    # rib-head Z offset. This is a *regression* guard, not a clinical tolerance.
    rib_threshold = RIB_LEVEL_WORSENING_FACTOR * baseline_max
    regressed_ribs = {
        k: v for k, v in proposal_offsets.items() if abs(v) > rib_threshold + 1e-6
    }

    changed = {k: round(_changed_mm(B[k], P[k]), 6) for k in B
               if _changed_mm(B[k], P[k]) > 0.001}
    thorax_shift = max(
        _changed_mm(B[k], P[k]) for k in ('t1', 't2', 't3', 't4', 't5')
    )
    lower_shift = max(
        _changed_mm(B[k], P[k]) for k in ('t10', 't11', 't12', 'l1')
    )
    rib_shift = max(_changed_mm(B[k], P[k]) for k in RIBS)
    sternum_shift = _changed_mm(B['sternum'], P['sternum'])
    ribs_stationary_despite_thorax = (lower_shift > COMPONENT_MOVE_FLAG_MM
                                    and rib_shift < 0.001)
    sternum_stationary_despite_thorax = (thorax_shift > COMPONENT_MOVE_FLAG_MM
                                        and sternum_shift < 0.001)
    changed_spine = [k for k in SPINE if k in changed]
    no_change = not changed_spine

    blockers = []
    if no_change:
        blockers.append('NO_SPINE_RECONSTRUCTION')
    if nonpositive:
        blockers.append('INTERVERTEBRAL_DISC_CLEARANCE_INSUFFICIENT')
    if too_large:
        blockers.append('INTERVERTEBRAL_DISC_CLEARANCE_OVERSIZE')
    if regressed_ribs:
        blockers.append('RIB_ARTICULAR_LEVEL_Z_REGRESSION')
    if ribs_stationary_despite_thorax:
        blockers.append('RIBS_NOT_COUPLED_TO_THORAX')
    if sternum_stationary_despite_thorax:
        blockers.append('STERNUM_NOT_COUPLED_TO_THORAX')
    return {
        'schema_version': 1,
        'kind': 'COUPLED_TRUNK_DIAGNOSTIC_ONLY',
        'safe_for_canonical_promotion': False,
        'status': 'REJECTED_MECHANICAL_PREFLIGHT' if blockers else 'NO_MECHANICAL_BLOCKER_ANATOMY_UNVERIFIED',
        'blockers': blockers,
        'bone_count_unchanged': True,
        'changed_spine_bones': changed_spine,
        'changed_trunk_components_mm': {
            'upper_thorax_max': round(thorax_shift, 3),
            'lower_thorax_max': round(lower_shift, 3),
            'ribs_max': round(rib_shift, 3),
            'sternum': round(sternum_shift, 3),
        },
        'disc_gaps_projected_mm': disc_gaps,
        'disc_gaps_nonpositive_or_lt_1mm': nonpositive,
        'disc_gaps_gt_20mm': too_large,
        'rib_level_reference_max_offset_mm': round(baseline_max, 4),
        'rib_level_proposal_max_offset_mm': round(proposed_max, 4),
        'rib_level_guard_threshold_mm': round(rib_threshold, 4),
        'rib_level_regressions_mm': regressed_ribs,
        'shoulder_anchor_follow_up_required': thorax_shift > COMPONENT_MOVE_FLAG_MM,
        'unverified_requirements': [
            'Sourced individual disc heights, wedge angles and intervertebral contact surfaces',
            'Evidence-based sternum-to-spine sagittal closure and S1 depth',
            'Sourced rib-head and rib-tubercle 3D contacts, cartilage and sternum relations',
            'ANSUR living-landmark correspondence and C7/SC/AC/GH height closure',
            'All joint frames, coupled motion, collision and whole-body tests',
            'Independent anatomical sign-off and no production promotion',
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--out', type=Path)
    opts = p.parse_args()
    base_data = opts.baseline.read_bytes()
    proposal_data = opts.proposal.read_bytes()
    result = examine(json.loads(base_data), json.loads(proposal_data))
    result['input_sha256'] = {
        'baseline': hashlib.sha256(base_data).hexdigest(),
        'proposal': hashlib.sha256(proposal_data).hexdigest(),
    }
    payload = json.dumps(result, indent=2) + '\n'
    if opts.out:
        with opts.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
