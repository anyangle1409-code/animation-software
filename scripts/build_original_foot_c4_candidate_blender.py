#!/usr/bin/env python3
"""ORIGINAL_v1 foot C4 (Claude, 14 Oct 2026): provisional development candidate built from C3 (279.9 mm skeleton).

Why C4 and not C3W: the C3W ball-breadth stage scaled x about each slice's foot centre with a weight that faded
along y.  Because the metatarsal-head line is oblique, every lesser toe received a different lateral shift at its
root than at its tip; that shear crumpled the little toes (visible in the C3W sole/three-quarter sheets, missed by its
pair-count check) and also moved toes 1 and 5 away from their unchanged phalanx stations.  C4 replaces it.

All changes are mesh-only (x only, y/z never change; topology, groups, weights, rigs and the 206-bone master are
untouched; every shape key gets the same delta) and are mirrored exactly to the other foot:

1. Toes, gap closing (relational, no invented toe dimensions).  The toes are separate tubes beyond the webs; the five
   tubes are the connected components of the forefoot skin anterior to Y_CUT, extended to the webs by multi-source
   geodesic growth over mesh edges (labels cannot jump across a gap).  In C3 the lesser toes are 9-12 mm wide and
   20-23 mm tall with 2.4-3.7 mm gaps.  Per 1 mm slice each toe's medial and lateral edges move apart independently
   (an affine x-map within the slice, so no shear along the toe) by half of each neighbouring gap minus TOE_GAP; the
   little toe's free lateral edge moves by the same amount as its medial edge; the hallux's medial edge does not move.
   The effect fades in over WEB_FADE behind each toe's web.
2. Ball breadth to the ANSUR II 1.82 m prediction (104.1 +/- 4.7 mm) by moving ONLY the skin medial of the first and
   lateral of the fifth metatarsal-head stations outwards (equal split), fading along y (ball line +-15 -> +-45 mm) and
   z (30 -> 70 mm), and excluded from the separate toe tubes with the same web fade as step 1.  The skin between those stations and every toe axis stay put, so toes remain on their stations.
3. Heel: NOT changed.  Measured on true plane sections, the C3 heel posterior to the malleoli (>= 15 mm behind the
   ankle-joint centre, any height) is 82.9 mm across at its widest (+1.75 SD), 75-81 mm at 20-30 mm behind the AJC,
   against ANSUR II 1.82 m 73.7 +/- 5.3 mm: not narrow; the exact value is landmark-sensitive, so it is left as is.  The earlier "58-61 mm, narrow heel" figures (C3W doc) came from
   vertex extents below 40 mm on a sparsely sampled heel and are withdrawn.  The ANSUR landmark wording itself was not
   retrievable here; the section definition is a disclosed assumption.

All breadths in C4 are measured on true plane sections (edge intersections), not on vertex extents.
Checks (all must pass; report): fingerprint unchanged, only x of foot-region vertices changed, exact mirror, foot
stations inside the skin, ball breadth on target, heel reported, toe gaps >= TOE_GAP_MIN, no reversed triangles and no new foot-region
self-intersections versus C3, minimum foot-region area ratio, lowest point and foot length unchanged.

  python3.13 build_original_foot_c4_candidate_blender.py --blend C3.blend --expect-sha SHA --out C4.blend --report JSON
"""
import argparse, hashlib, heapq, json, sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
MASTER = 'HGPT_ANATOMICAL_MASTER'
ANSUR_BREADTH, ANSUR_HEEL = 0.1041, 0.0737
Y_CUT, Y_GROW = -0.170, -0.150          # tubes are separate anterior of Y_CUT; labels grow back to Y_GROW
TOE_GAP, TOE_GAP_MIN = 0.0006, 0.0003
WEB_FADE = 0.008
GAP_WINDOW = 6                           # grid steps (0.5 mm) for the window-minimum gap
GRID = 0.0005
REF_BAND = (-0.195, -0.171)             # slices where the toe widths/gaps are measured
CORE, FADE, ZFULL, ZZERO = 0.015, 0.045, 0.030, 0.070
HEEL_RAMP, HEEL_ZFULL, HEEL_ZZERO = 0.020, 0.040, 0.080
SLICE = 0.001
BALL_SEARCH = 0.030                      # sections within +-30 mm of the mean metatarsal-head line
import os
STAGES = set(os.environ.get('C4_STAGES', 'toes,ball').split(','))   # diagnostics only; the candidate uses both


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def stations(master):
    keys = ('talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cun', 'intermediate_cun', 'lateral_cun', 'metatarsal', 'hallux', 'toe')
    out = {}
    for b in master.data.bones:
        n = b.name[5:] if b.name.startswith('anat_') else b.name
        if any(n.startswith(k) for k in keys):
            out[n + ':head'] = master.matrix_world @ b.head_local
            out[n + ':tail'] = master.matrix_world @ b.tail_local
    return out


