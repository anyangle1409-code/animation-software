#!/usr/bin/env python3
"""Rib-sternum coupling for the pump-handle breathing component (pure numpy/scipy; no bpy).

Closes the Phase 9 gap "rib-sternum coupling untested" with no new magnitude: ribs 1-7 take a pump-handle rotation
about the mediolateral axis through the rib head (the project convention, F-RIB-001) with the anterior end rising for
inspiration; ribs 8-10 follow the rib above through the interchondral joints; the sternum then takes the rigid
sagittal-plane motion (anteroposterior and vertical translation plus tilt about the mediolateral axis through IJ) that
least deforms the fourteen costal cartilages (costochondral -> sternocostal vectors). The sternal motion is SOLVED, not
chosen; its direction is reported and checked against the textbook pump-handle description (sternum rises and moves
anteriorly in inspiration), not imposed.

Amplitude: the isolated rib tests' TEST AMPLITUDE (Beyer 2014 smallest level mean of the two major components, FRC-TLC).
Not modelled: rib bucket-handle/long-axis components, costal cartilage elasticity, the shoulder girdle's response
(the clavicles are carried by the sternum in the Blender illustration), lung volume.
"""
import json, math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
SUPPLEMENT = ROOT / 'ORIGINAL_V1_WORK/anatomy/phase9_supplementary_observations.json'
LAT = np.array([1.0, 0.0, 0.0])


def amplitude():
    v = json.loads(SUPPLEMENT.read_text())['observations']['rib_cvj_range']['value']
    return min(v['dominant_axis_range_of_level_means'][0], v['second_axis_range_of_level_means'][0])


def rodrigues(axis, deg):
    a = np.asarray(axis, float) / np.linalg.norm(axis); t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def rigid(R, c, t=np.zeros(3)):
    """Map p -> c + R (p - c) + t, as (R, offset) with p' = R p + offset."""
    return R, np.asarray(c, float) - R @ np.asarray(c, float) + t


def apply(T, p):
    return T[0] @ np.asarray(p, float) + T[1]


def mm(v):
    return np.asarray(v, float) * 1000


def inspiration_sign(rec, side, n):
    """+1 if a positive rotation about +X through the head raises the anterior end (as isolated_tests.py)."""
    cv = mm(rec['joint_markers'][f'costovertebral_{n:02d}_{side}']['centre_m']); tip = mm(rec['bones'][f'rib_{n:02d}_{side}']['tail_m'])
    return 1.0 if ((rodrigues(LAT, 5.0) @ (tip - cv)) - (tip - cv))[2] > 0 else -1.0


def coupled_pose(rec, theta_deg):
    """World rigid transforms (mm) for ribs 1-10 and the sternum at inspiration angle theta (deg) + metrics."""
    J, B = rec['joint_markers'], rec['bones']
    T = {}
    for side in ('left', 'right'):
        for n in range(1, 8):
            cv = mm(J[f'costovertebral_{n:02d}_{side}']['centre_m'])
            T[f'rib_{n:02d}_{side}'] = rigid(rodrigues(LAT, inspiration_sign(rec, side, n) * theta_deg), cv)
        for n in (8, 9, 10):                                           # false ribs follow the rib above (interchondral)
            cv = mm(J[f'costovertebral_{n:02d}_{side}']['centre_m'])
            link = f'interchondral_{n - 1}_{n}_{side}'
            ic1 = apply(T[f'rib_{n - 1:02d}_{side}'], mm(J[link]['centre_m']))
            cc0 = mm(J[f'costochondral_{n:02d}_{side}']['centre_m'])
            v0 = mm(J[link]['centre_m']) - cc0
            f = lambda t: np.linalg.norm((ic1 - apply(rigid(rodrigues(LAT, t[0]), cv), cc0)) - v0)
            t = least_squares(lambda t: [f(t)], [0.0]).x[0]
            T[f'rib_{n:02d}_{side}'] = rigid(rodrigues(LAT, t), cv)
    ij = mm(rec['skeleton_input']['trunk']['ij_bone'])
    pairs = []
    for side in ('left', 'right'):
        for n in range(1, 8):
            cc0 = mm(J[f'costochondral_{n:02d}_{side}']['centre_m']); sc0 = mm(J[f'sternocostal_{n:02d}_{side}']['centre_m'])
            pairs.append((sc0, apply(T[f'rib_{n:02d}_{side}'], cc0), sc0 - cc0))

    def sternum_T(x):
        return rigid(rodrigues(LAT, x[2]), ij, np.array([0.0, x[0], x[1]]))

    def res(x):
        S = sternum_T(x)
        return np.concatenate([(apply(S, sc0) - cc1) - v0 for sc0, cc1, v0 in pairs])
    fit = least_squares(res, [0.0, 0.0, 0.0])
    T['sternum'] = sternum_T(fit.x)
    r = res(fit.x).reshape(-1, 3); r0 = res(np.zeros(3)).reshape(-1, 3)
    metrics = {'theta_deg': theta_deg, 'sternum_dy_mm': float(fit.x[0]), 'sternum_dz_mm': float(fit.x[1]), 'sternum_tilt_deg': float(fit.x[2]),
               'cartilage_change_max_mm': float(np.linalg.norm(r, axis=1).max()),
               'cartilage_change_max_if_sternum_fixed_mm': float(np.linalg.norm(r0, axis=1).max()),
               'false_rib_angles_deg': {k: round(math.degrees(math.atan2(v[0][2, 1], v[0][1, 1])), 4) for k, v in T.items() if k[4:6] in ('08', '09', '10')}}
    return T, metrics


def series(theta, n=9):
    """0 -> theta -> 0 with cosine easing; n keys per leg."""
    up = [theta * (1 - math.cos(math.pi * i / (n - 1))) / 2 for i in range(n)]
    return up + up[-2::-1]


if __name__ == '__main__':
    import sys
    rec = json.loads(Path(sys.argv[1]).read_text())
    _, m = coupled_pose(rec, amplitude())
    print(json.dumps(m, indent=1))
