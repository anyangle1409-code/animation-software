#!/usr/bin/env python3
"""Compare a Blender capture (cp3_rehearsal_blender.py capture) with the target record it was built from.

Pure Python + numpy (no bpy). Reports exact error figures; the only pass threshold is FLOAT32_M, the precision
Blender stores bone/object coordinates in (single-precision floats, a numerical, not anatomical, tolerance).

  cp3_roundtrip_compare.py --record FIT.json --capture CAPTURE.json [--out REPORT.json]
"""
import argparse, json, math, sys
from numbers import Real
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joint_markers as jm  # noqa: E402
from cp2_preflight import check_candidate, load_reference  # noqa: E402

FLOAT32_M = 1e-6          # ~8 float32 ulps at 2 m: storage precision of Blender coordinates
FLOAT32_AXIS = 1e-5       # unit-vector components after float32 matrix composition


def input_errors(data, label, capture=False):
    """Check all entries before max/min reductions can hide nonfinite values."""
    errors = []
    if not isinstance(data, dict):
        return [f'{label}: object required']

    def array(value, shape, name):
        try:
            raw = np.asarray(value, dtype=object)
            if raw.shape != shape or not all(isinstance(v, Real) and not isinstance(v, (bool, np.bool_)) and math.isfinite(v) for v in raw.flat):
                raise ValueError()
            return np.asarray(value, dtype=float)
        except (ValueError, TypeError, OverflowError):
            errors.append(f'{label}.{name}: finite numeric array {shape} required')
            return None

    for section in ('bones', 'joint_markers'):
        rows = data.get(section)
        if not isinstance(rows, dict) or not rows:
            errors.append(f'{label}.{section}: nonempty mapping required')
            continue
        for key, row in rows.items():
            name = f'{section}.{key}'
            if not isinstance(key, str) or not isinstance(row, dict):
                errors.append(f'{label}.{name}: text ID and object required')
                continue
            if section == 'bones':
                h = array(row.get('head_m'), (3,), name + '.head_m')
                t = array(row.get('tail_m'), (3,), name + '.tail_m')
                if h is not None and t is not None:
                    length = math.dist(h, t)
                    with np.errstate(over='ignore', invalid='ignore'):
                        frame_norm = float(np.linalg.norm(t - h))
                    if not math.isfinite(length) or length <= 0 or not math.isfinite(frame_norm) or frame_norm <= 0:
                        errors.append(f'{label}.{name}: finite nonzero bone length required')
                if 'parent' not in row or not isinstance(row.get('parent_relation'), dict):
                    errors.append(f'{label}.{name}: parent and parent relation required')
                if capture:
                    z = array(row.get('bone_z_axis'), (3,), name + '.bone_z_axis')
                    if z is not None and abs(math.hypot(*z) - 1) > FLOAT32_AXIS:
                        errors.append(f'{label}.{name}: unit bone Z axis required')
            else:
                array(row.get('centre_m'), (3,), name + '.centre_m')
                array(row.get('frame_axes_columns_XYZ'), (3, 3), name + '.frame_axes_columns_XYZ')
                if not isinstance(row.get('frame_bone'), str):
                    errors.append(f'{label}.{name}: frame bone ID required')
    return errors


def compare(rec, cap):
    errors = input_errors(rec, 'record') + input_errors(cap, 'capture', capture=True)
    if errors:
        return {'roundtrip_pass': False, 'input_errors': errors}
    rb, cb = rec['bones'], cap['bones']
    out = {'bone_ids_equal': set(rb) == set(cb), 'marker_ids_equal': set(rec['joint_markers']) == set(cap['joint_markers']),
           'roundtrip_pass': False, 'input_errors': []}
    if not out['bone_ids_equal'] or not out['marker_ids_equal']:
        out['input_errors'] = ['bone/marker identity sets must exactly match before coordinate comparison']
        return out
    out['marker_frame_bone_mismatches'] = sorted(k for k, m in rec['joint_markers'].items()
                                               if m['frame_bone'] != cap['joint_markers'][k]['frame_bone'])
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
    mw = max(mirror, key=mirror.get) if mirror else None
    out['max_bilateral_roll_mirror_error_deg'] = mirror[mw] if mw else None
    out['max_bilateral_roll_mirror_error_pair'] = mw
    mc = cap['joint_markers']
    cen = max(math.dist(m['centre_m'], mc[k]['centre_m']) for k, m in rec['joint_markers'].items() if k in mc)
    ax = max(float(np.abs(np.array(m['frame_axes_columns_XYZ']) - np.array(mc[k]['frame_axes_columns_XYZ'])).max())
             for k, m in rec['joint_markers'].items() if k in mc)
    out['max_marker_centre_error_m'] = cen
    out['max_marker_frame_component_error'] = ax
    out['roundtrip_pass'] = bool(out['bone_ids_equal'] and out['marker_ids_equal'] and pos <= FLOAT32_M and cen <= FLOAT32_M
                                 and ax <= FLOAT32_AXIS and not out['parent_mismatches'] and not out['parent_relation_mismatches']
                                 and not out['marker_frame_bone_mismatches'])
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
    if res['input_errors']:
        preflight = {'verdict': 'FAIL', 'scope': 'invalid round-trip input; CP2 geometry evaluation skipped'}
    else:
        pre = check_candidate(cap, *load_reference())
        preflight = {'verdict': pre['verdict'], 'counts': pre['counts'], 'checks': {c['id']: c['status'] for c in pre['checks']}}
    report = {'roundtrip': res, 'cp2_preflight_on_capture': preflight}
    if o.out:
        Path(o.out).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:3000])
    if not res['roundtrip_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
