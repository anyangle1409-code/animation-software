#!/usr/bin/env python3
"""P004: diagnostic ONLY — coupled ribs/sternum replay of rejected P003 discs.

NOT a canonical candidate. Nothing here establishes sagittal thoracic shape,
rib curvature, articulating surfaces, costal-cartilage deformation, clavicle
closure, living landmarks, clinical anatomy or exercise validity.

P003 source-bound segment lengths and spine edits are used as a reference,
without changing any of their numbers. For each rib, translate the bone and
its rib-carried contact markers by the change in the corresponding thoracic
articular level centre between c004 and P003. This restores the BASELINE
rib-head-to-level vector exactly by construction — it proves correspondence
mechanics, not correctness of the anatomy.

For the sternum, take the componentwise median of the first 7 ribs' endpoint
displacements (a reversible computational placeholder, NOT an anatomical
dimension). Translate sternal body and sternum-carried marker centres by that
amount, without changing sternum shape. Clavicles, scapulae, arm and neck
do NOT move — their closure becomes a flagged blocker.

C004 / P003 and all production assets stay untouched.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
C004 = ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
P003 = ANAT / 'audit/proposals/p003_spine_disc_repartition_rejected/proposal_record.json'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _add(a, b):
    return [x+y for x, y in zip(a, b)]


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _centre(record):
    return [(a + b)/2 for a, b in zip(record['head_m'], record['tail_m'])]


def vertebral_anchor(B, rib_index):
    """Preserve the explicitly documented rib 1 / 2–9 / 10–12 level map."""
    if rib_index == 1 or rib_index >= 10:
        return _centre(B[f't{rib_index}'])
    lo = B[f't{rib_index}']
    up = B[f't{rib_index - 1}']
    return [(a+b)/2 for a, b in zip(lo['tail_m'], up['head_m'])]


def _translate_bone(bone, shift):
    for key in ('head_m', 'tail_m'):
        bone[key] = _add(bone[key], shift)


def _translate_markers(record, shifted):
    count = 0
    ids = []
    for jid, marker in record['joint_markers'].items():
        frame = marker.get('frame_bone')
        if frame in shifted:
            marker['centre_m'] = _add(marker['centre_m'], shifted[frame])
            ids.append(jid)
            count += 1
    return sorted(ids)


def _distance(a, b):
    return math.dist(a, b) * 1000


def sternocostal_distances(bones, markers):
    """Straight-line endpoint-to-sternal contact corridor: proxy only.

    This is NOT cartilage length or a verified cartilage point: the rib stick
    ends need not be the actual costochondral junction.
    """
    out = {}
    for n in range(1, 8):
        for s in ('left', 'right'):
            rib = f'rib_{n:02d}_{s}'
            contact = f'sternocostal_{n:02d}_{s}'
            out[contact] = _distance(bones[rib]['tail_m'], markers[contact]['centre_m'])
    return out


def build(base, p003):
    if base.get('schema_version') != 1 or p003.get('schema_version') != 1:
        raise ValueError('unexpected input schemas')
    if p003.get('candidate', {}).get('id') != 'P003_SPINE_DISC_REPARTITION_DIAGNOSTIC_PROPOSAL':
        raise ValueError('requires exactly the documented rejected P003 source')
    if set(base['bones']) != set(p003['bones']) or set(base['joint_markers']) != set(p003['joint_markers']):
        raise ValueError('P003 identity/inventory has changed')
    out = copy.deepcopy(p003)
    before = copy.deepcopy(out)
    B, J = out['bones'], out['joint_markers']
    bbase = base['bones']
    per_rib, shifts = {}, {}
    for index in range(1, 13):
        old_level = vertebral_anchor(bbase, index)
        new_level = vertebral_anchor(B, index)
        delta = _sub(new_level, old_level)
        if not all(math.isfinite(x) for x in delta):
            raise ValueError('non-finite spine anchor displacement')
        for side in ('left', 'right'):
            rib_id = f'rib_{index:02d}_{side}'
            _translate_bone(B[rib_id], delta)
            shifts[rib_id] = delta
            per_rib[rib_id] = {
                'anchor_delta_mm': [round(x*1000, 4) for x in delta],
                'new_head_minus_new_level_mm': [
                    round((a-b)*1000, 4)
                    for a, b in zip(B[rib_id]['head_m'], new_level)],
                'original_head_minus_original_level_mm': [
                    round((a-b)*1000, 4)
                    for a, b in zip(bbase[rib_id]['head_m'], old_level)],
            }

    # Computational placeholder, not a sourced thorax pose solution:
    # use the median of the upper 7 rib *displacements*. Both sides included.
    upper = [shifts[f'rib_{i:02d}_{s}'] for i in range(1, 8)
             for s in ('left', 'right')]
    sternum_shift = [statistics.median(a[k] for a in upper) for k in range(3)]
    _translate_bone(B['sternum'], sternum_shift)
    shifts['sternum'] = sternum_shift
    moved_markers = _translate_markers(out, shifts)

    # Independent baseline-to-specified-proposal corridor diagnostics.
    # This uses rib tails and sternocostal marker centres, NOT articular surfaces.
    baseline_c = sternocostal_distances(base['bones'], base['joint_markers'])
    revised_c = sternocostal_distances(B, J)
    max_costal_change = max(abs(revised_c[k] - baseline_c[k]) for k in baseline_c)
    left_sc = _distance(J['sternoclavicular_left']['centre_m'], B['clavicle_left']['head_m'])
    right_sc = _distance(J['sternoclavicular_right']['centre_m'], B['clavicle_right']['head_m'])
    # The clavicles have intentionally not moved with the sternum. The
    # following measures show what remains to close if the SC articular
    # anchors follow the sternum in a later *evidence-based* candidate.
    sc_shift = math.sqrt(sum(x*x for x in sternum_shift))*1000

    out['candidate'] = {
        'id': 'P004_COUPLED_THORAX_MECHANICS_DIAGNOSTIC_REPLAY',
        'status': 'DIAGNOSTIC_ONLY_REQUIRES_ANATOMICAL_RECONSTRUCTION',
        'freeze_ready': False, 'canonical_promotion_allowed': False,
        'p003_spine_source': 'UNALTERED_REJECTED_P003_LENGTHS_AND_FRAMES',
        'rib_coupling': 'TRANSLATE_EACH_RIB_BY_ITS_THORACIC_ARTICULAR_LEVEL_DELTA',
        'sternum_coupling': 'MEDIAN_RIB1_TO_7_DELTA_HEURISTIC_NOT_ANATOMY',
        'sternum_shift_mm': [round(x*1000, 4) for x in sternum_shift],
        'sternum_shift_norm_mm': round(sc_shift, 4),
        'rib_source_level_correspondence': per_rib,
        'moved_joint_markers': moved_markers,
        'sternocostal_stick_endpoint_proxy': {
            'max_change_from_baseline_mm': round(max_costal_change, 4),
            'baseline_distances_mm': {k: round(v, 4) for k, v in baseline_c.items()},
            'replay_distances_mm': {k: round(v, 4) for k, v in revised_c.items()},
        },
        'unchanged_clavicle_SC_marker_to_head_mm': {
            'left': round(left_sc, 6), 'right': round(right_sc, 6)},
        'unresolved_clavicle_followup_shift_mm': round(sc_shift, 4),
        'preflight_limitations': [
            'The P003 spine curve is NOT the accepted lumbar/torso target.',
            'S1 AP depth, sternum-to-spine depth and per-level thoracic wedges are unsourced.',
            'Rib centreline curvature/articular surface contact and cartilage are unsourced.',
            'Sternum translation is a MEDIAN kinematic placeholder, not evidence.',
            'SC/AC/GH, scapula, arms and neck are unchanged; shoulder closure is OPEN.',
            'skeleton_input skin/mesh anchors are unchanged and should never set bone truth.',
            'Joint coordinate frames and downstream kinematic followers remain provisional.',
            'Do not use this replay for muscle/skin fitting or canonical promotion.'
        ],
    }
    for bone_id in ('sternum', 'clavicle_left', 'clavicle_right'):
        if bone_id.startswith('clavicle') and B[bone_id] != before['bones'][bone_id]:
            raise AssertionError('clavicles must be unchanged in P004')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=C004)
    parser.add_argument('--p003', type=Path, default=P003)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    base_data, p_data = args.baseline.read_bytes(), args.p003.read_bytes()
    generated = build(json.loads(base_data), json.loads(p_data))
    generated['candidate']['input_hashes_sha256'] = {
        'c004': _sha(base_data), 'p003': _sha(p_data)
    }
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(generated, f, indent=1)
        f.write('\n')
    print(json.dumps({
        'id': generated['candidate']['id'],
        'status': generated['candidate']['status'],
        'sternum_shift_mm': generated['candidate']['sternum_shift_mm'],
        'costal_proxy_change_mm':
            generated['candidate']['sternocostal_stick_endpoint_proxy']['max_change_from_baseline_mm'],
        'canonical_promotion_allowed': False,
        'out': str(args.out)
    }, indent=2))


if __name__ == '__main__':
    main()
