#!/usr/bin/env python3
"""Movement-follower verification on the committed c004 isolated run (read-only; changes no record, test or run).

Kneecap  (knee_flexion_with_patellar_follower_{side}; follower = sourced patellar_flexion_ratio x knee flexion about the
          fitted knee axis, translation path UNSOURCED in the model)
  expected vs observed  patellar rotation angle from the bone's world delta vs ratio x observed knee flexion
  continuity            patellar-ligament length: inferior pole -> tibia-fixed insertion. The insertion is the c004 inferior
                        pole + the Rajagopal 2016 rest ligament vector scaled by femur length (patellar_tracking_analysis);
                        compared with the plain knee_flexion_extension test (no follower)
  clearance             patella stick axis vs femur and tibia stick axes over the sweep (axis distance only)
Shoulder girdle (shoulder_complex_scapular_plane_{side}; follower = joint_solver FOLLOWER_COUPLINGS scapulothoracic rhythm)
  expected vs observed  upward rotation 0.43/deg GH elevation (0.43 x 117.5 = the McClure end value), tilt, external rotation,
                        clavicle posterior rotation and retraction scaled linearly to the end values
  continuity            SC: clavicle head displacement (sternum fixed); AC closure; GH-to-AC distance constancy
  clearance             clavicle vs rib 1-2, scapula vs ribs 2-8, humerus vs ribs 1-8 (axis distance only)
  gap                   clavicle elevation is NOT applied (only an upper bound is committed); measured, marked UNRESOLVED
Both: bilateral symmetry of every channel (left vs right, same frame index).

  follower_verification.py --osim Rajagopal2016.osim --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_solver as js  # noqa: E402
import hip_adduction_start_posture as hp  # noqa: E402
import patellar_tracking_analysis as pta  # noqa: E402

ROOT = HERE.parents[1]
REC = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
SAMPLES = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_c004_arm_inputs_001/isolated_samples.json'
ATLAS = ROOT / 'ORIGINAL_V1_WORK/anatomy/phase9_supplementary_observations.json'   # source of patellar_flexion_ratio (isolated_tests)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def app(M, p):
    return (np.asarray(M) @ np.append(p, 1.0))[:3]


def rot_angle(M):
    R = np.asarray(M)[:3, :3]
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(R) - 1) / 2))))


def seg(B, n, M=None):
    h, t = np.array(B[n]['head_m']), np.array(B[n]['tail_m'])
    return (h, t) if M is None else (app(M, h), app(M, t))


def knee(B, S, ratio, insertion0, side):
    t = S[f'knee_flexion_with_patellar_follower_{side}']
    plain = S[f'knee_flexion_extension_{side}']
    pole0 = np.array(B[f'patella_{side}']['tail_m'])
    ins0 = insertion0[side]
    L0 = float(np.linalg.norm(ins0 - pole0))
    rows, worst_err, lig, clr_f, clr_t = [], 0.0, [], 1e9, 1e9
    for f in t:
        D = f['moving_deltas']
        obs = rot_angle(D[f'patella_{side}'])
        exp = ratio * abs(f['flexion'])
        worst_err = max(worst_err, abs(obs - exp))
        pole = app(D[f'patella_{side}'], pole0); ins = app(D[f'tibia_{side}'], ins0)
        lig.append(float(np.linalg.norm(ins - pole)))
        ph, pt = seg(B, f'patella_{side}', D[f'patella_{side}'])
        clr_f = min(clr_f, hp.seg_dist(ph, pt, *seg(B, f'femur_{side}')))
        clr_t = min(clr_t, hp.seg_dist(ph, pt, *seg(B, f'tibia_{side}', D[f'tibia_{side}'])))
        rows.append({'knee_deg': round(abs(f['flexion']), 3), 'patella_rot_deg': round(obs, 4), 'expected_deg': round(exp, 4),
                     'ligament_mm': round(lig[-1] * 1000, 2)})
    lig_plain = []
    for f in plain:
        ins = app(f['moving_deltas'][f'tibia_{side}'], ins0)
        lig_plain.append(float(np.linalg.norm(ins - pole0)))
    return {'rows': rows[::5], 'max_flexion_deg': max(r['knee_deg'] for r in rows),
            'max_abs_follower_error_deg': round(worst_err, 6),
            'ligament_rest_mm': round(L0 * 1000, 2),
            'ligament_change_with_follower_mm': [round((min(lig) - L0) * 1000, 2), round((max(lig) - L0) * 1000, 2)],
            'ligament_change_plain_flexion_no_follower_mm': [round((min(lig_plain) - L0) * 1000, 2), round((max(lig_plain) - L0) * 1000, 2)],
            'min_patella_femur_axis_mm': round(clr_f * 1000, 2), 'min_patella_tibia_axis_mm': round(clr_t * 1000, 2)}


def shoulder(B, S, coup, side):
    t = S[f'shoulder_complex_scapular_plane_{side}']
    gmax = coup['gh_at_max_deg']; mx = coup['max_scapular_plane']
    sc0 = np.array(B[f'clavicle_{side}']['head_m'])
    ch0, ct0 = seg(B, f'clavicle_{side}')
    e0 = math.degrees(math.asin((ct0 - ch0)[2] / np.linalg.norm(ct0 - ch0)))
    err = {k: 0.0 for k in ('upward', 'tilt', 'scap_er', 'clav_post', 'clav_ret')}
    obs_key = {'upward': 'upward_about_axis', 'tilt': 'tilt_about_axis', 'scap_er': 'scap_er_about_axis', 'clav_post': 'clav_post', 'clav_ret': 'clav_ret'}
    sc_disp = ac_close = 0.0; gha = []; clr = {'clavicle_rib1_2': 1e9, 'scapula_ribs2_8': 1e9, 'humerus_ribs1_8': 1e9}; elev = []
    for f in t:
        e = f['elevation']; k = e / gmax
        exp = {'upward': coup['upward_rotation_per_gh_deg'] * e,
               'tilt': mx['posterior_tilt_deg'] * k, 'scap_er': mx['external_rotation_deg'] * k,
               'clav_post': 31.0 * k, 'clav_ret': coup['clavicle_retraction_deg'] * k}
        for c in err:
            err[c] = max(err[c], abs(f[obs_key[c]] - exp[c]))
        D = f['moving_deltas']
        sc_disp = max(sc_disp, float(np.linalg.norm(app(D[f'clavicle_{side}'], sc0) - sc0)))
        ac_close = max(ac_close, f['ac_closure_m']); gha.append(f['gh_to_ac_distance_m'])
        ch, ct = seg(B, f'clavicle_{side}', D[f'clavicle_{side}'])
        elev.append((f['humerothoracic_elevation'], math.degrees(math.asin((ct - ch)[2] / np.linalg.norm(ct - ch))) - e0))
        sh, st = seg(B, f'scapula_{side}', D[f'scapula_{side}']); hh, ht = seg(B, f'humerus_{side}', D[f'humerus_{side}'])
        for n in range(1, 9):
            r = seg(B, f'rib_{n:02d}_{side}')
            if n <= 2:
                clr['clavicle_rib1_2'] = min(clr['clavicle_rib1_2'], hp.seg_dist(ch, ct, *r))
            if n >= 2:
                clr['scapula_ribs2_8'] = min(clr['scapula_ribs2_8'], hp.seg_dist(sh, st, *r))
            clr['humerus_ribs1_8'] = min(clr['humerus_ribs1_8'], hp.seg_dist(hh, ht, *r))
    ht_max, ce_at_max = max(elev)
    return {'max_gh_elevation_deg': round(max(f['elevation'] for f in t), 3),
            'max_abs_error_vs_rhythm_deg': {k: round(v, 6) for k, v in err.items()},
            'max_SC_head_displacement_mm': round(sc_disp * 1000, 4), 'max_AC_closure_mm': round(ac_close * 1000, 5),
            'gh_to_ac_distance_range_mm': [round(min(gha) * 1000, 4), round(max(gha) * 1000, 4)],
            'min_axis_clearance_mm': {k: round(v * 1000, 2) for k, v in clr.items()},
            'clavicle_elevation_change_deg_at_max': round(ce_at_max, 3), 'humerothoracic_elevation_at_max_deg': round(ht_max, 3)}


def symmetry(S, test):
    L, R = S[f'{test}_left'], S[f'{test}_right']
    worst = {}
    for a, b in zip(L, R):
        for k, v in a.items():
            if isinstance(v, float) and isinstance(b.get(k), float) and k not in ('time_s',):
                d = abs(abs(v) - abs(b[k]))
                if k.endswith('_m'):
                    worst[k] = max(worst.get(k, 0.0), d)
                else:
                    worst[k] = max(worst.get(k, 0.0), d)
    return {k: float(f'{v:.3g}') for k, v in worst.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--osim', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rec = json.loads(REC.read_text()); B = rec['bones']; S = json.loads(SAMPLES.read_text())
    atlas = json.loads(ATLAS.read_text())
    O = atlas['observations']
    ratio = O['patellar_flexion_ratio']['value']['ratio']
    coup = js.FOLLOWER_COUPLINGS['scapulothoracic_rhythm']
    # insertion: left from the scaled Rajagopal rest ligament vector; right by X-mirror (c004 is mirror-symmetric, max 0.29 mm)
    raj, flen = pta.rajagopal(o.osim); pta.rajagopal.osim = o.osim
    c = pta.c004(raj, flen)
    hjc, kjc = np.array(B['femur_left']['head_m']), np.array(B['femur_left']['tail_m'])
    sup = (hjc - kjc) / np.linalg.norm(hjc - kjc)
    ant = np.array([0, -1.0, 0]) - sup * (np.array([0, -1.0, 0]) @ sup); ant /= np.linalg.norm(ant)
    s = c['femur_scale_c004_over_rajagopal']; r0 = raj[0]
    v = np.array(r0['tibia_point_in_femur_m']) - np.array(r0['patella_point_in_femur_m'])
    lig = s * (v[0] * ant + v[1] * sup)
    insL = np.array(B['patella_left']['tail_m']) + lig
    insR = np.array(B['patella_right']['tail_m']) + lig * np.array([-1, 1, 1])
    res = {'knee': {sd: knee(B, S, ratio, {'left': insL, 'right': insR}, sd) for sd in ('left', 'right')},
           'shoulder_girdle': {sd: shoulder(B, S, coup, sd) for sd in ('left', 'right')},
           'bilateral_symmetry_max_abs_diff': {'knee_flexion_with_patellar_follower': symmetry(S, 'knee_flexion_with_patellar_follower'),
                                               'shoulder_complex_scapular_plane': symmetry(S, 'shoulder_complex_scapular_plane')}}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_FOLLOWER_VERIFICATION', 'record': 'c004 (unchanged)',
           'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (REC, SAMPLES, ATLAS)},
           'external': {'rajagopal_2016': 'https://github.com/opensim-org/opensim-models/blob/d9b05d470b1a481c222372c85b75772faf8f7792/Models/Rajagopal/Rajagopal2016.osim'},
           'patellar_flexion_ratio': ratio, 'scapulothoracic_rhythm': coup, 'results': res,
           'unresolved': [
               'Patellar translation path: the c004 follower rotates the patella about the knee axis only (translation unsourced in '
               'the movement model), so the patellar ligament length is not conserved; a sourced path template exists (Rajagopal 2016, '
               'patellar_tracking_c004_v1.json) but is not installed and has not been reviewed for the shared machinery.',
               'Clavicle elevation during arm elevation: not applied (only a "below 10 deg" bound is committed; MoBL-lineage 0.1025 '
               'deg/deg conflicts above ~98 deg); see clavicle_elevation_gap_c004_v1.json.',
               'Clearances are stick-axis distances only; no bone envelopes exist, so no surface contact claim is made.',
               'The ligament insertion is a model-scaled point (Rajagopal), not a c004 landmark; the right side is its X-mirror.'],
           'inherited_failures': 'Not exercised here. The 9 inherited production-control test failures are unrelated and unchanged.'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for sd in ('left', 'right'):
        k = res['knee'][sd]; g = res['shoulder_girdle'][sd]
        print(sd, 'KNEE err', k['max_abs_follower_error_deg'], 'lig follower', k['ligament_change_with_follower_mm'], 'plain', k['ligament_change_plain_flexion_no_follower_mm'],
              'clr', k['min_patella_femur_axis_mm'], k['min_patella_tibia_axis_mm'])
        print(sd, 'SHOULDER err', g['max_abs_error_vs_rhythm_deg'], 'SC', g['max_SC_head_displacement_mm'], 'AC', g['max_AC_closure_mm'], 'GH-AC', g['gh_to_ac_distance_range_mm'],
              'clr', g['min_axis_clearance_mm'], 'clav elev', g['clavicle_elevation_change_deg_at_max'], '@HT', g['humerothoracic_elevation_at_max_deg'])
    print('symmetry', json.dumps(res['bilateral_symmetry_max_abs_diff'])[:600])


if __name__ == '__main__':
    main()
