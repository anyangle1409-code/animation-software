#!/usr/bin/env python3
"""Clavicular elevation during arm elevation: size of the missing follower (read-only; changes nothing).

Finding U3: the shoulder-complex sweep applies scapulothoracic upward rotation, tilt, external rotation and clavicular
retraction / posterior rotation (joint_solver.FOLLOWER_COUPLINGS['scapulothoracic_rhythm']) but NOT clavicular elevation,
because only an upper bound ("typically below 10 deg") was sourced. This script

 * reads the MoBL-ARMS-lineage shoulder rhythm as published in the MyoSuite arm model (MyoHub/myo_sim, pinned commit):
   sternoclavicular rotations coupled linearly to the thoracohumeral elevation coordinate shoulder_elv;
 * identifies the SC rotation whose axis is (anti)parallel to the thorax antero-posterior axis (= clavicular elevation);
 * reports the elevation it prescribes at 60/90/120/168 deg and the vertical rise of the c004 AC centre that a rotation of
   that size about the SC centre would produce (planar estimate in the clavicle's vertical plane), next to the same for
   the committed 10 deg bound.
Model frame: OpenSim/MoBL torso axes (x anterior, y superior, z right) as kept by MyoSuite.

  clavicle_elevation_gap.py --chain myoarm_r_chain.xml --assets myoarm_r_assets.xml --commit SHA --out JSON
"""
import argparse, hashlib, json, math, re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
C004 = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for a in ('--chain', '--assets', '--commit', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    chain, assets = Path(o.chain).read_text(), Path(o.assets).read_text()
    axes = {m.group(2): np.array([float(v) for v in m.group(1).split()])
            for m in re.finditer(r'<joint axis="([^"]+)" name="(sternoclavicular_r\d_r)"', chain)}
    coef = {m.group(1): [float(v) for v in m.group(3).split()]
            for m in re.finditer(r'joint1="(sternoclavicular_r\d_r)" joint2="(shoulder_elv_r)"[^>]*polycoef="([^"]+)"', assets)}
    ap_axis = np.array([1.0, 0, 0])
    elev = max(axes, key=lambda k: abs(axes[k] @ ap_axis) / np.linalg.norm(axes[k]))
    a = axes[elev] / np.linalg.norm(axes[elev]); c1 = coef[elev][1]
    # sign: does a positive coupled rotation lift the lateral end of a right clavicle (pointing +z)?
    th = 0.2; K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K
    lifts = (R @ np.array([0, 0, 1.0]))[1] > 0
    per_deg = c1 * (1 if lifts else -1)
    rec = json.loads(C004.read_text()); B = rec['bones']
    rows = {}
    for side in ('left', 'right'):
        h, t = np.array(B[f'clavicle_{side}']['head_m']), np.array(B[f'clavicle_{side}']['tail_m'])
        v = t - h; L = float(np.linalg.norm(v)); e0 = math.degrees(math.asin(v[2] / L))
        r = {'clavicle_chord_mm': round(L * 1000, 1), 'rest_elevation_deg': round(e0, 2)}
        for ht in (60, 90, 120, 168):
            d = per_deg * ht
            r[f'HT{ht}'] = {'model_clavicle_elevation_deg': round(d, 2),
                            'AC_rise_mm_model': round(L * 1000 * (math.sin(math.radians(e0 + d)) - math.sin(math.radians(e0))), 1),
                            'AC_rise_mm_at_committed_10deg_bound': round(L * 1000 * (math.sin(math.radians(e0 + min(d, 10))) - math.sin(math.radians(e0))), 1)}
        rows[side] = r
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_FOLLOWER_GAP', 'finding': 'U3',
           'source': {'model': f'https://github.com/MyoHub/myo_sim/blob/{o.commit}/myo_sim/models/arm/assets/myoarm_r_assets.xml',
                      'axes': f'https://github.com/MyoHub/myo_sim/blob/{o.commit}/myo_sim/models/arm/assets/myoarm_r_chain.xml',
                      'lineage': 'MoBL-ARMS upper-extremity model (Holzbaur et al. 2005; Saul et al. 2015) shoulder rhythm, linear '
                                 'regressions on thoracohumeral elevation after de Groot & Brand 2001 (as stated for that model family)',
                      'grade': 'published generic model; coupling template, not a population statistic'},
           'inputs_sha256': {str(C004.relative_to(ROOT)): sha(C004)},
           'sc_elevation_joint': elev, 'axis': a.round(4).tolist(), 'polycoef': coef[elev], 'clavicle_elevation_per_deg_HT': round(per_deg, 4),
           'other_sc_couplings': {k: v for k, v in coef.items() if k != elev},
           'c004': rows,
           'conflict': 'The model coefficient gives more than the committed "typically below 10 deg" bound above about '
                       f'{round(10 / per_deg, 0)} deg of thoracohumeral elevation; the bound is a secondary-review snippet. Not resolved.',
           'reading': 'Without clavicular elevation the AC (and the whole scapula-humerus chain) stays low in overhead positions by the '
                      'tabulated rise. The follower is not installed here (shared movement machinery).'}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    print(elev, out['axis'], 'per deg', out['clavicle_elevation_per_deg_HT'], json.dumps(rows['left']))


if __name__ == '__main__':
    main()