def inside_all(body, pts):
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    bad = []
    for k, p in pts.items():
        hits, o = 0, Vector(p)
        for _ in range(64):
            loc, *_ = bvh.ray_cast(o, Vector((0, 0, 1)))
            if loc is None:
                break
            hits += 1; o = loc + Vector((0, 0, 1e-6))
        if hits % 2 == 0:
            bad.append(k)
    return bad


def components(ids, edges, P):
    S = set(ids); par = {i: i for i in S}

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for a, b in edges:
        if a in S and b in S:
            par[f(a)] = f(b)
    out = {}
    for i in S:
        out.setdefault(f(i), []).append(i)
    return sorted(out.values(), key=lambda c: sum(P[i].x for i in c) / len(c))


def toe_labels(P, edges, side_ids):
    """Label forefoot skin of one (+X) foot with toe 1..5: tube components + geodesic growth to the webs."""
    tubes = components([i for i in side_ids if P[i].y < Y_CUT], edges, P)
    if len(tubes) != 5:
        raise RuntimeError(f'expected 5 toe tubes anterior of {Y_CUT}, found {len(tubes)}')
    region = {i for i in side_ids if P[i].y < Y_GROW}
    adj = {i: [] for i in region}
    for a, b in edges:
        if a in region and b in region:
            L = (P[a] - P[b]).length; adj[a].append((b, L)); adj[b].append((a, L))
    lab, heap = {}, []
    for k, c in enumerate(tubes, 1):
        for i in c:
            heapq.heappush(heap, (0.0, i, k))
    while heap:
        d, i, k = heapq.heappop(heap)
        if i in lab:
            continue
        lab[i] = k
        for j, L in adj[i]:
            if j not in lab:
                heapq.heappush(heap, (d + L, j, k))
    webs = {k: max(P[i].y for i in c) for k, c in enumerate(tubes, 1)}   # most posterior point of each separate tube
    return lab, tubes, webs


def slice_extent(P, ids):
    ext = {}
    for i in ids:
        k = round(P[i].y / SLICE)
        lo, hi = ext.get(k, (1.0, -1.0)); ext[k] = (min(lo, P[i].x), max(hi, P[i].x))
    return ext


def section_x(V, E, y0, zmax, zmin=-1.0):
    xs = []
    for a, b in E:
        pa, pb = V[a], V[b]
        if pa.x < 0.02 and pb.x < 0.02:
            continue
        if (pa.y - y0) * (pb.y - y0) < 0:
            t = (y0 - pa.y) / (pb.y - pa.y); q = pa.lerp(pb, t)
            if zmin <= q.z < zmax:
                xs.append(q.x)
    return (max(xs) - min(xs)) if len(xs) > 1 else 0.0


def ball_breadth(V, E, y_ball):
    """ANSUR foot-breadth analogue: maximum breadth of true plane sections (perpendicular to y) near the ball, z < 60 mm."""
    r = int(BALL_SEARCH * 1000)
    return max((section_x(V, E, y_ball + d * 0.001, 0.06), d) for d in range(-r, r + 1))


