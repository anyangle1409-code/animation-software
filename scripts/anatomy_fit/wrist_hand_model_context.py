#!/usr/bin/env python3
"""Wrist/hand source context from the published OpenSim wrist model (Gonzalez, Buchanan & Delp, J Biomech 30:705-712,
1997; opensim-org/opensim-models Models/WristModel/wrist.osim + Geometry/*.vtp). Read-only; changes no project geometry.

Reports, all computed:
  1. provenance: model credits/publication, repository commit, sha256 of the model and every mesh used;
  2. bone lengths (principal-axis extent of each bone mesh) against the registered male radiographic means
     (Aydinlioglu et al. 1998, DOGAN_1998_HAND_RELATIONS) and the model forearm; a non-constant / non-population scale
     disqualifies the model as a dimensional source;
  3. scale-free digit proportions (distal/proximal, middle/proximal phalanx) model vs radiographic means;
  4. carpal topology: standard anatomical relations evaluated on the model and on a003 (both sides) in a wrist frame
     (radial / distal / palmar). a003's palmar direction is derived from its committed digit-3 flexion sweep (the
     fingertip moves palmarly), not assumed;
  5. index-ray joint centres (MCP, PIP, DIP body origins) and the DIP-centre-to-bony-tip offset of the distal phalanx.
A single model is ONE source: nothing here is a coordinate target or acceptance.

  wrist_hand_model_context.py --models-repo DIR --out JSON
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import opensim_model_geometry as og  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
CARPALS = ['scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate']
MESH_OF = {'metacarpal_1': 'fingers17', 'thumb_proximal_phalanx': 'fingers18', 'thumb_distal_phalanx': 'fingers19',
           'metacarpal_2': 'fingers1', 'digit2_proximal_phalanx': 'fingers2', 'digit2_middle_phalanx': 'fingers3', 'digit2_distal_phalanx': 'fingers4',
           'metacarpal_3': 'fingers8', 'digit3_proximal_phalanx': 'fingers7', 'digit3_middle_phalanx': 'fingers6', 'digit3_distal_phalanx': 'fingers5',
           'metacarpal_4': 'fingers12', 'digit4_proximal_phalanx': 'fingers11', 'digit4_middle_phalanx': 'fingers10', 'digit4_distal_phalanx': 'fingers9',
           'metacarpal_5': 'fingers16', 'digit5_proximal_phalanx': 'fingers15', 'digit5_middle_phalanx': 'fingers14', 'digit5_distal_phalanx': 'fingers13'}
# standard carpal relations (any anatomy atlas): (a, b, axis, sign) means a lies on the `sign` side of b along axis
RELATIONS = [('scaphoid', 'lunate', 'radial', +1), ('lunate', 'triquetrum', 'radial', +1),
             ('trapezium', 'trapezoid', 'radial', +1), ('trapezoid', 'capitate', 'radial', +1), ('capitate', 'hamate', 'radial', +1),
             ('capitate', 'lunate', 'distal', +1), ('hamate', 'triquetrum', 'distal', +1), ('trapezium', 'scaphoid', 'distal', +1),
             ('pisiform', 'triquetrum', 'palmar', +1)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pca_extent(P):
    c = P.mean(0); ax = np.linalg.svd(P - c)[2][0]; p = (P - c) @ ax
    return float(p.max() - p.min()), ax, c


def model_part(repo):
    G = repo / 'Geometry'; osim = repo / 'Models/WristModel/wrist.osim'
    m = og.Model(osim, G)
    meshes, used = {}, {}
    for b in m.bodies:
        for f, W, s in m.meshes(b):
            V = og.read_vtp(G / f) * s
            meshes[f[:-4]] = (b, (W[:3, :3] @ V.T).T + W[:3, 3]); used[f] = sha(G / f)
    cen = {b: meshes[{'scaphoid': 'r_scaph', 'lunate': 'r_lun', 'trapezium': 'r_trpzm', 'trapezoid': 'r_trpzd', 'capitate': 'r_cap',
                      'pisiform': 'r_pis', 'triquetrum': 'r_triq', 'hamate': 'r_ham'}[b]][1].mean(0) for b in CARPALS}
    R, U = meshes['radius'][1], meshes['ulna'][1]
    lengths = {k: pca_extent(meshes[v][1])[0] * 1000 for k, v in MESH_OF.items()}
    forearm = {'radius_mesh_extent_mm': pca_extent(R)[0] * 1000, 'ulna_mesh_extent_mm': pca_extent(U)[0] * 1000}
    carp = np.mean(list(cen.values()), 0); c = R.mean(0); ax = np.linalg.svd(R - c)[2][0]
    if (carp - c) @ ax < 0:
        ax = -ax
    rad = R.mean(0) - U.mean(0); rad -= rad @ ax * ax; rad /= np.linalg.norm(rad)
    pal = np.cross(ax, rad)
    # palmar side of the model: the index fingertip moves palmarly under +90 deg MCP2 flexion (rest centroid of the distal
    # phalanx re-expressed in its body frame and carried by the flexed pose)
    W3 = m.body_world('Iphalanx3'); tip_rest = meshes['fingers4'][1].mean(0)
    tip_flexed = (m_body_world(m, 'Iphalanx3', np.pi / 2) @ np.linalg.inv(W3) @ np.append(tip_rest, 1))[:3]
    if (tip_flexed - tip_rest) @ pal < 0:
        pal = -pal
    frame = {b: [float((cen[b] - carp) @ rad), float((cen[b] - carp) @ ax), float((cen[b] - carp) @ pal)] for b in CARPALS}
    # index ray joint centres = child body origins of MCP2 / PIP / DIP
    J = {k: m.body_world(b)[:3, 3] for k, b in (('MCP2', 'Iphalanx1'), ('PIP2', 'Iphalanx2'), ('DIP2', 'Iphalanx3'))}
    dp = meshes['fingers4'][1]; L, dax, dc = pca_extent(dp)
    if (dc - J['DIP2']) @ dax < 0:
        dax = -dax
    tip = dp[np.argmax((dp - J['DIP2']) @ dax)]
    base_proj = float(((dp - J['DIP2']) @ dax).min())
    index = {'MCP_to_PIP_mm': float(np.linalg.norm(J['PIP2'] - J['MCP2']) * 1000), 'PIP_to_DIP_mm': float(np.linalg.norm(J['DIP2'] - J['PIP2']) * 1000),
             'DIP_centre_to_bony_tip_mm': float(np.linalg.norm(tip - J['DIP2']) * 1000), 'distal_phalanx_mesh_extent_mm': L * 1000,
             'DIP_centre_to_distal_phalanx_base_along_axis_mm': base_proj * 1000,
             'tip_offset_over_extent': float(np.linalg.norm(tip - J['DIP2']) / L)}
    commit = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    url = lambda rel: f'https://github.com/opensim-org/opensim-models/blob/{commit}/{rel}'      # external files: full URL at pinned commit
    used = {url(f'Geometry/{k}'): v for k, v in used.items()}
    prov = {'credits': m.root.find('credits').text, 'publication': m.root.find('publications').text,
            'repository': 'https://github.com/opensim-org/opensim-models', 'commit': subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
            'model_file': url('Models/WristModel/wrist.osim'), 'model_sha256': sha(osim), 'meshes_sha256': used,
            'mesh_vertex_counts': {k: int(len(v[1])) for k, v in meshes.items()},
            'note': 'decimated display meshes (26-201 vertices per bone); extents are coarse'}
    return prov, lengths, forearm, frame, index


def m_body_world(m, body, flex):
    m.coords['MCP2_flex'] = flex; m.world = {'ground': np.eye(4)}
    W = m.body_world(body); m.coords['MCP2_flex'] = 0.0; m.world = {'ground': np.eye(4)}
    return W


def a003_frames():
    a = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())['bones']
    S = json.loads((ANAT / 'audit/runs/isolated_bone_only_014/isolated_samples.json').read_text())
    out = {}
    for side in ('left', 'right'):
        r, u, e = (np.asarray(a[f'{n}_{side}']['tail_m']) for n in ('radius', 'ulna', 'humerus'))
        ax = r - e; ax /= np.linalg.norm(ax); rd = r - u; rd -= rd @ ax * ax; rd /= np.linalg.norm(rd)
        pal = np.cross(ax, rd); pal /= np.linalg.norm(pal)
        fr = S[f'digit3_flexion_{side}']; pk = max(fr, key=lambda f: f['commanded'].get('mcp', 0))
        D = np.asarray(pk['moving_deltas'][f'digit3_distal_phalanx_{side}']); tip = np.asarray(a[f'digit3_distal_phalanx_{side}']['tail_m'])
        if ((D[:3, :3] @ tip + D[:3, 3]) - tip) @ pal < 0:
            pal = -pal
        B = {b: (np.asarray(a[f'{b}_{side}']['head_m']) + np.asarray(a[f'{b}_{side}']['tail_m'])) / 2 for b in CARPALS}
        ca = np.mean(list(B.values()), 0)
        out[side] = {b: [float((B[b] - ca) @ rd), float((B[b] - ca) @ ax), float((B[b] - ca) @ pal)] for b in CARPALS}
    return out


def relations(frame):
    k = {'radial': 0, 'distal': 1, 'palmar': 2}
    rows = []
    for a, b, axis, sg in RELATIONS:
        d = (frame[a][k[axis]] - frame[b][k[axis]]) * 1000
        rows.append({'relation': f'{a} {"+" if sg > 0 else "-"}{axis} of {b}', 'offset_mm': round(d, 2), 'holds': bool(d * sg > 0)})
    return rows


def run(repo):
    prov, lengths, forearm, mframe, index = model_part(repo)
    hp = json.loads((ANAT / 'canonical_hand_proportion_audit_v1.json').read_text())['bones']
    tab, ratios = {}, []
    for k, L in lengths.items():
        mu = hp.get(k, {}).get('ayd1998_male_mean_mm')
        tab[k] = {'model_extent_mm': round(L, 2), 'ayd1998_male_mean_mm': mu, 'a003_mm': round(hp.get(k, {}).get('a003_mm', float('nan')), 2),
                  'model_over_ayd': round(L / mu, 3) if mu else None}
        if mu:
            ratios.append(L / mu)
    r = np.array(ratios)
    prop = {}
    for d, (pp, mp, dp) in {2: ('digit2_proximal_phalanx', 'digit2_middle_phalanx', 'digit2_distal_phalanx'), 3: ('digit3_proximal_phalanx', 'digit3_middle_phalanx', 'digit3_distal_phalanx'),
                            4: ('digit4_proximal_phalanx', 'digit4_middle_phalanx', 'digit4_distal_phalanx'), 5: ('digit5_proximal_phalanx', 'digit5_middle_phalanx', 'digit5_distal_phalanx')}.items():
        g = lambda k, src: tab[k]['model_extent_mm'] if src == 'm' else tab[k]['ayd1998_male_mean_mm']
        prop[f'digit{d}'] = {'DP/PP_model': round(g(dp, 'm') / g(pp, 'm'), 3), 'DP/PP_ayd': round(g(dp, 'a') / g(pp, 'a'), 3),
                             'MP/PP_model': round(g(mp, 'm') / g(pp, 'm'), 3), 'MP/PP_ayd': round(g(mp, 'a') / g(pp, 'a'), 3)}
    prop['thumb'] = {'DP/PP_model': round(tab['thumb_distal_phalanx']['model_extent_mm'] / tab['thumb_proximal_phalanx']['model_extent_mm'], 3),
                     'DP/PP_ayd': round(23 / 31, 3)}
    a3 = a003_frames()
    topo = {'model': relations(mframe), 'a003_left': relations(a3['left']), 'a003_right': relations(a3['right'])}
    return {'provenance': prov,
            'lengths': tab,
            'scale': {'model_over_ayd_mean': round(float(r.mean()), 3), 'sd': round(float(r.std()), 3), 'min': round(float(r.min()), 3), 'max': round(float(r.max()), 3),
                      'forearm': {k: round(v, 1) for k, v in forearm.items()},
                      'finding': 'model hand bones are 1.12-1.43x the male radiographic means (not a constant scale) while its radius is not enlarged; the model is NOT a dimensional source for any HGPT bone length or world coordinate'},
            'scale_free_digit_proportions': prop,
            'carpal_topology': topo,
            'carpal_topology_all_hold': {k: all(x['holds'] for x in v) for k, v in topo.items()},
            'index_ray_model': {k: round(v, 3) for k, v in index.items()},
            'decision': {'source_count_for_any_coordinate': 1, 'coordinates_or_lengths_adopted': 0,
                         'fingertip_tails': 'REMAIN UNRESOLVED: the model supplies one DIP-centre-to-bony-tip geometry (index only, decimated mesh, non-population scale); a second compatible independent source is still required',
                         'carpal_layout': 'topology corroboration only'}}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--models-repo', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    r = run(Path(o.models_repo))
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'SOURCE_CONTEXT_NOT_A_TARGET', **r}, indent=1) + '\n')
    print(json.dumps({k: r[k] for k in ('scale', 'carpal_topology_all_hold', 'index_ray_model', 'scale_free_digit_proportions')}, indent=0)[:3000])
    for k, v in r['carpal_topology'].items():
        print(k, [(x['relation'], x['offset_mm']) for x in v if not x['holds']])


if __name__ == '__main__':
    main()
