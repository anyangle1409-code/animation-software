#!/usr/bin/env python3
"""Single-specimen BodyParts3D cross-check: spine discs, shoulder girdle and hyoid (read-only evidence).

Same specimen, access path and grade as bodyparts3d_crosscheck.py: ONE reference male, grade D, never a target.
All landmark proxies below are geometric constructions on that specimen and are named as such.

  bodyparts3d_axial_shoulder.py MODELS_DIR --commit SHA --out JSON
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bodyparts3d_crosscheck import ANAT, Atlas, r, rib_curve, shape, weld  # noqa: E402
from endplate_clearance import clearance  # noqa: E402

VERT = {'C2': 'Axis', 'C3': 'Third cervical vertebra', 'C4': 'Fourth cervical vertebra', 'C5': 'Fifth cervical vertebra',
        'C6': 'Sixth cervical vertebra', 'C7': 'Seventh cervical vertebra', 'S1': 'Sacrum'}
ORD = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth', 'Eleventh', 'Twelfth']
VERT.update({f'T{i}': f'{ORD[i - 1]} thoracic vertebra' for i in range(1, 13)})
VERT.update({f'L{i}': f'{ORD[i - 1]} lumbar vertebra' for i in range(1, 6)})
LEVELS = ['C2', 'C3', 'C4', 'C5', 'C6', 'C7'] + [f'T{i}' for i in range(1, 13)] + [f'L{i}' for i in range(1, 6)] + ['S1']
DISC_ID = {'C2': 'FJ3202', 'T12': 'FJ3211'}            # 'of axis'; the unnamed disk (position-checked below)
CONTACT_MM = (1.0, 2.0, 3.0)                           # contact-patch thresholds: reported as a sensitivity, not a tolerance


def mesh_by_id(at, pid):
    p = next(q for q in at.meta['parts'] if q['id'] == pid)
    return _mesh(at, p)


def _mesh(at, p):
    from bodyparts3d_crosscheck import TO_HGPT
    if p['chunk'] not in at.bins:
        at.bins[p['chunk']] = (at.dir / f'body-{p["chunk"]}.bin').read_bytes()
    b = at.bins[p['chunk']]
    v = np.frombuffer(b, '<f4', p['vertexCount'] * 3, p['positions']).reshape(-1, 3).astype(float)
    f = np.frombuffer(b, '<u4', p['indexCount'], p['indices']).reshape(-1, 3).astype(np.int64)
    return (v @ TO_HGPT.T) * 1000.0, f


def disc_mesh(at, upper):
    if upper in DISC_ID:
        return weld(*mesh_by_id(at, DISC_ID[upper]))
    name = f'Intervertebral disk of {VERT[upper][0].lower() + VERT[upper][1:]}'
    v, f, _ = at.mesh(name)
    return weld(v, f)


def ray_hits(o, d, v, f):
    """All ray parameters t (any sign) where the line o + t d crosses the triangle mesh (Moller-Trumbore)."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    e1, e2 = b - a, c - a
    p = np.cross(d, e2)
    det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    s = o - a
    u = np.einsum('ij,ij->i', s, p) * inv
    q = np.cross(s, e1)
    w = (q @ d) * inv
    t = np.einsum('ij,ij->i', e2, q) * inv
    hit = ok & (u >= 0) & (w >= 0) & (u + w <= 1)
    return np.sort(t[hit])


def disc_frame(v):
    c = v.mean(0)
    w, U = np.linalg.eigh(np.cov((v - c).T))
    n = U[:, 0] * (1 if U[2, 0] > 0 else -1)                      # thinnest direction, superior-facing
    ant = np.array([0, -1.0, 0]); ant = ant - n * (ant @ n); ant /= np.linalg.norm(ant)   # HGPT anterior in the disc plane
    lat = np.cross(n, ant)
    proj = (v - c) @ np.c_[ant, lat]
    return c, n, ant, lat, (proj.max(0) - proj.min(0)) / 2


