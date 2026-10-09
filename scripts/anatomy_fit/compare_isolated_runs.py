#!/usr/bin/env python3
"""Compare two isolated-sweep sample files with explicit numerical tolerances (read-only).

GH plane of elevation is undefined at zero elevation and is not compared there; angle-like
differences are taken modulo 360. Fresh Blender builds re-quantise to float32, so byte equality is too strict: a test counts as MATERIALLY CHANGED only if
some numeric channel differs by more than --tol-deg (angles) / --tol-m (lengths; keys ending in _m or _mm handled) .

  compare_isolated_runs.py --a A.json --b B.json --out JSON
"""
import argparse, json
from pathlib import Path


def canon(x):
    """GH Y-X-Y: at |elevation| < 0.01 deg the plane of elevation is undefined (gimbal singularity; the measurement keeps the
    axial rotation in internal_rotation), so it is not compared there."""
    if isinstance(x, dict):
        y = {k: canon(v) for k, v in x.items()}
        if 'plane_of_elevation' in y and 'elevation' in y and isinstance(y['elevation'], (int, float)) and abs(y['elevation']) < 0.01:
            y['plane_of_elevation'] = 0.0
        r = y.get('isb_yxy_raw')
        if isinstance(r, list) and len(r) == 3 and all(isinstance(v, (int, float)) for v in r) and abs(r[1]) < 0.1:
            y['isb_yxy_raw'] = [0.0, 0.0, 0.0]      # raw YXY is ill-conditioned within 0.1 deg of the singular rest (diagnostic only)
        return y
    if isinstance(x, list):
        return [canon(v) for v in x]
    return x


def leaves(x, path=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f'{path}/{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f'{path}[{i}]')
    else:
        yield path, x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True); ap.add_argument('--b', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--tol-deg', type=float, default=1e-3); ap.add_argument('--tol-m', type=float, default=1e-6)
    o = ap.parse_args()
    A, B = json.loads(Path(o.a).read_text()), json.loads(Path(o.b).read_text())
    res = {}
    for t in sorted(set(A) | set(B)):
        if t not in A or t not in B:
            res[t] = {'status': 'MISSING'}; continue
        la, lb = dict(leaves(canon(A[t]))), dict(leaves(canon(B[t])))
        if set(la) != set(lb):
            res[t] = {'status': 'STRUCTURE_DIFFERS'}; continue
        worst_deg = worst_m = 0.0; other = 0
        for k, va in la.items():
            vb = lb[k]
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
                d = abs(va - vb)
                key = k.split('/')[-1].split('[')[0]
                if key.endswith('_m') or 'displacement' in key or 'glide' in key or key in ('centre', 'head', 'tail'):
                    worst_m = max(worst_m, d)
                else:
                    worst_deg = max(worst_deg, abs((d + 180.0) % 360.0 - 180.0) if d > 180 else d)      # angle wrap
            elif va != vb:
                other += 1
        changed = worst_deg > o.tol_deg or worst_m > o.tol_m or other
        res[t] = {'status': 'MATERIALLY_CHANGED' if changed else 'SAME_WITHIN_TOLERANCE', 'worst_angle_like': worst_deg, 'worst_length_m': worst_m,
                  'non_numeric_differences': other}
    summ = {s: sorted(t for t, v in res.items() if v['status'] == s) for s in ('MATERIALLY_CHANGED', 'SAME_WITHIN_TOLERANCE', 'MISSING', 'STRUCTURE_DIFFERS')}
    out = {'schema_version': 1, 'a': o.a, 'b': o.b, 'tolerances': {'deg_or_unitless': o.tol_deg, 'm': o.tol_m},
           'counts': {k: len(v) for k, v in summ.items()}, 'groups': summ, 'tests': res}
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(out['counts']); print('changed:', summ['MATERIALLY_CHANGED'])


if __name__ == '__main__':
    main()
