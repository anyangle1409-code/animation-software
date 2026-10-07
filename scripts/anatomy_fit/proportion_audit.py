#!/usr/bin/env python3
"""F-PROP-001 / F-GH-001 / F-HJC-001 investigation: independent proportion evidence.

Two parts, both read-only with respect to every model file:

1. ``measure`` (Blender, bpy): surface anthropometry of the r95 body taken from the audit file with
   methods that do not use the fitted joint centres (sections, extremes and loop splits). Each value
   carries its method; values that do depend on the fit are labelled ``fit_dependent``.
2. ``compare`` (numpy): the character against the ANSUR II male public data (4,082 subjects), as
   stature-conditioned z-scores; the fitted joint centres against ANSUR landmark heights; and the
   stature-equation chain (surface -> joint centre -> osteometric length -> Trotter-Gleser) applied
   to every ANSUR subject, to separate method bias from character proportion.

Run:
  python3 proportion_audit.py measure --blend AUDIT.blend --record FIT.json --out character_surface.json
  python3 proportion_audit.py compare --surface character_surface.json --record FIT.json --addendum ADDENDUM.json --ansur ANSUR.csv --out report.json
"""
import argparse, csv, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
SIDES = {'left': 1.0, 'right': -1.0}

# Trotter & Gleser (1952) white males, cm: stature = a * bone + b; SE in cm.
TG = {'femur': (2.38, 61.41, 3.27), 'humerus': (3.08, 70.45, 4.05), 'radius': (3.78, 79.01, 4.32)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ----------------------------------------------------------------------------- Blender measurement
def measure(o):
    import bpy
    from mesh_sections import plane_section
    src = Path(o.blend).resolve()
    before = sha(src)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    body = bpy.data.objects[BODY]
    mw = body.matrix_world
    V = np.array([mw @ v.co for v in body.data.vertices])
    tris = []
    for poly in body.data.polygons:
        vs = list(poly.vertices)
        for i in range(1, len(vs) - 1):
            tris.append([vs[0], vs[i], vs[i + 1]])
    T = np.array(tris)
    rec = json.loads(Path(o.record).read_text())
    floor = float(V[:, 2].min())
    out = {'stature_m': {'value': float(V[:, 2].max() - floor), 'method': 'Vertex (top of head) above the lowest sole vertex.'}}

    def horizontal(z):
        return [l for l in plane_section(V, T, (0, 0, z), (0, 0, 1)) if len(l) >= 8]

    per = {}
    for side, s in SIDES.items():
        m = {}
        # dactylion: follow the arm's own section loop down from the forearm until it ends (the hand
        # hangs beside the thigh, so a plain lowest-vertex search would find the leg)
        prev = None
        for l in horizontal(1.00):
            if (s * l[:, 0]).min() > 0.12:
                prev = l.mean(0)
        z, last = 1.00, None
        while z > 0.30 and prev is not None:
            z -= 0.001
            cand = [l for l in horizontal(z) if np.linalg.norm(l.mean(0)[:2] - prev[:2]) < 0.04 and (s * l[:, 0]).min() > 0.10]
            if not cand:
                break
            prev, last = cand[0].mean(0), z
        m['dactylion_height_m'] = {'value': float(last - floor), 'point': prev.tolist(),
                                   'method': 'Lowest horizontal section (1 mm steps) in which the arm loop, tracked down from the forearm, still exists.'}
        # axilla: highest level at which the arm separates from the trunk in a horizontal section
        ax = None
        for z in np.arange(1.45, 1.20, -0.001):
            loops = horizontal(z)
            arm_loops = [l for l in loops if (s * l[:, 0]).min() > 0.12]
            if arm_loops:
                ax = z
                break
        m['axilla_height_m'] = {'value': float(ax - floor), 'method': 'Highest horizontal section (1 mm steps) where the arm forms its own loop, separate from the trunk.'}
        # crotch: highest level at which the two legs are separate loops (midline gap opens)
        cr = None
        for z in np.arange(1.00, 0.60, -0.001):
            loops = horizontal(z)
            legs = [l for l in loops if (s * l[:, 0]).min() > -0.005 and abs(l[:, 0]).max() < 0.30 and (s * l[:, 0]).mean() > 0.02]
            trunk = [l for l in loops if l[:, 0].min() < -0.01 and l[:, 0].max() > 0.01 and abs(l[:, 0]).max() < 0.30]
            if legs and not trunk:
                cr = z
                break
        m['crotch_height_m'] = {'value': float(cr - floor), 'method': 'Highest horizontal section where the leg loop no longer crosses the midline.'}
        # lateral hip/thigh profile (trochanterion candidate) between crotch and waist
        prof = []
        for z in np.arange(0.70, 1.06, 0.005):
            body_loops = [l for l in horizontal(z) if not (s * l[:, 0]).min() > 0.12 and not (-s * l[:, 0]).min() > 0.12]   # drop the hanging arms
            pts = np.concatenate(body_loops)
            pts = pts[s * pts[:, 0] > 0.0]
            if len(pts):
                prof.append((float(z), float((s * pts[:, 0]).max())))
        prof = np.array(prof)
        loc = [i for i in range(1, len(prof) - 1) if prof[i, 1] >= prof[i - 1, 1] and prof[i, 1] >= prof[i + 1, 1]]
        m['lateral_hip_profile'] = {'z_and_half_width_m': prof.tolist(), 'local_maxima_z_m': [float(prof[i, 0]) for i in loc],
                                    'method': 'Lateral extreme of horizontal sections every 5 mm (0.70-1.05 m); the greater trochanter is not modelled, so maxima are soft-tissue.'}
        # arm sections: area, depth and width between shoulder and wrist (elbow and wrist evidence)
        arm_prof = []
        for z in np.arange(0.86, 1.36, 0.005):
            for l in horizontal(z):
                if (s * l[:, 0]).min() > 0.12:
                    c = l.mean(0)
                    x, y = l[:, 0], l[:, 1]
                    area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
                    arm_prof.append({'z': float(z), 'area_m2': float(area), 'ap_m': float(y.max() - y.min()), 'ml_m': float(x.max() - x.min()),
                                     'anterior_y': float(y.min()), 'posterior_y': float(y.max()), 'centre': c.tolist()})
        m['arm_sections'] = arm_prof
        per[side] = m
    out['sides'] = per
    # shoulder breadths
    sh = []
    for z in np.arange(1.38, 1.52, 0.002):
        pts = np.concatenate(horizontal(z))
        sh.append((float(z), float(pts[:, 0].max() - pts[:, 0].min())))
    sh = np.array(sh)
    out['bideltoid_breadth_m'] = {'value': float(sh[:, 1].max()), 'z_m': float(sh[np.argmax(sh[:, 1]), 0]),
                                  'method': 'Maximum horizontal-section width between 1.38 and 1.52 m (deltoid bulges).'}
    S = rec['landmarks_and_joint_centres']['sides']
    ac = [S[sd]['shoulder']['acromion_lateral_skin']['value_m'] for sd in ('left', 'right')]
    out['biacromial_skin_breadth_m'] = {'value': float(abs(ac[0][0] - ac[1][0])), 'method': 'Distance between the two recorded acromion skin corners (fit record; surface corner, not bone).'}
    out['acromial_height_m'] = {'value': float(np.mean([a[2] for a in ac]) - floor), 'method': 'Recorded acromion skin corner (exact coronal section; surface measurement).'}
    out['suprasternale_height_m'] = {'value': float(rec['landmarks_and_joint_centres']['trunk']['ij_skin']['value_m'][2] - floor), 'method': 'Authored sternal-notch ring front centre (fit record).'}
    ft = rec['landmarks_and_joint_centres']['sides']['left']['foot']
    out['foot_length_m'] = {'value': float(ft['foot_length_m']), 'method': 'Heel to longest toe (fit record).'}
    out['provenance'] = {'blend': str(src.name), 'blend_sha256': before, 'blend_sha256_after': sha(src), 'record': Path(o.record).name,
                         'record_sha256': sha(o.record), 'floor_z_m': floor, 'body_object': BODY, 'vertices': len(V), 'triangles': len(T)}
    with Path(o.out).open('x') as f:
        json.dump(out, f, indent=1)
    print('surface measured', out['stature_m']['value'])


# ----------------------------------------------------------------------------- comparison
def ansur(path):
    rows = list(csv.DictReader(open(path, encoding='cp1252')))
    cols = rows[0].keys()
    return {c: np.array([float(r[c]) for r in rows]) / 1000.0 for c in cols if all(r[c].replace('.', '', 1).isdigit() for r in rows[:50])}


def conditional(A, col, H):
    """Linear regression of an ANSUR measure on stature; prediction and residual SD at stature H (m)."""
    x, y = A['stature'], A[col]
    b, a = np.polyfit(x, y, 1)
    res = y - (a + b * x)
    sd = float(res.std(ddof=2))
    return float(a + b * H), sd, float(b)


def compare(o):
    A = ansur(o.ansur)
    surf = json.loads(Path(o.surface).read_text())
    rec = json.loads(Path(o.record).read_text())
    H = surf['stature_m']['value']
    L = rec['skeleton_input']['sides']
    LJ = rec['landmarks_and_joint_centres']['sides']
    sides = surf['sides']
    mean = lambda k: float(np.mean([sides[s][k]['value'] for s in SIDES]))
    wrist = float(np.mean([LJ[s]['elbow_wrist']['wrist_z_m'] for s in SIDES]))
    elbow = float(np.mean([LJ[s]['elbow_wrist']['elbow_waist_z_m'] for s in SIDES]))
    acrom = surf['acromial_height_m']['value']
    rows = {}

    def row(name, col, value, basis):
        pred, sd, slope = conditional(A, col, H)
        resid = A[col] - (pred + slope * (A['stature'] - H))
        rows[name] = {'ansur_column': col, 'character_m': value, 'ansur_predicted_at_stature_m': pred, 'residual_sd_m': sd,
                      'z': (value - pred) / sd, 'residual_percentile': float(100 * np.mean(resid < value - pred)), 'character_basis': basis}
    row('acromial_height', 'acromialheight', acrom, 'surface (recorded acromion skin corner)')
    row('axilla_height', 'axillaheight', mean('axilla_height_m'), 'surface (section loop split)')
    row('suprasternale_height', 'suprasternaleheight', surf['suprasternale_height_m']['value'], 'authored sternal-notch ring')
    row('crotch_height', 'crotchheight', mean('crotch_height_m'), 'surface (section loop split)')
    row('wrist_height', 'wristheight', wrist, 'surface (minimum-area wrist section, fit record)')
    row('hand_length', 'handlength', wrist - mean('dactylion_height_m'), 'surface (wrist section to lowest fingertip vertex)')
    A['_arm_total'] = A['acromionradialelength'] + A['radialestylionlength'] + A['handlength']
    row('acromion_to_dactylion (ARL+RSL+hand)', '_arm_total', acrom - mean('dactylion_height_m'), 'surface (acromion corner to lowest fingertip, arm hanging)')
    A['_acr_to_wrist'] = A['acromialheight'] - A['wristheight']
    row('acromion_to_wrist (acromial - wrist height)', '_acr_to_wrist', acrom - wrist, 'surface')
    row('lateral_femoral_epicondyle_height', 'lateralfemoralepicondyleheight', float(np.mean([LJ[s]['knee']['epicondyle_lateral_skin']['value_m'][2] for s in SIDES])), 'fit_dependent (soft-tissue joint line + sourced offset)')
    row('tibial_height', 'tibialheight', float(np.mean([LJ[s]['knee']['joint_line_soft_tissue_z_m'] for s in SIDES])), 'surface (minimum-area knee section)')
    row('lateral_malleolus_height', 'lateralmalleolusheight', float(np.mean([LJ[s]['ankle']['leg_foot_junction_z_m'] for s in SIDES])), 'surface (leg-foot junction; malleolus not modelled)')
    row('foot_length', 'footlength', surf['foot_length_m']['value'], 'surface')
    row('biacromial_breadth', 'biacromialbreadth', surf['biacromial_skin_breadth_m']['value'], 'surface corner (ANSUR is bony, caliper)')
    row('bideltoid_breadth', 'bideltoidbreadth', surf['bideltoid_breadth_m']['value'], 'surface')

    # fitted joint centres against ANSUR landmark heights (sourced anatomical relations)
    tr_pred, tr_sd, _ = conditional(A, 'trochanterionheight', H)
    ep_pred, ep_sd, _ = conditional(A, 'lateralfemoralepicondyleheight', H)
    jc = {}
    hjc = float(np.mean([L[s]['HJC'][2] for s in SIDES]))
    jc['HJC'] = {'fitted_z_m': hjc, 'ansur_trochanterion_pred_m': tr_pred, 'trochanterion_residual_sd_m': tr_sd,
                 'relation': 'Greater-trochanter tip lies on average 8 mm above the femoral head centre on neutral AP radiographs (75% above, 15% below, 10% level; two reports).',
                 'implied_hjc_z_m': tr_pred - 0.008, 'difference_m': hjc - (tr_pred - 0.008),
                 'z_vs_trochanterion_spread': (hjc - (tr_pred - 0.008)) / tr_sd}
    kjc = float(np.mean([L[s]['KJC'][2] for s in SIDES]))
    jc['KJC'] = {'fitted_z_m': kjc, 'ansur_lateral_femoral_epicondyle_pred_m': ep_pred, 'residual_sd_m': ep_sd, 'difference_m': kjc - ep_pred,
                 'relation': 'ISB knee centre = epicondyle midpoint, so its height equals epicondyle height.'}
    ac_pred, ac_sd, _ = conditional(A, 'acromialheight', H)
    A['_radiale_h'] = A['acromialheight'] - A['acromionradialelength']
    rad_pred, rad_sd, _ = conditional(A, '_radiale_h', H)
    jc['EJC'] = {'fitted_z_m': elbow, 'ansur_radiale_height_pred_m': rad_pred, 'residual_sd_m': rad_sd,
                 'character_radiale_from_own_acromion_m': acrom - conditional(A, 'acromionradialelength', H)[0],
                 'relation': 'Radiale (radial-head top) lies below the epicondylar axis; the fit assumes 15 mm (capitulum centre 5 mm below the EJC, radius 10 mm).',
                 'implied_ejc_z_m': rad_pred + 0.015, 'difference_m': elbow - (rad_pred + 0.015)}
    wr_pred, wr_sd, _ = conditional(A, 'wristheight', H)
    jc['WJC'] = {'fitted_z_m': wrist, 'ansur_wrist_height_pred_m': wr_pred, 'residual_sd_m': wr_sd, 'difference_m': wrist - wr_pred}
    gh = float(np.mean([L[s]['GH'][2] for s in SIDES]))
    jc['GH'] = {'fitted_z_m': gh, 'character_acromion_skin_m': acrom, 'ansur_acromial_pred_m': ac_pred, 'acromial_residual_sd_m': ac_sd,
                'depth_below_acromion_skin_m': acrom - gh,
                'note': 'ANSUR has no glenohumeral landmark; the depth chain (skin + acromion thickness + AHD + head radius) is the only sourced vertical relation used.'}

    # second check for the humerus: the character's acromion-to-elbow surface span against ANSUR, and the
    # GH depth below the acromion against two open musculoskeletal models (marker-to-joint vertical offset)
    arl_pred, arl_sd, _ = conditional(A, 'acromionradialelength', H)
    jc['upper_arm_surface_check'] = {'character_acromion_skin_to_EJC_m': acrom - elbow, 'ansur_ARL_pred_minus_15mm_m': arl_pred - 0.015,
                                     'difference_m': (acrom - elbow) - (arl_pred - 0.015), 'arl_residual_sd_m': arl_sd}
    jc['GH']['open_model_marker_offsets'] = {
        'Rajagopal2016 (1.70 m generic)': {'acromion_marker_minus_gh_vertical_m': 0.425 - 0.3715, 'scaled_to_character_m': (0.425 - 0.3715) * H / 1.70},
        'Arm26 (Holzbaur 2005 derived)': {'acromion_marker_minus_gh_vertical_m': 0.040 - (-0.007)},
        'note': 'Marker centres lie a marker radius plus skin above the bony landmark; the fitted depth is measured from the skin.'}

    # stature-equation chain applied to every ANSUR subject (method bias), with the fit's own conversions
    jl_off = float(np.mean([np.linalg.norm(np.asarray(L[s]['KJC']) - np.asarray(L[s]['tibial_plateau'])) for s in SIDES]))
    gh_depth = acrom - gh
    chain = {
        'femur': ('(trochanterion - 8 mm) - lateral femoral epicondyle + head radius 24.7 mm + epicondyle-to-joint-line offset',
                  (A['trochanterionheight'] - 0.008) - A['lateralfemoralepicondyleheight'] + 0.0247 + jl_off),
        'humerus': ('acromion-radiale - GH depth below acromion skin - 15 mm (radiale below EJC) + 24.7 mm + 12 mm (fit allowances)',
                    A['acromionradialelength'] - gh_depth - 0.015 + 0.0247 + 0.012),
        'radius': ('radiale-stylion (radial-head surface to styloid, as the fit measures the radius)', A['radialestylionlength']),
    }
    stature_cm = A['stature'] * 100
    tg_chain = {}
    fit = json.loads(Path(o.addendum).read_text())['trotter_gleser_corrected']['bones']
    for bone, (desc, length) in chain.items():
        a, b, se = TG[bone]
        est = a * length * 100 + b
        resid = est - stature_cm
        char = fit[bone + '_left']['difference_m'] * 100
        pct = float(100 * np.mean(resid < char))
        tg_chain[bone] = {'conversion': desc, 'ansur_mean_bias_cm': float(resid.mean()), 'ansur_sd_cm': float(resid.std(ddof=1)),
                          'ansur_p5_p95_cm': [float(np.percentile(resid, 5)), float(np.percentile(resid, 95))],
                          'fraction_of_ansur_beyond_minus_2se': float(np.mean(resid < -2 * se)),
                          'character_difference_cm': char, 'character_percentile_in_ansur_chain': pct,
                          'character_z_in_ansur_chain': float((char - resid.mean()) / resid.std(ddof=1)),
                          'reading': ('within the central 95% of real men processed by the same chain: the stature-equation shortfall is not evidence of a short bone'
                                      if 2.5 <= pct <= 97.5 else 'outside the central 95% of real men processed by the same chain: a character-specific difference remains')}
        if bone == 'femur':     # second, independent estimator: Feldesman et al. (1990) femur/stature = 26.74 %
            fel = length * 100 / 0.2674 - stature_cm
            tg_chain[bone]['feldesman_ratio_check'] = {'ansur_mean_bias_cm': float(fel.mean()), 'ansur_sd_cm': float(fel.std(ddof=1)),
                                                      'character_difference_cm': float(fit['femur_left']['length_m'] * 100 / 0.2674 - H * 100),
                                                      'note': 'Ratio reported to overestimate stature for long femurs (>50 cm); shown as a second estimator only.'}
    return_obj = {'schema_version': 1, 'purpose': 'F-PROP-001 / F-GH-001 / F-HJC-001 independent proportion evidence (read-only).',
                  'sources': {'ANSUR_II_MALE': {'file_sha256': sha(o.ansur), 'subjects': int(len(A['stature'])),
                                                'origin': 'US Army ANSUR II public release (2012 survey), male working file; copy retrieved from raw.githubusercontent.com/hkair/anthropometric-stats (data/ansur/ANSUR II MALE Public.csv). Integrity check: radialestylionlength mean 267.9 mm, SD 15.4 mm, as published.'},
                              'TROCHANTER_HEAD_LEVEL': 'Greater-trochanter tip on average 8 mm above the femoral head centre in 100 AP radiographs (search snippets of two reports).',
                              'TROTTER_GLESER_1952': 'White male equations: femur 2.38F+61.41 (SE 3.27); humerus 3.08H+70.45 (SE 4.05); radius 3.78R+79.01 (SE 4.32).'},
                  'character_stature_m': H, 'surface_vs_ansur': rows, 'joint_centres_vs_ansur_landmarks': jc,
                  'stature_equation_chain_on_ansur': tg_chain,
                  'character_trotter_gleser_corrected': fit,
                  'inputs': {'surface': Path(o.surface).name, 'surface_sha256': sha(o.surface), 'record_sha256': sha(o.record), 'addendum_sha256': sha(o.addendum)}}
    with Path(o.out).open('x') as f:
        json.dump(return_obj, f, indent=1)
    print(json.dumps({k: round(v['z'], 2) for k, v in rows.items()}, indent=0))
    print(json.dumps(jc, indent=0)[:3000])
    print(json.dumps(tg_chain, indent=0))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('measure'); m.add_argument('--blend', required=True); m.add_argument('--record', required=True); m.add_argument('--out', required=True)
    c = sub.add_parser('compare'); c.add_argument('--surface', required=True); c.add_argument('--record', required=True); c.add_argument('--ansur', required=True); c.add_argument('--addendum', required=True); c.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    {'measure': measure, 'compare': compare}[o.cmd](o)


if __name__ == '__main__':
    main()
