#!/usr/bin/env python3
"""P007: best-fit sternum rigid 6-DOF transformation, READ ONLY.

Fit a single rotation and translation to c004's 14 sternocostal control
marker centres so they approximately follow P004's 14 rigidly translated
rib tails. This checks whether sternum ROTATION could reduce the P006 pure
translation residual. It is an unconstrained geometric Procrustes fit, NOT
physiologically attainable or an anatomical/clinical sternum pose.

Implements Horn's unit-quaternion least-squares absolute orientation with
a deterministic symmetric Jacobi eigensolver in Python stdlib: no NumPy,
Blender, ML model, external geometry tool or network is needed.

No output is a production skeleton, cartilage model, bone surface or
canonical acceptance. The objective preserves control-marker vectors,
which are NOT source-verified costal-cartilage insertion landmarks.
"""
import argparse
import json
import math
from pathlib import Path

import p006_sternocostal_translation_feasibility as p6


def _add(a, b):
    return [x+y for x, y in zip(a,b)]


def _sub(a, b):
    return [x-y for x, y in zip(a,b)]


def _dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def _norm(v):
    return math.sqrt(_dot(v,v))


def _mean(points):
    return [sum(v[k] for v in points)/len(points) for k in range(3)]


def _matvec(M, v):
    return [sum(a*b for a,b in zip(row, v)) for row in M]


def _jacobi_top_eigenvector_4x4(sym):
    """Max eigenpair of symmetric 4x4 via plane rotations, no power-iteration traps."""
    A = [list(row) for row in sym]
    V = [[float(i == j) for j in range(4)] for i in range(4)]
    for _ in range(120):
        p, q = max(((i,j) for i in range(4) for j in range(i+1,4)),
                   key=lambda ij: abs(A[ij[0]][ij[1]]))
        if abs(A[p][q]) < 1e-14:
            break
        theta = .5*math.atan2(2*A[p][q], A[q][q]-A[p][p])
        cc, ss = math.cos(theta), math.sin(theta)
        # U columns p,q = (c,-s), (s,c) convention based on chosen
        # theta. Use explicit stable Jacobi updates preserving symmetry.
        app, aqq, apq = A[p][p], A[q][q], A[p][q]
        A[p][p] = cc*cc*app - 2*ss*cc*apq + ss*ss*aqq
        A[q][q] = ss*ss*app + 2*ss*cc*apq + cc*cc*aqq
        A[p][q] = A[q][p] = 0.0
        for k in range(4):
            if k == p or k == q:
                continue
            akp, akq = A[k][p], A[k][q]
            A[k][p] = A[p][k] = cc*akp - ss*akq
            A[k][q] = A[q][k] = ss*akp + cc*akq
        for k in range(4):
            vkp, vkq = V[k][p], V[k][q]
            V[k][p] = cc*vkp - ss*vkq
            V[k][q] = ss*vkp + cc*vkq
    else:
        raise ValueError('symmetric eigensolver did not converge')
    best = max(range(4), key=lambda i: A[i][i])
    raw = [V[k][best] for k in range(4)]
    length = _norm(raw)
    if length < 1e-12:
        raise ValueError('degenerate quaternion eigenvector')
    return [v/length for v in raw], A[best][best]


def _quat_rotation(q):
    w, x, y, z = q
    return [
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ]


def rigid_fit(source_points, target_points):
    if len(source_points) != len(target_points) or len(source_points) < 3:
        raise ValueError('matching triples of control points are required')
    if any(len(v) != 3 or not all(math.isfinite(c) for c in v)
           for v in source_points+target_points):
        raise ValueError('all control coordinates must be finite triples')
    pbar, qbar = _mean(source_points), _mean(target_points)
    p = [_sub(v, pbar) for v in source_points]
    q = [_sub(v, qbar) for v in target_points]
    # Row=source axis, column=target axis, S_{jk}=sum p_j q_k.
    S = [[sum(u[i]*v[j] for u, v in zip(p, q))
          for j in range(3)] for i in range(3)]
    x,y,z = 0,1,2
    xx,xy,xz = S[x]
    yx,yy,yz = S[y]
    zx,zy,zz = S[z]
    N = [
        [xx+yy+zz, yz-zy, zx-xz, xy-yx],
        [yz-zy, xx-yy-zz, xy+yx, zx+xz],
        [zx-xz, xy+yx, -xx+yy-zz, yz+zy],
        [xy-yx, zx+xz, yz+zy, -xx-yy+zz],
    ]
    quat, eig = _jacobi_top_eigenvector_4x4(N)
    R = _quat_rotation(quat)
    t = _sub(qbar, _matvec(R, pbar))
    residuals = [_norm(_sub(_add(_matvec(R, src), t), tgt))
                 for src, tgt in zip(source_points, target_points)]
    return {'rotation': R, 'quaternion_wxyz': quat, 'world_translation_m': t,
            'angle_deg': math.degrees(2*math.acos(min(1.0, abs(quat[0])))),
            'residuals_m': residuals, 'fit_eigenvalue': eig}


