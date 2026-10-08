#!/usr/bin/env python3
"""Humerus target review for a 1.82 m male (CP1, humerus region). Evidence and consistency only; nothing selected.

Joint-centre span evidence (ANSUR-derived GH-EJC, de Leva primary SJC-EJC) is tested for consistency with dry-bone
maximum-length evidence (Trotter-Gleser, Mall 2001) through the bone's own end geometry:
    maximum length ~= GH-EJC + humeral-head radius (GH is the head-sphere centre) + distal allowance
                       (EJC on the flexion axis lies about one trochlear/capitellar radius above the distal surface).
Literature values are abstract-level (web search, 8 Oct 2026) and labelled as such.

  humerus_target_review.py --out JSON
"""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
H_MM = 1820.0

END_GEOMETRY_MM = {
    'head_radius_of_curvature': {
        'male_radiologic': {'mean': 28.8, 'sd': 1.9, 'n': '30 male shoulders', 'source': 'Korean radiologic study (J Korean Orthop Assoc 30(5)), modality unstated in abstract'},
        'mixed_cadaver_MRI': {'mean': 24.0, 'sd': 2.1, 'n': '140 shoulders (96 cadaveric, 44 MRI), mixed sex', 'source': 'coronal-plane head radius; size correlates with height'},
    },
    'distal_allowance': {
        'capitellum_sagittal_radius': {'mean': 10.7, 'source': 'CT lateral-column study, 50 elbows, mixed sex (Springer 2023)'},
        'trochlear_width': {'mean': 22.0, 'sd': 3.0, 'source': 'CT trochlea/capitellum study, mixed sex'},
        'note': 'EJC (epicondyle midpoint, close to the trochlea-capitulum flexion axis) sits about one articular radius above the '
                'distal articular surface; a 10.7-13 mm allowance is used as a bracket, not a measured offset.'},
}


def build():
    prop = json.loads((ANAT / 'canonical_limb_length_proposal_182_v1.json').read_text())['spans']['upper_arm_GH_EJC']
    leva = json.loads((ANAT / 'canonical_de_leva_primary_endpoint_review_v1.json').read_text())
    tg_max = (H_MM / 10 - 78.10) / 2.89 * 10                  # Trotter-Gleser white male, inverted (upper-biased above mean stature)
    spans = {'ansur_GH_EJC': prop['proposed_mm'], 'ansur_GH_EJC_rajagopal_depth': prop['sensitivity_mm']['GH depth 56 mm (Rajagopal scaled to 1.82 m)'],
             'de_leva_SJC_EJC_scaled': round(leva['male_Table4_longitudinal_lengths_mm']['SJC_EJC'] * H_MM / 1741.0, 1)}
    head = [END_GEOMETRY_MM['head_radius_of_curvature'][k]['mean'] for k in ('mixed_cadaver_MRI', 'male_radiologic')]
    distal = [10.7, 13.0]
    implied_max = {'lowest': round(min(spans.values()) + head[0] + distal[0], 1), 'highest': round(max(spans.values()) + head[1] + distal[1], 1)}
    implied_span_from_tg = {'lowest': round(tg_max - head[1] - distal[1], 1), 'highest': round(tg_max - head[0] - distal[0], 1)}
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'EVIDENCE_REVIEW_NOT_SELECTED', 'freeze_ready': False,
        'owner_policy': 'PROPORTION_POLICY_182CM_MALE', 'stature_mm': H_MM,
        'joint_centre_span_evidence_mm': spans,
        'joint_span_agreement': f"ANSUR {spans['ansur_GH_EJC']} +/- {prop['ansur_residual_sd_mm']} and de Leva {spans['de_leva_SJC_EJC_scaled']} agree within 1 SD; "
                                f"a003 {prop['a003_mm']} lies inside both.",
        'end_geometry_mm': END_GEOMETRY_MM,
        'maximum_length_evidence_mm': {'trotter_gleser_inverted': round(tg_max, 1),
                                       'trotter_gleser_note': 'Inversion of stature-on-bone regression overstates length above the sample mean; '
                                                              'magnitude unknown without the original covariance.',
                                       'mall_2001_german_male_mean': 334.0, 'mall_note': 'Stature of the German anatomical-institute sample not stated here.'},
        'consistency': {
            'implied_maximum_length_from_joint_spans_mm': implied_max,
            'implied_GH_EJC_from_trotter_gleser_mm': implied_span_from_tg,
            'reading': 'INCONSISTENT AT THE MAXIMUM-LENGTH LEVEL: joint-span evidence implies a maximum humerus length of about '
                       f"{implied_max['lowest']}-{implied_max['highest']} mm, consistent with Mall's 334 mm but below the inverted "
                       f"Trotter-Gleser {round(tg_max, 1)} mm, which in turn implies GH-EJC {implied_span_from_tg['lowest']}-"
                       f"{implied_span_from_tg['highest']} mm. Same pattern as the thigh: surface/joint-centre sources run shorter "
                       'than inverted dry-bone stature equations. a003 is not established as short.'},
        'what_would_close_it': [
            'a known-stature adult male CT or dry-bone sample reporting maximum humerus length together with head radius and '
            'distal articular geometry (resolves the end allowances and the stature relation at once)',
            'or a direct humerus-length-on-stature regression (not an inverted stature equation) for adult males',
            'male-specific trochlear/capitellar radii (current distal values are mixed-sex)'],
        'blockers_kept': ['endpoint-defined humerus target for 1.82 m remains unselected',
                          'humeral head, trochlea and capitulum geometry consistent with the GH and elbow centres'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rep = build()
    Path(o.out).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps(rep['joint_centre_span_evidence_mm']), json.dumps(rep['consistency'], indent=1))


if __name__ == '__main__':
    main()
