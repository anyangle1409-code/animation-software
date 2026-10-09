#!/usr/bin/env python3
"""Outcome audit of the T001 coupled trunk experiment against c004 (read-only).

Every check uses evidence that was NOT an input of the T001 solve:
  T12/L1 height        P1 S1 (HJC + Hasegawa PTh/PT) + sourced lumbar rise (trunk_vertical_closure_audit)
  C7 spinous tip       ANSUR cervicale at 1.82 m (grade-D specimen tip offset, +/-10 deg lean sensitivity)
  IJ level             sternal notch at the T2-T3 vertebral bodies (Razzouk 2023, 1,035 supine CT; abstract level)
  rib 10 height        ANSUR tenth-rib height (directional; definitions differ)
  rib-head levels      rib head vs its articular level (rib 1, 10-12 own body; 2-9 the disc above)
  scapula-rib          minimum stick-axis distance scapula vs ribs 2-8 (the scapula lies on the posterolateral chest wall;
                       axis distance only, no envelopes)
  disc gaps            CP2 centre-line gap > 0 at every disc level
  thorax depth         skin IJ to the T2/T3 disc centre, horizontal (specimen context ~90-100 mm, grade D)

  t001_outcome_audit.py --discriminator JSON --record R.json [--record R2.json ...] --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spine_column_length_discriminator as sd  # noqa: E402
import hip_adduction_start_posture as hp  # noqa: E402

ROOT = HERE.parents[1]
CHAIN = ['l5', 'l4', 'l3', 'l2', 'l1'] + [f't{i}' for i in range(12, 0, -1)] + ['c7', 'c6', 'c5', 'c4', 'c3', 'c2']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mm(v):
    return np.array(v) * 1000


def audit(rec, disc, pred_t12l1):
    B = rec['bones']
    out = {}
    j = (mm(B['t12']['head_m']) + mm(B['l1']['tail_m'])) / 2
    out['T12_L1_mid_z_minus_pelvis_prediction_mm'] = round(float(j[2] - pred_t12l1), 1)
    c7 = sd.candidate_c7_from(rec); tip = disc['c7_spinous_tip_offset_specimen']['tip_minus_body_centre_local_mm']
    zt = [sd.tip_world((c7['c7_stick_mid_mm'][1], c7['c7_stick_mid_mm'][2]), c7['c7_axis_lean_deg'] + d, tip)[1] for d in (-10, 0, 10)]
    out['C7_tip_minus_ANSUR_cervicale_mm'] = {'lean-10': round(zt[0] - 1575.2, 1), 'central': round(zt[1] - 1575.2, 1), 'lean+10': round(zt[2] - 1575.2, 1)}
    ij = mm(B['sternum']['head_m'])
    t2 = (mm(B['t2']['head_m']) + mm(B['t2']['tail_m'])) / 2; t3 = (mm(B['t3']['head_m']) + mm(B['t3']['tail_m'])) / 2
    lo, hi = min(mm(B['t3']['head_m'])[2], mm(B['t2']['tail_m'])[2]), max(mm(B['t3']['head_m'])[2], mm(B['t2']['tail_m'])[2])
    out['IJ_bony_z_mm'] = round(float(ij[2]), 1)
    out['IJ_vs_T2_T3_bodies'] = {'T3_inferior_z': round(float(lo), 1), 'T2_superior_z': round(float(hi), 1),
                                 'inside': bool(lo <= ij[2] <= hi), 'mm_outside': round(float(max(lo - ij[2], ij[2] - hi, 0)), 1)}
    out['IJ_to_T2T3_horizontal_mm'] = round(float(((t2 + t3) / 2)[1] - ij[1]), 1)
    out['rib10_anterior_end_minus_ANSUR_tenth_rib_mm'] = round(min(mm(B[f'rib_10_{s}']['tail_m'])[2] for s in ('left', 'right')) - 1166.8, 1)
    lv = {}
    for n in range(1, 13):
        h = mm(B[f'rib_{n:02d}_left']['head_m'])
        if 2 <= n <= 9:
            ref = (mm(B[f't{n}']['tail_m']) + mm(B[f't{n - 1}']['head_m'])) / 2
        else:
            ref = (mm(B[f't{n}']['head_m']) + mm(B[f't{n}']['tail_m'])) / 2
        lv[f'rib_{n:02d}'] = round(float(h[2] - ref[2]), 2)
    out['rib_head_minus_articular_level_z_mm'] = lv
    sc = {}
    for s in ('left', 'right'):
        a, b = np.array(B[f'scapula_{s}']['head_m']), np.array(B[f'scapula_{s}']['tail_m'])
        dmin, which = 1e9, None
        for n in range(2, 9):
            r = B[f'rib_{n:02d}_{s}']
            dd = hp.seg_dist(a, b, np.array(r['head_m']), np.array(r['tail_m']))
            if dd < dmin:
                dmin, which = dd, n
        sc[s] = {'min_axis_distance_mm': round(dmin * 1000, 1), 'rib': which}
    out['scapula_rib_axis_distance'] = sc
    gaps = {}
    for lo_, up in zip(CHAIN, CHAIN[1:]):
        axis = np.array(B[lo_]['tail_m']) - np.array(B[lo_]['head_m'])
        step = np.array(B[up]['head_m']) - np.array(B[lo_]['tail_m'])
        gaps[f'{up}/{lo_}'] = round(float(step @ axis / np.linalg.norm(axis)) * 1000, 2)
    out['disc_centre_gaps_mm'] = {'min': min(gaps.values()), 'all_positive': all(g > 0 for g in gaps.values()), 'per_level': gaps}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--discriminator', required=True); ap.add_argument('--record', action='append', required=True)
    ap.add_argument('--closure', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    disc = json.loads(Path(o.discriminator).read_text())
    cl = json.loads(Path(o.closure).read_text())['detail']['T12_L1_height']
    pred = cl['P1_S1_plus_sourced_lumbar_mm']
    res = {p: audit(json.loads(Path(p).read_text()), disc, pred) for p in o.record}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_T001_OUTCOME_AUDIT',
           'inputs_sha256': {**{p: sha(p) for p in o.record}, o.discriminator: sha(o.discriminator), o.closure: sha(o.closure)},
           'T12_L1_pelvis_prediction_mm': pred, 'records': res}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for p, r in res.items():
        print('==', p.split('/')[-2] if '/' in p else p)
        print({k: v for k, v in r.items() if k not in ('rib_head_minus_articular_level_z_mm', 'disc_centre_gaps_mm')})
        print('rib levels', r['rib_head_minus_articular_level_z_mm'], 'discs min', r['disc_centre_gaps_mm']['min'])


if __name__ == '__main__':
    main()
