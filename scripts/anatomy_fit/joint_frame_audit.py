#!/usr/bin/env python3
"""Joint reference-frame audit at rest and through every committed Phase 9 sweep (read-only; no geometry change).

A. Rest (all joint markers): frame_axes_columns_XYZ finite, orthonormal (<= 1e-9) and right-handed (det +1). Bilateral
   pairs: a reflected frame is left-handed, so the left frame is reflected (M A_l, M = diag(-1,1,1)) and one axis sign is
   flipped to restore handedness; the flip (X, Y or Z) giving the smallest residual is the pair's mirror convention, and
   that residual angle is the INHERITED REST ASYMMETRY. Conventions are reported per joint family.
B. Motion (every articulation with a marker, every saved frame of the 135 sweeps): the joint frame is carried by its frame
   bone (world W = R_F A). Checked per frame: W orthonormal / right-handed (float32 bound 1e-5); the frame stays rigid to
   its frame bone (by definition of the rig; a check of the recorded deltas). For tests with a single non-zero commanded
   channel: the child-relative-to-parent rotation axis expressed in the joint frame (parent-carried) is tracked over frames
   with |angle| > 0.5 deg: AXIS DRIFT = max angle from its mean; SIGN = the rotation about the mean axis has one sign per
   sign of the command (no flips); the joint-frame axis it follows (X/Y/Z) and the alignment angle are reported, not graded
   (oblique axes exist by design).

  joint_frame_audit.py --record R.json --samples S.json --label NAME --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_attachment_scan as ja  # noqa: E402

M3 = np.diag([-1.0, 1.0, 1.0])
REST_TOL, F32 = 1e-9, 1e-5
MIN_ANGLE = 0.5


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def axes(m):
    return np.array(m['frame_axes_columns_XYZ'], float)          # columns X, Y, Z as stored (rows of the stored list are matrix rows)


def ang(u, v):
    return math.degrees(math.atan2(np.linalg.norm(np.cross(u, v)), float(np.dot(u, v))))


def axis_angle(R):
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    s = np.linalg.norm(w) / 2; c = (np.trace(R) - 1) / 2
    a = math.degrees(math.atan2(s, c))
    return (w / (2 * s) if s > 1e-12 else np.zeros(3)), a


def rest_audit(rec):
    J = rec['joint_markers']; bad, pairs, fam = [], {}, {}
    for k, m in J.items():
        A = axes(m)
        if not np.all(np.isfinite(A)):
            bad.append({'marker': k, 'kind': 'non_finite'}); continue
        o = float(np.abs(A.T @ A - np.eye(3)).max()); d = float(np.linalg.det(A))
        if o > REST_TOL or abs(d - 1) > REST_TOL:
            bad.append({'marker': k, 'kind': 'improper_rest_frame', 'orthonormality': o, 'det': d})
    for k in J:
        if not k.endswith('_left') or k[:-5] + '_right' not in J:
            continue
        Al, Ar = axes(J[k]), axes(J[k[:-5] + '_right'])
        best = None
        for i, lab in enumerate('XYZ'):
            S = np.eye(3); S[i, i] = -1
            res = math.degrees(math.acos(max(-1, min(1, (np.trace((M3 @ Al @ S).T @ Ar) - 1) / 2))))
            if best is None or res < best[1]:
                best = (lab, res)
        pairs[k[:-5]] = {'flip_axis': best[0], 'residual_deg': round(best[1], 6)}
        f = k.rsplit('_', 1)[0].rstrip('0123456789_').split('_')[0]
        fam.setdefault(f, set()).add(best[0])
    return {'markers': len(J), 'improper': bad, 'bilateral_pairs': len(pairs),
            'mirror_flip_by_family': {f: sorted(v) for f, v in sorted(fam.items())},
            'families_with_mixed_flip': sorted(f for f, v in fam.items() if len(v) > 1),
            'max_rest_asymmetry_deg': max(p['residual_deg'] for p in pairs.values()),
            'rest_asymmetry_top': sorted(({'joint': k, **v} for k, v in pairs.items()), key=lambda x: -x['residual_deg'])[:12],
            'pairs': pairs}


def motion_audit(rec, samples):
    B, J = rec['bones'], rec['joint_markers']
    parent = {n: B[n]['parent'] for n in B}
    arts = [a for a in ja.articulations() if a['id'] in J and len(a['participants']) == 2 and all(p in B for p in a['participants'])]

    def anc(n, deltas):
        m = n
        while m is not None:
            if m in deltas:
                return deltas[m]
            m = parent[m]
        return np.eye(4)
    worst_f32, frame_issues, tests = 0.0, [], {}
    for tid, frames in samples.items():
        chans = {k for fr in frames for k, v in fr['commanded'].items() if abs(v) > 1e-9}
        single = len(chans) == 1
        ch = next(iter(chans)) if single else None
        track = {}
        for fr in frames:
            deltas = {k: np.array(v) for k, v in fr['moving_deltas'].items()}
            for a in arts:
                F = J[a['id']]['frame_bone']
                RF = anc(F, deltas)[:3, :3] if F in B else np.eye(3)
                W = RF @ axes(J[a['id']])
                o = float(np.abs(W.T @ W - np.eye(3)).max()); dt = float(np.linalg.det(W))
                worst_f32 = max(worst_f32, o, abs(dt - 1))
                if o > F32 or abs(dt - 1) > F32:
                    frame_issues.append({'test': tid, 'frame': fr['frame'], 'joint': a['id'], 'orthonormality': o, 'det': dt})
                if not single:
                    continue
                p, c = a['participants']
                # orient parent/child by the bone tree when possible
                if parent.get(p) == c:
                    p, c = c, p
                Rp, Rc = anc(p, deltas)[:3, :3], anc(c, deltas)[:3, :3]
                rel = Rc @ Rp.T
                u, deg = axis_angle(rel)
                if deg < MIN_ANGLE:
                    continue
                A_par = Rp @ axes(J[a['id']])                 # joint frame carried by the parent
                cmd = fr['commanded'][ch]
                track.setdefault(a['id'], []).append((A_par.T @ u * math.copysign(1, cmd), deg, cmd))
        res = {}
        for j, rows in track.items():
            V = np.array([r[0] for r in rows]); mean = V.mean(0)
            if np.linalg.norm(mean) < 1e-9:
                res[j] = {'frames': len(rows), 'sign_flip': True}; continue
            mean /= np.linalg.norm(mean)
            drift = max(ang(v, mean) for v in V)
            flips = sum(1 for v in V if np.dot(v, mean) < 0)
            k = int(np.argmax(np.abs(mean)))
            res[j] = {'frames': len(rows), 'axis_drift_deg': round(drift, 6), 'sign_flip_frames': flips,
                      'follows_joint_axis': 'XYZ'[k] + ('+' if mean[k] > 0 else '-'), 'alignment_deg': round(ang(np.abs(mean), np.eye(3)[k]), 4)}
        tests[tid] = {'single_channel': ch, 'joints_moving': res}
    return {'frame_bound': F32, 'worst_orthonormality_or_det': worst_f32, 'frame_issues': frame_issues[:50], 'frame_issue_count': len(frame_issues),
            'single_channel_tests': sum(1 for t in tests.values() if t['single_channel']),
            'max_axis_drift_deg': max((r['axis_drift_deg'] for t in tests.values() for r in t['joints_moving'].values() if 'axis_drift_deg' in r), default=0.0),
            'sign_flip_total': sum(r.get('sign_flip_frames', 0) + (1 if r.get('sign_flip') is True else 0) for t in tests.values() for r in t['joints_moving'].values()),
            'tests': tests}


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    rec = json.loads(Path(o.record).read_text())
    rest = rest_audit(rec); mot = motion_audit(rec, json.loads(Path(o.samples).read_text()))
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_AUDIT_NO_GEOMETRY_CHANGE',
                                       'inputs_sha256': {o.record: sha(o.record), o.samples: sha(o.samples)}, 'rest': rest, 'motion': mot}, indent=1) + '\n')
    print(o.label, 'REST', {k: rest[k] for k in ('markers', 'bilateral_pairs', 'families_with_mixed_flip', 'max_rest_asymmetry_deg')}, 'improper', len(rest['improper']))
    print('  top asym', rest['rest_asymmetry_top'][:5])
    print('MOTION', {k: mot[k] for k in ('worst_orthonormality_or_det', 'frame_issue_count', 'single_channel_tests', 'max_axis_drift_deg', 'sign_flip_total')})


if __name__ == '__main__':
    main()
