#!/usr/bin/env python3
"""Standing thorax reference frame for a 1.82 m male, and what it implies for the SC joint (CP1a). Review only.

Vertical anchors come from the committed ANSUR II male file (standing, living), regressed on stature and evaluated at
1.82 m. The Seth/Holzbaur generic model supplies SC relative to IJ in its landmark-ISB thorax frame
(canonical_sc_primary_model_reference_v1.json). The single BodyParts3D specimen (grade D) supplies one bony four-landmark
set. The living and bony sources disagree on the C7-IJ vertical relation, i.e. on standing thorax pitch; that conflict is
reported, not resolved.

  thorax_frame_review.py --out JSON
"""
import argparse, importlib.util, json, math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
H = 1.82
# BodyParts3D specimen landmarks (HGPT axes, mm; IJ = highest midline point of the manubrial notch, C7/T8 = most posterior
# spinous point, PX = lowest xiphoid point), measured from the human-atlas packing at commit 1c38bf35 (see
# bodyparts3d_single_specimen_axial_shoulder_v1.json for access/hashes). Grade D, one specimen.
SPECIMEN = {'IJ': [3.5, -40.5, 1401.0], 'C7': [-3.5, 78.7, 1446.5], 'PX': [-1.3, -105.9, 1242.1], 'T8': [-0.3, 99.1, 1240.9]}