def spine(at):
    out, surfaces = {}, {}
    for i in range(len(LEVELS) - 1):
        up, lo = LEVELS[i], LEVELS[i + 1]
        dv, df = disc_mesh(at, up)
        c, n, ant, lat, half = disc_frame(dv)
        uv, uf = weld(*at.mesh(VERT[up])[:2])
        lv, lf = weld(*at.mesh(VERT[lo])[:2])
        row = {'disc_centroid_mm': r(c), 'disc_normal': r(n, 4), 'disc_half_depth_width_mm': r(half)}
        for tag, s in (('posterior', -0.7), ('centre', 0.0), ('anterior', 0.7)):
            o = c + s * half[0] * ant
            t = ray_hits(o, n, dv, df)
            tu = ray_hits(o, n, uv, uf); tl = ray_hits(o, n, lv, lf)
            up_hit = tu[tu > 0].min() if np.any(tu > 0) else None      # first upper-bone surface above the disc point
            lo_hit = tl[tl < 0].max() if np.any(tl < 0) else None      # first lower-bone surface below it
            row[tag] = {'disc_thickness_mm': r(t.max() - t.min()) if len(t) >= 2 else None,
                        'bone_to_bone_gap_mm': r(up_hit - lo_hit) if up_hit is not None and lo_hit is not None else None}
        thick = [row[k]['disc_thickness_mm'] for k in ('anterior', 'centre', 'posterior')]
        row['mean_of_three_disc_thickness_mm'] = r(np.mean(thick)) if None not in thick else None
        # endplate planes for the clearance checker: bone surfaces sampled on a 7x7 grid inside 60% of the disc footprint
        top, bot = [], []
        for a in np.linspace(-0.6, 0.6, 7):
            for b in np.linspace(-0.6, 0.6, 7):
                if a * a + b * b > 0.36:
                    continue
                o = c + a * half[0] * ant + b * half[1] * lat
                tu = ray_hits(o, n, uv, uf); tl = ray_hits(o, n, lv, lf)
                if np.any(tu > 0) and np.any(tl < 0):
                    top.append(o + tu[tu > 0].min() * n); bot.append(o + tl[tl < 0].max() * n)
        planes = []
        for pts in (np.array(top), np.array(bot)):
            pc = pts.mean(0); w, U = np.linalg.eigh(np.cov((pts - pc).T)); pn = U[:, 0] * (1 if U[2, 0] > 0 else -1)
            planes.append((pc, pn, float(np.abs((pts - pc) @ pn).max())))
        ext = np.abs(np.c_[ant[:2], lat[:2]]) @ (0.6 * half)          # conservative axis-aligned XY radii of the footprint
        surf = {'upper_origin_mm': r(planes[0][0], 4), 'upper_normal': r(planes[0][1], 6),
                'lower_origin_mm': r(planes[1][0], 4), 'lower_normal': r(planes[1][1], 6),
                'footprint_centre_xy_mm': r(c[:2], 4), 'footprint_radii_xy_mm': r(np.maximum(ext, 1.0), 4)}
        res = clearance(surf['upper_origin_mm'], surf['upper_normal'], surf['lower_origin_mm'], surf['lower_normal'],
                        surf['footprint_centre_xy_mm'], surf['footprint_radii_xy_mm'])
        row['endplate_plane_fit_max_residual_mm'] = [r(planes[0][2]), r(planes[1][2])]
        row['clearance_minimum_projected_gap_mm'] = r(res['minimum_projected_gap_mm'])
        row['samples'] = len(top)
        key = f'disc_{up.lower()}_{"sacrum" if lo == "S1" else lo.lower()}'
        out[f'{up}/{lo}'] = row
        surfaces[key] = surf
    return out, surfaces


def near(v, others, thr):
    d = np.min(np.linalg.norm(v[:, None, :] - others[None, :, :], axis=2), axis=1)
    return v[d <= d.min() + thr], float(d.min())


