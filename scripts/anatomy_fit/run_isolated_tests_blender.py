#!/usr/bin/env python3
"""Phase 9: author and measure isolated bone-only sweeps on HGPT_ANATOMICAL_MASTER (audit only).

1. Opens the fitted master audit file, keys every isolated test on its own frame range (dense keys, C1
   cosine easing between keyposes, rest at both ends) and saves a NEW audit file.
2. Re-opens the saved file and measures each frame from Blender's evaluated pose: signed JCS angles,
   joint-centre drift, off-axis residuals, distal-marker radius, continuity and left/right mirroring.
Numerical thresholds below check implementation integrity only; they are not anatomical tolerances.

Run: python3 run_isolated_tests_blender.py --source-blend A003 --record FIT.json --out-blend NEW.blend --out-dir RUN
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE)]

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

import isolated_tests as it  # noqa: E402

MASTER = 'HGPT_ANATOMICAL_MASTER'
INTEGRITY = {'angle_error_deg': 1e-3, 'centre_drift_m': 1e-6, 'off_axis_deg': 1e-3, 'mirror_angle_deg': 1e-3,
             'mirror_position_m': 1e-3, 'continuity_second_difference_deg': 1e-3, 'radius_variation_m': 1e-6}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def mat(M):
    return np.array([[M[r][c] for c in range(4)] for r in range(4)], float)


def author(arm, tests, F, rest):
    frame = 1
    ranges = {}
    for t in tests:
        series = it.series(t)
        start = frame
        bones = sorted({b for cmd in series for b in it.deltas(t, cmd, F)})
        for i, cmd in enumerate(series):
            G = it.deltas(t, cmd, F)
            for b in bones:
                R0 = rest[b]
                basis = np.linalg.inv(R0) @ G.get(b, np.eye(4)) @ R0
                pb = arm.pose.bones['anat_' + b]
                pb.rotation_mode = 'QUATERNION'
                M = Matrix(basis.tolist())
                loc, quat, _ = M.decompose()
                pb.location = loc
                pb.rotation_quaternion = quat
                pb.keyframe_insert('location', frame=start + i)
                pb.keyframe_insert('rotation_quaternion', frame=start + i)
        ranges[t['id']] = (start, start + len(series) - 1)
        frame = start + len(series) + 4
    return ranges, frame


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--source-blend', '--record', '--out-blend', '--out-dir'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    src, out_blend, out_dir = Path(o.source_blend).resolve(), Path(o.out_blend).resolve(), Path(o.out_dir).resolve()
    if out_blend.exists() or (out_dir.exists() and any(out_dir.iterdir())):
        raise FileExistsError('Use new output paths')
    rec = json.loads(Path(o.record).read_text())
    atlas = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json').read_text())
    src_hash = sha(src)
    if rec['provenance']['out_blend_sha256'] != src_hash:
        raise ValueError('Fit record does not describe this audit file')
    F = it.frames(rec)
    tests = it.specs(rec, atlas)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    arm = bpy.data.objects[MASTER]
    rest = {b.name[5:]: mat(arm.matrix_world @ b.matrix_local) for b in arm.data.bones}
    ranges, end = author(arm, tests, F, rest)
    sc = bpy.context.scene
    sc.render.fps, sc.render.fps_base = 24, 1.0
    sc.frame_start, sc.frame_end = 1, end
    sc.frame_set(1)
    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    authored_hash = sha(out_blend)
    # ---------------------------------------------------------------- measurement on the saved file
    bpy.ops.wm.open_mainfile(filepath=str(out_blend))
    sc = bpy.context.scene
    arm = bpy.data.objects[MASTER]
    rest = {b.name[5:]: mat(arm.matrix_world @ b.matrix_local) for b in arm.data.bones}
    initial = (sc.frame_current, sc.frame_subframe)
    fps = sc.render.fps / sc.render.fps_base
    results = {}
    try:
        for t in tests:
            a, b = ranges[t['id']]
            series = it.series(t)
            needed = set()
            for k in ('proximal',):
                if t.get(k) and t[k] != 'world':
                    needed.add(t[k])
            needed |= set(t.get('moving', [])) | set(t.get('stage2', []))
            for link in t.get('chain', []):
                needed |= {link['moving'], link['proximal']}
            rows = []
            for i, f in enumerate(range(a, b + 1)):
                sc.frame_set(f)
                dg = bpy.context.evaluated_depsgraph_get()
                ev = arm.evaluated_get(dg)
                pose = {n: mat(ev.matrix_world @ ev.pose.bones['anat_' + n].matrix) for n in needed}
                mk = {}
                for name in (t['marker'], t['distal_marker']):
                    obj = bpy.data.objects.get('HGPT_JOINT_' + name)
                    if obj is not None:
                        mk[name] = list(obj.evaluated_get(dg).matrix_world.translation)
                m = it.measure(t, pose, rest, F, mk)
                m['frame'] = f
                m['time_s'] = f / fps
                m['commanded'] = series[i]
                m['distal_marker_m'] = mk.get(t['distal_marker'])
                m['marker_m'] = mk.get(t['marker'])
                rows.append(m)
            results[t['id']] = rows
    finally:
        sc.frame_set(initial[0], subframe=initial[1])
    restored = (sc.frame_current, sc.frame_subframe) == initial
    after_hash = sha(out_blend)
    # ---------------------------------------------------------------- analysis
    summary = {}
    for t in tests:
        rows = results[t['id']]
        chans = it.commanded_channels(t)
        errs = {}
        for c in chans:
            meas_key = {'internal': 'internal_rotation', 'plane': 'plane_of_elevation'}.get(c, c)
            if t['kind'] == 'shoulder_complex' and c in ('upward', 'tilt', 'scap_er'):
                meas_key = c + '_about_axis'
            if t['kind'] in ('zxy', 'wrist') and c in ('flexion', 'adduction', 'internal'):
                meas_key = {'flexion': 'flexion', 'adduction': 'adduction', 'internal': 'internal_rotation'}[c]
            e = []
            for r in rows:
                cmd = r['commanded'].get(c, 0.0)
                if c == 'plane' and r['commanded'].get('elevation', 0.0) < 1.0:
                    continue
                if meas_key in r:
                    e.append(abs(r[meas_key] - cmd))
            errs[c] = max(e) if e else None
        # cross-talk on uncommanded JCS channels
        cross = 0.0
        if t['kind'] in ('zxy', 'wrist'):
            for key, cm in (('flexion', 'flexion'), ('adduction', 'adduction'), ('internal_rotation', 'internal')):
                if cm not in chans:
                    cross = max(cross, max(abs(r[key]) for r in rows))
        if t['kind'] == 'tmj':   # intended translation: drift must equal the commanded condylar glide
            drift = max(abs(r['centre_drift_m'] - r['commanded'].get('glide', 0.0)) for r in rows)
        else:
            drift = max(r['centre_drift_m'] for r in rows)
        offax = max([r.get('off_axis_deg', 0.0) or 0.0 for r in rows] + [r.get('pronation_off_axis_deg', 0.0) or 0.0 for r in rows])
        mvc = [r.get('marker_vs_proximal_carried_centre_m') for r in rows if r.get('marker_vs_proximal_carried_centre_m') is not None]
        prim = t['primary']
        mkey = {'internal': 'internal_rotation', 'plane': 'plane_of_elevation'}.get(prim, prim)
        meas_prim = [r[mkey] for r in rows]
        cmd_prim = [r['commanded'].get(prim, 0.0) for r in rows]
        d2m = np.diff(np.asarray(meas_prim, float), 2)
        d2c = np.diff(np.asarray(cmd_prim, float), 2)
        vel_m = np.diff(np.asarray(meas_prim, float))
        vel_c = np.diff(np.asarray(cmd_prim, float))
        def reversals(v, floor):
            sig = [0 if abs(x) <= floor else (1 if x > 0 else -1) for x in v]
            out, last = [], 0
            for i, x in enumerate(sig):
                if x and last and x != last:
                    out.append(i)
                if x:
                    last = x
            return out
        rev_c = reversals(vel_c, 1e-9)
        rev_m = reversals(vel_m, 1e-4)   # noise floor for single-precision evaluation
        radii = []
        for r in rows:
            if r['distal_marker_m'] is not None and r['marker_m'] is not None:
                radii.append(float(np.linalg.norm(np.asarray(r['distal_marker_m']) - np.asarray(r['marker_m']))))
        s = {'frames': [ranges[t['id']][0], ranges[t['id']][1]], 'samples': len(rows), 'channels': chans,
             'max_abs_error_deg': errs, 'max_uncommanded_jcs_deg': cross, 'max_centre_drift_m': drift,
             'max_off_axis_deg': offax, 'max_marker_vs_carried_centre_m': max(mvc) if mvc else None,
             'continuity_max_second_difference_mismatch_deg': float(np.max(np.abs(d2m - d2c))) if len(d2m) else None,
             'max_step_deg_per_frame': float(np.max(np.abs(vel_m))) if len(vel_m) else None,
             'commanded_reversal_frames': rev_c, 'measured_reversal_frames': rev_m,
             'distal_marker_radius_range_m': (max(radii) - min(radii)) if radii else None,
             'max_incisor_displacement_m': max((r.get('incisor_displacement_m') or 0.0) for r in rows) if t['kind'] == 'tmj' else None,
             'max_condylar_displacement_m': max((r.get('condylar_displacement_m') or 0.0) for r in rows) if t['kind'] == 'tmj' else None,
             'primary_channel': prim, 'primary_range_measured_deg': [float(min(meas_prim)), float(max(meas_prim))],
             'context': t['context'], 'amplitude_basis': t['amplitude_basis'], 'profile': t['profile'], 'side': t['side'],
             'plane': t['plane'], 'kind': t['kind']}
        ok = all(v is None or v <= INTEGRITY['angle_error_deg'] for v in errs.values()) and cross <= INTEGRITY['angle_error_deg'] \
            and drift <= INTEGRITY['centre_drift_m'] and offax <= INTEGRITY['off_axis_deg'] \
            and (s['continuity_max_second_difference_mismatch_deg'] is None or s['continuity_max_second_difference_mismatch_deg'] <= INTEGRITY['continuity_second_difference_deg']) \
            and rev_c == rev_m and (s['distal_marker_radius_range_m'] is None or s['distal_marker_radius_range_m'] <= INTEGRITY['radius_variation_m'] or t['kind'] in ('elbow', 'wrist', 'digit', 'tmj'))
        s['integrity_status'] = 'PASS' if ok else 'FAIL'
        summary[t['id']] = s
    mirror = {}
    for tid, s in summary.items():
        if tid.endswith('_left'):
            rid = tid[:-5] + '_right'
            L, R = results[tid], results[rid]
            ch = s['primary_channel']
            key = {'internal': 'internal_rotation', 'plane': 'plane_of_elevation'}.get(ch, ch)
            same_cmd = all(l['commanded'] == r['commanded'] for l, r in zip(L, R))
            if same_cmd:
                da = max(abs((l.get(key) or 0) - (r.get(key) or 0)) for l, r in zip(L, R))
                dp = max(float(np.linalg.norm(np.asarray(l['distal_marker_m']) * [-1, 1, 1] - np.asarray(r['distal_marker_m'])))
                         for l, r in zip(L, R) if l['distal_marker_m'] and r['distal_marker_m'])
                basis = 'identical commands: measured angles and mirrored distal-marker paths compared'
            else:
                da = max(abs(((l.get(key) or 0) - l['commanded'].get(ch, 0.0)) - ((r.get(key) or 0) - r['commanded'].get(ch, 0.0))) for l, r in zip(L, R))
                dp = None
                basis = 'side-specific source amplitudes: measured-minus-commanded errors compared; positions not mirror-comparable'
            mirror[tid[:-5]] = {'max_angle_difference_deg': da, 'max_mirrored_distal_marker_difference_m': dp, 'basis': basis,
                                'status': 'PASS' if da <= INTEGRITY['mirror_angle_deg'] and (dp is None or dp <= INTEGRITY['mirror_position_m']) else 'FAIL'}
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {'schema_version': 1, 'phase': 9,
              'scope': 'Isolated bone-only sweeps on the fitted master: implementation integrity of commands, JCS measurement, centres, continuity and symmetry. Not an anatomical acceptance; contact mechanics, translations and follower couplings are not exercised.',
              'provenance': {'source_blend': rel(src), 'source_sha256': src_hash, 'source_sha256_after': sha(src), 'fit_record': rel(o.record),
                             'test_blend': rel(out_blend), 'test_blend_sha256': authored_hash, 'test_blend_sha256_after_measurement': after_hash,
                             'frame_restored': restored, 'blender_version': bpy.app.version_string, 'fps': fps,
                             'scripts': {rel(p): sha(p) for p in (Path(__file__), HERE / 'isolated_tests.py', HERE / 'joint_solver.py')}},
              'integrity_thresholds': INTEGRITY, 'couplings': it.js.FOLLOWER_COUPLINGS,
              'summary': summary, 'mirror': mirror,
              'counts': {'tests': len(summary), 'integrity_pass': sum(1 for s in summary.values() if s['integrity_status'] == 'PASS'),
                         'mirror_pairs': len(mirror), 'mirror_pass': sum(1 for m in mirror.values() if m['status'] == 'PASS')},
              'character_accepted': False, 'completed_tracker_gates': []}
    with (out_dir / 'isolated_report.json').open('x') as f:
        json.dump(report, f, indent=1, default=float)
    with (out_dir / 'isolated_samples.json').open('x') as f:
        json.dump(results, f, default=float)
    print('tests', report['counts'])
    for tid, s in summary.items():
        if s['integrity_status'] != 'PASS':
            print('FAIL', tid, {k: s[k] for k in ('max_abs_error_deg', 'max_uncommanded_jcs_deg', 'max_centre_drift_m', 'max_off_axis_deg', 'continuity_max_second_difference_mismatch_deg', 'distal_marker_radius_range_m')}, s['commanded_reversal_frames'], s['measured_reversal_frames'])
    for k, m in mirror.items():
        if m['status'] != 'PASS':
            print('MIRROR FAIL', k, m)


if __name__ == '__main__':
    main()
