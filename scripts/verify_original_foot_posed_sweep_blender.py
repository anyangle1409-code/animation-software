#!/usr/bin/env python3
"""Posed foot deformation sweep for ORIGINAL_v1 foot candidates (bpy; read-only).

Runtime controls are rotated about their local X on both sides (F-SIDE-001 mirrored rest frames): foot_* from -30 to
+20 deg and toe_* from -50 (toe-off dorsiflexion: negative local X lifts the toes) to +30 deg.  In the foot region
(|x| > 20 mm, z < 160 mm at rest) every pose reports: faces with area ratio < 0.1 (collapse) and > 2 (stretch), min/max
area ratio, and self-intersecting face pairs (BVH overlap, no shared vertex).  Forward kinematics with the leg fixed:
no ground contact, IK or gait claim.

  python3.13 verify_original_foot_posed_sweep_blender.py --blend B.blend [--blend C.blend ...] --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
POSES = [('foot', a) for a in (-30, -15, 10, 20)] + [('toe', a) for a in (-50, -30, 30)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def area(V, f):
    a, b, c = V[f[0]], V[f[1]], V[f[2]]
    return (b - a).cross(c - a).length / 2


def evaluated(body):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    V = [ev.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


def sweep(path):
    bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()))
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    V0, F = evaluated(body)
    if any(len(f) != 3 for f in F):
        raise RuntimeError('triangulated body required')
    foot_v = {i for i, p in enumerate(V0) if abs(p.x) > 0.02 and p.z < 0.16}
    faces = [i for i, f in enumerate(F) if all(v in foot_v for v in f)]
    fset = set(faces)
    rows = {}
    for bone, ang in POSES:
        for pb in rig.pose.bones:
            pb.rotation_euler = (0, 0, 0)
        for sfx in ('l', 'r'):
            rig.pose.bones[f'{bone}_{sfx}'].rotation_euler = (math.radians(ang), 0, 0)
        bpy.context.view_layer.update()
        V, _ = evaluated(body)
        r = [area(V, F[i]) / area(V0, F[i]) for i in faces if area(V0, F[i]) > 1e-12]
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and (a in fset or b in fset) and not (set(F[a]) & set(F[b]))]
        rows[f'{bone}_{ang:+d}'] = {'collapse_lt_0_1': sum(x < 0.1 for x in r), 'stretch_gt_2': sum(x > 2 for x in r),
                                    'area_ratio_min': round(min(r), 4), 'area_ratio_max': round(max(r), 4),
                                    'self_intersecting_pairs': len(pairs)}
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    return {'blend': Path(path).name, 'sha256': sha(path), 'foot_faces': len(faces), 'poses': rows}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--blend', action='append', required=True)
    ap.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    out = {'schema_version': 1, 'scope': 'FK sweep, leg fixed; diagnostic, not gait/deformation acceptance',
           'results': [sweep(p) for p in o.blend]}
    Path(o.out).write_text(json.dumps(out, indent=1) + '\n')
    for r in out['results']:
        print(r['blend'], json.dumps({k: (v['collapse_lt_0_1'], v['stretch_gt_2'], v['area_ratio_min'], v['self_intersecting_pairs'])
                                      for k, v in r['poses'].items()}))


if __name__ == '__main__':
    main()
