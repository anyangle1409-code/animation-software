#!/usr/bin/env python3
"""CP1a shoulder-girdle solution for a standard 1.82 m male, as far as registered evidence permits (nothing frozen).

Everything is solved in the source thorax frame (ISB-like: origin IJ; components anterior, superior, lateral for the
side being solved), where the inputs were measured, and only then mapped to HGPT world coordinates for each unresolved
standing thorax pitch. Inputs, all registered:
  SC centre           SETH_2016_SCAPULOTHORACIC_MODEL (Holzbaur-derived), landmark-ISB coordinates
  clavicle midpoint   SHOULDER_STANDING_ALIGNMENT_2020 male standing table (surface SC/AC midpoint)
  clavicle chord      CLAVICLE_QIU_2016_ARTICULAR_CENTRE_CHORD (independent check of the derived chord)
  scapula orientation SHOULDER_STANDING_ALIGNMENT_2020 male standing angles (ISB, relative to thorax)
  scapula position    SHOULDER_STANDING_ALIGNMENT_2020 male AA/TS/AI triangle centroid
  scapula shape       LEE_2024_SCAPULA_RAW_3D 29 landmarks, coordinatewise OLS at 182 cm
  humeral head radius literature (abstract level), recorded in canonical_humerus_target_review_v1.json
  closure checks      ANSUR biacromial breadth at 1.82 m, SCAPULA_AC_LATERAL_2026 (34 +/- 8 mm), Seth AC-GH distance

Clavicle derivation: the surface-landmark offsets at the two clavicle ends cancel at the midpoint to first order, so
AC_centre = 2 * midpoint - SC_centre. The chord this yields is compared with Qiu's articular-centre chord rather than
forced to it. Scapular rotations are applied by anatomical meaning (each sense asserted), not by guessed Euler signs.

  shoulder_girdle_solver.py --out JSON
"""
import argparse, json, math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
H_CM = 182.0
LM = {'superior_angle': 3, 'TS': 5, 'AI': 7, 'root_of_spine': 14, 'glenoid_inferior': 15, 'glenoid_posterior': 16,
      'glenoid_anterior': 17, 'glenoid_superior': 18, 'glenoid_shallowest': 19, 'AA': 25, 'interior_acromial_angle': 26,
      'lateral_distal_acromion': 27}
HEAD_RADIUS_MM = {'male_radiologic_28.8': 28.8, 'mixed_cadaver_MRI_24.0': 24.0}


