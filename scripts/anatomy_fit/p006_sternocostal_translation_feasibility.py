#!/usr/bin/env python3
"""P006 read-only audit: best rigid TRANSLATION for 14 rib/sternal corridors.

For rib i, baseline rib-tail to sternocostal-marker vector is m_i - t_i.
If the rib moves rigidly by d_i and the sternum by a common translation s,
the vector changes by s - d_i. The least-squares translation is the
arithmetic mean of d_i. This is not a clinical or physical objective:
rib-tail controls and sternal markers are NOT cartilage anatomy.

The maximum pairwise separation of d_i divided by two is a mathematically
proven lower bound on the maximum error of ANY single translation. If that
bound exceeds an engineering guard, no translation can pass the guard
without changing rib control locations or interconnection deformation.

This does not rule out sternum ROTATION, rib ROTATION, deformable cartilage,
or alternative source-backed thoracic geometry. These could change the
relationship. No skeleton or production file is modified.
"""
import argparse
import json
import math
from pathlib import Path

CORRIDOR_GUARD_MM = 5.0
RIGID_TRANSLATION_TOLERANCE_MM = .01


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def _mm(vec):
    return [1000*x for x in vec]


def _distance_mm(a, b):
    return 1000*_norm(_sub(a, b))


def analyse_displacements(displacements_m, actual_translation_m, guard_mm=CORRIDOR_GUARD_MM):
    """Least-squares solution and Euclidean lower bound, independent of bones."""
    if not isinstance(displacements_m, dict) or len(displacements_m) < 2:
        raise ValueError('two or more corridor displacements required')
    if not isinstance(guard_mm, (int, float)) or not 0 < guard_mm < 1000:
        raise ValueError('engineering guard must be a positive finite millimetre threshold')
    vectors = {}
    for name, vec in displacements_m.items():
        if not (isinstance(vec, list) and len(vec) == 3 and
                all(type(v) in (int, float) and math.isfinite(v) for v in vec)):
            raise ValueError('invalid displacement vector')
        vectors[name] = vec
    if not (isinstance(actual_translation_m, list) and len(actual_translation_m) == 3
            and all(type(v) in (int, float) and math.isfinite(v) for v in actual_translation_m)):
        raise ValueError('invalid actual sternum translation')

    keys = sorted(vectors)
    mean = [sum(vectors[k][axis] for k in keys)/len(keys) for axis in range(3)]
    residuals_actual = {k: round(_distance_mm(actual_translation_m, vectors[k]), 6) for k in keys}
    residuals_mean = {k: round(_distance_mm(mean, vectors[k]), 6) for k in keys}
    sum_squares_actual = sum(v*v for v in residuals_actual.values())
    sum_squares_mean = sum(v*v for v in residuals_mean.values())
    worst_pair = None
    farthest = -1.0
    for i, ka in enumerate(keys):
        for kb in keys[i+1:]:
            sep = _distance_mm(vectors[ka], vectors[kb])
            if sep > farthest:
                farthest = sep
                worst_pair = [ka, kb]
    # For every translation s, triangle inequality:
    # distance(d_a,d_b) <= distance(d_a,s)+distance(s,d_b)
    # so max_i distance(d_i,s) >= max_(a,b) distance(d_a,d_b)/2.
    minimax_lower_bound = farthest / 2
    impossible_under_guard = minimax_lower_bound > guard_mm + 1e-8

    return {
        'number_of_corridors': len(keys),
        'actual_translation_mm': [round(v, 6) for v in _mm(actual_translation_m)],
        'least_squares_optimal_translation_mm': [round(v, 6) for v in _mm(mean)],
        'translation_difference_actual_vs_ls_mm': round(_distance_mm(actual_translation_m, mean), 6),
        'actual_worst_vector_change_mm': round(max(residuals_actual.values()), 6),
        'ls_worst_vector_change_mm': round(max(residuals_mean.values()), 6),
        'actual_root_mean_square_change_mm': round(math.sqrt(sum_squares_actual/len(keys)), 6),
        'ls_root_mean_square_change_mm': round(math.sqrt(sum_squares_mean/len(keys)), 6),
        'sum_of_squared_vector_changes_actual_mm2': round(sum_squares_actual, 6),
        'sum_of_squared_vector_changes_ls_mm2': round(sum_squares_mean, 6),
        'maximum_pairwise_rib_displacement_difference_mm': round(farthest, 6),
        'max_pairwise_displacement_rib_ids': worst_pair,
        'unavoidable_max_residual_lower_bound_for_translation_mm': round(minimax_lower_bound, 6),
        'engineering_review_threshold_mm': guard_mm,
        'single_translation_cannot_pass_every_corridor_guard': impossible_under_guard,
        'sternum_rotation_evaluated': False,
        'costal_cartilage_mechanics_modelled': False,
        'anatomical_target_selected': False,
        'canonical_promotion_allowed': False,
        'per_corridor_actual_residual_mm': residuals_actual,
        'per_corridor_least_squares_residual_mm': residuals_mean,
    }


