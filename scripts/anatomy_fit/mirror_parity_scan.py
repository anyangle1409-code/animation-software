#!/usr/bin/env python3
"""Left-right mirror parity of EVERY moved bone (commanded, follower and carried descendants) over committed Phase 9
isolated-test samples (read-only; no geometry change).

For each bilateral test pair X_left / X_right whose command series match (isolated_tests.commands_match; genuinely
side-specific source amplitudes are skipped and listed), at every frame:
  * transforms: each bone's world delta (nearest commanded ancestor rule) on the left, reflected (M D M, M = diag(-1,1,1,1)),
    against its partner on the right (midline bones against themselves); rotation Frobenius and translation differences;
  * displacements: rest-to-frame displacement of both bone ends, mirrored, left vs right (displacement, not absolute
    position, so the inherited a003 rest asymmetry of about 0.04 mm is not counted as motion asymmetry);
  * joint centres: for every sided articulation, each participant's displaced joint-centre copy, mirrored, left vs right;
  * attachment: the joint opening (max separation of participant copies) left vs right.
Implementation-integrity bounds only (no anatomical tolerance): transform 1e-5 (float32 matrices), positions 1e-5 m.

  mirror_parity_scan.py --record R.json --samples S.json --label NAME --out JSON
"""
import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isolated_tests as it  # noqa: E402
import joint_attachment_scan as ja  # noqa: E402

MX = np.diag([-1.0, 1.0, 1.0, 1.0])
BOUND_T, BOUND_P = 1e-5, 1e-5


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def partner(n):
    return n[:-5] + '_right' if n.endswith('_left') else (n[:-6] + '_left' if n.endswith('_right') else n)


def scan(rec, samples):
    B, J = rec['bones'], rec['joint_markers']
    parent = {n: B[n]['parent'] for n in B}
    arts = [a for a in ja.articulations() if a['id'] in J and a['id'].endswith('_left') and partner(a['id']) in J
            and all(p in B for p in a['participants'])]

    def anc(n, deltas):
        m = n
        while m is not None:
            if m in deltas:
                return deltas[m]
            m = parent[m]
        return np.eye(4)
    rest_asym = {n: max(float(np.linalg.norm(np.array(B[n][e]) * [-1, 1, 1] - np.array(B[partner(n)][e]))) for e in ('head_m', 'tail_m'))
                 for n in B if n.endswith('_left') and partner(n) in B}
    pairs, skipped = {}, []
    for tid in sorted(samples):
        if not tid.endswith('_left') or tid[:-5] + '_right' not in samples:
            continue
        L, R = samples[tid], samples[tid[:-5] + '_right']
        if len(L) != len(R) or not it.commands_match([x['commanded'] for x in L], [x['commanded'] for x in R]):
            skipped.append(tid[:-5]); continue
        w = {'transform': 0.0, 'displacement_m': 0.0, 'joint_centre_m': 0.0, 'opening_m': 0.0, 'bones_compared': 0,
             'unexplained_displacement_m': 0.0}
        worst_bone, worst_disp_bone = None, None
        for fl, fr in zip(L, R):
            dl = {k: np.array(v) for k, v in fl['moving_deltas'].items()}
            dr = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            moved = {n for n in B if anc(n, dl) is not None and not np.allclose(anc(n, dl), np.eye(4))} | \
                    {partner(n) for n in B if not np.allclose(anc(n, dr), np.eye(4))}
            moved = {n for n in moved if n.endswith('_left') or not n.endswith('_right')}
            w['bones_compared'] = max(w['bones_compared'], len(moved))
            for n in moved:
                p = partner(n)
                Dl, Dr = anc(n, dl), anc(p, dr)
                t = float(np.abs(MX @ Dl @ MX - Dr).max())
                if t > w['transform']:
                    w['transform'] = t; worst_bone = n
                for e in ('head_m', 'tail_m'):
                    pl, pr = np.array(B[n][e]), np.array(B[p][e])
                    disp_l = Dl[:3, :3] @ pl + Dl[:3, 3] - pl; disp_r = Dr[:3, :3] @ pr + Dr[:3, 3] - pr
                    mis = float(np.linalg.norm(disp_l * [-1, 1, 1] - disp_r))
                    if mis > w['displacement_m']:
                        w['displacement_m'] = mis; worst_disp_bone = n
                    # a rotation amplifies a rest offset by at most |R - I| <= 2: anything beyond is motion asymmetry
                    w['unexplained_displacement_m'] = max(w['unexplained_displacement_m'], mis - 2 * rest_asym.get(n, 0.0))
            for a in arts:
                ar = partner(a['id'])
                cl, cr = np.array(J[a['id']]['centre_m']), np.array(J[ar]['centre_m'])
                copies_l = [anc(q, dl)[:3, :3] @ cl + anc(q, dl)[:3, 3] - cl for q in a['participants']]
                copies_r = [anc(partner(q), dr)[:3, :3] @ cr + anc(partner(q), dr)[:3, 3] - cr for q in a['participants']]
                for xl, xr in zip(copies_l, copies_r):
                    w['joint_centre_m'] = max(w['joint_centre_m'], float(np.linalg.norm(xl * [-1, 1, 1] - xr)))
                op = lambda cs: max(float(np.linalg.norm(cs[i] - cs[j])) for i in range(len(cs)) for j in range(i + 1, len(cs)))
                w['opening_m'] = max(w['opening_m'], abs(op(copies_l) - op(copies_r)))
        if w['transform'] <= BOUND_T and max(w['displacement_m'], w['joint_centre_m'], w['opening_m']) <= BOUND_P:
            status = 'PASS'
        elif w['transform'] <= BOUND_T and w['opening_m'] <= BOUND_P and w['unexplained_displacement_m'] <= BOUND_P:
            status = 'REST_ASYMMETRY_ONLY'          # motion mirrors exactly; inherited rest-geometry asymmetry rotates with it
        else:
            status = 'FAIL'
        pairs[tid[:-5]] = {**{k: (float(f'{v:.3g}') if isinstance(v, float) else v) for k, v in w.items()}, 'worst_transform_bone': worst_bone,
                           'worst_displacement_bone': worst_disp_bone, 'status': status}
    return {'pairs_compared': len(pairs), 'pairs_failed': sorted(k for k, v in pairs.items() if v['status'] == 'FAIL'),
            'pairs_rest_asymmetry_only': sorted(k for k, v in pairs.items() if v['status'] == 'REST_ASYMMETRY_ONLY'),
            'rest_asymmetric_bones_mm': {k: round(v * 1000, 4) for k, v in sorted(rest_asym.items(), key=lambda kv: -kv[1]) if v > 1e-6},
            'side_specific_skipped': skipped, 'sided_articulations': len(arts),
            'global_max': {k: max(v[k] for v in pairs.values()) for k in ('transform', 'displacement_m', 'joint_centre_m', 'opening_m')},
            'pairs': pairs}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    r = scan(json.loads(Path(o.record).read_text()), json.loads(Path(o.samples).read_text()))
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_SCAN_NO_GEOMETRY_CHANGE',
                                       'bounds': {'transform': BOUND_T, 'position_m': BOUND_P},
                                       'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, **r}, indent=1) + '\n')
    print(o.label, {k: r[k] for k in ('pairs_compared', 'pairs_failed', 'pairs_rest_asymmetry_only', 'side_specific_skipped', 'global_max')})
    print({k: v['worst_displacement_bone'] for k, v in r['pairs'].items() if v['status'] != 'PASS'})


if __name__ == '__main__':
    main()