def rot_x(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(t):
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def scapula_rotation(internal_deg, upward_deg, anterior_tilt_deg):
    """Local (anterior, superior, lateral) -> thorax (anterior, superior, lateral), intrinsic Y-X'-Z'' (ISB order).
    Senses by meaning: internal rotation brings the lateral axis forward; upward rotation raises the lateral axis;
    anterior tilt brings the superior axis forward. Each is asserted on the result."""
    # in (ant=x, sup=y, lat=z) right-handed? x cross y = z  -> (1,0,0)x(0,1,0)=(0,0,1): yes
    Ry = rot_y(math.radians(internal_deg))          # z(lat) -> +x(ant) component: internal rotation
    Rx = rot_x(math.radians(upward_deg))            # rotates y toward z; lateral axis z gets +y?  checked below
    Rz = rot_z(math.radians(anterior_tilt_deg))     # rotates x toward y; superior axis y gets -x? checked below
    # choose signs so that the senses hold
    if (Rx @ [0, 0, 1])[1] < 0:
        Rx = rot_x(-math.radians(upward_deg))
    if (Rz @ [0, 1, 0])[0] < 0:
        Rz = rot_z(-math.radians(anterior_tilt_deg))
    R = Ry @ Rx @ Rz
    lat, sup = R @ [0, 0, 1], R @ [0, 1, 0]
    assert internal_deg <= 0 or lat[0] > 0, 'internal rotation must bring the lateral axis anterior'
    assert upward_deg <= 0 or (Rx @ [0, 0, 1])[1] > 0, 'upward rotation must raise the lateral axis'
    assert anterior_tilt_deg <= 0 or (Rz @ [0, 1, 0])[0] > 0, 'anterior tilt must bring the superior axis anterior'
    return R


def lee_local(model):
    """Right-scapula landmarks in (anterior, superior, lateral) mm, origin AA (LM25), from the stored HGPT-aligned shape."""
    r = np.array(model['relative_HGPT_landmarks_mm']['right'], float)   # right side: anterior=-Y, superior=+Z, lateral=-X
    return np.column_stack((-r[:, 1], r[:, 2], -r[:, 0]))


def thorax_to_world(v, side, ij_world, pitch_deg):
    """Thorax-frame (anterior, superior, lateral) -> HGPT world mm. pitch > 0 tilts the thorax top posteriorly (+Y)."""
    t = math.radians(pitch_deg)
    up = np.array([0, math.sin(t), math.cos(t)])
    ant = np.array([0, -math.cos(t), math.sin(t)])
    lat = np.array([1.0 if side == 'left' else -1.0, 0, 0])               # anatomical left = +X
    return np.asarray(ij_world) + v[0] * ant + v[1] * up + v[2] * lat


def solve(scale):
    reg = {s['id']: s for s in json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())['sources']}
    seth = json.loads((ANAT / 'canonical_sc_primary_model_reference_v1.json').read_text())
    mat = reg['SHOULDER_STANDING_ALIGNMENT_2020']
    qiu = reg['CLAVICLE_QIU_2016_ARTICULAR_CENTRE_CHORD']['male_chord_mm']
    lee = json.loads((ANAT / 'canonical_scapula_measured_landmark_model_v1.json').read_text())
    sc_isb = seth['source_to_ISB_frame_review']['SC_in_landmark_ISB_coordinates_mm']        # anterior, superior, lateral
    mid = mat['male_standing_centres_source_mm']['clavicle_surface_midpoint']
    cen = mat['male_standing_centres_source_mm']['scapula_triangle_centroid']
    ang = mat['male_standing_angles_deg']
    sc = scale * np.array(sc_isb)
    midpoint = scale * np.array([-mid['posterior']['mean'], mid['superior']['mean'], mid['lateral']['mean']])
    ac = 2 * midpoint - sc
    v = ac - sc
    L = float(np.linalg.norm(v))
    elev = math.degrees(math.asin(v[1] / L))
    retr = math.degrees(math.atan2(-v[0], v[2]))
    R = scapula_rotation(ang['scapula_internal_rotation']['mean'], ang['scapula_upward_rotation']['mean'],
                         ang['scapula_anterior_tilt']['mean'])
    local = lee_local(lee)
    tri = [LM['AA'] - 1, LM['TS'] - 1, LM['AI'] - 1]
    rotated = local @ R.T
    centroid_target = scale * np.array([-cen['posterior']['mean'], cen['superior']['mean'], cen['lateral']['mean']])
    scap = rotated - rotated[tri].mean(0) + centroid_target
    g = {k: scap[i - 1] for k, i in LM.items()}
    rim = scap[[LM['glenoid_inferior'] - 1, LM['glenoid_posterior'] - 1, LM['glenoid_anterior'] - 1, LM['glenoid_superior'] - 1]]
    rim_c = rim.mean(0)
    n = np.cross(rim[2] - rim[1], rim[3] - rim[0]); n /= np.linalg.norm(n)
    if n @ (rim_c - scap[LM['TS'] - 1]) < 0:                                   # outward: away from the medial border
        n = -n
    gh = {k: g['glenoid_shallowest'] + r * n for k, r in HEAD_RADIUS_MM.items()}
    seth_ac_gh = float(np.linalg.norm(np.array(seth['GH']['scapula_local_location_m']) - np.array(seth['AC_constraint']['location_body_2_m'])) * 1000)
    checks = {
        'derived_chord_vs_qiu': {'derived_mm': round(L, 1), 'qiu_mean_sd': [qiu['mean'], qiu['sd']], 'z': round((L - qiu['mean']) / qiu['sd'], 2)},
        'clavicle_angles_vs_matsumura_surface_line': {'derived_elevation_deg': round(elev, 1), 'derived_retraction_deg': round(retr, 1),
                                                      'source_elevation_mean_sd': [ang['clavicle_elevation']['mean'], ang['clavicle_elevation']['sd']],
                                                      'source_retraction_mean_sd': [ang['clavicle_retraction']['mean'], ang['clavicle_retraction']['sd']]},
        'AC_to_lateral_distal_acromion_mm': round(float(np.linalg.norm(ac - g['lateral_distal_acromion'])), 1),
        'AC_to_AA_mm': round(float(np.linalg.norm(ac - g['AA'])), 1),
        'AC_to_lateral_acromion_source_mm': {'mean': 34, 'sd': 8, 'range': [23, 52], 'source': 'SCAPULA_AC_LATERAL_2026'},
        'AC_to_GH_mm': {k: round(float(np.linalg.norm(ac - p)), 1) for k, p in gh.items()},
        'AC_to_GH_seth_model_mm': round(seth_ac_gh, 1),
        'bilateral_lateral_distal_acromion_breadth_mm': round(2 * float(g['lateral_distal_acromion'][2]), 1),
        'bilateral_AA_breadth_mm': round(2 * float(g['AA'][2]), 1),
        'bilateral_AC_breadth_mm': round(2 * float(ac[2]), 1),
        'TS_lateral_of_midline_mm': round(float(g['TS'][2]), 1),
        'AI_lateral_of_midline_mm': round(float(g['AI'][2]), 1),
    }
    return {'scale': scale, 'SC': sc, 'AC': ac, 'clavicle_vector': v, 'clavicle_length_mm': L, 'elevation_deg': elev,
            'retraction_deg': retr, 'scapula_rotation': R, 'scapula_landmarks': scap, 'named': g, 'glenoid_normal': n,
            'GH': gh, 'checks': checks}