def _pt(rec, bone, end):
    return rec['bones'][bone][f'{end}_m']


def audit(baseline, proposed, guard_mm=CORRIDOR_GUARD_MM):
    if set(baseline.get('bones', {})) != set(proposed.get('bones', {})):
        raise ValueError('bone inventory changed')
    if set(baseline.get('joint_markers', {})) != set(proposed.get('joint_markers', {})):
        raise ValueError('joint marker inventory changed')
    s = _sub(_pt(proposed, 'sternum', 'head'), _pt(baseline, 'sternum', 'head'))
    tail_translation = _sub(_pt(proposed, 'sternum', 'tail'), _pt(baseline, 'sternum', 'tail'))
    if _distance_mm(s, tail_translation) > RIGID_TRANSLATION_TOLERANCE_MM:
        raise ValueError('sternum is not a rigid pure translation; P006 cannot model rotation')
    displacements = {}
    for i in range(1, 8):
        for side in ('left', 'right'):
            rib = f'rib_{i:02d}_{side}'
            marker = f'sternocostal_{i:02d}_{side}'
            # P004/P005 should preserve rigid-body rib length and its
            # sternum-carried marker offset (if not, proof formula fails).
            head_shift = _sub(_pt(proposed, rib, 'head'), _pt(baseline, rib, 'head'))
            tail_shift = _sub(_pt(proposed, rib, 'tail'), _pt(baseline, rib, 'tail'))
            if _distance_mm(head_shift, tail_shift) > RIGID_TRANSLATION_TOLERANCE_MM:
                raise ValueError(f'{rib} not translated rigidly')
            original_m = baseline['joint_markers'][marker]
            updated_m = proposed['joint_markers'][marker]
            if original_m.get('frame_bone') != 'sternum' or updated_m.get('frame_bone') != 'sternum':
                raise ValueError('sternocostal marker does not belong to sternum')
            marker_shift = _sub(updated_m['centre_m'], original_m['centre_m'])
            if _distance_mm(marker_shift, s) > RIGID_TRANSLATION_TOLERANCE_MM:
                raise ValueError(f'{marker} was not translated with sternum')
            displacements[rib] = tail_shift

    result = analyse_displacements(displacements, s, guard_mm)
    result.update({
        'schema_version': 1,
        'kind': 'P006_RIGID_STERNUM_TRANSLATION_FEASIBILITY_AUDIT',
        'status': 'PURE_TRANSLATION_INSUFFICIENT_FOR_ENGINEERING_GUARD'
                  if result['single_translation_cannot_pass_every_corridor_guard']
                  else 'TRANSLATION_FEASIBILITY_NOT_ANATOMICAL_ACCEPTANCE',
        'source': 'c004_TO_P004_P005_RIB_AND_STERNAL_CONTROL_CORRIDOR_DISPLACEMENTS',
        'guard_is_not_a_clinical_tolerance': True,
        'disclaimer': 'Pure-translation lower bound only; changes to rib shape, cartilage or sternum rotation not evaluated.',
    })
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = audit(json.loads(args.baseline.read_text()),
                   json.loads(args.proposal.read_text()))
    payload = json.dumps(result, indent=2) + '\n'
    if args.out:
        with args.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
