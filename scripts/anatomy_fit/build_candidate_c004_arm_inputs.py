#!/usr/bin/env python3
"""c004: c003 with ONLY the six stale skeleton_input arm points per side resynchronised (audit candidate, not canonical).

c001-c003 builders moved the arm bones and joint markers rigidly with GH but left skeleton_input EJC, WJC, humeroulnar,
humeroradial, ulnar_styloid_bone and radial_styloid_bone at a003 values (joint_frame_audit / candidate_input_consistency).
isolated_tests.frames() builds the forearm and hand test frames from these points and specs() uses WJC as the wrist test
centre, so c003's derived hand/thumb axes and wrist centre are wrong although its geometry is right.

Correction rule (evidence-based, no new numbers): each point takes the committed c003 position of the reference it is
IDENTICAL to (<= 1e-9 m) in a003 - the joint-marker centre where one exists (WJC = radiocarpal, humeroulnar, humeroradial),
otherwise the bone endpoint (EJC = humerus tail, ulnar styloid = ulna tail, radial styloid = radius tail; no joint marker
coincides with these in a003: the nearest are 9.4 / 10.3 / 17.8 mm away, so using a marker would change the point's
definition). Every corrected value must also equal old + the side's GH translation (the arm moved rigidly), which is
asserted. Nothing else changes: bones, joint markers, landmarks, every other skeleton_input entry (including the carpals
and hand point dicts, also stale but outside this scope and recorded as UNRESOLVED), checks and provenance are c003's
byte-for-byte JSON values; only 'candidate' gains the c004 identity and the correction table.

  build_candidate_c004_arm_inputs.py --out-dir DIR
"""
import argparse, copy, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import skeleton_input_guard as guard  # noqa: E402

ROOT = HERE.parents[1]
ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
A003 = ANAT / 'character_fit_r95_a003.json'
C003 = ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json'
C003_BLEND = ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend'
C003_SHA = '3eb4fa1e2f7d815e'
A003_SHA = '11712ba3e105aa88'
KEYS = ('EJC', 'WJC', 'humeroulnar', 'humeroradial', 'ulnar_styloid_bone', 'radial_styloid_bone')
CANDIDATE_ID = 'r95_a003_shoulder_thorax_c004_arm_inputs'
TOL = 1e-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    assert sha(A003).startswith(A003_SHA) and sha(C003).startswith(C003_SHA), 'pinned inputs changed'
    a, c = json.loads(A003.read_text()), json.loads(C003.read_text())
    out = copy.deepcopy(c)
    A = guard.anchors(a); Rc = guard.references(c)
    table = []
    for side in ('left', 'right'):
        gh = np.asarray(c['joint_markers'][f'glenohumeral_{side}']['centre_m']) - np.asarray(a['joint_markers'][f'glenohumeral_{side}']['centre_m'])
        for k in KEYS:
            refs = A[f'{side}/{k}']
            assert refs, (side, k, 'no identity reference in a003')
            markers = [r for r in refs if r.startswith('marker:')]
            ref = markers[0] if markers else refs[0]
            old = np.asarray(c['skeleton_input']['sides'][side][k], float)
            assert np.array_equal(old, np.asarray(a['skeleton_input']['sides'][side][k], float)), (side, k, 'not stale')
            new = Rc[ref]
            assert np.linalg.norm(new - (old + gh)) <= TOL, (side, k, 'target is not the rigid GH translation')
            for r in refs:
                assert np.linalg.norm(new - Rc[r]) <= TOL, (side, k, r, 'other identity reference disagrees')
            nearest = sorted((float(np.linalg.norm(np.asarray(a['joint_markers'][m]['centre_m']) - np.asarray(a['skeleton_input']['sides'][side][k]))), m)
                             for m in a['joint_markers'] if m.endswith('_' + side))[0]
            out['skeleton_input']['sides'][side][k] = new.tolist()
            table.append({'side': side, 'key': k, 'before_m': old.tolist(), 'after_m': new.tolist(),
                          'before_mm': [round(x * 1000, 3) for x in old], 'after_mm': [round(x * 1000, 3) for x in new],
                          'shift_mm': [round(x * 1000, 3) for x in new - old], 'shift_norm_mm': round(float(np.linalg.norm(new - old)) * 1000, 3),
                          'target_reference': ref, 'a003_identity_references': refs,
                          'target_kind': 'joint_marker' if markers else 'bone_endpoint (no joint marker coincides in a003)',
                          'nearest_a003_joint_marker': {'id': nearest[1], 'distance_mm': round(nearest[0] * 1000, 3)},
                          'equals_old_plus_gh_translation': True})
    out['candidate'] = copy.deepcopy(c['candidate'])
    out['candidate'].update({
        'id': CANDIDATE_ID, 'status': 'AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED', 'freeze_ready': False,
        'derived_from': {'record': C003.relative_to(ROOT).as_posix(), 'sha256': sha(C003), 'id': c['candidate']['id']},
        'arm_input_correction': {'keys': list(KEYS), 'rule': 'c003 position of the a003 identity reference (joint marker if any, else bone endpoint); asserted equal to old + GH translation',
                                 'table': table,
                                 'unchanged_but_stale_out_of_scope': ['carpals', 'hand'],
                                 'blend': {'reused': C003_BLEND.relative_to(ROOT).as_posix(), 'sha256': sha(C003_BLEND),
                                           'note': 'geometry unchanged: the candidate blend builder reads only bones, joint_markers and scapula landmarks (+ scene id property); the c003 blend is reused byte-identically and still carries hgpt_candidate_id = c003'}}})
    return out, table


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out-dir', required=True); o = ap.parse_args()
    d = Path(o.out_dir)
    if d.exists():
        raise FileExistsError(d)
    out, table = build()
    d.mkdir(parents=True)
    (d / 'candidate_record.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps([(t['side'], t['key'], t['before_mm'], t['after_mm'], t['shift_norm_mm'], t['target_reference']) for t in table]))


if __name__ == '__main__':
    main()