def shoulder(at):
    man = weld(*at.mesh('Manubrium')[:2])[0]
    res = {}
    for side in ('left', 'right'):
        S = side.capitalize()
        cv, cf = weld(*at.mesh(f'{S} clavicle')[:2])
        sv, sf = weld(*at.mesh(f'{S} scapula')[:2])
        hv = weld(*at.mesh(f'{S} humerus')[:2])[0]
        D = np.linalg.norm(cv[:, None] - cv[None], axis=2)
        i, j = np.unravel_index(np.argmax(D), D.shape)
        c0 = cv.mean(0); t = (cv - c0) @ np.linalg.eigh(np.cov((cv - c0).T))[1][:, 2]
        e = np.linspace(t.min(), t.max(), 25)
        axial = np.array([cv[(t >= a) & (t <= b)].mean(0) for a, b in zip(e[:-1], e[1:]) if np.any((t >= a) & (t <= b))])
        row = {'clavicle_max_vertex_chord_mm': r(D[i, j], 1),
               'clavicle_axial_bin_centreline_arc_mm': r(np.linalg.norm(np.diff(axial, axis=0), axis=1).sum(), 1)}
        for thr in CONTACT_MM:
            sc, dsc = near(cv, man, thr)
            ac, dac = near(cv, sv, thr)
            gh, dgh = near(sv, hv, thr)
            row[f'contact_{thr:g}mm'] = {'SC_proxy_mm': r(sc.mean(0)), 'AC_proxy_mm': r(ac.mean(0)), 'GH_glenoid_proxy_mm': r(gh.mean(0)),
                                         'SC_AC_chord_mm': r(np.linalg.norm(sc.mean(0) - ac.mean(0)), 1),
                                         'closest_bone_distances_mm': {'clavicle_manubrium': r(dsc), 'clavicle_scapula': r(dac),
                                                                       'scapula_humerus': r(dgh)}}
        # scapula: inferior angle = lowest vertex; superior angle = highest vertex of the medial half of the blade
        ia = sv[np.argmin(sv[:, 2])]
        med = sv[np.abs(sv[:, 0]) <= np.median(np.abs(sv[:, 0]))]
        sa = med[np.argmax(med[:, 2])]
        gh2 = np.array(row['contact_2mm']['GH_glenoid_proxy_mm'])
        row['scapula'] = {'inferior_angle_proxy_mm': r(ia), 'superior_angle_proxy_mm': r(sa),
                          'superior_to_inferior_angle_mm': r(np.linalg.norm(sa - ia), 1),
                          'glenoid_proxy_to_inferior_angle_mm': r(np.linalg.norm(gh2 - ia), 1),
                          'principal_extents_mm': r(shape(sv, sf)['extents_mm'], 1)}
        res[side] = row
    for thr in CONTACT_MM:
        k = f'contact_{thr:g}mm'
        res[f'bilateral_SC_proxy_separation_{thr:g}mm'] = r(np.linalg.norm(np.array(res['left'][k]['SC_proxy_mm']) -
                                                                           np.array(res['right'][k]['SC_proxy_mm'])), 1)
        res[f'bilateral_AC_proxy_separation_{thr:g}mm'] = r(np.linalg.norm(np.array(res['left'][k]['AC_proxy_mm']) -
                                                                           np.array(res['right'][k]['AC_proxy_mm'])), 1)
    res['manubrium_X_extent_mm'] = r(man[:, 0].max() - man[:, 0].min(), 1)
    return res


def hyoid(at):
    ids = [p['id'] for p in at.meta['parts'] if p['name'] == 'Hyoid bone' and p['system'] == 'skeletal']
    meshes = [weld(*mesh_by_id(at, i)) for i in ids]
    same = all(m[0].shape == meshes[0][0].shape and np.allclose(m[0], meshes[0][0]) for m in meshes)
    v, f = meshes[0]
    curve, _ = rib_curve(v, f)                                      # geodesic ends = the two greater-horn tips
    mid = len(curve) // 2
    halves = {}
    for name, seg in (('first_half', curve[:mid + 1][::-1]), ('second_half', curve[mid:])):
        x = np.abs(seg[:, 0])
        k = int(np.argmax(x))
        halves[name] = {'tip_abs_x_mm': r(x[-1], 1), 'max_abs_x_mm': r(x.max(), 1),
                        'max_at_fraction_from_body_to_tip': r(k / (len(seg) - 1), 2),
                        'inward_turn_mm': r(x.max() - x[-1], 1)}
    return {'mesh_ids': ids, 'duplicate_entries_identical': bool(same),
            'total_X_width_mm': r(v[:, 0].max() - v[:, 0].min(), 1),
            'total_AP_Y_extent_mm': r(v[:, 1].max() - v[:, 1].min(), 1),
            'tip_span_centreline_ends_mm': r(np.linalg.norm(curve[0] - curve[-1]), 1),
            'horns': halves,
            'note': 'Tip span uses centreline bin means (inside the true tips). inward_turn_mm > 0 means the horn centreline '
                    'reaches its widest point before the tip, i.e. the horn is not straight.'}


