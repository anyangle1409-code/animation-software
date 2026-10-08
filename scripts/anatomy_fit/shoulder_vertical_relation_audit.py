#!/usr/bin/env python3
"""Shoulder vertical-relation audit and erratum for canonical_shoulder_girdle_solution_182_v1.json (read-only on inputs).

1. Erratum. The v1 solution's vertical_relation_check.reading proposed one hypothesis ("the living suprasternale sits about
   25-35 mm lower relative to C7 and the shoulder than the bony IJ"). Checked here by sign: the C7 relation needs the living
   suprasternale LOWER than the bony IJ, the acromion relation needs it HIGHER. One offset cannot fit both, so the hypothesis
   is WITHDRAWN. The v1 file is not edited (it is hashed into candidate c001); this audit records the correction.
2. IJ-independent check: acromion relative to C7. ANSUR acromial height minus cervicale height against the bony solution's
   acromion relative to C7 at both thorax pitches.
3. Absolute heights of the c001 candidate (bony pitch, IJ at a003) and of the IJ-at-ANSUR world variants, against ANSUR
   standing anchors at 1.82 m, in published residual SDs. No tolerance is invented; z-scores are reported, not graded.

  shoulder_vertical_relation_audit.py --out JSON
"""
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
SOLUTION = ANAT / 'canonical_shoulder_girdle_solution_182_v1.json'
THORAX = ANAT / 'canonical_thorax_frame_182_review_v1.json'
A003 = ANAT / 'character_fit_r95_a003.json'
CAND = ANAT / 'audit/candidates/shoulder_proposal_c001/candidate_record.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    s, t = json.loads(SOLUTION.read_text()), json.loads(THORAX.read_text())
    a, c = json.loads(A003.read_text()), json.loads(CAND.read_text())
    an = t['ansur_standing_anchors_at_182_mm']
    vr = s['vertical_relation_check']
    pc = t['thorax_pitch_conflict']
    r1 = lambda x: round(float(x), 1)
    living_c7_ij = an['C7_minus_IJ_vertical']['mean']
    living_acr_ij = vr['ANSUR_acromion_skin_minus_IJ_skin_mm']['mean']
    bony_c7_ij = {'seth_holzbaur_model': pc['seth_holzbaur_model_frame_C7_above_IJ_mm'], 'bodyparts3d_specimen': pc['bodyparts3d_specimen_C7_above_IJ_mm']}
    bony_ac_ij = vr['solution_AC_minus_IJ_mm']['bony_specimen_deg']
    # offset d = (living suprasternale) - (bony IJ), both relative to the same bony structure:
    # C7: living C7-IJ = bony C7-IJ - d  ->  d = bony - living ; acromion: same form.
    d_c7 = {k: r1(v - living_c7_ij) for k, v in bony_c7_ij.items()}
    d_acr = r1(bony_ac_ij - living_acr_ij)
    erratum = {
        'withdrawn_text': vr['reading'],
        'offset_definition': 'd = living suprasternale height minus bony IJ height, each taken relative to the same bony structure (negative = living lower)',
        'offset_required_by_C7_mm': d_c7,
        'offset_required_by_acromion_mm': d_acr,
        'consistent_single_offset': all(v * d_acr > 0 for v in d_c7.values()),
        'verdict': 'HYPOTHESIS_WITHDRAWN: the C7 relation needs the living suprasternale lower than the bony IJ, the acromion relation '
                   'needs it higher; no single suprasternale offset reconciles both.',
        'v1_file_edited': False,
    }
    # IJ-independent: acromion minus C7 (vertical)
    acr_c7_living = r1(an['acromialheight']['mean'] - an['cervicaleheight']['mean'])
    ac_ij = vr['solution_AC_minus_IJ_mm']
    aa_ij = vr['solution_AA_minus_IJ_mm']
    acr_c7_bony = {
        'bony_specimen_pitch': {'AC_minus_C7_seth': r1(ac_ij['bony_specimen_deg'] - bony_c7_ij['seth_holzbaur_model']),
                                'AC_minus_C7_bodyparts3d': r1(ac_ij['bony_specimen_deg'] - bony_c7_ij['bodyparts3d_specimen']),
                                'AA_minus_C7_bodyparts3d': r1(aa_ij['bony_specimen_deg'] - bony_c7_ij['bodyparts3d_specimen'])},
        'living_implied_pitch': {'AC_minus_C7': r1(ac_ij['living_ANSUR_implied_deg'] - living_c7_ij),
                                 'AA_minus_C7': r1(aa_ij['living_ANSUR_implied_deg'] - living_c7_ij),
                                 'note': 'C7 rise set equal to ANSUR by construction of this pitch'},
    }
    gap = r1(acr_c7_bony['living_implied_pitch']['AC_minus_C7'] - acr_c7_living)
    ij_independent = {
        'ANSUR_acromion_minus_cervicale_mm': acr_c7_living,
        'ANSUR_sd_note': 'acromial height SD and cervicale SD are published separately; their difference SD is not published (not invented here)',
        'solution_bony': acr_c7_bony,
        'smallest_shoulder_excess_over_living_mm': gap,
        'reading': f'Even at the living-implied pitch (which matches C7) the solved AC sits {gap} mm higher relative to C7 than the '
                   'ANSUR acromion does; at the bony pitch the excess is larger. Thorax pitch alone does not resolve it. Candidate '
                   'explanations (not adopted, not tested): skin landmark definitions (acromiale lateral-superior edge vs AC centre; '
                   'cervicale over the C7 spinous tip vs model C7 point), standing shoulder posture differences between the CT/specimen '
                   'cohorts and ANSUR, and cohort/stature scaling. OPEN.',
    }
    # absolute heights
    ij_a003 = r1(a['skeleton_input']['trunk']['ij_bone'][2] * 1000)
    absol = {'ANSUR_182_mm': {k: an[k] for k in ('suprasternaleheight', 'acromialheight', 'cervicaleheight')},
             'a003_bony_IJ_z_mm': ij_a003,
             'a003_IJ_minus_ANSUR_suprasternale_mm': r1(ij_a003 - an['suprasternaleheight']['mean']),
             'records': {}}
    acr = an['acromialheight']
    z = lambda v: round((v - acr['mean']) / acr['residual_sd'], 2)
    def entry(ac_z, lat_acr_z, gh_z):
        return {'AC_centre_z_mm': r1(ac_z), 'lateral_distal_acromion_LM27_z_mm': r1(lat_acr_z), 'GH_z_mm': r1(gh_z),
                'LM27_minus_ANSUR_acromial_mm': r1(lat_acr_z - acr['mean']), 'LM27_z_score_vs_ANSUR_acromial': z(lat_acr_z)}
    jm = a['joint_markers']
    absol['records']['a003'] = {'AC_centre_z_mm': r1(jm['acromioclavicular_left']['centre_m'][2] * 1000),
                                'GH_z_mm': r1(jm['glenohumeral_left']['centre_m'][2] * 1000),
                                'AC_minus_ANSUR_acromial_mm': r1(jm['acromioclavicular_left']['centre_m'][2] * 1000 - acr['mean'])}
    cj = c['joint_markers']
    absol['records']['c001_candidate'] = entry(cj['acromioclavicular_left']['centre_m'][2] * 1000,
                                               c['candidate']['scapula_landmarks_world_mm']['left'][26][2],
                                               cj['glenohumeral_left']['centre_m'][2] * 1000)
    for wk, w in s['variants']['source_scale']['world_mm'].items():
        L = w['left']
        absol['records'][f'solution_source_scale__{wk}'] = entry(L['AC'][2], L['lateral_distal_acromion'][2], L['GH_mixed_cadaver_MRI_24.0'][2])
    absol['reading'] = ('Lowest available variant (bony pitch, IJ at ANSUR suprasternale) still places the lateral acromion above ANSUR '
                        'acromial height; c001 (IJ at the a003 bony IJ, itself above ANSUR suprasternale) is higher still. This is a KNOWN '
                        'DEFECT of c001 inherited from the OPEN vertical relation, not a pass. a003 AC coincides with ANSUR acromial height '
                        '(how a003 reached that was not re-audited here); a003 does not satisfy the bony thorax-relative relations.')
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'AUDIT_OPEN_NOT_RESOLVED',
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (SOLUTION, THORAX, A003, CAND)},
        'erratum_v1_vertical_relation_reading': erratum,
        'ij_independent_acromion_vs_C7': ij_independent,
        'absolute_heights_vs_ANSUR_182': absol,
        'still_open': ['absolute shoulder height relative to the trunk (all variants place the shoulder above the ANSUR acromial height)',
                       'which skin-to-bone landmark offsets apply to acromiale and cervicale (needs a source pairing skin landmarks with bone)',
                       'standing chest/thorax pitch source disagreement (bony 7.04 deg vs living-implied -11.3 deg) - unchanged, unresolved'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    r = build()
    Path(o.out).write_text(json.dumps(r, indent=1) + '\n')
    print(json.dumps({'erratum': r['erratum_v1_vertical_relation_reading']['verdict'][:22],
                      'C7': r['erratum_v1_vertical_relation_reading']['offset_required_by_C7_mm'],
                      'acr': r['erratum_v1_vertical_relation_reading']['offset_required_by_acromion_mm'],
                      'ij_indep': r['ij_independent_acromion_vs_C7'],
                      'abs': r['absolute_heights_vs_ANSUR_182']}, indent=1))


if __name__ == '__main__':
    main()
