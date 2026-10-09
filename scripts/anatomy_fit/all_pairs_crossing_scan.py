#!/usr/bin/env python3
"""All-pairs bone-axis crossing scan for UNCONNECTED bones (read-only; no geometry change; no clearance claims).

Extends movement_collision_scan.py, which examined only the six nearest bones per moving bone and excluded only
parent/child pairs. Here every bone pair is eligible unless the two bones are connected (share an articulation in the
project inventory, or are parent/child). Criterion as documented there: central axes closer than 1 mm => interpenetration
(conservative mechanical bound; every adult bone radius far exceeds 0.5 mm). Reports:
  * static: unconnected pairs whose axes already cross at rest (previously silently excluded);
  * dynamic: unconnected pairs that come within the bound during any sampled frame but not at rest;
  * near approaches (< 3 mm) for information only, never graded.

  all_pairs_crossing_scan.py --record R.json --samples S.json --label NAME --out JSON [--stride 2]
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from movement_collision_scan import seg_dist_many  # noqa: E402
import joint_attachment_scan as ja  # noqa: E402

BOUND_M, INFO_M = 1e-3, 3e-3


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def connected_pairs(rec):
    B = rec['bones']
    conn = {frozenset((n, B[n]['parent'])) for n in B if B[n]['parent']}
    for a in ja.articulations():
        ps = [p for p in a['participants'] if p in B]
        conn |= {frozenset((ps[i], ps[j])) for i in range(len(ps)) for j in range(i + 1, len(ps))}
    return conn


def scan(rec, samples, stride=2):
    B = rec['bones']; names = sorted(B); idx = {n: i for i, n in enumerate(names)}
    H0 = np.array([B[n]['head_m'] for n in names], float); T0 = np.array([B[n]['tail_m'] for n in names], float)
    parent = {n: B[n]['parent'] for n in names}
    conn = connected_pairs(rec)
    elig = np.ones((len(names), len(names)), bool)
    np.fill_diagonal(elig, False)
    for pr in conn:
        a, b = tuple(pr) if len(pr) == 2 else (None, None)
        if a in idx and b in idx:
            elig[idx[a], idx[b]] = elig[idx[b], idx[a]] = False
    rest_d = np.array([seg_dist_many(H0[i], T0[i], H0, T0) for i in range(len(names))])
    static = sorted({tuple(sorted((names[i], names[j]))): round(float(rest_d[i, j]) * 1000, 3)
                     for i in range(len(names)) for j in range(i + 1, len(names)) if elig[i, j] and rest_d[i, j] < BOUND_M}.items())
    rest_contact = rest_d < BOUND_M

    def anc(n, deltas):
        m = n
        while m is not None:
            if m in deltas:
                return deltas[m]
            m = parent[m]
        return None
    dyn, near = {}, {}
    for tid, frames in samples.items():
        for fr in frames[::stride]:
            deltas = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            H, T = H0.copy(), T0.copy(); moved = []
            for n in names:
                D = anc(n, deltas)
                if D is not None:
                    i = idx[n]; H[i] = D[:3, :3] @ H0[i] + D[:3, 3]; T[i] = D[:3, :3] @ T0[i] + D[:3, 3]; moved.append(i)
            for i in moved:
                d = seg_dist_many(H[i], T[i], H, T)
                for j in np.where((d < INFO_M) & elig[i] & ~rest_contact[i])[0]:
                    key = (tid, tuple(sorted((names[i], names[j]))))
                    if d[j] < BOUND_M and (key not in dyn or d[j] < dyn[key]['axis_distance_mm'] / 1000):
                        dyn[key] = {'test': tid, 'bones': list(key[1]), 'frame': fr['frame'], 'axis_distance_mm': round(float(d[j]) * 1000, 3),
                                    'rest_axis_distance_mm': round(float(rest_d[i, j]) * 1000, 3)}
                    if key not in near or d[j] * 1000 < near[key]:
                        near[key] = round(float(d[j]) * 1000, 3)
    CHORD = {'mandible': 'chord from the condylar midpoint (a midline point between the TMJs, not on bone) to the mental region; passes through oral/pharyngeal space, so the axis-inside-bone premise of the bound does not hold'}
    return {'bones': len(names), 'eligible_pairs': int(elig.sum() // 2), 'connected_pairs_excluded': len(conn),
            'static_unconnected_axis_contacts': [{'bones': list(k), 'axis_distance_mm': v,
                                                  'classification': 'REPRESENTATION_ARTEFACT' if any(b in CHORD for b in k) else 'AXIS_CONTACT_AT_REST',
                                                  'reason': next((CHORD[b] for b in k if b in CHORD), None)} for k, v in static],
            'dynamic_new_crossings': sorted(dyn.values(), key=lambda x: (x['test'], x['bones'])),
            'dynamic_tests': sorted({v['test'] for v in dyn.values()}),
            'near_approaches_below_3mm_info_only': sorted(({'test': k[0], 'bones': list(k[1]), 'min_mm': v} for k, v in near.items()
                                                           if v >= BOUND_M * 1000), key=lambda x: x['min_mm'])[:30]}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--stride', type=int, default=2)
    o = ap.parse_args()
    r = scan(json.loads(Path(o.record).read_text()), json.loads(Path(o.samples).read_text()), o.stride)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_SCAN_NO_GEOMETRY_CHANGE',
                                       'criterion': 'unconnected bone axes closer than 1 mm => interpenetration (conservative mechanical bound); near approaches < 3 mm listed, not graded; no clearance claim',
                                       'stride': o.stride, 'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, **r}, indent=1) + '\n')
    print(o.label, {k: r[k] for k in ('bones', 'eligible_pairs', 'connected_pairs_excluded', 'dynamic_tests')}, 'static', len(r['static_unconnected_axis_contacts']))
    for x in r['static_unconnected_axis_contacts'][:20]:
        print('  STATIC', x)
    for x in r['dynamic_new_crossings'][:30]:
        print('  DYN', x)


if __name__ == '__main__':
    main()
