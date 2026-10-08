#!/usr/bin/env python3
"""ANSUR acromion landmark correspondence and c003 feasibility audit (read-only on all inputs; no candidate is built).

A. Definition (ANSUR II Measurer's Handbook, Hotzman et al. 2011, NATICK/TR-11/017, DTIC ADA548497, sections 5.2.1 and
   6.4.2; primary text verified by the project owner, unreachable from the cloud): the acromion landmark is a PALPATED BONY
   point, the intersection of the lateral border of the acromion with a line running from the trapezius point over the
   clavicle point toward the shoulder tip; acromial height is floor to that drawn right acromion point. No skin-thickness
   offset applies.
B. Correspondence: the only named Lee 2024 landmarks on the acromion lateral border are LM25 (exterior acromial angle,
   posterolateral corner) and LM27 (lateral distal acromial extent). The ANSUR point is modelled as the point of the
   LM25-LM27 border segment where the trapezius-clavicle line crosses it in the transverse plane. The trapezius and
   clavicle point definitions are not available here, so the line is bracketed by two constructions: (i) the clavicle
   axis SC->AC extended; (ii) a purely lateral line through AC. The a003 authored-mesh skin acromion is reported as a
   mesh point only (owner skeleton-first policy: not anatomical evidence).
C. Feasibility with hard constraints: SC held at the Seth relation on the retained a003 jugular notch (sternum not
   lowered); target ANSUR acromial height 1497.7 mm (and, for comparison only, the ANSUR within-subject relation
   acromion = suprasternale + 3.1 mm applied to the a003 notch). For each mapping and both thorax pitches the height is
   met exactly while minimising the joint departure (independent z-scores; no covariance is published) of clavicle
   elevation and, separately, also the three scapular angles from the Matsumura male standing means. The clavicle rotates
   about SC; the scapula re-attaches rigidly at AC. Every z is reported; |z| <= 2 is a labelled screening line, not a
   published hard range.

  shoulder_ansur_acromion_audit.py --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import shoulder_girdle_solver as sgs  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
SOLUTION = ANAT / 'canonical_shoulder_girdle_solution_182_v1.json'
THORAX = ANAT / 'canonical_thorax_frame_182_review_v1.json'
A003 = ANAT / 'character_fit_r95_a003.json'
SOURCES = ANAT / 'canonical_proportion_sources_v1.json'
LEE_SOURCES = ANAT / 'canonical_scapula_landmark_sources_v1.json'
C002 = ANAT / 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json'
DEFINITION = {
    'source': 'ANSUR II Measurer\'s Handbook: US Army and Marine Corps Anthropometric Surveys, 2010-2011 (Hotzman et al. 2011, NATICK/TR-11/017, DTIC ADA548497)',
    'url': 'https://apps.dtic.mil/sti/tr/pdf/ADA548497.pdf', 'sections': ['5.2.1 (landmark)', '6.4.2 (acromial height)'],
    'acromion_landmark': 'palpated bony point: intersection of the lateral border of the acromion with the line running from the trapezius point, over the clavicle point, toward the shoulder tip',
    'acromial_height': 'floor to the drawn right acromion landmark, standing',
    'skin_offset': 'none: the landmark is defined on bone by palpation',
    'verification': 'primary text verified by the project owner 2026-10-08; DTIC unreachable from this cloud environment, so wording is the owner\'s reading, not a verbatim quote',
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1(x):
    return round(float(x), 1)


def rot_about(axis, deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis); t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def seg_cross_2d(p, d, a, b):
    """Parameter t on segment a->b where the line p + s*d crosses it (2D, transverse plane: anterior, lateral)."""
    M = np.array([[d[0], a[0] - b[0]], [d[1], a[1] - b[1]]])
    s, t = np.linalg.solve(M, a - p)
    return float(t)


def correspondence(rc):
    """Thorax-frame points (anterior, superior, lateral) of the candidate ANSUR acromion correspondences."""
    P = rc['scapula_landmarks']; sc, ac = rc['SC'], rc['AC']
    L25, L27 = P[25 - 1], P[27 - 1]
    tp = lambda v: np.array([v[0], v[2]])               # transverse plane (anterior, lateral)
    out = {'LM27_lateral_distal_acromial_extent': {'point': L27, 't_on_LM25_LM27': 1.0},
           'LM25_exterior_acromial_angle': {'point': L25, 't_on_LM25_LM27': 0.0}}
    for name, d in (('border_x_clavicle_axis_line', tp(ac) - tp(sc)), ('border_x_lateral_line_through_AC', np.array([0.0, 1.0]))):
        t = seg_cross_2d(tp(ac), d, tp(L25), tp(L27))
        tc = min(1.0, max(0.0, t))
        out[name] = {'point': L25 + tc * (L27 - L25), 't_on_LM25_LM27': round(t, 3), 'clamped': t != tc}
    return out


def world_z(v, ij, pitch):
    return float(sgs.thorax_to_world(v, 'left', ij, pitch)[2])


def pose_girdle(rc, phi, angles):
    """Girdle pose with SC fixed: clavicle rotated about SC around the thorax anterior axis by phi; scapula given ABSOLUTE
    thorax-frame angles (IR, UR, AT) and re-attached rigidly at the moved AC (AC fixed in the scapula's local frame)."""
    sc, ac0, P0, R0 = rc['SC'], rc['AC'], rc['scapula_landmarks'], rc['rotation']
    ac = sc + (ac0 - sc) @ rot_about([1, 0, 0], phi).T
    R = sgs.scapula_rotation(*angles) @ R0.T
    return ac, ac + (P0 - ac0) @ R.T


def elevation(rc, ac):
    v = ac - rc['SC']
    return math.degrees(math.asin(v[1] / np.linalg.norm(v)))


def min_chi2_solution(rc, which, ij, pitch, target_z, el, a_mean, a_sd, free_scapula=True):
    """Least joint departure from the sourced standing means (clavicle elevation and, if free, the three scapular angles,
    as independent z-scores; no covariance is published) subject to the mapped point reaching target_z with SC closed."""
    from scipy.optimize import least_squares
    a0 = np.asarray(rc['angles_deg'], float)

    def unpack(x):
        return x[0], (x[1:4] if free_scapula else a0)

    def res(x):
        phi, ang = unpack(x)
        ac, P = pose_girdle(rc, phi, ang)
        z = world_z(correspondence(dict(rc, AC=ac, scapula_landmarks=P))[which]['point'], ij, pitch) - target_z
        r = [(elevation(rc, ac) - el['mean']) / el['sd']]
        if free_scapula:
            r += list((np.asarray(ang) - a_mean) / a_sd)
        return np.array(r + [z / 0.01])                     # 0.01 mm weight: equality enforced numerically
    x0 = np.concatenate([[0.0], a0]) if free_scapula else np.array([0.0])
    f = least_squares(res, x0)
    phi, ang = unpack(f.x)
    ac, P = pose_girdle(rc, phi, ang)
    r = res(f.x)
    zs = {'clavicle_elevation': round(float(r[0]), 2)}
    if free_scapula:
        zs.update({k: round(float(v), 2) for k, v in zip(('scapula_IR', 'scapula_UR', 'scapula_AT'), r[1:4])})
    return {'clavicle_elevation_deg': r1(elevation(rc, ac)), 'scapula_angles_IR_UR_AT_deg': [r1(x) for x in ang],
            'girdle_rotation_about_SC_deg': round(float(phi), 4), 'scapula_angles_exact_deg': [round(float(x), 4) for x in ang],
            'height_error_mm': round(float(r[-1] * 0.01), 3), 'z': zs, 'chi2': round(float(sum(v * v for v in zs.values())), 2),
            'max_abs_z': round(max(abs(v) for v in zs.values()), 2)}


def build():
    sol = json.loads(SOLUTION.read_text()); tf = json.loads(THORAX.read_text())
    a = json.loads(A003.read_text()); reg = {s['id']: s for s in json.loads(SOURCES.read_text())['sources']}
    lee_names = json.loads(LEE_SOURCES.read_text())
    rc = sgs.reconcile(1.0)
    P = sgs.pitches()
    ij = np.array(a['skeleton_input']['trunk']['ij_bone']) * 1000
    target = tf['ansur_standing_anchors_at_182_mm']['acromialheight']
    supra = tf['ansur_standing_anchors_at_182_mm']['suprasternaleheight']
    ang = reg['SHOULDER_STANDING_ALIGNMENT_2020']['male_standing_angles_deg']
    el = ang['clavicle_elevation']
    a_mean = [ang['scapula_internal_rotation']['mean'], ang['scapula_upward_rotation']['mean'], ang['scapula_anterior_tilt']['mean']]
    a_sd = [ang['scapula_internal_rotation']['sd'], ang['scapula_upward_rotation']['sd'], ang['scapula_anterior_tilt']['sd']]
    corr = correspondence(rc)
    table, heights = {}, {}
    for pname in ('bony_specimen_deg', 'living_ANSUR_implied_deg'):
        pitch = P[pname]
        sc_z = world_z(rc['SC'], ij, pitch)
        for k, c in corr.items():
            z0 = world_z(c['point'], ij, pitch)
            heights[f'{pname}__{k}'] = {'z_mm': r1(z0), 'minus_SC_mm': r1(z0 - sc_z), 'minus_target_mm': r1(z0 - target['mean']),
                                        'z_score_vs_ANSUR': round((z0 - target['mean']) / target['residual_sd'], 2)}
            row = {}
            for tname, tz in (('absolute_ANSUR_acromial_height', target['mean']),
                              ('ANSUR_within_subject_IJ_plus_3.1', ij[2] + tf['ansur_standing_anchors_at_182_mm']['acromion_minus_IJ_vertical']['mean'])):
                row[tname] = {'target_z_mm': r1(tz),
                              'clavicle_only_scapula_rigid': min_chi2_solution(rc, k, ij, pitch, tz, el, a_mean, a_sd, free_scapula=False),
                              'clavicle_and_scapula_min_chi2': min_chi2_solution(rc, k, ij, pitch, tz, el, a_mean, a_sd)}
            table[f'{pname}__{k}'] = row
    sol_ok = lambda v: v['max_abs_z'] <= 2 and abs(v['height_error_mm']) < 0.1
    feasible_abs = [k for k, r in table.items() if sol_ok(r['absolute_ANSUR_acromial_height']['clavicle_and_scapula_min_chi2'])]
    feasible_rel = [k for k, r in table.items() if sol_ok(r['ANSUR_within_subject_IJ_plus_3.1']['clavicle_and_scapula_min_chi2'])]
    best_abs = min(table.items(), key=lambda kv: kv[1]['absolute_ANSUR_acromial_height']['clavicle_and_scapula_min_chi2']['chi2'])
    abs_best = best_abs[1]['absolute_ANSUR_acromial_height']['clavicle_and_scapula_min_chi2']
    a_skin_z = (a['joint_markers']['acromioclavicular_left']['centre_m'][2] + 0.012) * 1000   # a003 generator: AC = skin + [.., 0, -0.012]
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'NO_DEFENSIBLE_C003' if not feasible_abs else 'C003_FEASIBLE_CANDIDATES_FOUND',
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (SOLUTION, THORAX, A003, SOURCES, LEE_SOURCES, C002)},
        'ansur_definition': DEFINITION,
        'lee_named_landmarks_on_acromion': {k: lee_names['sources']['LEE_2024_SCAPULA_RAW_3D']['landmark_mapping_1based'][k] for k in ('25', '26', '27')}
        if 'sources' in lee_names and isinstance(lee_names['sources'], dict) else 'see canonical_scapula_landmark_sources_v1.json',
        'mapping_decision': {
            'chosen': 'interpolated LM25-LM27 lateral-border point at the trapezius-clavicle line crossing (bracketed by two line constructions)',
            'why_not_LM27_alone': 'LM27 is the lateral distal extent (an extremal point), not defined by the trapezius-clavicle line; it is the upper bracket on the border',
            'why_not_LM25_alone': 'LM25 is the posterolateral angle, the posterior end of the lateral border; it is the lower bracket',
            'mesh_point': 'not used: the a003/r95 skin acromion is an authored-mesh surface point (owner skeleton-first policy), reported for comparison only',
            'limitation': 'trapezius and clavicle point definitions not available here; line AP position bracketed, not exact; only 12 of 29 Lee landmarks have recorded names',
        },
        'correspondence_points_thorax_frame_mm': {k: {'point_ant_sup_lat': [r1(x) for x in v['point']], **{kk: vv for kk, vv in v.items() if kk != 'point'}} for k, v in corr.items()},
        'heights_reconciled_girdle_on_a003_IJ': heights,
        'a003_authored_mesh_skin_acromion_z_mm': {'z_mm': r1(a_skin_z), 'minus_target_mm': r1(a_skin_z - target['mean']), 'status': 'mesh point, not evidence'},
        'targets': {'ANSUR_acromial_height_mm': target, 'ANSUR_suprasternale_mm': supra, 'a003_IJ_z_mm': r1(ij[2]),
                    'a003_IJ_minus_ANSUR_suprasternale_mm': r1(ij[2] - supra['mean']),
                    'clavicle_elevation_source': {'mean': el['mean'], 'sd': el['sd'], 'source': 'SHOULDER_STANDING_ALIGNMENT_2020 (Matsumura male standing CT)',
                                                  'screening_line_deg': [el['mean'] - 2 * el['sd'], el['mean'] + 2 * el['sd']],
                                                  'screening_note': 'mean +/- 2 SD; not a published hard range'}},
        'feasibility': table,
        'verdict': {
            'absolute_height_with_SC_closed_on_a003_sternum': 'INFEASIBLE' if not feasible_abs else feasible_abs,
            'screening_rule': 'every z within +/- 2 (labelled screening line; not a published hard range); height met to 0.1 mm; SC closed on the a003 notch',
            'best_absolute_case': {'variant': best_abs[0], **abs_best},
            'within_subject_relation_with_SC_closed': feasible_rel or 'INFEASIBLE',
            'reading': ('With SC closed on the retained a003 notch, every border mapping (LM25, LM27, and both interpolated crossings), '
                        'both thorax pitches and the most favourable scapular orientation inside 2 SD still need a negative clavicle '
                        'elevation or scapular angles beyond 2 SD (best case %s: clavicle %.1f deg, max |z| %.2f, chi2 %.1f on 4 angles) to put '
                        'the ANSUR acromion at 1497.7 mm. No defensible c003 '
                        'exists from this evidence. The retained a003 jugular notch sits %.1f mm above the ANSUR suprasternale of the same '
                        'survey; see within_subject_relation for whether the shoulder closes when the ANSUR acromion-suprasternale '
                        'relation is used instead of absolute height (reported, not applied: the sternum is not lowered).')
                       % (best_abs[0], abs_best['clavicle_elevation_deg'], abs_best['max_abs_z'], abs_best['chi2'], ij[2] - supra['mean']),
        },
        'c003_created': False,
        'still_open': ['exact trapezius-point and clavicle-point definitions (handbook 5.2.1) to fix the line crossing on the border',
                       'whether the retained a003 sternum height or the absolute acromial target governs (owner decision; same survey disagrees with a003 IJ by +24.7 mm)',
                       'standing thorax pitch (sensitivity variable)', 'scapulothoracic contact (rib geometry BLOCKED)'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    r = build()
    Path(o.out).write_text(json.dumps(r, indent=1) + '\n')
    print(json.dumps({'heights': r['heights_reconciled_girdle_on_a003_IJ'], 'verdict': r['verdict'],
                      'corr': r['correspondence_points_thorax_frame_mm']}, indent=1))


if __name__ == '__main__':
    main()
