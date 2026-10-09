#!/usr/bin/env python3
"""Patellar tracking during knee flexion (read-only analysis; changes no record, no test).

Defect L3 (skeleton_defect_register_v1.json): in plain knee flexion the c004 patella is a rigid child of the femur and
stays where it is. The patellar ligament (inferior pole -> tibial tuberosity) is nearly inextensible, so that cannot be
right; this script measures how wrong it is and tests a sourced follower.

Source of the follower: the published Rajagopal et al. 2016 full-body model (opensim-models, pinned commit), whose
patellofemoral CustomJoint prescribes the patella's flexion and sagittal translations relative to the femur as splines of
knee angle (coupled 1:1 to the walker-knee angle by a CoordinateCouplerConstraint). Its own patellar-ligament segment is
the quadriceps path from the patella point (vasint P4) to the tibia point (vasint P5).

Steps
 1. Rajagopal itself: ligament length over 0-120 deg of knee flexion (the model's own consistency).
 2. c004, plain flexion as the isolated test does it (tibia rotates about the fitted KJC flexion axis, patella static):
    ligament length change. The tibial insertion is the tibia-fixed point that, at 0 deg, lies at the Rajagopal rest
    ligament vector (scaled by the femur-length ratio) from the c004 inferior pole. No anatomical length is invented: the
    ligament rest vector is the model's, scaled.
 3. c004 with the follower: the inferior pole follows the Rajagopal patella-point path relative to the femur (scaled,
    sagittal components mapped to HGPT), the tibia as in 2; ligament length change.

  patellar_tracking_analysis.py --osim Rajagopal2016.osim --commit SHA --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from opensim_model_geometry import Model  # noqa: E402
import joint_solver as js  # noqa: E402

ROOT = HERE.parents[1]
C004 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
P_PAT = np.array([0.005, 0.00247, 0.00039])           # vasint_l-P4 on patella_l (Rajagopal2016)
P_TIB = np.array([0.03257, -0.0632, -0.00043])        # vasint_l-P5 on tibia_l
ANGLES = list(range(0, 125, 5))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rajagopal(osim):
    out = []
    for a in ANGLES:
        m = Model(osim)
        m.coords['knee_angle_l'] = math.radians(a); m.coords['knee_angle_l_beta'] = math.radians(a)
        F, P, Tb = m.body_world('femur_l'), m.body_world('patella_l'), m.body_world('tibia_l')
        pp = (P @ np.append(P_PAT, 1))[:3]; pt = (Tb @ np.append(P_TIB, 1))[:3]
        inv = np.linalg.inv(F)
        out.append({'knee_deg': a, 'ligament_mm': float(np.linalg.norm(pp - pt) * 1000),
                    'patella_point_in_femur_m': (inv @ np.append(pp, 1))[:3].tolist(),
                    'tibia_point_in_femur_m': (inv @ np.append(pt, 1))[:3].tolist()})
    m = Model(osim)
    hip = m.body_world('femur_l')[:3, 3]
    kf = m.body_world('femur_l') @ m.offset(m.joint_of['tibia_l'][1])
    femur_len = float(np.linalg.norm(kf[:3, 3] - hip))
    return out, femur_len


def c004(raj, raj_femur_len):
    rec = json.loads(C004.read_text())
    B, J = rec['bones'], rec['joint_markers']
    hjc, kjc = np.array(B['femur_left']['head_m']), np.array(B['femur_left']['tail_m'])
    s = float(np.linalg.norm(kjc - hjc)) / raj_femur_len
    frame = np.array(J['tibiofemoral_left']['frame_axes_columns_XYZ'])
    zax = frame[:, 2]
    ankle = np.array(B['tibia_left']['tail_m'])
    # flexion sign: the ankle must move posterior (+Y) for knee flexion
    sgn = 1.0 if (js.rot(zax, 10) @ (ankle - kjc))[1] > (ankle - kjc)[1] else -1.0
    # femur sagittal frame (anterior, superior) from the femur axis: superior = HJC - KJC, anterior = -Y made orthogonal
    sup = (hjc - kjc) / np.linalg.norm(hjc - kjc)
    ant = np.array([0, -1.0, 0]) - sup * (np.array([0, -1.0, 0]) @ sup); ant /= np.linalg.norm(ant)
    inf_pole = np.array(B['patella_left']['tail_m'])
    r0 = raj[0]
    # Rajagopal femur frame: x anterior, y superior. Map patella-point displacement and ligament vector by components.
    def to_hgpt(v):
        return s * (v[0] * ant + v[1] * sup)
    lig0 = to_hgpt(np.array(r0['tibia_point_in_femur_m']) - np.array(r0['patella_point_in_femur_m']))
    insertion0 = inf_pole + lig0
    L0 = float(np.linalg.norm(lig0) * 1000)
    rows = []
    for r in raj:
        R = js.rot(zax, sgn * r['knee_deg'])
        ins = kjc + R @ (insertion0 - kjc)
        static = float(np.linalg.norm(ins - inf_pole) * 1000)
        pole_f = inf_pole + to_hgpt(np.array(r['patella_point_in_femur_m']) - np.array(r0['patella_point_in_femur_m']))
        follow = float(np.linalg.norm(ins - pole_f) * 1000)
        rows.append({'knee_deg': r['knee_deg'], 'static_patella_ligament_mm': round(static, 2), 'follower_ligament_mm': round(follow, 2),
                     'follower_pole_shift_mm': round(float(np.linalg.norm(pole_f - inf_pole) * 1000), 2)})
    m = Model(rajagopal.osim)
    knee_f = np.linalg.inv(m.body_world('femur_l')) @ (m.body_world('femur_l') @ m.offset(m.joint_of['tibia_l'][1]))
    raj_rel = np.array(r0['patella_point_in_femur_m']) - knee_f[:3, 3]
    c_rel = inf_pole - kjc
    rest = {'rajagopal_patella_point_minus_knee_scaled_mm': {'anterior': round(float(raj_rel[0] * s * 1000), 1),
                                                             'superior': round(float(raj_rel[1] * s * 1000), 1)},
            'c004_inferior_pole_minus_KJC_mm': {'anterior': round(float(c_rel @ ant * 1000), 1), 'superior': round(float(c_rel @ sup * 1000), 1)},
            'note': 'knee origin of the Rajagopal walker knee vs the c004 ISB epicondylar KJC: definitions differ by a few mm'}
    return {'rest_position_comparison': rest, 'femur_scale_c004_over_rajagopal': round(s, 4), 'flexion_sign_about_marker_Z': sgn, 'rest_ligament_mm': round(L0, 2), 'rows': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--osim', required=True); ap.add_argument('--commit', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rajagopal.osim = o.osim
    raj, flen = rajagopal(o.osim)
    c = c004(raj, flen)
    L = [r['ligament_mm'] for r in raj]
    st = [r['static_patella_ligament_mm'] for r in c['rows']]; fo = [r['follower_ligament_mm'] for r in c['rows']]
    L0 = c['rest_ligament_mm']
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_PATELLAR_TRACKING_ANALYSIS',
           'source': {'model': f'https://github.com/opensim-org/opensim-models/blob/{o.commit}/Models/Rajagopal/Rajagopal2016.osim',
                      'reference': 'Rajagopal A, Dembia CL, DeMers MS, et al. Full-body musculoskeletal model for muscle-driven simulation of '
                                   'human gait. IEEE Trans Biomed Eng 2016;63:2068-79 (patellofemoral kinematics inherited from earlier '
                                   'OpenSim lower-limb models)',
                      'grade': 'published generic model; kinematic template, not a population statistic',
                      'spline_evaluation': 'piecewise linear between 10-deg knots (opensim_model_geometry.evaluate)'},
           'inputs_sha256': {str(C004.relative_to(ROOT)): sha(C004)},
           'rajagopal_femur_length_m': round(flen, 4),
           'rajagopal_ligament_mm': {'min': round(min(L), 2), 'max': round(max(L), 2), 'range': round(max(L) - min(L), 2),
                                     'per_angle': [round(x, 2) for x in L]},
           'c004': c,
           'summary': {'static_patella_ligament_change_max_mm': round(max(abs(x - L0) for x in st), 2),
                       'static_patella_ligament_change_max_percent': round(100 * max(abs(x - L0) for x in st) / L0, 1),
                       'follower_ligament_change_max_mm': round(max(abs(x - L0) for x in fo), 2),
                       'follower_ligament_change_max_percent': round(100 * max(abs(x - L0) for x in fo) / L0, 1),
                       'rajagopal_own_ligament_change_percent': round(100 * (max(L) - min(L)) / L[0], 1)},
           'reading': ['A rigid (static) patella stretches the ligament by the summary amount at 120 deg: this is a movement-model '
                       'defect (L3), not a geometry defect of the patella bone.',
                       'The follower is the model path transferred by femur-length scaling; the c004 knee is a pure rotation about '
                       'the fitted KJC while the Rajagopal knee translates, so the residual is the mismatch of the two knee models.',
                       'No follower is installed here; installing one changes the movement machinery and needs its own review.']}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out['summary']), 'rest', L0, 'scale', c['femur_scale_c004_over_rajagopal'])


if __name__ == '__main__':
    main()
