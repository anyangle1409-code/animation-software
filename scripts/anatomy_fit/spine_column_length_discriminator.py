#!/usr/bin/env python3
"""Spine column length discriminator (read-only; selects nothing, freezes nothing).

Question: the committed C2-S1 level stack (canonical_spine_level_stack_v1.json) and the c004 interpolated spine
disagree on the vertebral column length (C3-L5 stick sum 625.6 mm vs 536.0 mm sourced bodies + discs), and the two
committed thoracic body-height sources differ by ~30 %. Which stack is compatible with independent stature-conditioned
evidence for a 1.82 m man?

Two independent checks, both using committed data only:

1. ABSOLUTE (ANSUR II, n = 4,082 men, OLS on stature at 1.82 m): skin cervicale height (C7 spinous tip) above the floor,
   minus the provisional P1 S1 superior-endplate centre height (retained HJC + Hasegawa male PTh/PT; HJC is the
   grade-A corroborated anchor). The model side is the sagittal chain S1 -> L5/S1 disc -> ... -> C7 body centre
   built from the stack heights and the P1 lumbar endplate orientations, plus the C7 spinous-tip offset taken from
   the single BodyParts3D specimen in the C7 local frame (grade D, used only as an offset, never as a target).
   The thoracic per-level tilt distribution is NOT known (canonical_thoracic_qualitative_constraints_v1.json); the
   vertical projection is therefore reported as an ENVELOPE over every monotone distribution that meets the
   committed qualitative constraints (T1..T12 total 43.7 deg, T7 near horizontal, tilts monotone), not as a value.
2. SCALE-FREE (BodyParts3D single specimen, grade D): thoracic / lumbar centre-path ratio, which does not depend on
   stature or posture, compared with each candidate stack's ratio.

Lumbar definition bracket (canonical_lumbar_endplate_surface_semantics_v1.json): the CT stack uses MIDDLE body height and
AVERAGE disc height; the endplate-centre path is better approximated by EDGE heights (Hegazy 2014 male MRI), because
the endplate concavity lost from the middle body height reappears in the central disc height. Both are reported.

  spine_column_length_discriminator.py --models-dir HUMAN_ATLAS/public/models --out JSON
"""
import argparse, csv, hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
IN = {
    'stack': ANAT / 'canonical_spine_level_stack_v1.json',
    'geom': ANAT / 'canonical_spine_geometry_audit_v1.json',
    'frames': ANAT / 'canonical_lumbar_body_disc_frames_p1.json',
    's1': ANAT / 'canonical_s1_pelvic_frame_p1.json',
    'pose': ANAT / 'canonical_spine_reference_pose_p1.json',
    'thor_q': ANAT / 'canonical_thoracic_qualitative_constraints_v1.json',
    'edges': ANAT / 'canonical_lumbar_edge_height_crosscheck_v1.json',
    'concavity': ANAT / 'canonical_lumbar_endplate_surface_semantics_v1.json',
    'bp3d': ANAT / 'bodyparts3d_single_specimen_axial_shoulder_v1.json',
    'ansur': ANAT / 'sources/ansur2/ANSUR_II_MALE_Public.csv',
    'c004': ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json',
    'a003': ANAT / 'character_fit_r95_a003.json',
}
STATURE_MM = 1820.0
T = [f'T{i}' for i in range(1, 13)]
L = [f'L{i}' for i in range(1, 6)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(k):
    return json.loads(IN[k].read_text())


# ---------------------------------------------------------------- ANSUR
def ansur_at(col, stature=STATURE_MM):
    xs, ys = [], []
    with open(IN['ansur'], newline='', encoding='latin-1') as fh:
        for row in csv.DictReader(fh):
            xs.append(float(row['stature'])); ys.append(float(row[col]))
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx; a = my - b * mx
    res = [y - (a + b * x) for x, y in zip(xs, ys)]
    rsd = math.sqrt(sum(r * r for r in res) / (n - 2))
    se_mean = rsd * math.sqrt(1 / n + (stature - mx) ** 2 / sxx)
    return {'column': col, 'n': n, 'mean_stature_mm': round(mx, 1), 'slope': round(b, 4), 'prediction_mm': round(a + b * stature, 1),
            'residual_sd_mm': round(rsd, 1), 'se_of_mean_prediction_mm': round(se_mean, 2)}


# ---------------------------------------------------------------- sagittal geometry (Y posterior, Z up; angle phi of an
# element axis from vertical, positive = the superior end leans ANTERIOR (-Y))
def axis_angle_from_normal(n):
    """Endplate normal [0, ny, nz] -> lean of the column axis (deg, + = anterior)."""
    return math.degrees(math.atan2(-n[1], n[2]))


def walk(start_yz, elements):
    y, z = start_yz
    pts = [(y, z)]
    for h, phi in elements:
        r = math.radians(phi)
        y -= h * math.sin(r); z += h * math.cos(r)
        pts.append((y, z))
    return pts


def lumbar_elements(stack_mode, frames, stack, edges):
    """L5/S1 disc up to the L1 body, inferior to superior, with P1 orientations.
    Returns [(height, phi)], plus the L1 superior-endplate axis angle."""
    g = frames['geometry']
    sup = {k: axis_angle_from_normal(v['normal']) for k, v in g['superior_frames'].items()}
    inf = {k: axis_angle_from_normal(v['normal']) for k, v in g['inferior_frames'].items()}
    disc_h, body_h = {}, {}
    for lv in L:
        if stack_mode == 'CT_middle_body_avg_disc':
            body_h[lv] = stack['vertebral_bodies_mm'][lv]['candidate']
        else:                                   # MRI edge heights: mean of anterior and posterior border heights
            e = edges['body_edge_heights'][lv]; body_h[lv] = (e['anterior_mean_mm'] + e['posterior_mean_mm']) / 2
    for a, b in [('L1', 'L2'), ('L2', 'L3'), ('L3', 'L4'), ('L4', 'L5'), ('L5', 'S1')]:
        k = f'{a}/{b}'
        if stack_mode == 'CT_middle_body_avg_disc':
            disc_h[k] = stack['disc_gaps_mm'][k]['candidate']
        else:
            e = edges['disc_edge_gaps'][k]; disc_h[k] = (e['anterior_mean_mm'] + e['posterior_mean_mm']) / 2
    els = []
    below = 'S1'
    for lv in ['L5', 'L4', 'L3', 'L2', 'L1']:
        k = f'{lv}/{below}'
        els.append((disc_h[k], (inf[lv] + sup[below]) / 2, f'disc {k}'))
        els.append((body_h[lv], (inf[lv] + sup[lv]) / 2, f'body {lv}'))
        below = lv
    return els, sup['L1'], body_h, disc_h


def thoracic_heights(variant, stack, geom):
    body = {}
    for t in T:
        if variant == 'A_anatomical_2011':
            body[t] = stack['vertebral_bodies_mm'][t]['candidate']
        else:
            body[t] = geom['comparisons'][t.lower()]['sourceB_mean_mm']
    disc = {f'T{i}/T{i + 1}': stack['disc_gaps_mm'][f'T{i}/T{i + 1}']['candidate'] for i in range(1, 12)}
    return body, disc


def thoracic_envelope(body, disc, phi_L1sup, kyphosis_deg, t7_band_deg=3.0, steps=None):
    """Vertical rise from the T12 inferior endplate centre to the T1 superior endplate centre, min/max over every
    monotone per-element axis-angle sequence from phi(T12 inferior) = phi_L1sup (T12/L1 disc taken parallel; its
    sensitivity is reported separately) to phi(T1 superior) = phi_L1sup + kyphosis, with T7 inside +/-t7_band of
    horizontal-endplate (phi = 0). Elements T12 body .. T1 body with discs between (discs carry ~0 wedge,
    canonical_thoracic_qualitative_constraints_v1.json: 0.6 %). Exhaustive over step positions on a 1-deg grid of
    two-level 'step' sequences, which are the extremal sequences of the monotone set for a concave cos objective."""
    order = list(reversed(T))                        # T12 .. T1
    lo_phi, hi_phi = phi_L1sup, phi_L1sup + kyphosis_deg
    hs = []
    for i, t in enumerate(order):
        hs.append((body[t], t))
        if t != 'T1':
            nxt = order[i + 1]
            hs.append((disc[f'{nxt}/{t}'], f'{nxt}/{t}'))
    # element angle sequences: body angles monotone non-decreasing from lo to hi; a disc takes the mean of neighbours
    import itertools
    best = {'min': None, 'max': None}
    grid = [lo_phi + k * (hi_phi - lo_phi) / 40 for k in range(41)]
    idx_T7 = order.index('T7')

    def rise(bang):
        tot = 0.0
        for j, t in enumerate(order):
            tot += body[t] * math.cos(math.radians(bang[j]))
            if t != 'T1':
                tot += disc[f'{order[j + 1]}/{t}'] * math.cos(math.radians((bang[j] + bang[j + 1]) / 2))
        return tot
    # enumerate monotone 3-plateau sequences: [lo .. a] on T12..T8, T7 in band, [b .. hi] on T6..T1, each block a
    # two-value step at any position; this spans the extremes of sum cos over the monotone set
    n_low = idx_T7                                    # T12..T8 count
    n_high = len(order) - idx_T7 - 1                  # T6..T1 count
    t7_choices = [x for x in grid if -t7_band_deg <= x <= t7_band_deg] or [0.0]
    for t7 in t7_choices:
        for v1 in [x for x in grid if lo_phi <= x <= t7]:
            for s1 in range(n_low + 1):
                low = [lo_phi] * s1 + [v1] * (n_low - s1)
                for v2 in [x for x in grid if t7 <= x <= hi_phi]:
                    for s2 in range(n_high + 1):
                        high = [v2] * s2 + [hi_phi] * (n_high - s2)
                        seq = low + [t7] + high
                        seq[0] = lo_phi; seq[-1] = hi_phi       # end elements pinned to the end endplate angles
                        r = rise(seq)
                        if best['min'] is None or r < best['min'][0]:
                            best['min'] = (r, seq)
                        if best['max'] is None or r > best['max'][0]:
                            best['max'] = (r, seq)
    arc = sum(h for h, _ in hs)
    return {'arc_mm': arc, 'rise_min_mm': best['min'][0], 'rise_max_mm': best['max'][0],
            'min_sequence_deg': [round(x, 2) for x in best['min'][1]], 'max_sequence_deg': [round(x, 2) for x in best['max'][1]]}


# ---------------------------------------------------------------- BodyParts3D C7 spinous-tip offset (grade D)
def c7_tip_offset(models_dir, bp3d):
    sys.path.insert(0, str(HERE))
    import numpy as np
    from bodyparts3d_crosscheck import Atlas
    v, f, pid = Atlas(models_dir).mesh('Seventh cervical vertebra')
    sp = bp3d['spine']
    up_disc = np.array(sp['C6/C7']['disc_centroid_mm']); dn_disc = np.array(sp['C7/T1']['disc_centroid_mm'])
    centre = (up_disc + dn_disc) / 2
    # endplate-normal frame (mean of the two facing disc normals), the same frame in which the candidate C7 lean is
    # defined (T1 superior endplate angle); the disc-centroid line of this specimen leans ~10 deg less
    ax = np.array(sp['C6/C7']['disc_normal']) + np.array(sp['C7/T1']['disc_normal']); ax[0] = 0; ax /= np.linalg.norm(ax)
    tip = v[np.argmax(v[:, 1])]                                       # most posterior vertex (HGPT +Y posterior)
    d = tip - centre
    along = float(d @ ax)
    post_dir = np.array([0.0, ax[2], -ax[1]])                         # in-plane perpendicular, pointing posterior
    if post_dir[1] < 0:
        post_dir = -post_dir
    perp = float(d @ post_dir)
    # same specimen: C7 body-centre path length C6/C7->C7/T1 as a size reference
    return {'part_id': pid, 'tip_minus_body_centre_local_mm': {'along_axis_superior': round(along, 2), 'posterior': round(perp, 2)},
            'specimen_c7_centre_mm': [round(float(x), 2) for x in centre], 'specimen_tip_mm': [round(float(x), 2) for x in tip],
            'specimen_vertical_tip_minus_centre_mm': round(float(d[2]), 2),
            'definition': 'body centre proxy = midpoint of the C6/C7 and C7/T1 disc centroids; axis = mean C6/C7 and C7/T1 disc '
            'normal; tip = most posterior C7 vertex'}


def tip_world(centre_yz, phi_deg, off):
    """Rotate the local (along, posterior) offset into the sagittal plane for a C7 axis leaning phi (+ anterior)."""
    r = math.radians(phi_deg)
    ax = (-math.sin(r), math.cos(r))                  # (y, z) of the column axis
    post = (math.cos(r), math.sin(r))                 # perpendicular, posterior-pointing
    a, p = off['along_axis_superior'], off['posterior']
    return (centre_yz[0] + a * ax[0] + p * post[0], centre_yz[1] + a * ax[1] + p * post[1])


def specimen_ratio(bp3d):
    sp = bp3d['spine']

    def path(levels):
        tot = 0.0
        for a, b in zip(levels, levels[1:]):
            pa, pb = sp[a]['disc_centroid_mm'], sp[b]['disc_centroid_mm']
            tot += math.dist(pa, pb)
        return tot
    th = path(['C7/T1'] + [f'T{i}/T{i + 1}' for i in range(1, 12)] + ['T12/L1'])
    lu = path(['T12/L1', 'L1/L2', 'L2/L3', 'L3/L4', 'L4/L5', 'L5/S1'])
    return {'thoracic_C7T1_to_T12L1_centre_path_mm': round(th, 1), 'lumbar_T12L1_to_L5S1_centre_path_mm': round(lu, 1),
            'ratio': round(th / lu, 4), 'definition': 'polyline through disc centroids; each thoracic span = 12 bodies + 11 discs '
            '+ half of the C7/T1 and T12/L1 discs; lumbar = 5 bodies + 4 discs + half of T12/L1 and L5/S1'}


def stack_ratio(tbody, tdisc, lbody, ldisc, stack):
    c7t1 = stack['disc_gaps_mm']['C7/T1']['candidate']; t12l1 = stack['disc_gaps_mm']['T12/L1']['candidate']
    th = sum(tbody.values()) + sum(tdisc.values()) + c7t1 / 2 + t12l1 / 2
    lu = sum(lbody.values()) + sum(v for k, v in ldisc.items() if k != 'L5/S1') + t12l1 / 2 + ldisc['L5/S1'] / 2
    return th, lu, th / lu


def candidate_c7(rec_path):
    return candidate_c7_from(json.loads(Path(rec_path).read_text()))


def candidate_c7_from(rec):
    b = rec['bones']['c7']
    h, t = b['head_m'], b['tail_m']
    return {'c7_stick_mid_mm': [round(1000 * (h[i] + t[i]) / 2, 2) for i in range(3)],
            'c7_axis_lean_deg': round(math.degrees(math.atan2(-(t[1] - h[1]), t[2] - h[2])), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models-dir', required=True)
    ap.add_argument('--atlas-commit', default='1c38bf35c254a891200d3cedecfd57abebe83d8d')
    ap.add_argument('--out', required=True)
    o = ap.parse_args()
    stack, geom, frames, s1, pose = load('stack'), load('geom'), load('frames'), load('s1'), load('pose')
    edges, conc, bp3d = load('edges'), load('concavity'), load('bp3d')
    kyph = pose['global_male_reference_deg']['thoracic_kyphosis_T1_T12']

    cerv = ansur_at('cervicaleheight')
    s1c = s1['derived_S1_superior_endplate']['centre_m']
    s1_yz = (1000 * s1c[1], 1000 * s1c[2])
    target_rise = cerv['prediction_mm'] - s1_yz[1]
    tip = c7_tip_offset(o.models_dir, bp3d)
    spec = specimen_ratio(bp3d)

    variants = {}
    c7_body = stack['vertebral_bodies_mm']['C7']['candidate']
    c7t1_opts = {'anatomical_4.5': stack['disc_gaps_mm']['C7/T1']['candidate'],
                 'radiographic_6.1': stack['disc_gaps_mm']['C7/T1']['crosscheck_male_radiographic']}
    t12l1 = stack['disc_gaps_mm']['T12/L1']['candidate']
    for lmode in ['CT_middle_body_avg_disc', 'MRI_edge_mean']:
        lel, phi_L1, lbody, ldisc = lumbar_elements(lmode, frames, stack, edges)
        lpts = walk(s1_yz, [(h, p) for h, p, _ in lel])
        l1_top = lpts[-1]
        for tv in ['A_anatomical_2011', 'B_CT_2016']:
            tbody, tdisc = thoracic_heights(tv, stack, geom)
            env = thoracic_envelope(tbody, tdisc, phi_L1, kyph)
            # T12/L1 disc at the L1-superior angle; C7/T1 disc and half the C7 body at the T1-superior angle
            phi_T1 = phi_L1 + kyph
            base = l1_top[1] + t12l1 * math.cos(math.radians(phi_L1))
            for ck, c7t1 in c7t1_opts.items():
                top_add = (c7t1 + c7_body / 2) * math.cos(math.radians(phi_T1))
                # tip vertical offset in the C7 frame, C7 axis taken at the T1-superior angle (+/-10 deg sensitivity)
                tip_dz = {d: tip_world((0, 0), phi_T1 + d, tip['tip_minus_body_centre_local_mm'])[1] for d in (-10, 0, 10)}
                zc_min = base + env['rise_min_mm'] + top_add
                zc_max = base + env['rise_max_mm'] + top_add
                key = f'{lmode}|{tv}|C7T1_{ck}'
                variants[key] = {
                    'lumbar_S1_to_L1_superior_rise_mm': round(l1_top[1] - s1_yz[1], 1),
                    'lumbar_centre_path_mm': round(sum(h for h, _, _ in lel), 1),
                    'thoracic_arc_mm': round(env['arc_mm'], 1),
                    'thoracic_rise_envelope_mm': [round(env['rise_min_mm'], 1), round(env['rise_max_mm'], 1)],
                    'C7_body_centre_z_envelope_mm': [round(zc_min, 1), round(zc_max, 1)],
                    'C7_tip_z_envelope_mm': [round(zc_min + min(tip_dz.values()), 1), round(zc_max + max(tip_dz.values()), 1)],
                    'C7_tip_z_central_mm': round((zc_min + zc_max) / 2 + tip_dz[0], 1),
                    'ANSUR_cervicale_minus_central_mm': round(cerv['prediction_mm'] - ((zc_min + zc_max) / 2 + tip_dz[0]), 1),
                    'ANSUR_inside_envelope': (zc_min + min(tip_dz.values())) <= cerv['prediction_mm'] <= (zc_max + max(tip_dz.values())),
                    'z_vs_ANSUR_residual_sd_central': round((cerv['prediction_mm'] - ((zc_min + zc_max) / 2 + tip_dz[0])) / cerv['residual_sd_mm'], 2),
                }
                # scale-free reading: the uniform column scale that would put the central C7 tip on ANSUR, and the
                # mean stature that the source cohorts would then need (column length taken proportional to stature)
                rise_c = (zc_min + zc_max) / 2 + tip_dz[0] - s1_yz[1]
                need = (cerv['prediction_mm'] - s1_yz[1]) / rise_c
                variants[key]['required_column_scale_to_meet_ANSUR'] = round(need, 4)
                variants[key]['implied_source_cohort_stature_m'] = round(STATURE_MM / need / 1000, 3)
                th, lu, ratio = stack_ratio(tbody, tdisc, lbody, ldisc, stack)
                variants[key]['thoracic_over_lumbar_ratio'] = round(ratio, 4)
                variants[key]['ratio_minus_specimen'] = round(ratio - spec['ratio'], 4)

    # candidates as built (their C7 stick midpoint, no envelope needed)
    cands = {}
    for k in ('c004', 'a003'):
        c = candidate_c7(IN[k])
        zt = tip_world((c['c7_stick_mid_mm'][1], c['c7_stick_mid_mm'][2]), c['c7_axis_lean_deg'], tip['tip_minus_body_centre_local_mm'])[1]
        cands[k] = {**c, 'C7_tip_z_mm': round(zt, 1), 'ANSUR_cervicale_minus_tip_mm': round(cerv['prediction_mm'] - zt, 1),
                    'rise_from_P1_S1_mm': round(c['c7_stick_mid_mm'][2] - s1_yz[1], 1)}

    out = {
        'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_SPINE_LENGTH_DISCRIMINATOR', 'selects_nothing': True,
        'stature_mm': STATURE_MM,
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in IN.values()},
        'external': {'bodyparts3d_atlas': f'https://github.com/ashemag/human-atlas/tree/{o.atlas_commit}/public/models',
                     'grade': 'D single specimen: offset and ratio cross-check only'},
        'ansur_cervicale_at_182': cerv,
        'P1_S1_superior_endplate_centre_mm_yz': [round(x, 2) for x in s1_yz],
        'target_rise_S1_to_cervicale_mm': round(target_rise, 1),
        'c7_spinous_tip_offset_specimen': tip,
        'specimen_scale_free_ratio': spec,
        'kyphosis_T1_T12_deg': kyph,
        'variants': variants,
        'candidates_as_built': cands,
        'reading_rule': 'A variant is incompatible with a 1.82 m man if the source cohorts would need an implausible mean '
                        'stature (below ~1.60 m, i.e. below typical adult female means) to explain the gap; the gap of a '
                        'compatible variant is of the order of the stature scaling, the C7 tip offset and the envelope.',
        'limitations': [
            'Population means from cohorts of unrecorded mean stature are compared with a 1.82 m ANSUR prediction; the '
            'ANSUR slope reported here converts a stature difference into a cervicale shift.',
            'Cervicale is a living-skin landmark over the C7 spinous tip; the vertical skin-bone offset is taken as 0.',
            'The C7 spinous-tip offset comes from one BodyParts3D specimen (grade D) and is applied in the C7 frame.',
            'The P1 S1 centre is provisional (Hasegawa male PTh 107 +/- 8 mm, PT 9.2 +/- 6.2 deg) on the retained HJC.',
            'T12/L1 disc wedge is taken as 0 (parallel T12 inferior / L1 superior endplates); the thoracic envelope '
            'covers every monotone tilt distribution with T7 within +/-3 deg of horizontal-endplate.',
            'MRI edge heights are supine (Hegazy 2014); CT middle/average heights are mixed-sex for bodies (LUMBAR_CT_2026).',
        ],
    }
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print('ANSUR cervicale', cerv['prediction_mm'], 'S1 z', round(s1_yz[1], 1), 'target rise', round(target_rise, 1))
    print('tip offset', tip['tip_minus_body_centre_local_mm'], 'specimen ratio', spec['ratio'])
    for k, v in variants.items():
        print(f"{k:70s} tip z {v['C7_tip_z_envelope_mm']} centre-resid {v['ANSUR_cervicale_minus_central_mm']:6.1f} "
              f"in={v['ANSUR_inside_envelope']} scale {v['required_column_scale_to_meet_ANSUR']} -> cohort {v['implied_source_cohort_stature_m']} m ratio {v['thoracic_over_lumbar_ratio']} (spec {spec['ratio']})")
    for k, v in cands.items():
        print(k, v)


if __name__ == '__main__':
    main()
