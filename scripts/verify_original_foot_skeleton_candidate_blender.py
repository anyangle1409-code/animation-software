#!/usr/bin/env python3
"""Verify the ORIGINAL_v1 foot skeleton-revision candidate (C3) against its parent (bpy; read-only on both files).

FAIL conditions:
  * topology, vertex groups, any weight, modifiers or object transforms differ;
  * any master bone outside the feet, or any runtime bone other than foot_l/r and toe_l/r, differs;
  * the runtime foot_* heads (ankle) or the talus head / tibia / fibula stations move;
  * any vertex moved outside the foot region (|x| > 20 mm, z < 130 mm);
  * shape-key relative deltas change; asymmetry > 1e-6 m;
  * any foot bone station (head/tail of every tarsal, metatarsal and phalanx, both feet) lies outside the skin;
  * the neutral foot length, ball-of-foot length or heel position miss their targets by > 1 mm;
  * the lowest body point is below the parent's, or any toe floats > 1 mm in neutral.
Reported (not pass/fail): bone lengths before/after, posed min-z and toe/foot area-ratio extremes for runtime toe
+/-30 deg and foot +20/-30 deg about local X (both sides) vs the parent in the same poses.

  python3.13 verify_original_foot_skeleton_candidate_blender.py --parent A003.blend --candidate C3.blend --out JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
MASTER = 'HGPT_ANATOMICAL_MASTER'
FOOT = {'talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cuneiform', 'intermediate_cuneiform', 'lateral_cuneiform'} | \
    {f'metatarsal_{k}' for k in range(1, 6)} | {'hallux_proximal_phalanx', 'hallux_distal_phalanx'} | \
    {f'toe{k}_{s}_phalanx' for k in range(2, 6) for s in ('proximal', 'middle', 'distal')}
ANSUR_FOOT, ANSUR_BALL = 279.9, 207.4


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def base(n):
    n = n[5:] if n.startswith('anat_') else n
    for s in ('_left', '_right'):
        if n.endswith(s):
            return n[:-len(s)]
    return n


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()))
    body, rig, master = (bpy.data.objects[n] for n in (BODY, RIG, MASTER))
    me = body.data
    d = {'faces': [tuple(p.vertices) for p in me.polygons], 'groups': [g.name for g in body.vertex_groups],
         'weights': [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices],
         'co': [tuple(body.matrix_world @ v.co) for v in me.vertices],
         'keys': {kb.name: [tuple(x.co) for x in kb.data] for kb in me.shape_keys.key_blocks},
         'mods': [(m.name, m.type, getattr(m, 'object', None) and m.object.name) for m in body.modifiers],
         'matrix': [tuple(r) for r in body.matrix_world],
         'master': {b.name: (tuple(b.head_local), tuple(b.tail_local)) for b in master.data.bones},
         'rig': {b.name: (tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones},
         'ajc': tuple(bpy.data.objects['LM_tibia_left__AJC'].matrix_world.translation)}
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    inside = {}
    for n, (h, t) in d['master'].items():
        if base(n) in FOOT:
            for end, p in (('head', h), ('tail', t)):
                hits, o = 0, Vector(p)
                for _ in range(64):
                    loc, *_ = bvh.ray_cast(o, Vector((0, 0, 1)))
                    if loc is None:
                        break
                    hits += 1; o = loc + Vector((0, 0, 1e-6))
                inside[f'{n}:{end}'] = hits % 2 == 1
    d['inside'] = inside
    d['posed'] = {}
    for pname, (bone, ang) in {'toe_+30': ('toe', 30), 'toe_-30': ('toe', -30), 'foot_+20': ('foot', 20), 'foot_-30': ('foot', -30)}.items():
        for pb in rig.pose.bones:
            pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
        for sfx in ('l', 'r'):
            rig.pose.bones[f'{bone}_{sfx}'].rotation_euler = (math.radians(ang), 0, 0)
        bpy.context.view_layer.update()
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); em = ev.to_mesh()
        d['posed'][pname] = [tuple(ev.matrix_world @ v.co) for v in em.vertices]
        ev.to_mesh_clear()
    return d


def area(P, f):
    a, b, c = (Vector(P[i]) for i in f[:3])
    return (b - a).cross(c - a).length / 2


def foot_measures(d):
    P = d['co']; zmin = min(p[2] for p in P)
    F = [p for p in P if p[0] > 0.02 and p[2] < zmin + 0.16]
    heel = max(p[1] for p in F); tip = min(p[1] for p in F)
    mtp1 = d['master']['anat_metatarsal_1_left'][1]
    toes = [p for p in F if p[1] < mtp1[1] - 0.025]
    return {'length_mm': round((heel - tip) * 1000, 3), 'breadth_mm': round((max(p[0] for p in F) - min(p[0] for p in F)) * 1000, 3),
            'heel_to_MTP1_station_mm': round((heel - mtp1[1]) * 1000, 3), 'heel_behind_AJC_mm': round((heel - d['ajc'][1]) * 1000, 3),
            'lowest_toe_skin_mm': round(min(p[2] for p in toes) * 1000, 3), 'body_min_z_mm': round(zmin * 1000, 4)}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--parent', '--candidate', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--heel-behind-ajc-mm', type=float, default=60.0)
    o = ap.parse_args(argv)
    A, C = load(o.parent), load(o.candidate)
    res, fails = {'parent_sha256': sha(o.parent), 'candidate_sha256': sha(o.candidate)}, []
    prot = {k: A[k] == C[k] for k in ('faces', 'groups', 'weights', 'mods', 'matrix')}
    res['protected_identical'] = prot
    fails += [f'protected changed: {k}' for k, v in prot.items() if not v]
    mchg = sorted(n for n in A['master'] if A['master'][n] != C['master'][n])
    bad = [n for n in mchg if base(n) not in FOOT or (base(n) == 'talus' and A['master'][n][0] != C['master'][n][0])]
    res['master_bones_changed'] = len(mchg); res['master_bones_changed_outside_rule'] = bad
    fails += [f'master bone changed outside the foot rule: {bad}'] if bad else []
    rchg = sorted(n for n in A['rig'] if A['rig'][n] != C['rig'][n])
    rbad = [n for n in rchg if n not in ('foot_l', 'foot_r', 'toe_l', 'toe_r')] + \
           [n for n in ('foot_l', 'foot_r') if A['rig'][n][0] != C['rig'][n][0]]
    res['runtime_bones_changed'] = rchg
    fails += [f'runtime change outside rule: {rbad}'] if rbad else []
    moved = [i for i, (a, c) in enumerate(zip(A['co'], C['co'])) if (Vector(a) - Vector(c)).length > 1e-9]
    out = [i for i in moved if not (abs(A['co'][i][0]) > 0.02 and A['co'][i][2] < 0.13)]
    res['moved_vertices'] = len(moved); res['moved_outside_foot_region'] = len(out)
    fails += [f'{len(out)} vertices moved outside the foot region'] if out else []
    kd = 0.0
    for name in A['keys']:
        for i in moved:
            kd = max(kd, ((Vector(A['keys'][name][i]) - Vector(A['keys']['Basis'][i])) -
                          (Vector(C['keys'][name][i]) - Vector(C['keys']['Basis'][i]))).length)
    res['shape_key_relative_delta_max_change_m'] = kd
    fails += ['shape-key deltas changed'] if kd > 1e-6 else []
    tree = KDTree(len(A['co']))
    for i, p in enumerate(A['co']):
        tree.insert(Vector(p), i)
    tree.balance()
    sym = 0.0
    for i in moved:
        _, j, _ = tree.find(Vector((-A['co'][i][0], A['co'][i][1], A['co'][i][2])))
        c, m = C['co'][i], C['co'][j]
        sym = max(sym, (Vector((-c[0], c[1], c[2])) - Vector(m)).length)
    res['symmetry_max_m'] = sym
    fails += [f'asymmetry {sym}'] if sym > 1e-6 else []
    res['containment'] = {'stations': len(C['inside']), 'parent_outside': sorted(k for k, v in A['inside'].items() if not v),
                          'candidate_outside': sorted(k for k, v in C['inside'].items() if not v)}
    fails += [f"stations outside the skin: {res['containment']['candidate_outside']}"] if res['containment']['candidate_outside'] else []
    ma, mc = foot_measures(A), foot_measures(C)
    res['neutral_plusX_foot'] = {'parent': ma, 'candidate': mc,
                                 'targets': {'length_mm': ANSUR_FOOT, 'heel_behind_AJC_mm': o.heel_behind_ajc_mm, 'ball_of_foot_ANSUR_mm': ANSUR_BALL}}
    if abs(mc['length_mm'] - ANSUR_FOOT) > 1.0:
        fails.append('foot length off target')
    if abs(mc['heel_behind_AJC_mm'] - o.heel_behind_ajc_mm) > 1.0:
        fails.append('heel position off target')
    if abs(mc['heel_to_MTP1_station_mm'] - ANSUR_BALL) > 1.0:
        fails.append('ball-of-foot (heel to MTP1 station) off target')
    if mc['body_min_z_mm'] < ma['body_min_z_mm'] - 1e-3:
        fails.append('body goes below the parent floor')
    if mc['lowest_toe_skin_mm'] > 1.0:
        fails.append('toes float in neutral')
    res['bone_lengths_mm_left'] = {base(n): [round((Vector(A['master'][n][1]) - Vector(A['master'][n][0])).length * 1000, 2),
                                             round((Vector(C['master'][n][1]) - Vector(C['master'][n][0])).length * 1000, 2)]
                                   for n in sorted(A['master']) if base(n) in FOOT and n.endswith('_left')}
    posed = {}
    foot_i = [i for i, p in enumerate(A['co']) if abs(p[0]) > 0.02 and p[2] < 0.16]
    ff = [f for f in A['faces'] if all(abs(A['co'][i][0]) > 0.02 and A['co'][i][2] < 0.12 for i in f)]
    for pname in A['posed']:
        row = {}
        for lab, D in (('parent', A), ('candidate', C)):
            r = [area(D['posed'][pname], f) / area(D['co'], f) for f in ff if area(D['co'], f) > 1e-12]
            row[lab] = {'foot_min_z_mm': round(min(D['posed'][pname][i][2] for i in foot_i) * 1000, 3),
                        'foot_area_ratio_min_max': [round(min(r), 4), round(max(r), 4)]}
        posed[pname] = row
    res['posed_local_X_rotations'] = posed
    res['fails'] = fails; res['verdict'] = 'PASS' if not fails else 'FAIL'
    Path(o.out).write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'bone_lengths_mm_left'}, indent=1))
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()
