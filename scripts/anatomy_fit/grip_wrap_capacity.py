#!/usr/bin/env python3
"""Finger grip capacity from the bony chain (read-only; changes nothing).

For digits 2-5 of a record, using the record's own phalanx stick lengths and the committed active-flexion means
(whole_body_movement_atlas.json, FINGER_ACTIVE: 195 adults / 390 hands), this reports:

 1. wrap: the smallest cylinder radius R around which the bony phalanx axis polygon (MCP, PIP, DIP, tip on the circle;
    the metacarpal tangent at the MCP) can close without any joint exceeding its active-mean flexion. Joint angles
    needed for a chord polygon: MCP = phi1/2, PIP = (phi1+phi2)/2, DIP = (phi2+phi3)/2 with phi_i = 2 asin(L_i / 2R).
    R is a bone-AXIS radius; the handle diameter it corresponds to is 2 (R - t) where t is the palmar soft tissue plus
    the half bone thickness, which is NOT sourced here and is therefore tabulated, not chosen.
 2. full active flexion in the sagittal plane of the ray: distance from the tip to the metacarpal axis segment
    (a bony analogue of the clinical pulp-to-palm distance; soft tissue excluded).
Distal-phalanx tips are evidence gap H2 (ten fingertip endpoints unsourced), so every result that uses L3 says so.

  grip_wrap_capacity.py --record R.json --label NAME --out JSON
"""
import argparse, hashlib, json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def needed(R, L):
    phi = [2 * math.asin(min(1.0, l / (2 * R))) for l in L]
    return [math.degrees(phi[0] / 2), math.degrees((phi[0] + phi[1]) / 2), math.degrees((phi[1] + phi[2]) / 2)], math.degrees(sum(phi))


def min_radius(L, lim):
    lo, hi = max(L) / 2 + 1e-9, 1.0
    if any(a > b for a, b in zip(needed(hi, L)[0], lim)):
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        ok = all(a <= b + 1e-12 for a, b in zip(needed(mid, L)[0], lim))
        hi, lo = (mid, lo) if ok else (hi, mid)
    return hi


def tip_to_palm(Lmc, L, ang):
    """Planar chain: MCP at origin, metacarpal from (-Lmc, 0) to 0, phalanges along +x then flexed toward -y (palmar)."""
    p, th, pts = np.zeros(2), 0.0, []
    for l, a in zip(L, ang):
        th += math.radians(a); p = p + l * np.array([math.cos(th), -math.sin(th)]); pts.append(p.copy())
    tip = pts[-1]
    x = min(0.0, max(-Lmc, tip[0]))
    return float(np.hypot(tip[0] - x, tip[1])), tip


def main():
    ap = argparse.ArgumentParser()
    for a in ('--record', '--label', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args()
    rec = json.loads(Path(o.record).read_text()); B = rec['bones']
    atlas = json.loads(ATLAS.read_text())
    O = {x['id']: x for x in atlas['observations']} if isinstance(atlas['observations'], list) else atlas['observations']
    res = {}
    for side in ('left', 'right'):
        for d in (2, 3, 4, 5):
            ln = lambda k: float(np.linalg.norm(np.array(B[k]['tail_m']) - np.array(B[k]['head_m'])))
            L = [ln(f'digit{d}_{p}_phalanx_{side}') for p in ('proximal', 'middle', 'distal')]
            Lmc = ln(f'metacarpal_{d}_{side}')
            lim = [O[f'digit{d}_{j}_flexion']['value']['mean'] for j in ('mcp', 'pip', 'dip')]
            R = min_radius(L, lim)
            ang, wrap = needed(R, L) if R else (None, None)
            dist, tip = tip_to_palm(Lmc, L, lim)
            res[f'digit{d}_{side}'] = {
                'lengths_mm': {'metacarpal': round(Lmc * 1000, 2), 'proximal': round(L[0] * 1000, 2), 'middle': round(L[1] * 1000, 2),
                               'distal_H2_unsourced_tip': round(L[2] * 1000, 2)},
                'active_mean_limits_deg': lim,
                'min_bone_axis_wrap_radius_mm': round(R * 1000, 2) if R else None,
                'joint_angles_at_min_radius_deg': [round(x, 2) for x in ang] if ang else None,
                'binding_joint': ['MCP', 'PIP', 'DIP'][int(np.argmax([a / b for a, b in zip(ang, lim)]))] if ang else None,
                'wrap_angle_at_min_radius_deg': round(wrap, 1) if wrap else None,
                'handle_diameter_mm_if_axis_offset_t': {f't={t}mm': round(2 * (R * 1000 - t), 1) for t in (5, 10, 15)} if R else None,
                'full_active_flexion_tip_to_metacarpal_axis_mm': round(dist * 1000, 2)}
    out = {'schema_version': 1, 'created': '2026-10-09', 'kind': 'READ_ONLY_GRIP_CAPACITY', 'label': o.label,
           'inputs_sha256': {o.record: sha(o.record), str(ATLAS.relative_to(ROOT)): sha(ATLAS)},
           'digits': res,
           'limits': ['bone axes only; soft tissue and bone thickness enter only through the tabulated offset t',
                      'planar flexion; MCP abduction, axial rotation and ray cupping (4th/5th CMC) are not modelled',
                      'distal phalanx length uses the unsourced tip endpoint (evidence gap H2)',
                      'active means, not maxima: half of healthy adults exceed them']}
    Path(o.out).parent.mkdir(parents=True, exist_ok=True)
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for k, v in res.items():
        if k.endswith('left'):
            print(k, v['lengths_mm'], 'Rmin', v['min_bone_axis_wrap_radius_mm'], v['binding_joint'], 'wrap', v['wrap_angle_at_min_radius_deg'],
                  'tip-palm', v['full_active_flexion_tip_to_metacarpal_axis_mm'])


if __name__ == '__main__':
    main()