def reconcile(scale):
    """Joint weighted least squares over AC (3), scapula translation (3) and scapula rotations (3), using only published
    spreads: clavicle midpoint SD (Matsumura male), articular chord SD (Qiu), AC-to-lateral-acromion SD (2026 cadaver),
    scapula triangle-centroid SD and the three angle SDs (Matsumura male). SC is held at the Seth model centre (no SD is
    published for it). Returns the fit and every residual as a z-score; a large residual is a reported tension."""
    from scipy.optimize import least_squares
    reg = {x['id']: x for x in json.loads((ANAT / 'canonical_proportion_sources_v1.json').read_text())['sources']}
    seth = json.loads((ANAT / 'canonical_sc_primary_model_reference_v1.json').read_text())
    mat = reg['SHOULDER_STANDING_ALIGNMENT_2020']
    qiu = reg['CLAVICLE_QIU_2016_ARTICULAR_CENTRE_CHORD']['male_chord_mm']
    lat_ac = reg['SCAPULA_AC_LATERAL_2026']['values_mm']['lateral_acromion_to_AC_joint']
    local = lee_local(json.loads((ANAT / 'canonical_scapula_measured_landmark_model_v1.json').read_text()))
    sc = scale * np.array(seth['source_to_ISB_frame_review']['SC_in_landmark_ISB_coordinates_mm'])
    m = mat['male_standing_centres_source_mm']; a = mat['male_standing_angles_deg']
    mid = scale * np.array([-m['clavicle_surface_midpoint']['posterior']['mean'], m['clavicle_surface_midpoint']['superior']['mean'],
                            m['clavicle_surface_midpoint']['lateral']['mean']])
    mid_sd = scale * np.array([m['clavicle_surface_midpoint'][k]['sd'] for k in ('posterior', 'superior', 'lateral')])
    cen = scale * np.array([-m['scapula_triangle_centroid']['posterior']['mean'], m['scapula_triangle_centroid']['superior']['mean'],
                            m['scapula_triangle_centroid']['lateral']['mean']])
    cen_sd = scale * np.array([m['scapula_triangle_centroid'][k]['sd'] for k in ('posterior', 'superior', 'lateral')])
    ang = np.array([a['scapula_internal_rotation']['mean'], a['scapula_upward_rotation']['mean'], a['scapula_anterior_tilt']['mean']])
    ang_sd = np.array([a['scapula_internal_rotation']['sd'], a['scapula_upward_rotation']['sd'], a['scapula_anterior_tilt']['sd']])
    chord, chord_sd = scale * qiu['mean'], scale * qiu['sd']
    tri = [LM['AA'] - 1, LM['TS'] - 1, LM['AI'] - 1]

    def pose(x):
        R = scapula_rotation(*x[6:9])
        P = local @ R.T
        return P - P[tri].mean(0) + x[3:6]

    def residuals(x):
        ac = x[0:3]; P = pose(x)
        return np.concatenate([((sc + ac) / 2 - mid) / mid_sd, [(np.linalg.norm(ac - sc) - chord) / chord_sd],
                               [(np.linalg.norm(ac - P[LM['lateral_distal_acromion'] - 1]) - lat_ac['mean']) / lat_ac['sd']],
                               (P[tri].mean(0) - cen) / cen_sd, (x[6:9] - ang) / ang_sd])
    x0 = np.concatenate([2 * mid - sc, cen, ang])
    fit = least_squares(residuals, x0)
    r = residuals(fit.x)
    labels = ['midpoint_anterior', 'midpoint_superior', 'midpoint_lateral', 'chord', 'AC_to_lateral_acromion',
              'centroid_anterior', 'centroid_superior', 'centroid_lateral', 'internal_rotation', 'upward_rotation', 'anterior_tilt']
    P = pose(fit.x); ac = fit.x[0:3]; v = ac - sc; L = float(np.linalg.norm(v))
    return {'AC': ac, 'scapula_landmarks': P, 'angles_deg': fit.x[6:9], 'centroid': fit.x[3:6], 'clavicle_length_mm': L,
            'elevation_deg': math.degrees(math.asin(v[1] / L)), 'retraction_deg': math.degrees(math.atan2(-v[0], v[2])),
            'residual_z': {k: round(float(z), 2) for k, z in zip(labels, r)}, 'chi2': round(float(r @ r), 2), 'dof': len(r) - len(fit.x),
            'SC': sc, 'rotation': scapula_rotation(*fit.x[6:9])}