def audit(baseline, proposed):
    # First demand the explicit assumptions of P006 hold, preventing
    # disjoint markers being silently re-fitted.
    previous = p6.audit(baseline, proposed)
    src, dst, ids = [], [], []
    for index in range(1,8):
        for side in ('left','right'):
            jid = f'sternocostal_{index:02d}_{side}'
            rid = f'rib_{index:02d}_{side}'
            original_marker = baseline['joint_markers'][jid]['centre_m']
            old_tail = baseline['bones'][rid]['tail_m']
            new_tail = proposed['bones'][rid]['tail_m']
            rib_shift = _sub(new_tail, old_tail)
            src.append(original_marker)
            dst.append(_add(original_marker, rib_shift))
            ids.append(jid)
    fit = rigid_fit(src, dst)
    residuals_mm = [1000*x for x in fit['residuals_m']]
    return {
        'schema_version': 1,
        'kind': 'P007_FREE_STERNUM_ROTATION_TRANSLATION_GEOMETRIC_FIT',
        'status': 'NUMERICAL_FIT_ONLY_ANATOMY_UNVERIFIED',
        'number_of_sternocostal_marker_controls': len(ids),
        'control_marker_ids': ids,
        'best_fit_rotation_angle_deg': round(fit['angle_deg'], 6),
        'best_fit_world_translation_m': [round(v, 9) for v in fit['world_translation_m']],
        'best_fit_rotation_matrix': [[round(x, 9) for x in row] for row in fit['rotation']],
        'max_3d_proxy_vector_residual_mm': round(max(residuals_mm), 6),
        'rms_3d_proxy_vector_residual_mm':
            round(math.sqrt(sum(v*v for v in residuals_mm)/len(residuals_mm)), 6),
        'individual_sternocostal_marker_residual_mm':
            {k: round(v, 6) for k, v in zip(ids, residuals_mm)},
        'comparison_previous_sternum_pure_translation_max_mm':
            previous['actual_worst_vector_change_mm'],
        'comparison_optimal_pure_translation_l2_max_mm':
            previous['ls_worst_vector_change_mm'],
        'comparison_unavoidable_pure_translation_max_lower_bound_mm':
            previous['unavoidable_max_residual_lower_bound_for_translation_mm'],
        'marker_residual_over_5mm_engineering_review':
            {k: round(v,6) for k,v in zip(ids,residuals_mm) if v > 5},
        'free_rotation_has_no_source_based_range_of_motion': True,
        'sternum_joint_kinematics_verified': False,
        'sternum_surface_pose_verified': False,
        'sc_ap_gh_chain_after_rotation_verified': False,
        'costal_cartilage_mechanics_modelled': False,
        'canonical_promotion_allowed': False,
        'not_a_candidate_record': True,
        'unverified': [
            'Actual sternum/manubrium/xiphoid geometry and joint constraints',
            'The 14 recorded control markers are not 3D cartilage insertion surfaces',
            'Rotation must not break SC/AC/GH/clavicle and scapulothoracic contacts',
            'Sourced physiological sternum orientation, breathing and load',
            'Whole-body muscle/skin deformation and exercise clearance'
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--proposal', type=Path, required=True)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    result = audit(json.loads(a.baseline.read_text()), json.loads(a.proposal.read_text()))
    payload = json.dumps(result, indent=2) + '\n'
    if a.out:
        with a.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
