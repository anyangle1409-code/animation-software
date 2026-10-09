#!/usr/bin/env python3
"""Audit of the remaining stale carpals/hand skeleton_input points (c001-c004) and source-rebuild test (read-only).

A. Point audit. skeleton_input.sides.<side>.carpals.<carpal> and .hand.<key> are [head, tail] pairs consumed ONLY by
   skeleton_fit.build (one bone each; isolated_tests / joint_markers do not read them). For every point: the bone endpoint
   it constructs, its a003 relation to that endpoint (exact identity, or the containment offset recorded on the bone),
   the candidate value (stale = equal to a003), the committed c004 bone endpoint, the displacement vector, and whether a
   correction is UNIQUELY determined by c004 geometry:
     UNIQUE_EXACT         a003 input == a003 bone endpoint; c004 endpoint is the only consistent value;
     NOT_ENCODED          a003 input is a pre-containment station (skeleton_fit.contain moved the bone tail inside the
                          a003 skin); c004 encodes only the post-containment endpoint, so the input is not determined.
B. Source rebuild (skeleton_fit.build -> enforce_midline -> contain against the a003 body mesh; the master builder's
   pipeline) of: a003 inputs (must reproduce a003 bones); c004 inputs (stale hand); hypothesis H1 (every carpal/hand
   point + the side's GH translation) and H2 (every point = its c004 bone endpoint). Each rebuild is compared with the
   committed bones. Without --mesh, contain() is skipped and only bones with no containment record are compared.

  hand_input_source_rebuild_audit.py --out JSON [--mesh MESH.npz]   (MESH from export_body_mesh_blender.py)
"""
import argparse, copy, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import skeleton_fit as sf  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
CAND = ANAT / 'audit/candidates'
P = {'a003': ANAT / 'character_fit_r95_a003.json', 'c001': CAND / 'shoulder_proposal_c001/candidate_record.json',
     'c002': CAND / 'shoulder_proposal_c002_ansur_height/candidate_record.json', 'c003': CAND / 'shoulder_thorax_c003_ansur_coupled/candidate_record.json',
     'c004': CAND / 'shoulder_thorax_c004_arm_inputs/candidate_record.json'}
SKULL = {'parietal_left', 'parietal_right', 'frontal', 'zygomatic_left', 'zygomatic_right', 'temporal_left', 'temporal_right', 'sphenoid', 'ethmoid', 'occipital'}
ENDS = ('head_m', 'tail_m')
CONSUMERS = ['scripts/anatomy_fit/skeleton_fit.py:build (bone head/tail)']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bone_of(group, key, side):
    if group == 'carpals':
        return f'{key}_{side}'
    if key in ('th_pp', 'th_dp'):
        return {'th_pp': 'thumb_proximal_phalanx', 'th_dp': 'thumb_distal_phalanx'}[key] + f'_{side}'
    if key.startswith('mc'):
        return f'metacarpal_{key[2:]}_{side}'
    d, ph = key.split('_')
    return f'digit{d[1:]}_{ {"pp": "proximal", "mp": "middle", "dp": "distal"}[ph]}_phalanx_{side}'


def gh_shift(rec, base, side):
    return np.asarray(rec['joint_markers'][f'glenohumeral_{side}']['centre_m']) - np.asarray(base['joint_markers'][f'glenohumeral_{side}']['centre_m'])


def point_audit(R):
    a, c4 = R['a003'], R['c004']
    rows = []
    for side in ('left', 'right'):
        for group in ('carpals', 'hand'):
            for key, pair in a['skeleton_input']['sides'][side][group].items():
                b = bone_of(group, key, side)
                for i, end in enumerate(ENDS):
                    pa = np.asarray(pair[i]); ea = np.asarray(a['bones'][b][end]); e4 = np.asarray(c4['bones'][b][end])
                    adj = a['bones'][b].get('containment_adjustment_m', {}).get(end)
                    exact = float(np.linalg.norm(pa - ea)) <= 1e-12
                    row = {'side': side, 'group': group, 'key': key, 'index': i, 'bone': b, 'end': end,
                           'a003_relation': 'identical_to_bone_endpoint' if exact else 'pre_containment_station',
                           'a003_offset_mm': [round(x * 1000, 3) for x in pa - ea], 'a003_containment_adjustment_mm': None if adj is None else round(adj * 1000, 3),
                           'c004_bone_endpoint_m': e4.tolist(), 'c004_endpoint_minus_input_mm': [round(x * 1000, 3) for x in e4 - np.asarray(c4['skeleton_input']['sides'][side][group][key][i])],
                           'c004_bone_moved_by_gh_shift': bool(np.linalg.norm((e4 - ea) - gh_shift(c4, a, side)) <= 1e-9),
                           'stale_in': [k for k in ('c001', 'c002', 'c003', 'c004') if R[k]['skeleton_input']['sides'][side][group][key][i] == pair[i]],
                           'correction': 'UNIQUE_EXACT' if exact else 'NOT_ENCODED'}
                    rows.append(row)
    return rows


