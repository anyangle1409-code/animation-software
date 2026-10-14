#!/usr/bin/env python3
"""ORIGINAL_v1 foot C5 (Claude, 14 Oct 2026): plantar heel brought to the floor (provisional; parent C4).

Defect (present in the frozen a003 and inherited by C3/C4): in the neutral standing pose no heel skin behind the
ankle-joint centre (AJC) touches the floor.  On true plane sections the plantar contour is lowest just in FRONT of the
AJC (1.2 mm at AJC-10 mm) and rises behind it (C4: 9.9 mm at +20, 19.3 mm at +40, 27.9 mm at +50 mm), so the standing
foot rocks on its midfoot/forefoot.  A standing human foot bears weight on the heel under the calcaneal tuberosity and
on the first and fifth metatarsal heads (the plantar "tripod"); the heel pad lies between the tuberosity and the floor.

Change (z only, mesh-only; x/y never change; topology, weights, rigs and the 206-bone master untouched; mirrored; every
shape key gets the same delta):
  * target plantar profile T(y): 0 (floor) from FLAT_START (AJC - 10 mm) to FLAT_END = heel back - ROUND_R, then a
    circular round-off of radius ROUND_R up to the heel back;
  * per 0.5 mm y the current lowest point L(y) of the true section is found; where L(y) > T(y) the whole section is
    lowered rigidly by L(y) - T(y) with a vertical fade: full up to L(y) + Z_FULL, zero at L(y) + Z_ZERO, so the heel
    pad thickens and the calcaneus stays inside the skin;
  * the move is blended in over BLEND behind FLAT_START so there is no step at the midfoot.
Checks: fingerprint, only foot z changed (downwards), exact mirror, stations inside, no new self-intersection, no
reversed triangle, area ratios, floor not penetrated, heel contact present.

  python3.13 build_original_foot_heel_contact_blender.py --blend C4.blend --expect-sha SHA --out C5.blend --report JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_original_foot_c4_candidate_blender as c4  # noqa: E402

FLAT_START = -0.010            # relative to the AJC (posterior is +y)
ROUND_R = 0.035              # 22 mm left a boxy heel corner; 45 mm lifted the pad off the floor (measured, sheets)
BLEND = 0.012
Z_FULL, Z_ZERO = 0.015, 0.060
STEP = 0.0005


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def section_low(V, E, y0):
    zs = []
    for a, b in E:
        pa, pb = V[a], V[b]
        if pa.x < 0.02 and pb.x < 0.02:
            continue
        if (pa.y - y0) * (pb.y - y0) < 0:
            t = (y0 - pa.y) / (pb.y - pa.y); zs.append(pa.z + (pb.z - pa.z) * t)
    return min(zs) if zs else None


def contact_zones(V, ajc_y, y_ball, x_mid, tol=0.002):
    floor = min(v.z for v in V)
    c = [v for v in V if v.x > 0.02 and v.z - floor < tol]
    return {'heel': sum(v.y > ajc_y for v in c),
            'midfoot_lateral': sum(y_ball + 0.02 < v.y <= ajc_y and v.x > x_mid for v in c),
            'midfoot_medial_arch': sum(y_ball + 0.02 < v.y <= ajc_y and v.x <= x_mid for v in c),
            'metatarsal_heads': sum(y_ball - 0.02 <= v.y <= y_ball + 0.02 for v in c),
            'toes': sum(v.y < y_ball - 0.02 for v in c)}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--expect-sha', '--out', '--report'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    if Path(o.out).exists():
        raise FileExistsError(o.out)
    parent_sha = hashlib.sha256(Path(o.blend).read_bytes()).hexdigest()
    if parent_sha != o.expect_sha:
        raise SystemExit(f'parent SHA mismatch {parent_sha}')
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    body = bpy.data.objects[c4.BODY]; me = body.data; master = bpy.data.objects[c4.MASTER]
    assert body.matrix_world.is_identity
    P = [v.co.copy() for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    E = [tuple(e.vertices) for e in me.edges]
    fingerprint = (F, [g.name for g in body.vertex_groups], [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    st = c4.stations(master)
    heads = [st[f'metatarsal_{k}_left:tail'] for k in range(1, 6)]
    y_ball = sum(h.y for h in heads) / 5.0
    ajc_y = bpy.data.objects['LM_tibia_left__AJC'].matrix_world.translation.y
    floor = min(p.z for p in P)
    foot = [i for i, p in enumerate(P) if p.x > 0.02 and p.z < 0.12]
    heel_back = max(P[i].y for i in foot if P[i].z < 0.10)
    y0, y1 = ajc_y + FLAT_START - BLEND, heel_back
    flat_end = heel_back - ROUND_R

    def target(y):
        if y <= flat_end:
            return floor
        u = min(y - flat_end, ROUND_R)
        return floor + ROUND_R - math.sqrt(ROUND_R ** 2 - u ** 2)
    ys = [y0 + n * STEP for n in range(int((y1 - y0) / STEP) + 1)]
    low = {round(y, 6): section_low(P, E, y) for y in ys}
    drop = {}
    for y in ys:
        L = low[round(y, 6)]
        if L is None:
            continue
        ramp = smooth((y - y0) / BLEND)                      # 0 at FLAT_START - BLEND, 1 from FLAT_START
        drop[round(y, 6)] = (L, ramp * max(0.0, L - target(y)))

    def lookup(y):
        k = round(y0 + round((y - y0) / STEP) * STEP, 6)
        return drop.get(k)
    D = {}
    for i in foot:
        p = P[i]
        if p.y < y0 or p.y > y1:
            continue
        r = lookup(p.y)
        if not r or r[1] <= 0:
            continue
        L, d = r
        w = 1.0 - smooth((p.z - (L + Z_FULL)) / (Z_ZERO - Z_FULL))
        if w > 0:
            D[i] = max(floor, p.z - d * w) - p.z          # never below the floor (sections interpolate between vertices)
    kd = KDTree(len(P))
    for i, p in enumerate(P):
        kd.insert(p, i)
    kd.balance()
    full, worst = {}, 0.0
    for i, d in D.items():
        _, j, dist = kd.find(Vector((-P[i].x, P[i].y, P[i].z)))
        worst = max(worst, dist); full[i] = d; full[j] = d
    assert worst < 1e-6, worst
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in full.items():
        me.vertices[i].co.z += d
        for kb in keys:
            kb.data[i].co.z += d
    me.update(); bpy.context.view_layer.update()
    Q = [v.co.copy() for v in me.vertices]
    c = {}
    c['topology_groups_weights_unchanged'] = fingerprint == (F, [g.name for g in body.vertex_groups],
                                                             [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    c['only_foot_z_lowered'] = all(Q[i].x == P[i].x and Q[i].y == P[i].y and Q[i].z <= P[i].z for i in range(len(P))) and \
        all(abs(P[i].x) > 0.02 and P[i].z < 0.12 for i in full)
    c['mirror_map_max_error_m'] = worst
    c['symmetry_max_m'] = max(abs(Q[i].z - Q[kd.find(Vector((-P[i].x, P[i].y, P[i].z)))[1]].z) for i in full)
    c['foot_stations_outside_skin'] = c4.inside_all(body, st)
    flips, ratios = 0, []
    for f in F:
        if not any(i in full for i in f):
            continue
        a0 = (P[f[1]] - P[f[0]]).cross(P[f[2]] - P[f[0]]); a1 = (Q[f[1]] - Q[f[0]]).cross(Q[f[2]] - Q[f[0]])
        flips += a0.dot(a1) <= 0
        if a0.length > 1e-12:
            ratios.append(a1.length / a0.length)
    c['reversed_triangles'] = flips
    c['area_ratio_range'] = [round(min(ratios), 4), round(max(ratios), 4)]

    def foot_pairs(V):
        sub = [f for f in F if all(abs(V[i].x) > 0.02 and V[i].z < 0.12 for i in f)]
        t = BVHTree.FromPolygons(V, sub, all_triangles=True); fs = [set(f) for f in sub]
        return sum(1 for a, b in t.overlap(t) if a < b and not (fs[a] & fs[b]))
    c['foot_self_intersecting_pairs'] = [foot_pairs(P), foot_pairs(Q)]
    c['lowest_point_mm'] = [round(floor * 1000, 3), round(min(q.z for q in Q) * 1000, 3)]
    prof = lambda V: [(d, round((section_low(V, E, ajc_y + d / 1000) - floor) * 1000, 1)) for d in range(-20, int((heel_back - ajc_y) * 1000), 10)]
    c['plantar_profile_mm_vs_AJC'] = {'before': prof(P), 'after': prof(Q)}
    x_mid = heads[2].x
    c['contact_vertices_within_2mm'] = {'before': contact_zones(P, ajc_y, y_ball, x_mid), 'after': contact_zones(Q, ajc_y, y_ball, x_mid)}
    c['max_drop_mm'] = round(-min(full.values()) * 1000, 2) if full else 0.0
    ok = (c['topology_groups_weights_unchanged'] and c['only_foot_z_lowered'] and c['symmetry_max_m'] < 1e-6
          and not c['foot_stations_outside_skin'] and flips == 0 and c['area_ratio_range'][0] > 0.5
          and c['foot_self_intersecting_pairs'][1] <= c['foot_self_intersecting_pairs'][0]
          and c['lowest_point_mm'][1] >= c['lowest_point_mm'][0] - 1e-6
          and c['contact_vertices_within_2mm']['after']['heel'] > 0)
    c['verdict'] = 'PASS' if ok else 'FAIL'
    rep = {'schema_version': 1, 'stage': 'ORIGINAL_V1_FOOT_HEEL_CONTACT_C5_CLAUDE', 'status': 'PROVISIONAL_DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
           'parent': {'path': Path(o.blend).name, 'sha256': parent_sha},
           'evidence': 'standing foot bears weight on the heel (calcaneal tuberosity) and first/fifth metatarsal heads; no numeric heel-pad target used',
           'parameters': {'flat_start_rel_ajc_m': FLAT_START, 'round_radius_m': ROUND_R, 'blend_m': BLEND, 'z_full_m': Z_FULL, 'z_zero_m': Z_ZERO,
                          'heel_back_rel_ajc_mm': round((heel_back - ajc_y) * 1000, 1)},
           'changed_vertices': len(full), 'checks': c, 'shape_keys_updated': [kb.name for kb in keys]}
    print(json.dumps(rep, indent=1, default=str))
    if not ok:
        raise SystemExit('checks failed')
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    rep['output'] = {'path': Path(o.out).name, 'sha256': hashlib.sha256(Path(o.out).read_bytes()).hexdigest()}
    Path(o.report).write_text(json.dumps(rep, indent=1, default=str) + '\n')


if __name__ == '__main__':
    main()
