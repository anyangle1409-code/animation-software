#!/usr/bin/env python3
"""Candidate record input consistency (read-only): which skeleton_input.sides points did each shoulder candidate builder
leave at a003 values while the bones/joint markers they belong to were moved with GH. isolated_tests.frames() derives the
forearm and hand test frames from these inputs, so stale values tilt derived test axes (seen in joint_frame_audit as
hand/thumb axis-alignment differences). Committed candidates are NOT modified; a fix requires a new named revision.

  candidate_input_consistency.py --out JSON
"""
import argparse, hashlib, json
from pathlib import Path

import numpy as np

ANAT = Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy'
BASE = 'character_fit_r95_a003.json'
CANDS = {'c001': 'audit/candidates/shoulder_proposal_c001/candidate_record.json',
         'c002': 'audit/candidates/shoulder_proposal_c002_ansur_height/candidate_record.json',
         'c003': 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json'}
ARM_INPUTS = {'EJC': 'humeroulnar', 'WJC': 'radiocarpal'}            # input -> joint marker it should coincide with in a003
ARM_KEYS = ('EJC', 'WJC', 'humeroulnar', 'humeroradial', 'ulnar_styloid_bone', 'radial_styloid_bone')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audit():
    a = json.loads((ANAT / BASE).read_text()); out = {}
    for name, rel in CANDS.items():
        c = json.loads((ANAT / rel).read_text()); sides = {}
        for side in ('left', 'right'):
            S0, S1 = a['skeleton_input']['sides'][side], c['skeleton_input']['sides'][side]
            gh = (np.array(c['joint_markers'][f'glenohumeral_{side}']['centre_m']) - np.array(a['joint_markers'][f'glenohumeral_{side}']['centre_m'])) * 1000
            stale = [k for k in ARM_KEYS if k in S1 and S1[k] == S0[k]]
            gaps = {}
            for k, j in ARM_INPUTS.items():
                if k in S1 and isinstance(S1[k], list) and len(S1[k]) == 3:
                    gaps[k] = {'marker': f'{j}_{side}',
                               'a003_mm': round(float(np.linalg.norm(np.array(S0[k]) - np.array(a['joint_markers'][f'{j}_{side}']['centre_m'])) * 1000), 3),
                               'candidate_mm': round(float(np.linalg.norm(np.array(S1[k]) - np.array(c['joint_markers'][f'{j}_{side}']['centre_m'])) * 1000), 3)}
            sides[side] = {'gh_shift_mm': [round(float(x), 2) for x in gh], 'gh_shift_norm_mm': round(float(np.linalg.norm(gh)), 2),
                           'stale_arm_inputs': stale, 'input_to_marker_gap': gaps}
        out[name] = {'record': rel, 'record_sha256': sha(ANAT / rel), 'sides': sides,
                     'classification': 'CANDIDATE_PROVENANCE_DEFECT' if any(s['stale_arm_inputs'] for s in sides.values()) else 'CONSISTENT'}
    return {'baseline': BASE, 'baseline_sha256': sha(ANAT / BASE), 'candidates': out,
            'effect': 'isolated_tests.frames() hand frame uses WJC and forearm frame uses EJC/styloids from skeleton_input.sides; '
                      'bones and joint markers are moved correctly, so geometry is unaffected but derived hand/thumb test axes are '
                      'tilted (joint_frame_audit candidate differences up to ~19 deg)',
            'disposition': 'UNRESOLVED; committed c001/c002/c003 preserved unchanged; a fix requires a new named candidate revision '
                           'that translates the arm skeleton_input points with GH and re-runs Phase 9'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); o = ap.parse_args()
    r = audit()
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'status': 'READ_ONLY_PROVENANCE_AUDIT', **r}, indent=1) + '\n')
    for k, v in r['candidates'].items():
        print(k, v['classification'], {s: (x['gh_shift_norm_mm'], x['input_to_marker_gap']) for s, x in v['sides'].items()})


if __name__ == '__main__':
    main()
