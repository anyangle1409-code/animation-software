#!/usr/bin/env python3
"""Verify an ORIGINAL_v1 foot-shape candidate against its parent (bpy; read-only on both files).

Checks (each reported with values; FAIL conditions explicit):
  protected   topology, vertex-group names and every (vertex, group, weight), both armatures' bone heads/tails/rolls/parents,
              object transforms, modifiers, shape-key names, and every vertex outside the declared forefoot box -> must be identical
  keys        relative shape-key deltas (key - basis) unchanged for every key and vertex
  symmetry    candidate vertex vs X-mirror partner
  floor       global minimum z; per-digit minimum z in neutral (both feet)
  length      heel-to-toe length and breadth per foot
  contain     206-bone foot stations (metatarsal and phalanx heads/tails) inside the closed body surface (ray parity),
              parent vs candidate
  stretch     triangle area ratio candidate/parent at rest in the changed region
  posed       runtime toe control rotated +/-30 deg and foot control +20/-30 deg about its local X (both sides, mirrored),
              evaluated through the armature: minimum z of the foot region and toe-region area-ratio extremes vs the same pose
              on the parent
Nothing is saved.

  python3.13 verify_original_foot_shape_candidate_blender.py --parent P.blend --candidate C.blend --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
MASTER = 'HGPT_ANATOMICAL_MASTER'
BOX_Y = -0.188          # forefoot box: |x| > 0.02, z < 0.07, y < BOX_Y (the builder's declared region plus margin)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()))
    body = bpy.data.objects[BODY]; me = body.data; rig = bpy.data.objects[RIG]; master = bpy.data.objects[MASTER]
    d = {'n_v': len(me.vertices), 'n_e': len(me.edges), 'n_f': len(me.polygons),
         'faces': [tuple(p.vertices) for p in me.polygons],
         'groups': [g.name for g in body.vertex_groups],
         'weights': [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices],
         'co': [tuple(body.matrix_world @ v.co) for v in me.vertices],
         'keys': {kb.name: [tuple(x.co) for x in kb.data] for kb in (me.shape_keys.key_blocks if me.shape_keys else [])},
         'mods': [(m.name, m.type, getattr(m, 'object', None) and m.object.name) for m in body.modifiers],
         'matrix': [tuple(r) for r in body.matrix_world],
         'rigs': {}}
    for arm in (rig, master):
        d['rigs'][arm.name] = {b.name: (tuple(b.head_local), tuple(b.tail_local), b.parent.name if b.parent else None,
                                        tuple(tuple(r) for r in b.matrix_local)) for b in arm.data.bones}
    mb = {b.name[5:] if b.name.startswith('anat_') else b.name: b for b in master.data.bones}
    st = {}
    for n, b in mb.items():
        if any(n.startswith(k) for k in ('metatarsal', 'hallux', 'toe')) and n.endswith(('_left', '_right')):
            st[n + ':head'] = tuple(master.matrix_world @ b.head_local); st[n + ':tail'] = tuple(master.matrix_world @ b.tail_local)
    d['stations'] = st
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body, dg)
    inside = {}
    for k, p in st.items():
        hits, o = 0, Vector(p)
        for _ in range(64):
            loc, nrm, idx, dist = bvh.ray_cast(o, Vector((0, 0, 1)))
            if loc is None:
                break
            hits += 1; o = loc + Vector((0, 0, 1e-6))
        inside[k] = hits % 2 == 1
    d['inside'] = inside
    # posed evaluations
    poses = {'toe_+30': ('toe', 30), 'toe_-30': ('toe', -30), 'foot_+20': ('foot', 20), 'foot_-30': ('foot', -30)}
    d['posed'] = {}
    for pname, (bone, ang) in poses.items():
        for pb in rig.pose.bones:
            pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
        for sfx in ('l', 'r'):
            rig.pose.bones[f'{bone}_{sfx}'].rotation_euler = (math.radians(ang), 0, 0)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(dg); em = ev.to_mesh()
        d['posed'][pname] = [tuple(ev.matrix_world @ v.co) for v in em.vertices]
        ev.to_mesh_clear()
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    return d


def tri_area(P, f):
    a, b, c = (Vector(P[i]) for i in f[:3])
    s = (b - a).cross(c - a).length / 2
    if len(f) == 4:
        d = Vector(P[f[3]]); s += (c - a).cross(d - a).length / 2
    return s


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--parent', '--candidate', '--out'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    hp, hc = sha(o.parent), sha(o.candidate)
    A = load(o.parent); C = load(o.candidate)
    fails, res = [], {'parent_sha256': hp, 'candidate_sha256': hc}
    same = lambda k: A[k] == C[k]
    prot = {k: same(k) for k in ('n_v', 'n_e', 'n_f', 'faces', 'groups', 'weights', 'mods', 'matrix', 'rigs', 'stations')}
    res['protected_identical'] = prot
    fails += [f'protected changed: {k}' for k, v in prot.items() if not v]
    inbox = lambda p: abs(p[0]) > 0.02 and p[2] < 0.07 and p[1] < BOX_Y
    moved = [i for i, (a, c) in enumerate(zip(A['co'], C['co'])) if (Vector(a) - Vector(c)).length > 1e-9]
    outside = [i for i in moved if not inbox(A['co'][i])]
    res['moved_vertices'] = len(moved); res['moved_outside_box'] = len(outside)
    if outside:
        fails.append(f'{len(outside)} vertices moved outside the forefoot box')
    kd = 0.0
    for name in A['keys']:
        if name not in C['keys']:
            fails.append(f'shape key {name} missing'); continue
        for i in moved:
            da = Vector(A['keys'][name][i]) - Vector(A['keys']['Basis'][i]) if 'Basis' in A['keys'] else Vector()
            dc = Vector(C['keys'][name][i]) - Vector(C['keys']['Basis'][i]) if 'Basis' in C['keys'] else Vector()
            kd = max(kd, (da - dc).length)
    res['shape_key_relative_delta_max_change_m'] = kd
    if kd > 1e-6:
        fails.append('shape-key relative deltas changed')
    from mathutils.kdtree import KDTree
    tree = KDTree(len(C['co']))
    for i, p in enumerate(A['co']):
        tree.insert(Vector(p), i)
    tree.balance()
    sym = 0.0
    for i in moved:
        _, j, _ = tree.find(Vector((-A['co'][i][0], A['co'][i][1], A['co'][i][2])))
        c, m = C['co'][i], C['co'][j]
        sym = max(sym, (Vector((-c[0], c[1], c[2])) - Vector(m)).length)
    res['symmetry_max_m'] = sym
    if sym > 1e-6:
        fails.append(f'asymmetry {sym}')

    def feet(P):
        out = {}
        zmin = min(p[2] for p in P)
        for side, sg in (('plusX', 1), ('minusX', -1)):
            F = [p for p in P if p[0] * sg > 0.02 and p[2] < zmin + 0.16]
            out[side] = {'length_mm': round((max(p[1] for p in F) - min(p[1] for p in F)) * 1000, 3),
                         'breadth_mm': round((max(p[0] for p in F) - min(p[0] for p in F)) * 1000, 3),
                         'toe_region_min_z_mm': round(min(p[2] for p in F if p[1] < -0.215) * 1000, 3)}
        out['global_min_z_mm'] = round(zmin * 1000, 4)
        return out
    res['neutral'] = {'parent': feet(A['co']), 'candidate': feet(C['co'])}
    res['containment'] = {'parent_outside': sorted(k for k, v in A['inside'].items() if not v),
                          'candidate_outside': sorted(k for k, v in C['inside'].items() if not v)}
    newly = set(res['containment']['candidate_outside']) - set(res['containment']['parent_outside'])
    if newly:
        fails.append(f'stations newly outside the skin: {sorted(newly)}')
    faces = [f for f in A['faces'] if any(i in set(moved) for i in f)]
    ratios = [tri_area(C['co'], f) / tri_area(A['co'], f) for f in faces if tri_area(A['co'], f) > 1e-12]
    res['rest_area_ratio_changed_faces'] = {'n': len(ratios), 'min': round(min(ratios), 4), 'max': round(max(ratios), 4)}
    posed = {}
    for pname in A['posed']:
        PA, PC = A['posed'][pname], C['posed'][pname]
        foot = [i for i, p in enumerate(A['co']) if abs(p[0]) > 0.02 and p[2] < 0.16]
        fz = lambda P: min(P[i][2] for i in foot)
        toe_faces = [f for f in A['faces'] if all(A['co'][i][1] < -0.17 and abs(A['co'][i][0]) > 0.02 and A['co'][i][2] < 0.07 for i in f)]
        r = [tri_area(PC, f) / tri_area(C['co'], f) for f in toe_faces if tri_area(C['co'], f) > 1e-12]
        rp = [tri_area(PA, f) / tri_area(A['co'], f) for f in toe_faces if tri_area(A['co'], f) > 1e-12]
        posed[pname] = {'foot_min_z_mm_parent': round(fz(PA) * 1000, 3), 'foot_min_z_mm_candidate': round(fz(PC) * 1000, 3),
                        'toe_area_ratio_vs_rest_parent': [round(min(rp), 4), round(max(rp), 4)],
                        'toe_area_ratio_vs_rest_candidate': [round(min(r), 4), round(max(r), 4)]}
    res['posed_local_X_rotations'] = posed
    res['fails'] = fails
    res['verdict'] = 'PASS' if not fails else 'FAIL'
    Path(o.out).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items()}, indent=1)[:4000])
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()