def pa_module():
    spec = importlib.util.spec_from_file_location('proportion_audit', HERE / 'proportion_audit.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def build():
    pa = pa_module()
    A = pa.ansur(ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv')
    at = lambda v: [round(x * 1000, 1) for x in pa.conditional({'stature': A['stature'], 'v': v}, 'v', H)[:2]]
    anchors = {c: at(A[c]) for c in ('suprasternaleheight', 'cervicaleheight', 'acromialheight', 'chestheight', 'tenthribheight')}
    c7_minus_ij = at(A['cervicaleheight'] - A['suprasternaleheight'])
    ac_minus_ij = at(A['acromialheight'] - A['suprasternaleheight'])
    seth = json.loads((ANAT / 'canonical_sc_primary_model_reference_v1.json').read_text())
    sc_isb = seth['source_to_ISB_frame_review']['SC_in_landmark_ISB_coordinates_mm']   # X anterior, Y superior, Z right (ISB)
    c7_model = [v * 1000 for v in seth['source_markers']['c7']['location_m']]
    sp = {k: np.array(v) for k, v in SPECIMEN.items()}
    sp_c7_ij = float(sp['C7'][2] - sp['IJ'][2])
    sp_line = math.degrees(math.atan2(sp['C7'][2] - sp['IJ'][2], sp['C7'][1] - sp['IJ'][1]))
    model_line = math.degrees(math.atan2(c7_model[1], -c7_model[0]))
    # implied IJ->C7 line elevation if the bony horizontal depth (90-120 mm) were combined with the living vertical
    living_line = [round(math.degrees(math.atan2(c7_minus_ij[0], d)), 1) for d in (120.0, 90.0)]
    # SC height relative to IJ under thorax pitch uncertainty: rotate the ISB (anterior, superior) components by pitch
    pitches = (-20, -10, 0, 10, 20)
    sc_rel_up = {p: round(sc_isb[1] * math.cos(math.radians(p)) + sc_isb[0] * math.sin(math.radians(p)), 1) for p in pitches}
    ij = anchors['suprasternaleheight']
    rec = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
    a_ij = rec['skeleton_input']['trunk']['ij_bone'][2] * 1000
    a_sc = rec['joint_markers']['sternoclavicular_left']['centre_m']
    a_sc_r = rec['joint_markers']['sternoclavicular_right']['centre_m']
    return {
        'schema_version': 1, 'created': '2026-10-08', 'status': 'REVIEW_PROVISIONAL_NOT_SELECTED', 'freeze_ready': False,
        'owner_policy': 'PROPORTION_POLICY_182CM_MALE', 'stature_m': H,
        'ansur_standing_anchors_at_182_mm': {'definitions': 'standing living skin landmarks above the floor; prediction and residual SD',
                                             **{k: {'mean': v[0], 'residual_sd': v[1]} for k, v in anchors.items()},
                                             'C7_minus_IJ_vertical': {'mean': c7_minus_ij[0], 'residual_sd': c7_minus_ij[1]},
                                             'acromion_minus_IJ_vertical': {'mean': ac_minus_ij[0], 'residual_sd': ac_minus_ij[1]}},
        'thorax_pitch_conflict': {
            'living_ANSUR_C7_above_IJ_mm': c7_minus_ij[0],
            'seth_holzbaur_model_frame_C7_above_IJ_mm': round(c7_model[1], 1),
            'bodyparts3d_specimen_C7_above_IJ_mm': round(sp_c7_ij, 1),
            'IJ_to_C7_line_elevation_deg': {'seth_model_frame': round(model_line, 1), 'bodyparts3d_specimen': round(sp_line, 1),
                                            'living_vertical_with_bony_depth_90_120mm': living_line},
            'reading': 'Both bony models put C7 about 33-46 mm above IJ (IJ-C7 line about 20 deg); 4,082 standing men put the '
                       f'skin landmarks {c7_minus_ij[0]} +/- {c7_minus_ij[1]} mm apart. Either the generic/specimen thoraces are '
                       'pitched differently from standing men, or skin landmarks differ from the bony points. The standing thorax '
                       'pitch, and therefore the global ISB thorax axes, stays OPEN.'},
        'SC_relative_to_IJ': {
            'source_ISB_mm': {'anterior': round(sc_isb[0], 1), 'superior': round(sc_isb[1], 1), 'lateral': round(sc_isb[2], 1)},
            'source': 'SETH_2016_SCAPULOTHORACIC_MODEL (Holzbaur-derived generic model, unscaled)',
            'bilateral_SC_centre_breadth_mm': round(2 * sc_isb[2], 1),
            'SC_height_above_IJ_vs_thorax_pitch_mm': {f'{p} deg': v for p, v in sc_rel_up.items()},
            'reading': 'SC is close to IJ, so pitch uncertainty of +/-20 deg moves its height relative to IJ by only a few mm; '
                       'its absolute height is dominated by the IJ height.'},
        'provisional_SC_height_mm': {'value': round(ij[0] + sc_rel_up[0], 1), 'band': [round(ij[0] + min(sc_rel_up.values()) - ij[1], 1),
                                                                               round(ij[0] + max(sc_rel_up.values()) + ij[1], 1)],
                                     'basis': 'ANSUR suprasternale at 1.82 m (skin; bony notch taken at the same height) plus Seth SC-above-IJ'},
        'a003': {'IJ_bone_height_mm': round(a_ij, 1), 'IJ_minus_standard_mm': round(a_ij - ij[0], 1), 'IJ_z': round((a_ij - ij[0]) / ij[1], 2),
                 'SC_height_mm': round(a_sc[2] * 1000, 1), 'SC_minus_provisional_mm': round(a_sc[2] * 1000 - (ij[0] + sc_rel_up[0]), 1),
                 'bilateral_SC_breadth_mm': round(math.dist(a_sc, a_sc_r) * 1000, 1),
                 'reading': 'a003 IJ (and SC with it) sits about 2 SD above the 1.82 m standard because it follows the authored '
                            'r95 sternal notch; under the owner policy the canonical IJ follows the standard. a003 SC breadth '
                            'matches the model breadth.'},
        'still_open': ['IJ-C7 horizontal depth and standing thorax pitch for a 1.82 m male (resolves the ISB axes)',
                       'whether ANSUR skin suprasternale equals the bony notch height (expected within a few mm; unmeasured here)',
                       'scaling of the generic SC offset to 1.82 m (model stature not established)',
                       'SC bone-head vs cartilage-patch vs kinematic centre semantics (canonical_SC_contact_semantics_v1.json)'],
    }


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rep = build()
    Path(o.out).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: rep[k] for k in ('thorax_pitch_conflict', 'SC_relative_to_IJ', 'provisional_SC_height_mm', 'a003')}, indent=1))


if __name__ == '__main__':
    main()