def pitches():
    rev = json.loads((ANAT / 'canonical_thorax_frame_182_review_v1.json').read_text())
    tf = rev['thorax_pitch_conflict']
    # specimen thorax pitch (grade D bony); living-implied pitch rotates the bony IJ->C7 vector so its rise equals ANSUR's
    import thorax_frame_review as tfr
    sp = {k: np.array(v) for k, v in tfr.SPECIMEN.items()}
    upv = (sp['IJ'] + sp['C7']) / 2 - (sp['PX'] + sp['T8']) / 2
    bony = math.degrees(math.atan2(upv[1], upv[2]))
    d = sp['C7'] - sp['IJ']
    r = math.hypot(d[1], d[2]); a0 = math.atan2(d[2], d[1])
    need = math.asin(min(1.0, tf['living_ANSUR_C7_above_IJ_mm'] / r))
    living = bony - math.degrees(need - a0)
    return {'bony_specimen_deg': round(bony, 2), 'living_ANSUR_implied_deg': round(living, 2),
            'definition': 'tilt of the thorax Y axis (PX/T8 midpoint to IJ/C7 midpoint) from vertical; + = top posterior',
            'living_derivation': 'bony IJ->C7 vector (specimen) rotated until its vertical rise equals the ANSUR C7-IJ value'}