def heel_breadth(V, E, ajc_y):
    """Maximum breadth of true sections >= 15 mm behind the ankle-joint centre (posterior to the malleoli), z < 100 mm."""
    return max((section_x(V, E, ajc_y + d * 0.001, 0.10), d) for d in range(15, 56))


def tube_sections(V, E, ids, grid):
    """x-extent of the true plane section of one toe tube at each grid y (edges with both ends in the tube)."""
    out = {}
    tube_edges = [(a, b) for a, b in E if a in ids and b in ids]
    for y0 in grid:
        xs = [V[a].x + (V[b].x - V[a].x) * (y0 - V[a].y) / (V[b].y - V[a].y)
              for a, b in tube_edges if (V[a].y - y0) * (V[b].y - y0) < 0]
        xs += [V[a].x for a in ids if abs(V[a].y - y0) < 1e-9]
        if len(xs) > 1:
            out[y0] = (min(xs), max(xs))
    return out


def section_geometry(ext):
    """Mean width per toe and mean gap per neighbouring pair over REF_BAND, from true sections."""
    widths, gaps = [], []
    for k in range(1, 6):
        ys = [y for y in ext[k] if REF_BAND[0] <= y <= REF_BAND[1]]
        widths.append(sum(ext[k][y][1] - ext[k][y][0] for y in ys) / len(ys))
    for k in range(1, 5):
        ys = [y for y in ext[k] if y in ext[k + 1] and REF_BAND[0] <= y <= REF_BAND[1]]
        gaps.append(min(ext[k + 1][y][0] - ext[k][y][1] for y in ys))
    return widths, gaps