def sternum(at):
    """Sternal segment extents and costal-cartilage 1-7 attachment levels (contact-patch centroid, 2 mm threshold),
    measured down from the top of the manubrium. Vertical extents in the specimen's standing frame."""
    parts = {k: weld(*at.mesh(n)[:2])[0] for k, n in (('manubrium', 'Manubrium'), ('body', 'Body of sternum'), ('xiphoid', 'Xiphoid process'))}
    allv = np.vstack(list(parts.values()))
    top, bot = parts['manubrium'][:, 2].max(), parts['xiphoid'][:, 2].min()
    out = {'segment_vertical_extent_mm': {k: r(v[:, 2].max() - v[:, 2].min(), 1) for k, v in parts.items()},
           'manubrium_X_width_mm': r(np.ptp(parts['manubrium'][:, 0]), 1), 'body_X_width_mm': r(np.ptp(parts['body'][:, 0]), 1),
           'total_vertical_extent_mm': r(top - bot, 1), 'manubriosternal_level_mm': r(top - parts['manubrium'][:, 2].min(), 1),
           'costal_attachment_depth_mm': {}}
    for side in ('left', 'right'):
        for i, o in enumerate(['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh'], 1):
            cv = weld(*at.mesh(f'{side.capitalize()} {o} costal cartilage')[:2])[0]
            patch, _ = near(cv, allv, 2.0)
            out['costal_attachment_depth_mm'][f'{side}_{i}'] = r(top - patch[:, 2].mean(), 1)
    return out


def crosschecks(sp, sh, hy):
    stack = json.loads((ANAT / 'canonical_spine_level_stack_v1.json').read_text())['disc_gaps_mm']
    heg = json.loads((ANAT / 'canonical_lumbar_edge_height_crosscheck_v1.json').read_text())['disc_edge_gaps']
    cl = json.loads((ANAT / 'canonical_clavicle_endpoint_crosscheck_v1.json').read_text())
    gird = json.loads((ANAT / 'canonical_shoulder_girdle_audit_v1.json').read_text())
    ab = json.loads((ANAT / 'canonical_hyoid_geometry_targets_v1.json').read_text())['source_evidence'][1]['male_mean_mm']
    discs = {}
    for k, row in sp.items():
        ref = stack.get(k, {})
        m = row['mean_of_three_disc_thickness_mm']
        e = {'specimen_mean_of_three_mm': m, 'source_candidate_mm': ref.get('candidate'), 'source_sd_mm': ref.get('sd'),
             'source_definition': ref.get('definition'),
             'z': r((m - ref['candidate']) / ref['sd']) if ref.get('sd') and m is not None else None}
        if k in heg:
            e['hegazy_supine_edge_gaps_mm'] = {'anterior': heg[k]['anterior_mean_mm'], 'posterior': heg[k]['posterior_mean_mm']}
            e['specimen_edge_thickness_mm'] = {'anterior': row['anterior']['disc_thickness_mm'], 'posterior': row['posterior']['disc_thickness_mm']}
        discs[k] = e
    sh2 = sh['left']['contact_2mm'], sh['right']['contact_2mm']
    ext = gird['external_reference_mm']
    return {
        'disc_heights': discs,
        'clavicle': {'qiu_articular_centre_chord_male_mm': cl['source']['male_chord_mm'],
                     'specimen_SC_AC_proxy_chord_mm_left_right': [sh2[0]['SC_AC_chord_mm'], sh2[1]['SC_AC_chord_mm']],
                     'centreline_male_cadaver_mm': ext['clavicle_centerline_length_male_cadaver_2013'],
                     'specimen_centreline_arc_mm_left_right': [sh['left']['clavicle_axial_bin_centreline_arc_mm'],
                                                                sh['right']['clavicle_axial_bin_centreline_arc_mm']],
                     'extremal_chord_CT_2018_mean_mm': cl['comparison']['existing_extremal_chord_mean_mm'],
                     'specimen_max_vertex_chord_mm_left_right': [sh['left']['clavicle_max_vertex_chord_mm'],
                                                                 sh['right']['clavicle_max_vertex_chord_mm']],
                     'a003_SC_AC_span_mm': r(gird['current_a003_mm']['clavicle_SC_to_AC_straight_span'], 1)},
        'scapula': {'superior_to_inferior_angle_male_2018_mm': ext['scapula_superior_to_inferior_angle_male_2018'],
                    'specimen_mm_left_right': [sh['left']['scapula']['superior_to_inferior_angle_mm'],
                                               sh['right']['scapula']['superior_to_inferior_angle_mm']],
                    'a003_GH_to_inferior_angle_mm': r(gird['current_a003_mm']['scapula_GH_to_inferior_angle_span'], 1),
                    'specimen_glenoid_proxy_to_inferior_angle_mm_left_right': [sh['left']['scapula']['glenoid_proxy_to_inferior_angle_mm'],
                                                                               sh['right']['scapula']['glenoid_proxy_to_inferior_angle_mm']]},
        'bi_AC': {'a003_mm': r(gird['current_a003_mm']['bi_AC_joint_breadth'], 1), 'specimen_proxy_mm': sh['bilateral_AC_proxy_separation_2mm'],
                  'ANSUR_biacromial_at_HGPT_stature_mm': r(ext['ANSUR_stature_conditioned_biacromial_breadth']['mean'], 1),
                  'note': 'Biacromial breadth is measured at the lateral acromia, lateral to the AC joints.'},
        'SC': {'specimen_bilateral_SC_proxy_mm_by_threshold': {f'{t:g}': sh[f'bilateral_SC_proxy_separation_{t:g}mm'] for t in CONTACT_MM},
               'manubrium_outer_breadth_context_mm': {'mean': 68.2, 'sd': 8, 'source': 'STERNUM_SELTHOFER_2006',
                                                      'semantics': 'outer clavicular-notch breadth, not SC centres'},
               'specimen_manubrium_X_extent_mm': sh['manubrium_X_extent_mm']},
        'hyoid': {'abdelkader_2025_male_mm': {k: ab[k] for k in ('overall_width_lateral_greater_horn_to_lateral_greater_horn',
                                                                  'greater_horn_center_distance', 'greater_horn_posterior_end_distance')},
                  'specimen_total_width_mm': hy['total_X_width_mm'], 'specimen_tip_span_mm': hy['tip_span_centreline_ends_mm'],
                  'specimen_inward_turn_mm': [h['inward_turn_mm'] for h in hy['horns'].values()]}}


