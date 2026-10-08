#!/usr/bin/env python3
"""Proposal (for GPT review, not a selection): joint-centre long-bone spans for a 1.82 m adult male.

Owner policy 2026-10-08: the canonical skeleton uses normal 1.82 m male proportions; the mesh is refitted to it.
Each span is computed per subject from the committed ANSUR II male file with the landmark-to-joint conversions
already used as provisional proxies in proportion_audit.py, then regressed on stature and evaluated at 1.82 m (prediction
and residual SD). Trotter-Gleser (bone maximum lengths) and de Leva 1996 (joint-centre proportions) are recorded as
cross-checks with their own definitions; disagreements are reported, never averaged.

  limb_length_proposal.py --out JSON
"""
import argparse, importlib.util, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
H = 1.82
HEAD_RADIUS = 0.0247          # femoral/humeral head radius allowance used by proportion_audit.py
RADIALE_BELOW_EJC = 0.015     # proportion_audit.py: radiale lies 15 mm below the EJC
HUMERUS_FIT_ALLOWANCE = 0.012
# Trotter & Gleser 1952/1958 white male: stature_cm = a * length_cm + b, SEE (cm)
TG = {'femur': (2.38, 61.41, 3.27), 'tibia': (2.52, 78.62, 3.37), 'humerus': (2.89, 78.10, 4.57), 'radius': (3.79, 79.42, 4.66),
      'ulna': (3.76, 75.55, 4.72)}
# de Leva 1996 PRIMARY Table 4, male longitudinal spans at stature 1741 mm.
# Table 1 uses original bony landmarks, not these adjusted joint-centre spans.
# 434.0 is KJC--LMAL; the separate KJC--AJC alternative is 440.3.
DE_LEVA_STATURE = 1741.0
DE_LEVA_STATUS = 'PRIMARY_TABLE4_VERIFIED_CONTEXT_ONLY'
DE_LEVA = {'thigh_HJC_KJC': (422.2, DE_LEVA_STATUS), 'shank_KJC_AJC': (440.3, DE_LEVA_STATUS),
           'upper_arm_GH_EJC': (281.7, DE_LEVA_STATUS), 'forearm_EJC_WJC': (268.9, DE_LEVA_STATUS)}