def build():
    import sys
    sys.path.insert(0, str(HERE))
    a = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
    ij_a003 = np.array(a['skeleton_input']['trunk']['ij_bone']) * 1000
    tf = json.loads((ANAT / 'canonical_thorax_frame_182_review_v1.json').read_text())
    ij_std = ij_a003.copy(); ij_std[2] = tf['ansur_standing_anchors_at_182_mm']['suprasternaleheight']['mean']
    P = pitches()
    scale_std = H_CM / 171.4
    out = {'schema_version': 1, 'created': '2026-10-08', 'status': 'PROVISIONAL_SOLUTION_NOT_SELECTED_NOT_FROZEN', 'freeze_ready': False,
           'owner_policy': 'PROPORTION_POLICY_182CM_MALE', 'stature_cm': H_CM, 'pitch_family': P, 'variants': {}}
    for sname, scale in (('source_scale', 1.0), ('stature_proportional_182_over_171_4', scale_std)):
        s = solve(scale)
        rc = reconcile(scale)
        rc_named = {k: rc['scapula_landmarks'][i - 1] for k, i in LM.items()}
        rim = rc['scapula_landmarks'][[LM['glenoid_inferior'] - 1, LM['glenoid_posterior'] - 1, LM['glenoid_anterior'] - 1, LM['glenoid_superior'] - 1]]
        n = np.cross(rim[2] - rim[1], rim[3] - rim[0]); n /= np.linalg.norm(n)
        if n @ (rim.mean(0) - rc_named['TS']) < 0:
            n = -n
        rc_gh = {k: rc_named['glenoid_shallowest'] + r * n for k, r in HEAD_RADIUS_MM.items()}
        rnd = lambda x: [round(float(t), 2) for t in x]
        world = {}
        for pname in ('bony_specimen_deg', 'living_ANSUR_implied_deg'):
            for ijname, ij in (('IJ_at_a003', ij_a003), ('IJ_at_ANSUR_182', ij_std)):
                w = {}
                for side in ('left', 'right'):
                    w[side] = {'SC': rnd(thorax_to_world(rc['SC'], side, ij, P[pname])), 'AC': rnd(thorax_to_world(rc['AC'], side, ij, P[pname])),
                               **{f'GH_{k}': rnd(thorax_to_world(p, side, ij, P[pname])) for k, p in rc_gh.items()},
                               **{k: rnd(thorax_to_world(p, side, ij, P[pname])) for k, p in rc_named.items()},
                               'scapula_all_29': [rnd(thorax_to_world(p, side, ij, P[pname])) for p in rc['scapula_landmarks']]}
                world[f'{pname}__{ijname}'] = w
        ac = rc['AC']; g = rc_named
        rc_checks = {'AC_to_lateral_distal_acromion_mm': round(float(np.linalg.norm(ac - g['lateral_distal_acromion'])), 1),
                     'AC_to_GH_mm': {k: round(float(np.linalg.norm(ac - p)), 1) for k, p in rc_gh.items()},
                     'AC_to_GH_seth_model_mm': s['checks']['AC_to_GH_seth_model_mm'],
                     'bilateral_AC_breadth_mm': round(2 * float(ac[2]), 1), 'bilateral_AA_breadth_mm': round(2 * float(g['AA'][2]), 1),
                     'bilateral_max_acromion_breadth_mm': round(2 * max(float(g['AA'][2]), float(g['lateral_distal_acromion'][2]), float(g['interior_acromial_angle'][2])), 1),
                     'ANSUR_biacromial_skin_182_mm': {'mean': 425.2, 'residual_sd': 16.2},
                     'TS_lateral_of_midline_mm': round(float(g['TS'][2]), 1), 'AI_lateral_of_midline_mm': round(float(g['AI'][2]), 1)}
        out['variants'][sname] = {
            'reconciled': {'method': 'joint weighted least squares; SC fixed at the Seth centre; published SDs only',
                           'clavicle_joint_centre_length_mm': round(rc['clavicle_length_mm'], 1),
                           'clavicle_elevation_deg': round(rc['elevation_deg'], 1), 'clavicle_retraction_deg': round(rc['retraction_deg'], 1),
                           'scapula_angles_deg': {'internal_rotation': round(float(rc['angles_deg'][0]), 1), 'upward_rotation': round(float(rc['angles_deg'][1]), 1),
                                                  'anterior_tilt': round(float(rc['angles_deg'][2]), 1)},
                           'residual_z': rc['residual_z'], 'chi2': rc['chi2'], 'dof': rc['dof'],
                           'thorax_frame_mm': {'SC': rnd(rc['SC']), 'AC': rnd(rc['AC']), 'scapula_triangle_centroid': rnd(rc['centroid']),
                                               'scapula_named_landmarks': {k: rnd(p) for k, p in rc_named.items()},
                                               'GH': {k: rnd(p) for k, p in rc_gh.items()}},
                           'checks': rc_checks},
            'unreconciled_direct': {'note': 'Midpoint-derived clavicle with the scapula placed only by Matsumura centroid/angles. '
                                            'Kept as evidence of the tension the reconciliation resolves.'},
            'thorax_frame_mm': {'SC': rnd(s['SC']), 'AC': rnd(s['AC']), 'clavicle_vector': rnd(s['clavicle_vector']),
                                'scapula_named_landmarks': {k: rnd(p) for k, p in s['named'].items()},
                                'scapula_all_29_landmarks': [rnd(p) for p in s['scapula_landmarks']],
                                'glenoid_outward_normal': rnd(s['glenoid_normal']),
                                'GH': {k: rnd(p) for k, p in s['GH'].items()},
                                'axes': 'anterior, superior, lateral (mirror lateral for the left side); origin IJ'},
            'clavicle_joint_centre_length_mm': round(s['clavicle_length_mm'], 1),
            'clavicle_elevation_deg': round(s['elevation_deg'], 1), 'clavicle_retraction_deg': round(s['retraction_deg'], 1),
            'scapula_rotation_local_to_thorax': [rnd(r) for r in s['scapula_rotation']],
            'checks': s['checks'], 'world_mm': world}
    v0, v1 = out['variants']['source_scale'], out['variants']['stature_proportional_182_over_171_4']
    ansur_bi = 425.2
    r0, r1 = v0['reconciled'], v1['reconciled']
    out['preferred_provisional_variant'] = 'source_scale'
    out['readings'] = {
        'tension': f"Unreconciled, the midpoint-derived clavicle (retraction {v0['clavicle_retraction_deg']} deg) puts AC "
                   f"{v0['checks']['AC_to_lateral_distal_acromion_mm']} mm from the lateral acromion of the Matsumura-placed scapula "
                   '(source 34 +/- 8 mm): the inputs cannot all hold at their means. The derived retraction is very sensitive to the '
                   'generic Seth SC anteroposterior position (about 2 deg per mm of the AC posterior component).',
        'clavicle_length': f"Reconciled joint-centre chord {r0['clavicle_joint_centre_length_mm']} mm (Qiu 152.9 +/- 9.3; residual z "
                           f"{r0['residual_z']['chord']}). Source cohorts are about 1.71 m.",
        'standing_angle': f"Reconciled joint-centre clavicle line relative to the thorax: elevation {r0['clavicle_elevation_deg']} deg, "
                          f"retraction {r0['clavicle_retraction_deg']} deg (source surface line 8 +/- 4 and 23 +/- 6). World-frame angles depend "
                          'on the unresolved thorax pitch; both pitch variants are given.',
        'AC_and_scapula': f"Reconciled fit chi2 {r0['chi2']} on {r0['dof']} dof, every residual within {max(abs(z) for z in r0['residual_z'].values())} SD. "
                          f"AC to lateral acromion {r0['checks']['AC_to_lateral_distal_acromion_mm']} mm; scapula angles "
                          f"{r0['scapula_angles_deg']}. AC-GH is {r0['checks']['AC_to_GH_mm']} against the Seth model's "
                          f"{r0['checks']['AC_to_GH_seth_model_mm']} mm: "
                          + ('bracketed by the two head radii, an independent agreement' if min(r0['checks']['AC_to_GH_mm'].values())
                             <= r0['checks']['AC_to_GH_seth_model_mm'] <= max(r0['checks']['AC_to_GH_mm'].values()) else 'not bracketed, a reported discrepancy')
                          + ' (GH here is glenoid point plus head radius, not a sphere fit).',
        'stature_scaling': f"ANSUR 1.82 m biacromial breadth is 425.2 +/- 16.2 mm (skin). Source-scale maximum bony acromion breadth is "
                           f"{r0['checks']['bilateral_max_acromion_breadth_mm']} mm; stature-proportional is {r1['checks']['bilateral_max_acromion_breadth_mm']} mm. "
                           'The source-scale offsets fit the 1.82 m breadth better, so they are the preferred provisional variant; the Lee scapula '
                           'shape itself is already conditioned on 182 cm.',
        'GH': 'Glenoid shallowest point plus the outward glenoid normal times a humeral-head radius (24.0 or 28.8 mm). Not a measured GH centre.'}
    # vertical relation of the shoulder to IJ: bony sources against ANSUR living skin landmarks
    import importlib.util
    spec = importlib.util.spec_from_file_location('proportion_audit', HERE / 'proportion_audit.py')
    pa = importlib.util.module_from_spec(spec); spec.loader.exec_module(pa)
    A = pa.ansur(ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv')
    acr_ij = [round(x * 1000, 1) for x in pa.conditional({'stature': A['stature'], 'v': A['acromialheight'] - A['suprasternaleheight']}, 'v', H_CM / 100)[:2]]
    spec_sh = json.loads((ANAT / 'bodyparts3d_single_specimen_axial_shoulder_v1.json').read_text())['shoulder']
    import thorax_frame_review as tfr
    sp_ij = tfr.SPECIMEN['IJ'][2]
    wv = {p: v0['world_mm'][f'{p}__IJ_at_a003']['left'] for p in ('bony_specimen_deg', 'living_ANSUR_implied_deg')}
    ij_z = float(ij_a003[2])
    out['vertical_relation_check'] = {
        'ANSUR_acromion_skin_minus_IJ_skin_mm': {'mean': acr_ij[0], 'residual_sd': acr_ij[1]},
        'solution_AC_minus_IJ_mm': {p: round(w['AC'][2] - ij_z, 1) for p, w in wv.items()},
        'solution_AA_minus_IJ_mm': {p: round(w['AA'][2] - ij_z, 1) for p, w in wv.items()},
        'bodyparts3d_AC_minus_IJ_mm': round((spec_sh['left']['contact_2mm']['AC_proxy_mm'][2] + spec_sh['right']['contact_2mm']['AC_proxy_mm'][2]) / 2 - sp_ij, 1),
        'reading': 'Bony sources agree (AC about 23-27 mm above IJ); ANSUR living skin puts the acromion only about 3 mm above the '
                   'suprasternale. With the C7 conflict (living 80.7 mm vs bony 33-58 mm), no single thorax pitch fits both living '
                   'relations (they pull in opposite directions). One hypothesis fits both: the living suprasternale landmark sits '
                   'about 25-35 mm lower relative to C7 and the shoulder than the bony IJ of the models. Recorded as a HYPOTHESIS, '
                   'not adopted: absolute shoulder height relative to the trunk stays OPEN.'}
    out['a003_comparison_mm'] = {
        'clavicle_SC_AC': round(math.dist(a['joint_markers']['sternoclavicular_left']['centre_m'], a['joint_markers']['acromioclavicular_left']['centre_m']) * 1000, 1),
        'bilateral_AC': round(math.dist(a['joint_markers']['acromioclavicular_left']['centre_m'], a['joint_markers']['acromioclavicular_right']['centre_m']) * 1000, 1),
        'AA_TS': round(math.dist(a['skeleton_input']['sides']['left']['AA'], a['skeleton_input']['sides']['left']['TS']) * 1000, 1),
        'AC_GH': round(math.dist(a['joint_markers']['acromioclavicular_left']['centre_m'], a['joint_markers']['glenohumeral_left']['centre_m']) * 1000, 1)}
    out['still_open'] = ['standing thorax pitch (living vs bony sources; canonical_thorax_frame_182_review_v1.json)',
                         'clavicle stature allometry from source cohorts (~1.71 m) to 1.82 m',
                         'AC articular centre on the scapula (no Lee landmark for the clavicular facet)',
                         'measured GH centre (sphere fit) rather than glenoid point plus head radius',
                         'scapulothoracic contact against a curved rib cage (a003 ribs are straight)']
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rep = build()
    Path(o.out).write_text(json.dumps(rep, indent=1) + '\n')
    for k, v in rep['variants'].items():
        print(k, 'L', v['clavicle_joint_centre_length_mm'], 'elev', v['clavicle_elevation_deg'], 'retr', v['clavicle_retraction_deg'])
        print('  ', json.dumps(v['checks']))
    print(rep['pitch_family']); print(rep['a003_comparison_mm'])


if __name__ == '__main__':
    main()
