#!/usr/bin/env python3
"""Independent read-only bridge from literature endpoints to model PROXIES.

Model points in the c004 control-skeleton are not verified physical
endplate-centre / manubrium / pelvic APP landmarks. Numerical agreement
with population studies MUST NOT promote a skeleton or select coordinates.

Two independently verified source records:
- Baker et al., 2021 thoracic inlet (supine CT, 65 patients)
- Imai et al., 2019 male APP pelvic reference (55 male CT volunteers)
The registry retains source endpoint definitions, cohort, uncertainty
and the abstract/Table 1 disagreement of 66.1 vs 65.9 mm.

NO COORDINATES ARE CHANGED. NO NEW SKELETON IS GENERATED.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

SRC_IDS = {'TID_BAKER_2021', 'S1_HIP_IMAI_2019'}


def _vector(point):
    if (not isinstance(point, list) or len(point) != 3 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in point)):
        raise ValueError('missing or nonfinite landmark control point')
    return point


def _mid(a, b):
    return [(x+y)/2 for x, y in zip(a, b)]


def _diff_mm(a, b):
    return [1000*(x-y) for x, y in zip(a, b)]


def _distance_mm(a, b):
    return 1000*math.dist(a, b)


def _compare_to_study(value, mean, observed_range):
    """Merely compare numbers; never call this anatomical acceptance."""
    return {
        'proxy_minus_source_mean_mm': round(value - mean, 3),
        'within_observed_study_minmax_context': observed_range[0] <= value <= observed_range[1],
        'not_a_patient_anatomical_fit': True,
        'source_population_stature_transfer_unverified': True,
    }


def audit(record, registry):
    if registry.get('schema_version') != 1 or registry.get('canonical_promotion_allowed') is not False:
        raise ValueError('invalid or promotable landmark registry')
    sources = registry.get('source_landmarks', [])
    by_id = {x['id']: x for x in sources}
    if len(by_id) != len(sources) or set(by_id) != SRC_IDS:
        raise ValueError('exact expected pinned source inventory required')
    if any(x.get('decision') != 'CONTEXT_ONLY_NOT_A_COORDINATE_TARGET' or
           x['model_proxy'].get('equivalence_verified') is not False for x in sources):
        raise ValueError('source/proxy not approved for anatomical coordinate targeting')

    bone = record['bones']
    if (record.get('conventions', {}).get('world') !=
            'Blender world metres; +Z up; character faces -Y; anatomical LEFT = +X (F-SIDE-001)'):
        raise ValueError('world coordinate convention changed, registration must be revisited')
    if not all(k in bone for k in ('t1', 'sternum', 'sacrum', 'femur_left', 'femur_right')):
        raise ValueError('missing anatomical controls')

    # T1.tail is upper endplate of a control STICK; sternum.head a
    # schematic manubrium/jugular control point — NOT verified physical points.
    tid_a = _vector(bone['t1']['tail_m'])
    tid_b = _vector(bone['sternum']['head_m'])
    tid_mm = _distance_mm(tid_a, tid_b)
    tid_study = by_id['TID_BAKER_2021']['measurement']
    if (not (tid_study['table1_mean_mm'] == 65.9 and
             tid_study['abstract_mean_mm'] == 66.1 and
             tid_study['range_mm'] == [52,83])):
        raise ValueError('published thoracic inlet source has been modified without review')

    # APP study reports S1-to-hip-axis as sagittal magnitudes/coordinates
    # *after* alignment to APP. World +Y is model posterior, but model's
    # ASIS/pubis plane has NOT been registered to study APP. These absolute
    # model components are thus comparative raw control metrics ONLY.
    hip_l = _vector(bone['femur_left']['head_m'])
    hip_r = _vector(bone['femur_right']['head_m'])
    hip = _mid(hip_l, hip_r)
    s1 = _vector(bone['sacrum']['tail_m'])
    y_mm = 1000*(s1[1] - hip[1])
    z_mm = 1000*(s1[2] - hip[2])
    projected_length_mm = math.hypot(y_mm, z_mm)
    pelvic_study = by_id['S1_HIP_IMAI_2019']['measurement']
    if pelvic_study.get('male_dyp_pm_2sd_mm') != 21.2:
        raise ValueError('Imai table spreads must be explicitly TWO SD')
    if not (pelvic_study['male_total_mean_mm'] == 107.0 and
            pelvic_study['male_dyp_mean_mm'] == 18.8 and
            pelvic_study['male_dzp_mean_mm'] == 104.7):
        raise ValueError('published pelvic endpoints have been modified without review')
    models = {
        'TID_BAKER_2021': {
            'model_proxy_T1_superior_to_sternum_head_mm': round(tid_mm, 3),
            'model_raw_t1_minus_manubrial_control_xyz_mm':
                [round(x, 3) for x in _diff_mm(tid_a, tid_b)],
            'study_table1_mean_mm': tid_study['table1_mean_mm'],
            'study_abstract_mean_mm': tid_study['abstract_mean_mm'],
            'study_mean_discrepancy_mm': round(
                tid_study['abstract_mean_mm'] - tid_study['table1_mean_mm'], 3),
            'study_sd_mm': tid_study['sd_mm'],
            'study_observed_range_mm': tid_study['range_mm'],
            **_compare_to_study(tid_mm, tid_study['table1_mean_mm'], tid_study['range_mm']),
            'source_landmark_equivalence_verified': False,
            'sternum_to_spine_AP_depth_measured': False,
        },
        'S1_HIP_IMAI_2019': {
            'model_S1_minus_hip_axis_world_y_mm': round(y_mm, 3),
            'model_S1_minus_hip_axis_world_z_mm': round(z_mm, 3),
            'model_sagittal_yz_length_mm': round(projected_length_mm, 3),
            'study_male_AP_component_mm': pelvic_study['male_dyp_mean_mm'],
            'study_male_vertical_component_mm': pelvic_study['male_dzp_mean_mm'],
            'study_male_sagittal_length_mm': pelvic_study['male_total_mean_mm'],
            'study_stature_m': by_id['S1_HIP_IMAI_2019']['cohort']['male_mean_stature_m'],
            'study_spreads_are_2SD': True,
            'model_world_to_study_APP_transform_verified': False,
            'model_endplate_and_hip_landmark_identity_verified': False,
            'not_allowed_to_apply_source_numbers_as_coordinates': True,
        },
    }
    return {
        'schema_version': 1,
        'kind': 'EXTERNAL_TRUNK_LANDMARK_COMPARATIVE_AUDIT',
        'status': 'COMPARATIVE_ONLY_NO_ANATOMICAL_REGISTRATION',
        'canonical_promotion_allowed': False,
        'candidate_or_mesh_updated': False,
        'population_means_not_canonical_targets': True,
        'source_ids': sorted(SRC_IDS),
        'comparisons': models,
        'blocking_gates': [
            'Verify actual CT-compatible manubrium apex and superior T1 endplate surfaces',
            'Verify physical S1 endplate centre and bilateral femoral head articular centres',
            'Register pelvic APP to 3D world using ASIS/pubic symphysis, not an assumed axis',
            'Resolve cohort stature/sex and supine CT versus 1.82m standing exercise reference',
            'Find second independent compatible source for each anatomical coordinate target',
            'Solve per-level thoracic wedge angles, sternocostal cartilage geometry and SC/AC/GH articular closure'
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--record', type=Path, required=True)
    ap.add_argument('--source-registry', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    opt = ap.parse_args()
    b = opt.record.read_bytes()
    s = opt.source_registry.read_bytes()
    result = audit(json.loads(b), json.loads(s))
    result['input_sha256'] = {
        'record': hashlib.sha256(b).hexdigest(),
        'source_registry': hashlib.sha256(s).hexdigest(),
    }
    payload = json.dumps(result, indent=2) + '\n'
    if opt.out:
        with opt.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