def audit_module():
    spec = importlib.util.spec_from_file_location('proportion_audit', HERE / 'proportion_audit.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def at_stature(A, values):
    x = A['stature']
    b, a = np.polyfit(x, values, 1)
    res = values - (a + b * x)
    return float(a + b * H), float(res.std(ddof=2)), float(b)


def build():
    pa = audit_module()
    A = pa.ansur(ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv')
    rec = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
    S = rec['skeleton_input']['sides']
    j = rec['joint_markers']
    d = lambda a, b: math.dist(j[a]['centre_m'], j[b]['centre_m'])
    gh_depth = float(np.mean([S[s]['acromion_skin_minus_GH_m'] for s in S])) if 'acromion_skin_minus_GH_m' in S['left'] else 0.047
    jl_off = float(np.mean([math.dist(S[s]['KJC'], S[s]['tibial_plateau']) for s in ('left', 'right')]))

    hjc = A['trochanterionheight'] - 0.008
    kjc = A['lateralfemoralepicondyleheight']
    ajc = A['lateralmalleolusheight']
    spans = {
        'thigh_HJC_KJC': (hjc - kjc, '(trochanterion height - 8 mm) - lateral femoral epicondyle height; vertical span in standing',
                          'femoral mechanical axis is within a few degrees of vertical in standing, so the 3-D span is longer by under 0.5%'),
        'shank_KJC_AJC': (kjc - ajc, 'lateral femoral epicondyle height - lateral malleolus height; vertical span',
                          'ISB AJC is the malleolar midpoint; the medial malleolus sits higher, so AJC is a few mm above the lateral malleolus and this span is slightly long'),
        'upper_arm_GH_EJC': (A['acromionradialelength'] - RADIALE_BELOW_EJC - gh_depth,
                             f'acromion-radiale length - 15 mm (radiale below EJC) - GH depth below acromion skin ({gh_depth * 1000:.0f} mm, corroborated by Arm26 47 mm / Rajagopal 53.5 mm)',
                             'GH depth uncertainty is about +/- 7 mm between the two open models'),
        'forearm_EJC_WJC': (A['radialestylionlength'] + RADIALE_BELOW_EJC,
                            'radiale-stylion length + 15 mm (EJC above radiale); WJC taken at stylion level',
                            'ISB WJC is the styloid midpoint, a few mm proximal of the radial styloid tip, so this span is slightly long'),
    }
    a003 = {'thigh_HJC_KJC': d('hip_left', 'tibiofemoral_left'), 'shank_KJC_AJC': d('tibiofemoral_left', 'talocrural_left'),
            'upper_arm_GH_EJC': d('glenohumeral_left', 'humeroulnar_left'), 'forearm_EJC_WJC': d('humeroulnar_left', 'radiocarpal_left')}
    tg_len = {k: (H * 100 - b) / a * 10 for k, (a, b, _) in TG.items()}
    tg_sd = {k: see / a * 10 for k, (a, b, see) in TG.items()}
    # Trotter-Gleser maximum lengths converted to joint-centre spans with the allowances proportion_audit.py uses
    tg_span = {'thigh_HJC_KJC': (tg_len['femur'] - (HEAD_RADIUS + jl_off) * 1000, f'femur max - head radius 24.7 mm - KJC-to-plateau {jl_off * 1000:.1f} mm'),
               'upper_arm_GH_EJC': (tg_len['humerus'] - (HEAD_RADIUS + HUMERUS_FIT_ALLOWANCE) * 1000, 'humerus max - 24.7 mm head - 12 mm distal allowance'),
               'forearm_EJC_WJC': (tg_len['radius'] + RADIALE_BELOW_EJC * 1000, 'radius max + 15 mm (radial head top is about radiale)'),
               'shank_KJC_AJC': (None, 'TG white-male tibia omits the malleolus (Jantz 1995); no defensible joint-span conversion here')}
    out = {}
    for k, (vals, definition, caveat) in spans.items():
        pred, sd, slope = at_stature(A, vals)
        dl, dl_status = DE_LEVA[k]
        dl_scaled = dl * H * 1000 / DE_LEVA_STATURE
        tgv, tgdef = tg_span[k]
        row = {'proposed_mm': round(pred * 1000, 1), 'ansur_residual_sd_mm': round(sd * 1000, 1),
               'ansur_residual_sd_excludes_joint_conversion_uncertainty': True,
               'proposed_band_1sd_mm': [round((pred - sd) * 1000, 1), round((pred + sd) * 1000, 1)],
               'stature_slope_mm_per_m': round(slope * 1000, 1), 'definition': definition, 'caveat': caveat,
               'n': int(len(vals)),
               'crosscheck_trotter_gleser_mm': None if tgv is None else round(tgv, 1), 'trotter_gleser_conversion': tgdef,
               'crosscheck_de_leva_scaled_mm': round(dl_scaled, 1), 'de_leva_status': dl_status,
               'a003_mm': round(a003[k] * 1000, 1),
               'a003_minus_proposed_mm': round((a003[k] - pred) * 1000, 1),
               'a003_z_vs_ansur': round((a003[k] - pred) / sd, 2)}
        row['agreement'] = {
            'tg_minus_proposed_mm': None if tgv is None else round(tgv - pred * 1000, 1),
            'de_leva_minus_proposed_mm': round(dl_scaled - pred * 1000, 1),
            'tg_within_1sd': None if tgv is None else bool(abs(tgv - pred * 1000) <= sd * 1000),
            'de_leva_within_1sd': bool(abs(dl_scaled - pred * 1000) <= sd * 1000)}
        out[k] = row
    # sensitivity: alternative endpoint conversions and the Trotter-Gleser inversion bias
    x = A['stature']
    def pred(vals):
        return at_stature(A, vals)[0] * 1000
    # Trotter-Gleser equations predict stature from bone; inverting them (bone from stature) overstates bone length
    # above the sample mean stature. Only the direction is asserted: the sample stature SD is not available here.
    tg_inv = {bone: 'inverting stature-on-bone overstates bone length above the sample mean stature' for bone in TG}
    out['thigh_HJC_KJC']['sensitivity_mm'] = {
        'HJC_at_trochanterion_level (classic Nelaton relation, offset 0)': round(pred(A['trochanterionheight'] - kjc), 1),
        'HJC 8 mm below trochanterion (used here, 7 Oct radiographic relation)': round(pred(hjc - kjc), 1),
        'HJC 8 mm above trochanterion': round(pred(A['trochanterionheight'] + 0.008 - kjc), 1),
        'de Leva Table 2 HJC 3.2 mm proximal at 1.741 m, scaled; longitudinal-to-vertical approximation only':
            round(pred(A['trochanterionheight'] + 0.0032 * H / 1.741 - kjc), 1),
        'trotter_gleser_inversion': tg_inv['femur']}
    out['forearm_EJC_WJC']['sensitivity_mm'] = {
        'WJC at stylion (used here)': out['forearm_EJC_WJC']['proposed_mm'],
        'WJC 5 mm proximal of stylion': round(out['forearm_EJC_WJC']['proposed_mm'] - 5, 1),
        'WJC 10 mm proximal of stylion': round(out['forearm_EJC_WJC']['proposed_mm'] - 10, 1)}
    out['upper_arm_GH_EJC']['sensitivity_mm'] = {
        'GH depth 47 mm (Arm26, used here)': out['upper_arm_GH_EJC']['proposed_mm'],
        'GH depth 56 mm (Rajagopal scaled to 1.82 m)': round(out['upper_arm_GH_EJC']['proposed_mm'] - 9, 1)}
    readings = {
        'forearm_EJC_WJC': 'ROBUST shortness signal under the provisional endpoint conversions (281-293 mm), but methods do not yet measure identical endpoints. de Leva is outside the unshifted ANSUR 1-SD band. Select radius and ulna separately only after endpoint mapping; no numerical target selected.',
        'thigh_HJC_KJC': 'CONTESTED: ANSUR 419 (a003 within 0.3 SD) against de Leva 441 and Trotter-Gleser 455 (inflated by inversion). The HJC-trochanterion relation moves ANSUR by up to 16 mm. Resolve endpoint definitions before selecting; a003 is not established as short.',
        'upper_arm_GH_EJC': 'CONSISTENT: ANSUR and de Leva agree within 1 SD and a003 matches; the Trotter-Gleser conversion (+37 mm) depends on an uncertain distal allowance and the inversion bias.',
        'shank_KJC_AJC': 'CONSISTENT with the provisional ANSUR proxy; no gross shank defect established. Primary de Leva KJC-AJC is 440.3 mm at 1.741 m, not the 434.0 mm KJC-LMAL row. Proportional scaling and lateral-malleolus/midpoint definitions remain distinct.'}
    for k, v in readings.items():
        out[k]['reading'] = v
    return {
        'schema_version': 1, 'created': '2026-10-08',
        'status': 'PROPOSAL_FOR_GPT_REVIEW_NOT_SELECTED',
        'freeze_ready': False,
        'owner_policy': 'PROPORTION_POLICY_182CM_MALE (canonical_target_selection_v1.json owner_decisions)',
        'stature_m': H,
        'primary_method': 'Per-subject joint-centre spans from the committed ANSUR II male file (n = 4,082), using the landmark-to-joint '
                          'conversions used as provisional proxies in proportion_audit.py, regressed on stature and evaluated at 1.82 m. Residual SD excludes conversion uncertainty.',
        'why_ansur_primary': 'Stature-conditioned, large, committed and recomputable; its HJC/KJC/EJC conversions were independently '
                             'reviewed as provisional offsets on 7 October, not direct per-subject joint centres. Trotter-Gleser measures dry-bone maximum lengths and needs '
                             'endpoint allowances; inversion is not an independently fitted bone-on-stature prediction. de Leva Table 4 is now primary-verified but uses estimated longitudinal spans and proportional scaling.',
        'de_leva_source_review': 'canonical_de_leva_primary_endpoint_review_v1.json',
        'spans': out,
        'not_decided_here': ['endpoint mapping of each span onto the canonical bone geometry (head, condyles, trochlea, styloids)',
                             'separate ulna target (olecranon/coronoid endpoints)', 'left/right identical by policy unless evidence says otherwise',
                             'whether to adopt ANSUR or reconcile with de Leva where they disagree'],
        'scripts': {'generator': 'scripts/anatomy_fit/limb_length_proposal.py', 'conversions': 'scripts/anatomy_fit/proportion_audit.py'},
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rep = build()
    Path(o.out).write_text(json.dumps(rep, indent=1) + '\n')
    for k, v in rep['spans'].items():
        print(k, v['proposed_mm'], '+/-', v['ansur_residual_sd_mm'], '| TG', v['crosscheck_trotter_gleser_mm'], '| deLeva', v['crosscheck_de_leva_scaled_mm'],
              v['de_leva_status'], '| a003', v['a003_mm'], 'z', v['a003_z_vs_ansur'])


if __name__ == '__main__':
    main()
