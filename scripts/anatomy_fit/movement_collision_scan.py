#!/usr/bin/env python3
"""Dynamic bone-axis crossing scan over committed Phase 9 isolated-test samples (read-only; no geometry change).

The isolated runs check implementation integrity but do not exercise contact. This scan reconstructs every bone's stick
(head-tail axis) at every sampled frame from the committed samples: a bone's world pose is the recorded world delta of
its nearest commanded ancestor (itself included), applied to its rest endpoints; unmoved bones stay at rest.

Collision criterion: two bone CENTRAL AXES closer than 1 mm means the bones interpenetrate, because every adult bone in the
206 set has a cross-sectional radius far above 0.5 mm (a conservative mechanical lower bound, not an anatomical tolerance;
no bone surface dimensions are used). Pairs are reported only if they were NOT already in axis contact at
rest; parent/child pairs (they share an articulation) are excluded. Closest approaches are listed for information,
never graded (sticks are not bone surfaces).

  movement_collision_scan.py --record R.json --samples S.json --label NAME --out JSON [--stride 2]
"""
import argparse, hashlib, json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CONTACT_M = 1e-3


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg_dist_many(p1, q1, P2, Q2):
    """Minimum distances between one segment p1-q1 and N segments P2-Q2 (vectorised, clamped closest points)."""
    d1 = q1 - p1; D2 = Q2 - P2; R = p1 - P2
    a = d1 @ d1; e = np.einsum('ij,ij->i', D2, D2); f = np.einsum('ij,ij->i', D2, R)
    c = R @ d1; b = D2 @ d1
    den = a * e - b * b
    s = np.where(den > 1e-18, np.clip((b * f - c * e) / np.where(den > 1e-18, den, 1), 0, 1), 0.0)
    t = np.clip((b * s + f) / np.where(e > 1e-18, e, 1), 0, 1)
    s = np.clip((b * t - c) / (a if a > 1e-18 else 1), 0, 1)
    diff = (p1 + np.outer(s, d1)) - (P2 + D2 * t[:, None])
    return np.linalg.norm(diff, axis=1)


def scan(rec, samples, stride=2):
    B = rec['bones']; names = sorted(B)
    idx = {n: i for i, n in enumerate(names)}
    H0 = np.array([B[n]['head_m'] for n in names], float); T0 = np.array([B[n]['tail_m'] for n in names], float)
    parent = {n: B[n]['parent'] for n in names}
    related = {frozenset((n, p)) for n, p in parent.items() if p}
    # rest contacts (excluded from 'new')
    rest_contact = set()
    for i, n in enumerate(names):
        d = seg_dist_many(H0[i], T0[i], H0, T0)
        for j in np.where(d < CONTACT_M)[0]:
            if j != i:
                rest_contact.add(frozenset((n, names[j])))

    def anc_delta(n, deltas):
        m = n
        while m is not None:
            if m in deltas:
                return deltas[m]
            m = parent[m]
        return None
    new, closest, tests_with_new = [], {}, set()
    for tid, frames in samples.items():
        for fr in frames[::stride]:
            deltas = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            H, T = H0.copy(), T0.copy()
            moved = []
            for n in names:
                Dm = anc_delta(n, deltas)
                if Dm is not None:
                    i = idx[n]; H[i] = Dm[:3, :3] @ H0[i] + Dm[:3, 3]; T[i] = Dm[:3, :3] @ T0[i] + Dm[:3, 3]; moved.append(i)
            if not moved:
                continue
            mset = set(moved)
            for i in moved:
                d = seg_dist_many(H[i], T[i], H, T)
                for j in np.argsort(d)[:6]:
                    if j == i or (j in mset and j < i):
                        continue
                    pair = frozenset((names[i], names[j]))
                    if pair in related or pair in rest_contact:
                        continue
                    key = (tid, tuple(sorted(pair)))
                    if key not in closest or d[j] < closest[key]:
                        closest[key] = float(d[j])
                    if d[j] < CONTACT_M:
                        new.append({'test': tid, 'frame': fr['frame'], 'bones': sorted(pair), 'axis_distance_m': float(d[j])})
                        tests_with_new.add(tid)
    worst = {}
    for c in new:
        k = (c['test'], tuple(c['bones']))
        if k not in worst or c['axis_distance_m'] < worst[k]['axis_distance_m']:
            worst[k] = c
    near = sorted(({'test': k[0], 'bones': list(k[1]), 'min_axis_distance_mm': round(v * 1000, 2)} for k, v in closest.items()),
                  key=lambda x: x['min_axis_distance_mm'])[:25]
    profiles = {}
    for (tid, pair), c in worst.items():                    # full-resolution distance profile for each crossing
        a, b = idx[pair[0]], idx[pair[1]]
        rows = []
        for fr in samples[tid]:
            deltas = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            ends = []
            for i in (a, b):
                Dm = anc_delta(names[i], deltas)
                h, t = (H0[i], T0[i]) if Dm is None else (Dm[:3, :3] @ H0[i] + Dm[:3, 3], Dm[:3, :3] @ T0[i] + Dm[:3, 3])
                ends.append((h, t))
            d = float(seg_dist_many(ends[0][0], ends[0][1], np.array([ends[1][0]]), np.array([ends[1][1]]))[0])
            rows.append({'frame': fr['frame'], 'commanded': fr['commanded'], 'axis_distance_mm': round(d * 1000, 3)})
        inside = [r for r in rows if r['axis_distance_mm'] < CONTACT_M * 1000]
        profiles[f'{tid}|{pair[0]}|{pair[1]}'] = {'first_frame_below_bound': inside[0] if inside else None,
                                                  'minimum': min(rows, key=lambda r: r['axis_distance_mm']), 'frames_below_bound': len(inside)}
    return {'tests_scanned': len(samples), 'stride': stride, 'rest_axis_contacts_excluded': len(rest_contact), 'crossing_profiles': profiles,
            'new_axis_crossings': sorted(worst.values(), key=lambda c: (c['test'], c['bones'])),
            'tests_with_new_crossings': sorted(tests_with_new), 'closest_new_approaches_info_only': near}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--stride', type=int, default=2)
    o = ap.parse_args()
    rec = json.loads(Path(o.record).read_text()); samples = json.loads(Path(o.samples).read_text())
    r = scan(rec, samples, o.stride)
    out = {'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_SCAN_NO_GEOMETRY_CHANGE',
           'criterion': f'bone central axes closer than {CONTACT_M} m => interpenetration (every adult bone radius far exceeds 0.5 mm; conservative mechanical bound); parent/child and rest-contact pairs excluded; closest approaches not graded',
           'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, **r}
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(o.label, 'tests', r['tests_scanned'], 'new crossings', len(r['new_axis_crossings']), 'in tests', r['tests_with_new_crossings'][:20])
    for c in r['new_axis_crossings'][:30]:
        print('  ', c)
    print('closest', r['closest_new_approaches_info_only'][:8])


if __name__ == '__main__':
    main()