def build(models_dir, commit):
    at = Atlas(models_dir)
    sp, surfaces = spine(at)
    sh = shoulder(at)
    hy = hyoid(at)
    stn = sternum(at)
    t12 = sp['T12/L1']['disc_centroid_mm'][2]
    if not sp['T11/T12']['disc_centroid_mm'][2] > t12 > sp['L1/L2']['disc_centroid_mm'][2]:
        raise ValueError('unnamed disk FJ3211 is not between T11/T12 and L1/L2')
    return {'schema_version': 1, 'created': '2026-10-08', 'status': 'SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET',
            'evidence_grade_note': 'Same single BodyParts3D 4.0 male as bodyparts3d_single_specimen_crosscheck_v1.json. Grade D: '
                                   'plausibility and topology only. Never freeze a value from it.',
            'source_access_path': f'https://github.com/ashemag/human-atlas at {commit}, public/models (hashes in the companion file)',
            'frame': 'HGPT axes (left +X, anterior -Y, superior +Z), mm, arbitrary origin.',
            'methods': {
                'disc': 'Disc mesh normal = its thinnest principal axis; rays along it at 70% of the posterior half-depth, the centre and '
                        '70% of the anterior half-depth. Disc thickness = outer crossings of the disc mesh; bone gap = first upper-vertebra '
                        'and lower-vertebra surfaces along the same line. Mean of three is a stand-in for the sources\' average heights.',
                'endplate_surfaces': 'Planes fitted to the bone surfaces hit by a 7x7 ray grid inside 60% of the disc footprint; fed to '
                                     'endplate_clearance.clearance() exactly as cp2_preflight.py would. The footprint is a conservative XY box.',
                'contact_proxies': 'SC/AC/glenoid proxies = mean of the bone vertices within (closest distance + threshold) of the partner '
                                   'bone; thresholds 1/2/3 mm reported as a sensitivity. They are articular-region centres, not rotation centres.',
                'clavicle': 'Max vertex chord (extremal-point chord) and a centreline from 24 bins along the first principal axis '
                            '(a geodesic centreline zigzags on this coarse mesh and was rejected: 253-263 mm).',
                'scapula': 'Inferior angle = lowest vertex; superior angle = highest vertex in the medial half of the blade.',
                'hyoid': 'Geodesic centreline between the two farthest surface points (greater-horn tips).'},
            'spine': sp, 'disc_surfaces_for_cp2_preflight': surfaces, 'shoulder': sh, 'hyoid': hy, 'sternum': stn,
            'crosschecks': crosschecks(sp, sh, hy)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('models_dir'); ap.add_argument('--commit', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = build(o.models_dir, o.commit)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out['crosschecks'], indent=1))


if __name__ == '__main__':
    main()
