#!/usr/bin/env python3
"""Shoulder-proposal audit candidate c002: c001 translated vertically to the living ANSUR acromial-height anchor.

Owner modelling policy SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING (8 October 2026): absolute shoulder height in the 1.82 m
reference body follows the living standing ANSUR survey; internal clavicle length/orientation, scapular geometry and
AC-GH relations stay those of the reconciled bony solution. This is a modelling policy for a living exercise character,
not a settled skin-to-bone relationship.

Construction (no other change):
  * source: the committed c001 record (sha256 pinned), itself a003 + reconciled shoulder solution (bony pitch, IJ at a003);
  * mapping: ANSUR II 'acromial height' (skin acromion landmark, standing, regressed on stature at 1.82 m from the
    committed 4,082-man file) <-> Lee 2024 LM27 lateral distal acromion; skin-to-bone offset NOT applied (unquantified);
  * one vertical translation dz = target - LM27_z (identical both sides) applied rigidly to every c001-moved bone and
    marker, the 29 scapula landmarks per side and the shoulder skeleton_input points. Trunk, sternum, ribs and spine are
    a003's, unchanged.
Closure against the retained trunk is measured and reported, never forced.

  build_shoulder_candidate_c002.py --out JSON
"""
import argparse, copy, hashlib, json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
C001 = ANAT / 'audit/candidates/shoulder_proposal_c001/candidate_record.json'
C001_SHA256 = '08e9f2e1187dbeda'          # prefix pinned in the c001 README; c001 is never edited
SOLUTION = ANAT / 'canonical_shoulder_girdle_solution_182_v1.json'
THORAX = ANAT / 'canonical_thorax_frame_182_review_v1.json'
STERNUM = ANAT / 'canonical_sternum_target_review_v1.json'
ANSUR_CSV = ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv'
CANDIDATE_ID = 'r95_a003_shoulder_proposal_c002_ansur_height'
LM_PRIMARY, LM_BRACKET = 27, 25            # 1-based Lee 2024: lateral distal acromion; exterior acromial angle
SHOULDER_INPUT_KEYS = ('SC', 'AC', 'AA', 'TS', 'AI', 'GH', 'glenoid')
POLICY_ID = 'SHOULDER_HEIGHT_ANCHOR_ANSUR_LIVING'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r1(x):
    return round(float(x), 1)


def ansur_target():
    """Acromial height at 1.82 m: OLS on stature over all 4,082 men in the committed file (as thorax_frame_review)."""
    t = json.loads(THORAX.read_text())['ansur_standing_anchors_at_182_mm']
    return {'acromialheight': t['acromialheight'], 'suprasternaleheight': t['suprasternaleheight'],
            'source': 'canonical_thorax_frame_182_review_v1.json -> sources/ansur2/ANSUR_II_MALE_Public.csv (n=4082, OLS on stature at 1820 mm)'}


def manubrium_length_range():
    """Range of published male mean manubrium lengths (a range of means, not a population interval)."""
    return json.loads(STERNUM.read_text())['population_male_means_mm']['manubrium_length_range']


def sensitivity(target_z, sol, ij_a003_z):
    """dz and resulting SC-minus-IJ (each world's own IJ) for every recorded pitch/IJ world and both acromion landmarks."""
    out = {}
    ij = {'IJ_at_a003': ij_a003_z, 'IJ_at_ANSUR_182': ansur_target()['suprasternaleheight']['mean']}
    seth = sol['variants']['source_scale']['reconciled']['thorax_frame_mm']['SC'][1]
    for wk, w in sol['variants']['source_scale']['world_mm'].items():
        L = w['left']
        ij_z = ij[wk.split('__')[1]]
        for lm in (LM_PRIMARY, LM_BRACKET):
            dz = target_z - L['scapula_all_29'][lm - 1][2]
            out[f'{wk}__LM{lm}'] = {'dz_mm': r1(dz), 'SC_z_after_mm': r1(L['SC'][2] + dz), 'AC_z_after_mm': r1(L['AC'][2] + dz),
                                    'IJ_z_mm': r1(ij_z), 'SC_minus_IJ_after_mm': r1(L['SC'][2] + dz - ij_z),
                                    'source_SC_minus_IJ_mm': seth}
    return out


