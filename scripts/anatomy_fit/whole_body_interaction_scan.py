#!/usr/bin/env python3
"""Whole-body interaction scan over committed isolated sweeps (read-only). For every frame, the minimum axis-to-axis
distance between each MOVED bone and every bone of a DIFFERENT body region (left arm, right arm, left leg, right leg, trunk/
head) is computed. Pairs closer than 10 mm are listed with the rest-pose distance. No bone radii are sourced in the project,
so nothing is graded as contact: the list identifies sweeps whose end posture needs surface geometry (or a different start
posture) to judge. The 1 mm crossing bound of all_pairs_crossing_scan is the only graded criterion and is reported too.

  whole_body_interaction_scan.py --record R.json --samples S.json --label NAME --out JSON [--stride 2]
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from movement_collision_scan import seg_dist_many  # noqa: E402
from all_pairs_crossing_scan import connected_pairs  # noqa: E402

LIST_MM, CROSS_MM = 10.0, 1.0
ARM = ('clavicle', 'scapula', 'humerus', 'radius', 'ulna', 'scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezium', 'trapezoid', 'capitate', 'hamate', 'metacarpal', 'digit', 'thumb')
LEG = ('hip_bone', 'femur', 'patella', 'tibia', 'fibula', 'talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform', 'metatarsal', 'hallux', 'toe')


def body_region(n):
    side = 'left' if n.endswith('_left') else 'right' if n.endswith('_right') else None
    if side and n.startswith(ARM):
        return 'arm_' + side
    if side and n.startswith(LEG):
        return 'leg_' + side
    return 'trunk_head'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def scan(rec, samples, stride=2):
    B = rec['bones']; names = sorted(B); idx = {n: i for i, n in enumerate(names)}
    H0 = np.array([B[n]['head_m'] for n in names]); T0 = np.array([B[n]['tail_m'] for n in names])
    reg = np.array([body_region(n) for n in names]); par = {n: B[n]['parent'] for n in names}
    rest = {}
    conn = connected_pairs(rec)            # articulating partners (e.g. the two hip bones at the symphysis) are not interactions

    def anc(n, d):
        m = n
        while m is not None:
            if m in d:
                return d[m]
            m = par[m]
        return None
    hits = {}
    for tid, frames in samples.items():
        for fr in frames[::stride]:
            d = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            H, T = H0.copy(), T0.copy(); moved = []
            for n in names:
                D = anc(n, d)
                if D is not None:
                    i = idx[n]; H[i] = D[:3, :3] @ H0[i] + D[:3, 3]; T[i] = D[:3, :3] @ T0[i] + D[:3, 3]; moved.append(i)
            for i in moved:
                dist = seg_dist_many(H[i], T[i], H, T) * 1000
                for j in np.where((dist < LIST_MM) & (reg != reg[i]))[0]:
                    if frozenset((names[i], names[j])) in conn:
                        continue
                    key = (tid, tuple(sorted((names[i], names[j]))))
                    if key not in hits or dist[j] < hits[key]['min_axis_mm']:
                        if key[1] not in rest:
                            a, b = key[1]; rest[key[1]] = float(seg_dist_many(H0[idx[a]], T0[idx[a]], H0[idx[b]][None], T0[idx[b]][None])[0] * 1000)
                        hits[key] = {'test': tid, 'bones': list(key[1]), 'regions': sorted({reg[i], reg[j]}), 'min_axis_mm': round(float(dist[j]), 2),
                                     'frame': fr['frame'], 'rest_axis_mm': round(rest[key[1]], 1)}
    rows = sorted(hits.values(), key=lambda r: r['min_axis_mm'])
    by_test = {}
    for r in rows:
        by_test.setdefault(r['test'], r)
    return {'listed_pairs': len(rows), 'graded_crossings_below_1mm': [r for r in rows if r['min_axis_mm'] < CROSS_MM],
            'tests_with_cross_region_approach_below_10mm': sorted(by_test.values(), key=lambda r: r['min_axis_mm']), 'pairs': rows[:200]}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--stride', type=int, default=2)
    o = ap.parse_args()
    r = scan(json.loads(Path(o.record).read_text()), json.loads(Path(o.samples).read_text()), o.stride)
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'kind': 'INTERACTION_LIST_NOT_GRADED',
                                       'list_threshold_axis_mm': LIST_MM, 'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, **r}, indent=1) + '\n')
    print(o.label, 'pairs', r['listed_pairs'], 'graded crossings', len(r['graded_crossings_below_1mm']))
    for x in r['tests_with_cross_region_approach_below_10mm']:
        print('  ', x['test'], x['bones'], x['min_axis_mm'], 'rest', x['rest_axis_mm'])


if __name__ == '__main__':
    main()