def toe_geometry(P, tubes):
    """Mean width per toe and gap per neighbouring pair over REF_BAND (tube vertices only)."""
    rows = []
    for c in tubes:
        ext = slice_extent(P, [i for i in c if REF_BAND[0] <= P[i].y <= REF_BAND[1]])
        rows.append(ext)
    widths, gaps = [], []
    for ext in rows:
        widths.append(sum(b - a for a, b in ext.values()) / len(ext) if ext else None)
    for j in range(4):
        common = set(rows[j]) & set(rows[j + 1])
        gaps.append(sum(rows[j + 1][k][0] - rows[j][k][1] for k in common) / len(common) if common else None)
    return widths, gaps


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--expect-sha', '--out', '--report'):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    if Path(o.out).exists():
        raise FileExistsError(o.out)
    parent_sha = sha(o.blend)
    if parent_sha != o.expect_sha:
        raise SystemExit(f'parent SHA mismatch {parent_sha}')
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    body = bpy.data.objects[BODY]; me = body.data; master = bpy.data.objects[MASTER]
    assert body.matrix_world.is_identity
    P = [v.co.copy() for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    E = [tuple(e.vertices) for e in me.edges]
    fingerprint = (F, [g.name for g in body.vertex_groups], [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    st = stations(master)
    heads = [st[f'metatarsal_{k}_left:tail'] for k in range(1, 6)]
    assert all(h.x > 0 for h in heads)                      # +X foot carries the anatomical-left station names
    y_ball = sum(h.y for h in heads) / 5.0
    x_mt1, x_mt5 = heads[0].x, heads[4].x
    ajc_y = bpy.data.objects['LM_tibia_left__AJC'].matrix_world.translation.y
    side = [i for i, p in enumerate(P) if p.x > 0.02 and p.z < max(ZZERO, HEEL_ZZERO, 0.06)]
    D = {}                                                   # x displacement of +X foot vertices

    # 1. toes
    lab, tubes, webs = toe_labels(P, E, [i for i in side if P[i].z < 0.06 and P[i].y < -0.10])
    tube_ids = {k: [i for i, kk in lab.items() if kk == k and P[i].y < webs[k]] for k in range(1, 6)}
    grid = [round(-0.230 + n * GRID, 6) for n in range(int((0.230 + max(webs.values())) / GRID) + 2)]
    ext = {k: tube_sections(P, E, set(tube_ids[k]), grid) for k in range(1, 6)}
    widths0, gaps0 = section_geometry(ext)
    gap = {k: {y: ext[k + 1][y][0] - ext[k][y][1] for y in grid if y in ext[k] and y in ext[k + 1]} for k in range(1, 5)}
    half_move = {k: {} for k in range(1, 5)}
    for k in range(1, 5):
        ys = sorted(gap[k])
        for n, y in enumerate(ys):                         # window minimum: never close more than the narrowest nearby gap
            win = [gap[k][q] for q in ys[max(0, n - GAP_WINDOW):n + GAP_WINDOW + 1]]
            half_move[k][y] = 0.5 * max(0.0, min(win) - TOE_GAP)
        for kk in (k, k + 1):                              # hold the last value anteriorly past a shorter neighbour's tip
            last = None
            for y in sorted(ext[kk], reverse=True):
                if y in half_move[k]:
                    last = half_move[k][y]
                elif last is not None:
                    half_move[k][y] = last

    def interp(table, y):
        ks = sorted(table)
        if not ks:
            return None
        if y <= ks[0]:
            return table[ks[0]]
        if y >= ks[-1]:
            return table[ks[-1]]
        n = int((y - ks[0]) / GRID)
        n = min(max(n, 0), len(ks) - 2)
        y0, y1 = ks[n], ks[n + 1]
        t = (y - y0) / (y1 - y0) if y1 > y0 else 0.0
        v0, v1 = table[y0], table[y1]
        return tuple(a + (b - a) * t for a, b in zip(v0, v1)) if isinstance(v0, tuple) else v0 + (v1 - v0) * t

    if 'toes' in STAGES:
        for k in range(1, 6):
            for i in tube_ids[k]:
                y = P[i].y
                ab = interp(ext[k], y)
                if ab is None or ab[1] - ab[0] < 1e-5:
                    continue
                u = min(1.0, max(0.0, (P[i].x - ab[0]) / (ab[1] - ab[0])))
                lo = -(interp(half_move[k - 1], y) or 0.0) if k > 1 else 0.0
                hi = (interp(half_move[k], y) or 0.0) if k < 5 else -lo   # little toe: free lateral edge mirrors its medial move
                w = smooth((webs[k] - y) / WEB_FADE)                       # 0 at the web, 1 from WEB_FADE anterior of it
                D[i] = D.get(i, 0.0) + w * ((1 - u) * lo + u * hi)

    # 2. ball breadth: margins only (medial of MT1, lateral of MT5), solved on true plane sections
    def yz_weight(p):
        return (1.0 - smooth((abs(p.y - y_ball) - CORE) / (FADE - CORE))) * (1.0 - smooth((p.z - ZFULL) / (ZZERO - ZFULL)))

    def tube_weight(i):          # 1 on a separate toe tube, 0 behind its web (the same fade as step 1)
        k = lab.get(i)
        return smooth((webs[k] - P[i].y) / WEB_FADE) if k else 0.0
    near = [i for i in side if abs(P[i].y - y_ball) < BALL_SEARCH + 0.01 and P[i].z < 0.07]
    xmin_b = min(P[i].x for i in near); xmax_b = max(P[i].x for i in near)
    margin = {}
    for i in side:
        p = P[i]
        w = yz_weight(p) * (1.0 - tube_weight(i))       # toe tubes never take the margin push (no shear along a toe)
        if w <= 0:
            continue
        if p.x < x_mt1:          # medial margin: full move at the skin edge, 0 at the MT1 station
            margin[i] = -w * smooth((x_mt1 - p.x) / max(1e-6, x_mt1 - xmin_b))
        elif p.x > x_mt5:
            margin[i] = w * smooth((p.x - x_mt5) / max(1e-6, xmax_b - x_mt5))
    b0, _ = ball_breadth(P, E, y_ball)
    Dt = dict(D)                                           # include the toe moves when solving
    lo, hi = 0.0, 0.02
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        V = [P[i] + Vector((Dt.get(i, 0.0) + margin.get(i, 0.0) * mid, 0, 0)) for i in range(len(P))]
        lo, hi = (mid, hi) if ball_breadth(V, E, y_ball)[0] < ANSUR_BREADTH else (lo, mid)
    half = hi if 'ball' in STAGES else 0.0
    for i, m in margin.items():
        D[i] = D.get(i, 0.0) + m * half

    # mirror and apply
    kd = KDTree(len(P))
    for i, p in enumerate(P):
        kd.insert(p, i)
    kd.balance()
    full, worst = {}, 0.0
    for i, d in D.items():
        if abs(d) < 1e-12:
            continue
        _, j, dist = kd.find(Vector((-P[i].x, P[i].y, P[i].z)))
        worst = max(worst, dist); full[i] = d; full[j] = -d
    assert worst < 1e-6, worst
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in full.items():
        me.vertices[i].co.x += d
        for kb in keys:
            kb.data[i].co.x += d
    me.update(); bpy.context.view_layer.update()
    Q = [v.co.copy() for v in me.vertices]

    # checks
    c = {}
    c['topology_groups_weights_unchanged'] = fingerprint == (F, [g.name for g in body.vertex_groups],
                                                             [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    c['only_x_changed_in_foot_region'] = all(Q[i].y == P[i].y and Q[i].z == P[i].z for i in range(len(P))) and \
        all(abs(P[i].x) > 0.02 and P[i].z < max(ZZERO, HEEL_ZZERO, 0.06) for i in full)
    c['mirror_map_max_error_m'] = worst
    c['symmetry_max_m'] = max(abs(-Q[i].x - Q[kd.find(Vector((-P[i].x, P[i].y, P[i].z)))[1]].x) for i in full)
    c['foot_stations_outside_skin'] = inside_all(body, st)
    c['ball_breadth_section_mm'] = [round(b0 * 1000, 2), round(ball_breadth(Q, E, y_ball)[0] * 1000, 2)]
    c['heel_breadth_section_mm'] = [round(heel_breadth(P, E, ajc_y)[0] * 1000, 2), round(heel_breadth(Q, E, ajc_y)[0] * 1000, 2)]
    ext_q = {k: tube_sections(Q, E, set(tube_ids[k]), grid) for k in range(1, 6)}
    widths1, gaps1 = section_geometry(ext_q)
    gaps1_all = [min(ext_q[k + 1][y][0] - ext_q[k][y][1] for y in grid if y in ext_q[k] and y in ext_q[k + 1]) for k in range(1, 5)]
    c['toe_gap_min_along_whole_toe_mm'] = [round(g * 1000, 2) for g in gaps1_all]
    c['toe_mean_width_mm'] = [[round(w * 1000, 2) for w in widths0], [round(w * 1000, 2) for w in widths1]]
    c['toe_min_gap_ref_band_mm'] = [[round(g * 1000, 2) for g in gaps0], [round(g * 1000, 2) for g in gaps1]]
    c['toe_webs_y_mm'] = {k: round(v * 1000, 1) for k, v in webs.items()}
    flips, ratios = 0, []
    for f in F:
        if not any(i in full for i in f):
            continue
        a0 = (P[f[1]] - P[f[0]]).cross(P[f[2]] - P[f[0]]); a1 = (Q[f[1]] - Q[f[0]]).cross(Q[f[2]] - Q[f[0]])
        if a0.dot(a1) <= 0:
            flips += 1
        if a0.length > 1e-12:
            ratios.append(a1.length / a0.length)
    c['reversed_triangles'] = flips
    c['foot_area_ratio_range'] = [round(min(ratios), 4), round(max(ratios), 4)]

    def foot_pairs(V):
        idx = [n for n, f in enumerate(F) if all(abs(V[i].x) > 0.02 and V[i].z < 0.09 for i in f)]
        sub = [F[n] for n in idx]
        t = BVHTree.FromPolygons(V, sub, all_triangles=True)
        fs = [set(f) for f in sub]
        return sum(1 for a, b in t.overlap(t) if a < b and not (fs[a] & fs[b]))
    c['foot_self_intersecting_pairs'] = [foot_pairs(P), foot_pairs(Q)]
    c['lowest_point_mm'] = [round(min(p.z for p in P) * 1000, 3), round(min(q.z for q in Q) * 1000, 3)]
    flen = lambda V: (max(v.y for v in V if v.x > 0.02 and v.z < 0.16) - min(v.y for v in V if v.x > 0.02 and v.z < 0.16)) * 1000
    c['foot_length_mm'] = [round(flen(P), 2), round(flen(Q), 2)]
    ok = (c['topology_groups_weights_unchanged'] and c['only_x_changed_in_foot_region'] and c['symmetry_max_m'] < 1e-6
          and not c['foot_stations_outside_skin'] and abs(c['ball_breadth_section_mm'][1] - ANSUR_BREADTH * 1000) < 0.5
          and min(gaps1_all) >= TOE_GAP_MIN and flips == 0 and c['foot_self_intersecting_pairs'][1] <= c['foot_self_intersecting_pairs'][0]
          and c['foot_area_ratio_range'][0] > 0.5 and c['lowest_point_mm'][0] == c['lowest_point_mm'][1]
          and c['foot_length_mm'][0] == c['foot_length_mm'][1])
    c['verdict'] = 'PASS' if ok else 'FAIL'
    rep = {'schema_version': 1, 'stage': 'ORIGINAL_V1_FOOT_C4_CLAUDE', 'status': 'PROVISIONAL_DEVELOPMENT_CANDIDATE_NOT_ACCEPTED',
           'parent': {'path': Path(o.blend).name, 'sha256': parent_sha},
           'evidence': {'ansur_ball_breadth_mm': 104.1, 'ansur_ball_sd_mm': 4.7, 'ansur_heel_breadth_mm': 73.7, 'ansur_heel_sd_mm': 5.3,
                        'heel_definition': 'max breadth of true sections >=15 mm behind the AJC (posterior to the malleoli), any height < 100 mm; disclosed assumption. Not changed: C3 measures 82.9 mm (+1.75 SD), 75-81 mm at 20-30 mm behind the AJC',
                        'toe_targets': 'relational only: gaps closed to 0.6 mm (true sections); no sourced toe widths available'},
           'parameters': {'y_cut_m': Y_CUT, 'y_grow_m': Y_GROW, 'toe_gap_m': TOE_GAP, 'web_fade_m': WEB_FADE, 'ball_line_y_mm': round(y_ball * 1000, 2),
                          'ball_margin_move_each_side_mm': round(half * 1000, 3),
                          'toe_half_gap_move_mm_max': {f'{k}-{k + 1}': round(max(half_move[k].values()) * 1000, 2) for k in range(1, 5)}},
           'changed_vertices': len(full), 'max_x_displacement_mm': round(max(abs(d) for d in full.values()) * 1000, 3),
           'checks': c, 'shape_keys_updated': [kb.name for kb in keys]}
    print(json.dumps(rep, indent=1, default=str))
    if not ok:
        diag = os.environ.get('C4_DIAG_SAVE')            # diagnostics only: inspect a failing build outside the repo
        if diag:
            bpy.ops.wm.save_as_mainfile(filepath=diag, copy=True)
        raise SystemExit('checks failed')
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    rep['output'] = {'path': Path(o.out).name, 'sha256': sha(o.out)}
    Path(o.report).write_text(json.dumps(rep, indent=1, default=str) + '\n')


if __name__ == '__main__':
    main()