def build():
    if not sha(C001).startswith(C001_SHA256):
        raise RuntimeError('c001 record changed; c002 is defined relative to the pinned c001')
    c1 = json.loads(C001.read_text())
    sol = json.loads(SOLUTION.read_text())
    tgt = ansur_target()
    target_z = tgt['acromialheight']['mean']
    lms = c1['candidate']['scapula_landmarks_world_mm']
    lz = {s: lms[s][LM_PRIMARY - 1][2] for s in ('left', 'right')}
    if abs(lz['left'] - lz['right']) > 1e-6:
        raise RuntimeError('c001 LM27 heights differ between sides')
    dz_mm = target_z - lz['left']
    d = np.array([0.0, 0.0, dz_mm / 1000.0])
    c = copy.deepcopy(c1)
    B, J = c['bones'], c['joint_markers']
    for k in c1['candidate']['moved_bones']:
        for e in ('head_m', 'tail_m'):
            B[k][e] = [float(x) for x in np.array(B[k][e]) + d]
    for k in c1['candidate']['moved_markers']:
        J[k]['centre_m'] = [float(x) for x in np.array(J[k]['centre_m']) + d]
    new_lms = {}
    for side in ('left', 'right'):
        S = c['skeleton_input']['sides'][side]
        for key in SHOULDER_INPUT_KEYS:
            S[key] = [float(x) for x in np.array(S[key]) + d]
        new_lms[side] = [[p[0], p[1], p[2] + dz_mm] for p in lms[side]]
    # closure against the retained a003 trunk
    ij_z = c1['skeleton_input']['trunk']['ij_bone'][2] * 1000
    sc_z = J['sternoclavicular_left']['centre_m'][2] * 1000
    seth_sc_sup = sol['variants']['source_scale']['reconciled']['thorax_frame_mm']['SC'][1]
    man = manubrium_length_range()
    sc_below_ij = ij_z - sc_z
    closure = {
        'retained_trunk': 'a003 (sternum head = bony IJ at z %.1f mm)' % ij_z,
        'SC_z_mm': r1(sc_z), 'SC_minus_IJ_mm': r1(sc_z - ij_z),
        'expected_SC_minus_IJ_superior_mm_thorax_frame': seth_sc_sup,
        'displacement_from_expected_mm': r1((sc_z - ij_z) - seth_sc_sup),
        'published_male_mean_manubrium_length_range_mm': man,
        'SC_below_IJ_exceeds_whole_manubrium_length': bool(man and sc_below_ij > max(man)),
        'status': 'FAIL',
        'reading': ('The rigid ANSUR-height translation carries the SC joints %.1f mm below the retained a003 jugular notch, beyond '
                    'the full range of published male mean manubrium lengths (%s mm); the clavicles no longer reach the clavicular notches of the '
                    'retained sternum. The girdle does not close against the a003 trunk. Not forced, not repaired.') % (sc_below_ij, man),
    }
    if not closure['SC_below_IJ_exceeds_whole_manubrium_length']:
        closure['status'] = 'FAIL_DISPLACED_FROM_SOURCE_RELATION'
        closure['reading'] = ('SC joints sit %.1f mm below the retained jugular notch against the source relation of %.1f mm above; '
                              'the clavicles no longer meet the clavicular notches at the source relation. Not forced.') % (sc_below_ij, seth_sc_sup)
    c['candidate'] = {
        'id': CANDIDATE_ID, 'status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED', 'freeze_ready': False,
        'owner_policy': POLICY_ID,
        'policy_caveat': 'owner modelling policy for a living exercise character; not proof that the skin-to-bone landmark relation is settled',
        'base_record': {'path': str(C001.relative_to(ROOT)), 'sha256': sha(C001), 'id': c1['candidate']['id']},
        'solution': c1['candidate']['solution'],
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (SOLUTION, THORAX, STERNUM, ANSUR_CSV)},
        'landmark_mapping': {
            'target': 'ANSUR II acromial height (standing; skin acromion landmark on the lateral edge of the acromion at the shoulder tip, palpated)',
            'target_definition_status': 'primary ANSUR II landmark text (Hotzman et al. 2011 NATICK/TR-11/017; Gordon et al. 2014) not reachable from this environment; wording from secondary descriptions',
            'target_mm': tgt['acromialheight'], 'target_source': tgt['source'],
            'matched_bony_landmark': 'Lee 2024 LM27 lateral distal acromion (both sides; bilateral heights identical)',
            'bracket_landmark': 'Lee 2024 LM25 exterior acromial angle (posterolateral corner)',
            'LM27_minus_LM25_z_in_c001_mm': r1(lms['left'][LM_PRIMARY - 1][2] - lms['left'][LM_BRACKET - 1][2]),
            'skin_to_bone_offset': 'NOT APPLIED: unquantified. The bony landmark lies below the skin point by the local soft-tissue thickness, so honouring it would lower the bones further.',
        },
        'translation_mm': {'x': 0.0, 'y': 0.0, 'z': r1(dz_mm)},
        'uncertainty_mm': {
            'ANSUR_residual_sd_at_182': tgt['acromialheight']['residual_sd'],
            'landmark_mapping_LM27_vs_LM25': r1(lms['left'][LM_PRIMARY - 1][2] - lms['left'][LM_BRACKET - 1][2]),
            'skin_to_bone_offset': 'unquantified, one-sided (bones lower)',
            'thorax_pitch': 'sensitivity variable, OPEN (bony 7.04 deg used, as c001; living-implied -11.3 deg in sensitivity table)',
        },
        'sensitivity_dz_by_world_and_landmark': sensitivity(target_z, sol, ij_z),
        'before_after_mm': {
            'LM27_z': [r1(lz['left']), r1(lz['left'] + dz_mm)],
            'AC_z': [r1(c1['joint_markers']['acromioclavicular_left']['centre_m'][2] * 1000), r1(J['acromioclavicular_left']['centre_m'][2] * 1000)],
            'GH_z': [r1(c1['joint_markers']['glenohumeral_left']['centre_m'][2] * 1000), r1(J['glenohumeral_left']['centre_m'][2] * 1000)],
            'SC_z': [r1(c1['joint_markers']['sternoclavicular_left']['centre_m'][2] * 1000), r1(sc_z)],
        },
        'closure_vs_retained_trunk': closure,
        'closure_in_any_recorded_variant': all(v['SC_minus_IJ_after_mm'] < 0 for v in sensitivity(target_z, sol, ij_z).values()) and
            'NO: in every recorded pitch/IJ/landmark variant the SC ends below its own jugular notch, against the source relation of SC above IJ',
        'moved_bones': c1['candidate']['moved_bones'], 'moved_markers': c1['candidate']['moved_markers'],
        'scapula_landmarks_world_mm': new_lms,
        'open_questions': [
            'SC closure: the living acromial anchor and the bony SC-on-manubrium relation cannot both hold with the retained a003 trunk and the reconciled clavicle orientation (owner decision needed: lower the thorax/sternum too, or accept a different clavicle orientation on evidence)',
            'skin-to-bone offset at acromiale (direction known, magnitude unquantified)',
            'standing thorax pitch (sensitivity variable, unresolved)',
            'scapulothoracic contact with the retained ribs (rib geometry BLOCKED; not evaluated)'],
        'limitations': c1['candidate']['limitations'],
    }
    c['character_accepted'] = False
    return c


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = Path(o.out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    c = build()
    out.write_text(json.dumps(c, indent=1) + '\n')
    k = c['candidate']
    print(json.dumps({'translation_mm': k['translation_mm'], 'before_after_mm': k['before_after_mm'], 'closure': k['closure_vs_retained_trunk'],
                      'sensitivity': k['sensitivity_dz_by_world_and_landmark']}, indent=1))


if __name__ == '__main__':
    main()
