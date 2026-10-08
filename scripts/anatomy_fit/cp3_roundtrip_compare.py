#!/usr/bin/env python3
"""Compare a Blender capture (cp3_rehearsal_blender.py capture) with the target record it was built from.

Pure Python + numpy (no bpy). Reports exact error figures; the only pass threshold is FLOAT32_M, the precision
Blender stores bone/object coordinates in (single-precision floats, a numerical, not anatomical, tolerance).

  cp3_roundtrip_compare.py --record FIT.json --capture CAPTURE.json [--out REPORT.json]
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_markers as jm  # noqa: E402
from cp2_preflight import check_candidate, load_reference  # noqa: E402

FLOAT32_M = 1e-6          # ~8 float32 ulps at 2 m: storage precision of Blender coordinates
FLOAT32_AXIS = 1e-5       # unit-vector components after float32 matrix composition


def compare(rec, cap):
    rb, cb = rec['bones'], cap['bones']
    out = {'bone_ids_equal': set(rb) == set(cb), 'marker_ids_equal': set(rec['joint_markers']) == set(cap['joint_markers'])}
    pos = max(max(math.dist(rb[k][e], cb[k][e]) for e in ('head_m', 'tail_m')) for k in rb if k in cb)
    out['max_bone_endpoint_error_m'] = pos
    out['parent_mismatches'] = sorted(k for k in rb if k in cb and rb[k]['parent'] != cb[k]['parent'])
    out['parent_relation_mismatches'] = sorted(k for k in rb if k in cb and rb[k]['parent_relation'] != cb[k]['parent_relation'])
    # roll: expected bone Z = roll target (same rule as build_anatomical_master_blender.roll_reference) made
    # perpendicular to the bone. 'unreferenced' lists bones whose ANTERIOR target is parallel to the bone: under the
    # original builder their roll was undefined; under the fixed builder they use the superior reference.
    roll_err, superior_ref = {}, []
    for k in rb:
        h, t = np.array(rb[k]['head_m']), np.array(rb[k]['tail_m'])
        y = (t - h) / np.linalg.norm(t - h)
        R = jm.bone_frame(h, t)
        target = R[:, 0]
        if np.linalg.norm(np.cross(target, y)) <= 1e-9:
            superior_ref.append(k); target = R[:, 1]
        perp = target - (target @ y) * y
        z = np.array(cb[k]['bone_z_axis'])
        roll_err[k] = math.degrees(math.acos(max(-1.0, min(1.0, float(z @ (perp / np.linalg.norm(perp)))))))
    worst = max(roll_err, key=roll_err.get)
    out['max_roll_error_deg'] = roll_err[worst]
    out['max_roll_error_bone'] = worst
    out['bones_needing_superior_roll_reference'] = {'count': len(superior_ref), 'bones': superior_ref,
                                                    'max_roll_error_deg': max(roll_err[k] for k in superior_ref) if superior_ref else None}
    mirror = {}
    for k in cb:
        if k.endswith('_left') or '_left_' in k:
            o = k.replace('_left', '_right')
            if o in cb:
                zl, zr = np.array(cb[k]['bone_z_axis']), np.array(cb[o]['bone_z_axis']) * [-1, 1, 1]
                mirror[k] = math.degrees(math.acos(max(-1.0, min(1.0, float(zl @ zr)))))
    mw = max(mirror, key=mirror.get)
    out['max_bilateral_roll_mirror_error_deg'] = mirror[mw]
    out['max_bilateral_roll_mirror_error_pair'] = mw
    mc = cap['joint_markers']
    cen = max(math.dist(m['centre_m'], mc[k]['centre_m']) for k, m in rec['joint_markers'].items() if k in mc)
    ax = max(float(np.abs(np.array(m['frame_axes_columns_XYZ']) - np.array(mc[k]['frame_axes_columns_XYZ'])).max())
             for k, m in rec['joint_markers'].items() if k in mc)
    out['max_marker_centre_error_m'] = cen
    out['max_marker_frame_component_error'] = ax
    out['roundtrip_pass'] = bool(out['bone_ids_equal'] and out['marker_ids_equal'] and pos <= FLOAT32_M and cen <= FLOAT32_M
                                 and ax <= FLOAT32_AXIS and not out['parent_mismatches'] and not out['parent_relation_mismatches'])
    out['roll_note'] = ('Roll is reported, not gated: Blender align_roll reproduces the intended bone Z within the max_roll_error_deg '
                        'shown. Horizontal bones use the perpendicular superior reference; roll errors remain '
                        'reported measurements rather than an anatomical acceptance gate.')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--record', required=True); ap.add_argument('--capture', required=True); ap.add_argument('--out')
    o = ap.parse_args()
    rec, cap = json.loads(Path(o.record).read_text()), json.loads(Path(o.capture).read_text())
    res = compare(rec, cap)
    pre = check_candidate(cap, *load_reference())
    report = {'roundtrip': res, 'cp2_preflight_on_capture': {'verdict': pre['verdict'], 'counts': pre['counts'],
              'checks': {c['id']: c['status'] for c in pre['checks']}}}
    if o.out:
        Path(o.out).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:3000])


if __name__ == '__main__':
    main()
