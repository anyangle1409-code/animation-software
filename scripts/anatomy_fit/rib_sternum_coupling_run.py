#!/usr/bin/env python3
"""Phase 9 rib-sternum coupled breathing run: plan (python3) -> key + capture (bpy) -> compare (python3).

  python3    rib_sternum_coupling_run.py plan    --record R.json --out PLAN.json
  python3.13 rib_sternum_coupling_run.py key     --blend SRC.blend --plan PLAN.json --out-blend NEW.blend --capture CAP.json
  python3    rib_sternum_coupling_run.py compare --record R.json --plan PLAN.json --capture CAP.json --source-blend SRC.blend --out-dir RUN

The key step opens the candidate blend (never saved in place), keys ribs 1-10 and the sternum from the planned world
transforms on frames 1..N, saves a NEW test blend, re-opens it in the same process and captures evaluated bone ends and
joint-marker centres per frame. The compare step checks implementation integrity (captured vs planned), costovertebral
drift, costal-cartilage change from captured markers, mirror symmetry and continuity, and writes the run report. The
clavicles are children of the sternum, so the girdle is carried rigidly in this illustration (shoulder response to
breathing not modelled). Thresholds are implementation-integrity checks, not anatomical tolerances.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
MOVED = [f'rib_{n:02d}_{s}' for n in range(1, 11) for s in ('left', 'right')] + ['sternum']
INTEGRITY = {'bone_end_error_m': 1e-5, 'costovertebral_drift_m': 1e-6, 'mirror_m': 1e-5}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def plan(o):
    import numpy as np
    import rib_sternum_coupling as rs
    rec = json.loads(Path(o.record).read_text())
    amp = rs.amplitude()
    frames = []
    for i, th in enumerate(rs.series(amp)):
        T, met = rs.coupled_pose(rec, th)
        G = {}
        for b in MOVED:
            R, off = T[b]
            M = np.eye(4); M[:3, :3] = R; M[:3, 3] = off / 1000.0       # world metres
            G[b] = M.tolist()
        frames.append({'frame': i + 1, 'theta_deg': th, 'world_transforms': G, 'metrics': met})
    Path(o.out).write_text(json.dumps({'record': o.record, 'record_sha256': sha(o.record), 'amplitude_deg': amp,
                                       'amplitude_basis': 'TEST AMPLITUDE: Beyer 2014 smallest level mean of the two major components (FRC-TLC), as the isolated rib tests',
                                       'frames': frames}) + '\n')
    print('planned', len(frames))


def key(o):
    import bpy
    from mathutils import Matrix
    P = json.loads(Path(o.plan).read_text())
    src = Path(o.blend).resolve(); before = sha(src)
    out_blend = Path(o.out_blend).resolve()
    if out_blend.exists():
        raise FileExistsError(out_blend)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    for f in P['frames']:
        for b, M in f['world_transforms'].items():
            pb = arm.pose.bones['anat_' + b]
            pb.rotation_mode = 'QUATERNION'
            R0 = arm.matrix_world @ pb.bone.matrix_local
            pb.matrix_basis = R0.inverted() @ Matrix(M) @ R0
            pb.keyframe_insert('location', frame=f['frame']); pb.keyframe_insert('rotation_quaternion', frame=f['frame'])
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, len(P['frames'])
    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    bpy.ops.wm.open_mainfile(filepath=str(out_blend))
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']; sc = bpy.context.scene
    want_m = [f'{k}_{n:02d}_{s}' for k in ('costovertebral', 'costochondral', 'sternocostal') for n in range(1, 11) for s in ('left', 'right')] + \
             [f'interchondral_{n}_{n + 1}_{s}' for n in range(6, 10) for s in ('left', 'right')] + \
             [f'sternoclavicular_{s}' for s in ('left', 'right')] + ['manubriosternal', 'xiphisternal']
    markers = {ob['hgpt_joint_id']: ob for ob in bpy.data.objects if ob.name.startswith('HGPT_JOINT_') and ob['hgpt_joint_id'] in want_m}
    cap = []
    for f in P['frames']:
        sc.frame_set(f['frame']); bpy.context.view_layer.update()
        mw = arm.matrix_world
        bones = {b: {'head_m': list(mw @ arm.pose.bones['anat_' + b].head), 'tail_m': list(mw @ arm.pose.bones['anat_' + b].tail)} for b in MOVED}
        cap.append({'frame': f['frame'], 'bones': bones, 'markers': {k: list(ob.matrix_world.translation) for k, ob in markers.items()}})
    sc.frame_set(1)
    Path(o.capture).write_text(json.dumps({'test_blend': str(out_blend), 'test_blend_sha256': sha(out_blend), 'source_blend': str(src),
                                           'source_sha256_before': before, 'source_sha256_after': sha(src),
                                           'blender': bpy.app.version_string, 'frames': cap}) + '\n')
    print('captured', len(cap))


def compare(o):
    import numpy as np
    rec = json.loads(Path(o.record).read_text()); P = json.loads(Path(o.plan).read_text()); C = json.loads(Path(o.capture).read_text())
    out = Path(o.out_dir); out.mkdir(parents=True, exist_ok=True)
    B0, J0 = rec['bones'], rec['joint_markers']
    err_b, drift, mirror, cart, sternum, cont = 0.0, 0.0, 0.0, [], [], []
    prev = None
    for f, c in zip(P['frames'], C['frames']):
        for b, M in f['world_transforms'].items():
            M = np.array(M)
            for e in ('head_m', 'tail_m'):
                exp = M[:3, :3] @ np.array(B0[b][e]) + M[:3, 3]
                err_b = max(err_b, float(np.linalg.norm(exp - np.array(c['bones'][b][e]))))
        mk = {k: np.array(v) for k, v in c['markers'].items()}
        for s in ('left', 'right'):
            for n in range(1, 11):
                drift = max(drift, float(np.linalg.norm(mk[f'costovertebral_{n:02d}_{s}'] - np.array(J0[f'costovertebral_{n:02d}_{s}']['centre_m']))))
                link = f'sternocostal_{n:02d}_{s}' if n <= 7 else f'interchondral_{n - 1}_{n}_{s}'
                v0 = np.array(J0[link]['centre_m']) - np.array(J0[f'costochondral_{n:02d}_{s}']['centre_m'])
                v1 = mk[link] - mk[f'costochondral_{n:02d}_{s}']
                cart.append((float(np.linalg.norm(v1 - v0)) * 1000, f['frame'], link))
        for b in [x for x in f['world_transforms'] if x.endswith('_left')]:   # motion symmetry: displacement from rest, mirrored
            br = b[:-5] + '_right'
            dl = np.array(c['bones'][b]['tail_m']) - np.array(B0[b]['tail_m'])
            dr = np.array(c['bones'][br]['tail_m']) - np.array(B0[br]['tail_m'])
            mirror = max(mirror, float(np.linalg.norm(dl * [-1, 1, 1] - dr)))
        st = np.array(c['bones']['sternum']['head_m']) - np.array(B0['sternum']['head_m'])
        sternum.append({'frame': f['frame'], 'theta_deg': round(f['theta_deg'], 4), 'IJ_displacement_mm': [round(float(x) * 1000, 3) for x in st],
                        'sternum_x_mm': round(float(np.array(c['bones']['sternum']['head_m'])[0]) * 1000, 6)})
        if prev is not None:
            cont.append(abs(f['theta_deg'] - prev))
        prev = f['theta_deg']
    peak = max(P['frames'], key=lambda f: f['theta_deg'])
    pm = peak['metrics']
    ok = err_b <= INTEGRITY['bone_end_error_m'] and drift <= INTEGRITY['costovertebral_drift_m'] and mirror <= INTEGRITY['mirror_m'] \
        and C['source_sha256_before'] == C['source_sha256_after']
    rep = {
        'schema_version': 1, 'phase': 9, 'test': 'rib_sternum_coupled_inspiration',
        'scope': 'Implementation integrity of the coupled pump-handle rib/sternum solver in Blender; not anatomical acceptance; bucket-handle, cartilage elasticity and shoulder response not modelled',
        'provenance': {'record': o.record, 'record_sha256': sha(o.record), 'source_blend': o.source_blend, 'source_sha256_before': C['source_sha256_before'],
                       'source_sha256_after': C['source_sha256_after'], 'test_blend_sha256': C['test_blend_sha256'], 'blender': C['blender'],
                       'scripts': {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), HERE / 'rib_sternum_coupling.py')}},
        'amplitude_deg': P['amplitude_deg'], 'amplitude_basis': P['amplitude_basis'], 'frames': len(P['frames']),
        'integrity_thresholds': INTEGRITY,
        'results': {'max_bone_end_error_m': err_b, 'max_costovertebral_drift_m': drift, 'max_mirror_displacement_error_m': mirror, 'mirror_basis': 'mirrored left vs right displacement from rest (a003 rest ribs carry an inherited ~0.04 mm asymmetry)',
                    'max_costal_link_change_mm': round(max(x[0] for x in cart), 3), 'worst_link': max(cart)[2],
                    'peak_solver_metrics': pm, 'max_theta_step_deg': round(max(cont), 4),
                    'sternum_direction_at_peak': {'superior': pm['sternum_dz_mm'] > 0, 'anterior': pm['sternum_dy_mm'] < 0,
                                                  'reading': 'textbook pump-handle: sternum rises and moves anteriorly in inspiration (direction emerges from the solve)'}},
        'sternum_path': sternum,
        'integrity_status': 'PASS' if ok else 'FAIL',
        'frames_for_clips': [1, len(P['frames'])],
    }
    (out / 'rib_sternum_report.json').write_text(json.dumps(rep, indent=1) + '\n')
    (out / 'clip_report.json').write_text(json.dumps({'summary': {'rib_sternum_coupled_inspiration': {'frames': [1, len(P['frames'])]}}}) + '\n')
    print(json.dumps({k: rep['results'][k] for k in ('max_bone_end_error_m', 'max_costovertebral_drift_m', 'max_mirror_displacement_error_m', 'max_costal_link_change_mm', 'sternum_direction_at_peak')}, indent=1), rep['integrity_status'])


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan'); p.add_argument('--record', required=True); p.add_argument('--out', required=True)
    k = sub.add_parser('key')
    for a in ('--blend', '--plan', '--out-blend', '--capture'):
        k.add_argument(a, required=True)
    c = sub.add_parser('compare')
    for a in ('--record', '--plan', '--capture', '--source-blend', '--out-dir'):
        c.add_argument(a, required=True)
    o = ap.parse_args(argv)
    {'plan': plan, 'key': key, 'compare': compare}[o.cmd](o)


if __name__ == '__main__':
    main()
