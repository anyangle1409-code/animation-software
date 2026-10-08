#!/usr/bin/env python3
"""Shoulder-proposal audit candidate record (fit-record schema), NOT a canonical skeleton.

a003's record with only the shoulder girdle replaced by the reconciled CP1a solution
(canonical_shoulder_girdle_solution_182_v1.json, preferred source-scale variant, bony-specimen thorax pitch, IJ at the a003
bony IJ). The humerus and everything distal to it are translated rigidly so the GH centre moves to the proposed one;
their lengths and orientations are a003's. Trunk, spine, ribs, sternum and every other bone are a003's, unchanged.
Choices are recorded in the output: GH head radius 24.0 mm (the variant closest to the independent Seth AC-GH check).

  build_shoulder_candidate_record.py --out JSON
"""
import argparse, copy, hashlib, json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
BASE = ANAT / 'character_fit_r95_a003.json'
SOLUTION = ANAT / 'canonical_shoulder_girdle_solution_182_v1.json'
VARIANT, WORLD = 'source_scale', 'bony_specimen_deg__IJ_at_a003'
GH_KEY = 'GH_mixed_cadaver_MRI_24.0'
CANDIDATE_ID = 'r95_a003_shoulder_proposal_c001'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def descendants(bones, root):
    out, frontier = {root}, [root]
    while frontier:
        cur = frontier.pop()
        for k, b in bones.items():
            if b['parent'] == cur and k not in out:
                out.add(k); frontier.append(k)
    return out


def build():
    rec = json.loads(BASE.read_text())
    sol = json.loads(SOLUTION.read_text())
    w = sol['variants'][VARIANT]['world_mm'][WORLD]
    cand = copy.deepcopy(rec)
    B, J = cand['bones'], cand['joint_markers']
    m = lambda v: [float(x) / 1000.0 for x in v]
    moved_bones, moved_markers, deltas = {}, {}, {}
    for side in ('left', 'right'):
        s = w[side]
        sc, ac, gh = m(s['SC']), m(s['AC']), m(s[GH_KEY])
        ts, ai, glen = m(s['TS']), m(s['AI']), m(s['glenoid_shallowest'])
        d = np.array(gh) - np.array(rec['joint_markers'][f'glenohumeral_{side}']['centre_m'])
        deltas[side] = [round(float(x) * 1000, 2) for x in d]
        B[f'clavicle_{side}']['head_m'], B[f'clavicle_{side}']['tail_m'] = sc, ac
        B[f'scapula_{side}']['head_m'], B[f'scapula_{side}']['tail_m'] = glen, ai
        arm = descendants(B, f'humerus_{side}')
        for k in arm:
            for e in ('head_m', 'tail_m'):
                B[k][e] = [float(x) for x in np.array(B[k][e]) + d]
        B[f'humerus_{side}']['head_m'] = gh
        for k in sorted(arm | {f'clavicle_{side}', f'scapula_{side}'}):
            B[k]['placement'] = 'shoulder_proposal' if k in (f'clavicle_{side}', f'scapula_{side}') else B[k]['placement']
            moved_bones[k] = 'replaced' if k in (f'clavicle_{side}', f'scapula_{side}') else 'translated with GH'
        J[f'sternoclavicular_{side}']['centre_m'] = sc
        J[f'acromioclavicular_{side}']['centre_m'] = ac
        J[f'glenohumeral_{side}']['centre_m'] = gh
        J[f'scapulothoracic_{side}']['centre_m'] = [(a + b) / 2 for a, b in zip(ts, ai)]
        for k in (f'sternoclavicular_{side}', f'acromioclavicular_{side}', f'glenohumeral_{side}', f'scapulothoracic_{side}'):
            moved_markers[k] = 'replaced (centre only; frame orientation kept from a003)'
        for jid, mk in J.items():
            if jid in moved_markers:
                continue
            if mk.get('frame_bone') in arm:
                mk['centre_m'] = [float(x) for x in np.array(mk['centre_m']) + d]
                moved_markers[jid] = 'translated with GH'
        S = cand['skeleton_input']['sides'][side]
        for key, val in (('SC', sc), ('AC', ac), ('AA', m(s['AA'])), ('TS', ts), ('AI', ai), ('GH', gh), ('glenoid', glen)):
            S[key] = val
    cand['candidate'] = {
        'id': CANDIDATE_ID, 'status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED', 'freeze_ready': False,
        'base_record': {'path': str(BASE.relative_to(ROOT)), 'sha256': sha(BASE)},
        'solution': {'path': str(SOLUTION.relative_to(ROOT)), 'sha256': sha(SOLUTION), 'variant': VARIANT, 'world': WORLD, 'GH_radius_variant': GH_KEY},
        'changed': 'clavicles and scapulae replaced; SC/AC/GH/scapulothoracic centres replaced; humerus subtree translated rigidly',
        'unchanged': 'every other bone and marker; trunk height and thorax of a003 (IJ at the a003 bony IJ)',
        'GH_translation_mm': deltas, 'moved_bones': moved_bones, 'moved_markers': moved_markers,
        'scapula_landmarks_world_mm': {side: w[side]['scapula_all_29'] for side in ('left', 'right')},
        'open_questions': sol['still_open'] + ['absolute shoulder height relative to the trunk (vertical_relation_check)'],
        'limitations': ['a003 arm lengths and trunk retained; forearm shortness (owner policy) not applied in this shoulder-stage candidate',
                        'SC/AC/GH marker frames keep a003 orientations; only their centres changed',
                        'the scapula reference bone is a glenoid-to-inferior-angle stick; the 29 measured landmarks are stored separately',
                        'r95 mesh is not refitted; bones may lie outside the authored skin by design (skeleton-first)']}
    cand['character_accepted'] = False
    return cand


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    out = Path(o.out); out.parent.mkdir(parents=True, exist_ok=True)
    c = build()
    out.write_text(json.dumps(c, indent=1) + '\n')
    print(json.dumps({k: c['candidate'][k] for k in ('id', 'GH_translation_mm')}), len(c['candidate']['moved_bones']), 'bones changed',
          len(c['candidate']['moved_markers']), 'markers changed')


if __name__ == '__main__':
    main()
