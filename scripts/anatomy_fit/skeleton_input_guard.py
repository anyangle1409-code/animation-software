#!/usr/bin/env python3
"""Guard against stale skeleton_input points in derived candidate records (read-only).

isolated_tests.frames()/specs() and skeleton_fit.py read record['skeleton_input'] directly, so a builder that moves bones
and joint markers but not the inputs they were built from silently desynchronises derived test frames and centres (the
c001-c003 defect). For every 3-vector in skeleton_input['sides'] (nested dicts and point lists included) the guard records,
in the BASE record, which joint-marker centres and bone endpoints it coincides with (<= 1e-9 m: exact construction
identity, not an anatomical tolerance). In the CANDIDATE the same point must coincide with the same references. Points
that coincide with nothing in the base are listed as unanchored (not checkable by identity).

  skeleton_input_guard.py --base BASE.json --candidate CAND.json [--out JSON]
"""
import argparse, json
from pathlib import Path

import numpy as np

TOL_M = 1e-9


def points(sides):
    out = {}

    def walk(v, path):
        if isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v):
            out[path] = np.asarray(v, float)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                walk(x, f'{path}[{i}]')
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(x, f'{path}/{k}')
    for side, d in sides.items():
        walk(d, side)
    return out


def references(rec):
    R = {f'marker:{k}': np.asarray(m['centre_m'], float) for k, m in rec['joint_markers'].items()}
    for n, b in rec['bones'].items():
        R[f'bone:{n}:head'] = np.asarray(b['head_m'], float); R[f'bone:{n}:tail'] = np.asarray(b['tail_m'], float)
    return R


def anchors(rec):
    P, R = points(rec['skeleton_input']['sides']), references(rec)
    names = list(R); M = np.array([R[n] for n in names])
    return {p: [names[i] for i in np.where(np.linalg.norm(M - v, axis=1) <= TOL_M)[0]] for p, v in P.items()}


def check(base, cand):
    A = anchors(base); P = points(cand['skeleton_input']['sides']); R = references(cand)
    viol, ok = [], 0
    for p, refs in A.items():
        if not refs:
            continue
        if p not in P:
            viol.append({'point': p, 'kind': 'missing_in_candidate'}); continue
        gaps = {r: float(np.linalg.norm(P[p] - R[r])) * 1000 for r in refs if r in R}
        bad = {r: round(g, 4) for r, g in gaps.items() if g > TOL_M * 1000}
        if bad:
            viol.append({'point': p, 'anchored_to': refs, 'gap_mm': bad})
        else:
            ok += 1
    return {'points': len(A), 'anchored': sum(1 for r in A.values() if r), 'unanchored': sorted(p for p, r in A.items() if not r),
            'consistent': ok, 'violations': viol, 'violation_keys': sorted({v['point'].split('/', 1)[1].split('/')[0].split('[')[0] for v in viol})}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--base', required=True); ap.add_argument('--candidate', required=True); ap.add_argument('--out')
    o = ap.parse_args()
    r = check(json.loads(Path(o.base).read_text()), json.loads(Path(o.candidate).read_text()))
    if o.out:
        Path(o.out).write_text(json.dumps(r, indent=1) + '\n')
    print({k: r[k] for k in ('points', 'anchored', 'consistent', 'violation_keys')}, 'violations', len(r['violations']))


if __name__ == '__main__':
    main()