def rebuild(L, clearance):
    S = sf.build(copy.deepcopy(L)); sf.enforce_midline(S)
    if clearance is not None:
        cc = L['head']['cranial_centre']
        sf.contain(S, clearance, anchors={**{b: cc for b in SKULL}, '__fallback__': cc})
    return S.bones


def compare(Bn, B, skip_contained):
    out = {}
    for n, b in B.items():
        if skip_contained and 'containment_adjustment_m' in b:
            continue
        e = max(float(np.linalg.norm(np.asarray(Bn[n][k]) - np.asarray(b[k]))) for k in ENDS)
        if e > 1e-9:
            out[n] = round(e * 1000, 3)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def hypotheses(R):
    a, c4 = R['a003'], R['c004']
    H = {}
    for h in ('H1_rigid_gh_translation', 'H2_snap_to_c004_endpoint'):
        L = copy.deepcopy(c4['skeleton_input'])
        for side in ('left', 'right'):
            T = gh_shift(c4, a, side)
            for group in ('carpals', 'hand'):
                for key, pair in L['sides'][side][group].items():
                    for i, end in enumerate(ENDS):
                        pair[i] = (np.asarray(pair[i]) + T).tolist() if h.startswith('H1') else list(c4['bones'][bone_of(group, key, side)][end])
        H[h] = L
    return H


def run(mesh=None):
    R = {k: json.loads(p.read_text()) for k, p in P.items()}
    rows = point_audit(R)
    clearance, mesh_info = None, None
    if mesh:
        import character_fit as cf
        m = np.load(mesh)
        clearance = cf.make_clearance(m['V'], m['T'])
        mesh_info = {'vertices': int(len(m['V'])), 'triangles': int(len(m['T'])), 'from_blend_sha256': str(m['blend_sha256']),
                     'record_character': R['a003']['provenance']['character']}
    skip = clearance is None
    reb = {'a003_inputs_vs_a003': compare(rebuild(R['a003']['skeleton_input'], clearance), R['a003']['bones'], skip),
           'c004_inputs_vs_c004': compare(rebuild(R['c004']['skeleton_input'], clearance), R['c004']['bones'], skip)}
    for h, L in hypotheses(R).items():
        reb[f'{h}_vs_c004'] = compare(rebuild(L, clearance), R['c004']['bones'], skip)
    arm_outside = None
    if clearance is not None:
        arm_outside = {}
        for k in ('a003', 'c004'):
            pts = [(n, e) for n in R[k]['bones'] if n.endswith('_left') and any(n.startswith(p) for p in ('humerus', 'radius', 'ulna', 'scaphoid', 'lunate', 'capitate', 'metacarpal', 'digit', 'thumb'))
                   for e in ENDS]
            arm_outside[k] = sorted(f'{n}:{e}' for n, e in pts if clearance(R[k]['bones'][n][e]) < 0)
    n = len(rows)
    uniq = sum(r['correction'] == 'UNIQUE_EXACT' for r in rows)
    return {'inputs_sha256': {k: sha(p) for k, p in P.items()}, 'consumers': CONSUMERS, 'mesh': mesh_info, 'contain_applied': clearance is not None,
            'points': n, 'unique_exact': uniq, 'not_encoded': [f"{r['side']}/{r['group']}/{r['key']}[{r['index']}] ({r['bone']} {r['end']}, contained {r['a003_containment_adjustment_mm']} mm)" for r in rows if r['correction'] == 'NOT_ENCODED'],
            'stale_counts': {k: sum(k in r['stale_in'] for r in rows) for k in ('c001', 'c002', 'c003', 'c004')},
            'all_c004_hand_bones_moved_by_gh_shift': all(r['c004_bone_moved_by_gh_shift'] for r in rows),
            'rebuild': {k: {'bones_differing': len(v), 'max_mm': max(v.values()) if v else 0.0, 'bones': v} for k, v in reb.items()},
            'c004_arm_points_outside_a003_skin_left': arm_outside,
            'decision': None, 'points_detail': rows}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--mesh')
    o = ap.parse_args()
    r = run(o.mesh)
    full = r['contain_applied']
    ok_unique = r['unique_exact'] == r['points']
    h_ok = all(r['rebuild'][k]['bones_differing'] == 0 for k in r['rebuild'] if k.startswith('H'))
    r['decision'] = ('C005_DEFENSIBLE' if ok_unique and h_ok else
                     'NO_C005: ' + '; '.join(x for x in [
                         None if ok_unique else f"{len(r['not_encoded'])} fingertip inputs are pre-containment stations not encoded by c004 bones/markers",
                         None if h_ok else ('no correction hypothesis reproduces c004 geometry by source rebuild' + (' (contain() against the unmoved a003 skin relocates the translated hand)' if full else ''))] if x))
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_INPUT_AUDIT_AND_SOURCE_REBUILD', **r}, indent=1) + '\n')
    print({k: r[k] for k in ('points', 'unique_exact', 'stale_counts', 'all_c004_hand_bones_moved_by_gh_shift', 'decision')})
    print({k: (v['bones_differing'], v['max_mm']) for k, v in r['rebuild'].items()})
    print('not encoded', r['not_encoded']); print('arm outside skin', r['c004_arm_points_outside_a003_skin_left'])


if __name__ == '__main__':
    main()
