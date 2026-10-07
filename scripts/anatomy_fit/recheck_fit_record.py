#!/usr/bin/env python3
"""Addendum checks on a committed fit record after the independent review (no Blender, no geometry change).

- Trotter-Gleser cross-check with the corrected derivations (tibia excludes the malleolus; radius from the
  radial-head surface).
- Midline placement BEFORE enforce_midline (the record's check runs after snapping and cannot fail).
- Whether any joint marker used the parallel-segment branch of segment_closest.
Run: python3 recheck_fit_record.py --record FIT.json --out NEW.json
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import joint_markers as jm
import skeleton_fit as sf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--record', required=True); ap.add_argument('--out', required=True)
    o = ap.parse_args()
    rec = json.loads(Path(o.record).read_text())
    L, bones = rec['skeleton_input'], rec['bones']
    stature = rec['landmarks_and_joint_centres']['global']['stature_m']
    tg = {}
    for s in ('left', 'right'):
        for bone, (length, how) in jm.anatomical_lengths(L, s, bones).items():
            a, b0, se = jm.TROTTER_GLESER[bone]
            pred = (a * length * 100 + b0) / 100
            tg[f'{bone}_{s}'] = {'length_m': float(length), 'derivation': how, 'predicted_stature_m': pred,
                                 'difference_m': pred - stature, 'se_m': se / 100, 'within_2se': bool(abs(pred - stature) <= 2 * se / 100)}
    S = sf.build(L)   # rebuild WITHOUT enforce_midline
    mid = {k: max(abs(b['head_m'][0]), abs(b['tail_m'][0])) for k, b in S.bones.items() if sf.is_midline(k)}
    degenerate = []
    B = {k: (np.asarray(b['head_m']), np.asarray(b['tail_m'])) for k, b in bones.items()}
    for jid, m in rec['joint_markers'].items():
        parts = [p for p in m.get('participants', []) if p in B] if 'participants' in m else []
        if len(parts) >= 2:
            d1, d2 = B[parts[0]][1] - B[parts[0]][0], B[parts[1]][1] - B[parts[1]][0]
            if (d1 @ d1) * (d2 @ d2) - (d1 @ d2) ** 2 <= 1e-12:
                degenerate.append(jid)
    plan = json.loads((Path(__file__).resolve().parents[2] / 'ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json').read_text())
    for jid, m in rec['joint_markers'].items():
        parts = [p for p in plan['joint_markers'][jid]['participants'] if p in B]
        if len(parts) >= 2:
            d1, d2 = B[parts[0]][1] - B[parts[0]][0], B[parts[1]][1] - B[parts[1]][0]
            if (d1 @ d1) * (d2 @ d2) - (d1 @ d2) ** 2 <= 1e-12 and jid not in degenerate:
                degenerate.append(jid)
    out = {'record': o.record, 'record_out_blend_sha256': rec['provenance']['out_blend_sha256'],
           'trotter_gleser_corrected': {'status': 'PASS' if all(v['within_2se'] for v in tg.values()) else 'FAIL', 'bones': tg,
                                        'corrections': ['tibia: no malleolar allowance (Trotter & Gleser measured the tibia excluding the malleolus)',
                                                        'radius: measured from the radial-head surface, ~10 mm distal of the capitulum centre']},
           'midline_before_snapping': {'max_abs_x_m': max(mid.values()), 'bones_over_0_5mm': sorted(k for k, v in mid.items() if v > 5e-4),
                                       'note': 'The record check runs after enforce_midline and cannot fail; this is the pre-snap value.'},
           'parallel_segment_markers': degenerate,
           'scope': 'Addendum after independent review; supersedes the trotter_gleser_cross_check in the record. Geometry unchanged.'}
    with open(o.out, 'x') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({'tg': out['trotter_gleser_corrected']['status'], 'mid_max': out['midline_before_snapping']['max_abs_x_m'],
                      'mid_over': out['midline_before_snapping']['bones_over_0_5mm'], 'parallel': degenerate}))
    for k, v in tg.items():
        if k.endswith('left'):
            print(k, round(v['length_m'], 4), round(v['predicted_stature_m'], 3), round(v['difference_m'], 3), v['within_2se'])


if __name__ == '__main__':
    main()
