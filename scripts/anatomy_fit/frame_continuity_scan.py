#!/usr/bin/env python3
"""Joint/bone reference-frame continuity over committed Phase 9 isolated-test samples (read-only; no geometry change).

Per test, over every saved frame:
  1. bookkeeping: frame numbers contiguous (+1), constant time step, every numeric value finite (recursively);
  2. transforms: every recorded world delta is a proper rigid transform (orthonormality residual and |det - 1| both
     <= 1e-5, a float32 bound (Blender matrices are float32); det < 0 would be a reflection / frame sign flip; bottom row (0, 0, 0, 1));
  3. no frame jumps: the rotation of each bone's delta between consecutive frames must not exceed the summed change of the
     commanded ANGULAR channels (a rotation composed of component rotations cannot turn further than the sum of the
     components' changes), plus 1e-3 deg numerics; measured angle channels must not change by more than 90 deg between
     consecutive frames (wrap or sign flip), except plane of elevation where elevation < 1 deg (undefined there);
  4. rest at both ends: first and last frame deltas are identity within 1e-6.
No anatomical tolerance is used; thresholds are numerical-integrity bounds only.

  frame_continuity_scan.py --samples S.json --label NAME --out JSON
"""
import argparse, hashlib, json, math
from pathlib import Path

import numpy as np

NUM = 1e-6
NUM_F32 = 1e-5   # Blender stores float32 matrices; composed products reach ~1e-6 (eps32 = 1.2e-7); bound ~80 x eps32
STEP_SLACK_DEG = 1e-3
NON_ANGULAR_COMMANDS = {'glide'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def finite(x):
    if isinstance(x, dict):
        return all(finite(v) for v in x.values())
    if isinstance(x, list):
        return all(finite(v) for v in x)
    if isinstance(x, (int, float)):
        return math.isfinite(x)
    return True


def rot_angle_deg(R):
    """Rotation angle accurate at small angles: atan2(|skew part|, symmetric part) instead of acos of the trace."""
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    return math.degrees(math.atan2(np.linalg.norm(w) / 2, (np.trace(R) - 1) / 2))


def check_test(frames):
    issues, worst = [], {'orthonormality': 0.0, 'det_error': 0.0, 'step_excess_deg': -1e9, 'max_measured_jump_deg': 0.0, 'rest_end_error': 0.0}
    dt = None
    for i, fr in enumerate(frames):
        if not finite(fr):
            issues.append({'frame': fr['frame'], 'kind': 'non_finite'})
        if i:
            pv = frames[i - 1]
            if fr['frame'] != pv['frame'] + 1:
                issues.append({'frame': fr['frame'], 'kind': 'frame_gap', 'previous': pv['frame']})
            d = fr['time_s'] - pv['time_s']
            if dt is None:
                dt = d
            elif abs(d - dt) > 1e-9:
                issues.append({'frame': fr['frame'], 'kind': 'time_step', 'dt': d, 'expected': dt})
        for b, M in fr['moving_deltas'].items():
            M = np.array(M); R = M[:3, :3]
            o = float(np.abs(R.T @ R - np.eye(3)).max()); de = float(np.linalg.det(R))
            worst['orthonormality'] = max(worst['orthonormality'], o); worst['det_error'] = max(worst['det_error'], abs(de - 1))
            if o > NUM_F32 or abs(de - 1) > NUM_F32 or de < 0 or not np.allclose(M[3], [0, 0, 0, 1]):
                issues.append({'frame': fr['frame'], 'kind': 'improper_transform', 'bone': b, 'orthonormality': o, 'det': de})
        if i:
            pv = frames[i - 1]
            bound = sum(abs(fr['commanded'][k] - pv['commanded'].get(k, 0.0)) for k in fr['commanded'] if k not in NON_ANGULAR_COMMANDS)
            for b, M in fr['moving_deltas'].items():
                if b not in pv['moving_deltas']:
                    continue
                step = rot_angle_deg(np.array(M)[:3, :3] @ np.array(pv['moving_deltas'][b])[:3, :3].T)
                worst['step_excess_deg'] = max(worst['step_excess_deg'], step - bound)
                if step > bound + STEP_SLACK_DEG:
                    issues.append({'frame': fr['frame'], 'kind': 'rotation_jump', 'bone': b, 'step_deg': round(step, 5), 'commanded_bound_deg': round(bound, 5)})
            low_elev = fr.get('elevation', 90.0) < 1.0 or pv.get('elevation', 90.0) < 1.0
            for k, v in fr.items():
                if not isinstance(v, (int, float)) or k in ('frame', 'time_s') or k.endswith('_m') or not isinstance(pv.get(k), (int, float)):
                    continue
                if k in ('plane_of_elevation', 'gh_plane') and low_elev:
                    continue
                jump = abs(v - pv[k])
                worst['max_measured_jump_deg'] = max(worst['max_measured_jump_deg'], jump)
                if jump > 90:
                    issues.append({'frame': fr['frame'], 'kind': 'measured_angle_jump', 'channel': k, 'jump_deg': round(jump, 3)})
    for fr in (frames[0], frames[-1]):
        for b, M in fr['moving_deltas'].items():
            e = float(np.abs(np.array(M) - np.eye(4)).max())
            worst['rest_end_error'] = max(worst['rest_end_error'], e)
            if e > NUM:
                issues.append({'frame': fr['frame'], 'kind': 'not_at_rest', 'bone': b, 'error': e})
    return issues, worst


def scan(samples):
    tests, summary = {}, {'issues_by_kind': {}}
    for tid, frames in samples.items():
        iss, w = check_test(frames)
        tests[tid] = {'frames': len(frames), 'issues': iss[:20], 'issue_count': len(iss),
                      'worst': {k: (round(v, 9) if k != 'step_excess_deg' else round(v, 6)) for k, v in w.items()}}
        for x in iss:
            summary['issues_by_kind'][x['kind']] = summary['issues_by_kind'].get(x['kind'], 0) + 1
    summary['tests'] = len(tests); summary['frames'] = sum(t['frames'] for t in tests.values())
    summary['tests_with_issues'] = sorted(t for t, v in tests.items() if v['issue_count'])
    summary['global_worst'] = {k: max(t['worst'][k] for t in tests.values()) for k in ('orthonormality', 'det_error', 'step_excess_deg', 'max_measured_jump_deg', 'rest_end_error')}
    return summary, tests


def main():
    ap = argparse.ArgumentParser()
    for a in ('--samples', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    summary, tests = scan(json.loads(Path(o.samples).read_text()))
    Path(o.out).write_text(json.dumps({'schema_version': 1, 'created': '2026-10-09', 'label': o.label, 'status': 'MECHANICAL_SCAN_NO_GEOMETRY_CHANGE',
                                       'bounds': {'numeric': NUM, 'float32_transform': NUM_F32, 'step_slack_deg': STEP_SLACK_DEG, 'measured_jump_deg': 90, 'non_angular_commands': sorted(NON_ANGULAR_COMMANDS)},
                                       'inputs_sha256': {o.samples: sha(o.samples)}, 'summary': summary, 'tests': tests}, indent=1) + '\n')
    print(o.label, json.dumps(summary)[:1500])


if __name__ == '__main__':
    main()
