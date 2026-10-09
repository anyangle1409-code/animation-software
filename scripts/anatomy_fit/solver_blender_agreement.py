#!/usr/bin/env python3
"""Solver <-> Blender agreement over committed Phase 9 isolated runs (read-only; pure Python; no geometry change).

The runner keyframes, per frame, a pose basis derived from the pure-Python solver (isolated_tests.deltas) and records the
Blender-EVALUATED world deltas of every commanded bone (depsgraph: keyframe evaluation, quaternion decomposition, parent
composition) plus the measured clinical angles. This audit recomputes both from the CURRENT repository code and the record:
  A. series: the committed commanded series equals isolated_tests.series(spec) for every test (spec drift since the run);
  B. evaluation: every recorded delta equals the solver delta composed through its commanded ancestors (D_b = prod G_a * G_b);
     the uncomposed reading (D_b = G_b) is reported too, to show the check is not tautological;
  C. measurement: isolated_tests.measure re-run on the reconstructed pose reproduces every recorded numeric channel.
     Rest matrices are rebuilt from the record (translation = head, Y column = unit(tail - head), the only rest quantity
     measure() reads besides D = pose * rest^-1). plane_of_elevation / gh_plane are skipped where elevation < 1 deg
     (undefined there; the runner's own rule).
Bounds are numerical only: transforms 1e-5 (float32); angles degrees(3 * 1e-5) = 1.7e-3 deg (rotation-angle error of a
matrix perturbation with max entry eps is at most its Frobenius norm <= 3 eps); lengths 1e-5 m.

  solver_blender_agreement.py --record R.json --samples S.json --label NAME --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import isolated_tests as it  # noqa: E402

ROOT = HERE.parents[1]
T_BOUND, M_BOUND = 1e-5, 1e-5
A_BOUND = math.degrees(3 * T_BOUND)
UNDEFINED_AT_ZERO_ELEVATION = ('plane_of_elevation', 'gh_plane')
SKIP = {'frame', 'time_s', 'commanded', 'moving_deltas', 'moving_delta'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rest_matrices(rec):
    out = {}
    for n, b in rec['bones'].items():
        h, t = np.asarray(b['head_m'], float), np.asarray(b['tail_m'], float)
        y = (t - h) / np.linalg.norm(t - h)
        a = np.eye(3)[int(np.argmin(np.abs(y)))]
        x = np.cross(y, a); x /= np.linalg.norm(x); z = np.cross(x, y)
        M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, h
        out[n] = M
    return out


def composed(G, b, parent):
    C = G.get(b, np.eye(4)); a = parent[b]
    while a is not None:
        if a in G:
            C = G[a] @ C
        a = parent[a]
    return C


def bound_for(key):
    return M_BOUND if key.endswith('_m') else A_BOUND


def audit(rec, atlas, samples):
    F = it.frames(rec); specs = {t['id']: t for t in it.specs(rec, atlas)}
    B = rec['bones']; parent = {n: B[n]['parent'] for n in B}; rest = rest_matrices(rec)
    out = {'tests_in_samples': len(samples), 'tests_in_current_specs': len(specs),
           'missing_from_current_specs': sorted(set(samples) - set(specs)), 'not_in_samples': sorted(set(specs) - set(samples))}
    series_drift, eval_fail, meas_fail = [], [], []
    worst = {'composed': 0.0, 'uncomposed': 0.0, 'channels': {}}
    frames_n = deltas_n = channels_n = 0
    for tid in sorted(set(samples) & set(specs)):
        t, frames = specs[tid], samples[tid]
        ser = it.series(t)
        if len(ser) != len(frames) or not it.commands_match(ser, [f['commanded'] for f in frames]):
            series_drift.append(tid)
        for fr in frames:
            frames_n += 1
            G = it.deltas(t, fr['commanded'], F)
            pose = {}
            for b in B:
                C = composed(G, b, parent)
                pose[b] = C @ rest[b]
            for b, M in fr['moving_deltas'].items():
                deltas_n += 1
                M = np.asarray(M); C = composed(G, b, parent)
                ec, eu = float(np.abs(M - C).max()), float(np.abs(M - G.get(b, np.eye(4))).max())
                worst['composed'] = max(worst['composed'], ec); worst['uncomposed'] = max(worst['uncomposed'], eu)
                if ec > T_BOUND:
                    eval_fail.append({'test': tid, 'frame': fr['frame'], 'bone': b, 'max_abs': ec})
            mk = {}
            for k, nm in (('marker_m', t.get('marker')), ('distal_marker_m', t.get('distal_marker'))):
                if nm and fr.get(k) is not None:
                    mk[nm] = fr[k]
            m = it.measure(t, pose, rest, F, mk)
            low = fr.get('elevation', fr.get('humerothoracic_elevation', 90.0)) < 1.0
            for k, v in fr.items():
                if k in SKIP or k not in m or isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                if k in UNDEFINED_AT_ZERO_ELEVATION and low:
                    continue
                channels_n += 1
                d = abs(float(m[k]) - float(v))
                if d > worst['channels'].get(k, 0.0):
                    worst['channels'][k] = d
                if d > bound_for(k):
                    meas_fail.append({'test': tid, 'frame': fr['frame'], 'channel': k, 'recorded': v, 'recomputed': m[k], 'abs_diff': d})
    out.update({'frames': frames_n, 'deltas_compared': deltas_n, 'channels_compared': channels_n,
                'bounds': {'transform': T_BOUND, 'angle_deg': A_BOUND, 'length_m': M_BOUND},
                'series_drift_tests': series_drift,
                'evaluation_failures': eval_fail[:50], 'evaluation_failure_count': len(eval_fail),
                'measurement_failures': meas_fail[:50], 'measurement_failure_count': len(meas_fail),
                'worst_composed_delta': worst['composed'], 'worst_uncomposed_delta_info': worst['uncomposed'],
                'worst_channel_diff': {k: float(f'{v:.3g}') for k, v in sorted(worst['channels'].items(), key=lambda kv: -kv[1])}})
    out['status'] = 'AGREE' if not (series_drift or eval_fail or meas_fail or out['missing_from_current_specs']) else 'DISAGREE'
    return out


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    atlas_p = ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json'
    r = audit(json.loads(Path(o.record).read_text()), json.loads(atlas_p.read_text()), json.loads(Path(o.samples).read_text()))
    src = {p: sha(p) for p in (o.record, o.samples, str(atlas_p.relative_to(ROOT)), 'scripts/anatomy_fit/isolated_tests.py', 'scripts/anatomy_fit/joint_solver.py')}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'kind': 'MECHANICAL_CROSS_IMPLEMENTATION_CHECK_NO_GEOMETRY_CHANGE',
                                       'inputs_sha256': src, **r}, indent=1) + '\n')
    print(o.label, {k: r[k] for k in ('status', 'tests_in_samples', 'frames', 'deltas_compared', 'channels_compared', 'series_drift_tests',
                                       'evaluation_failure_count', 'measurement_failure_count', 'worst_composed_delta', 'worst_uncomposed_delta_info')})
    print(' worst channels', dict(list(r['worst_channel_diff'].items())[:6]))
    for x in r['measurement_failures'][:10]:
        print('  MEAS', x)


if __name__ == '__main__':
    main()
