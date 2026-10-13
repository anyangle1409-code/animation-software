#!/usr/bin/env python3
"""ORIGINAL_v1 foot-breadth stage (Claude): ball and heel breadth to the ANSUR II 1.82 m predictions, mesh-only.

Evidence: ANSUR II male (OLS on stature, n = 4,082) horizontal foot breadth at 1.82 m = 104.1 +/- 4.7 mm; the a003,
C2 and C3 feet measure 96.4 mm across the metatarsal heads (-7.7 mm, -1.6 SD).  The skeleton does not constrain this:
the metatarsal-head stations stay where they are and only the surrounding soft tissue widens.

Heel (OPT-IN, off by default): ANSUR heel breadth at 1.82 m = 73.7 +/- 5.3 mm.  On this model the result depends on
where the heel is measured: 87.0 mm across the heel-midfoot transition at the ankle line, but 58.2 mm (a003/C2) /
60.7 mm (C3) across the heel proper >= 20 mm behind the ankle-joint centre.  The ANSUR landmark cannot be located
unambiguously on this mesh, so no heel change is made unless --heel is passed (then:  The heel zone weight is 0 at
the AJC, 1 from 20 mm behind it, with the same height fade (z 40 -> 80 mm) so the malleoli/Achilles are untouched; its
scale is solved so the heel breadth (z < 40 mm, >= 20 mm behind the AJC) reaches the ANSUR prediction).

Change (applies to any parent with the a003 body topology, e.g. C2 or C3):
  * per 2 mm y-slice the foot's medial/lateral centre is found; x is scaled about it by 1 + (s - 1) * w(y) * h(z);
  * w(y): 1 within +-15 mm of the ball line (mean metatarsal-head y), smoothstep to 0 at +-45 mm, so the heel and the
    toes are untouched; h(z): 1 below 30 mm, smoothstep to 0 at 70 mm, so the dorsum/ankle are untouched;
  * s is solved (bisection) so the maximum breadth across the ball reaches the ANSUR prediction;
  * the heel zone is scaled the same way about the slice centre with its own solved scale;
  * mirrored exactly to the other foot; y and z never change; every shape key gets the same delta.
Checks (all must pass; written to the report): topology/groups/weights/rigs untouched, only foot-region x moved,
mirror symmetry, every foot bone station still inside the skin, ball breadth on target, heel breadth reported.

  python3.13 build_original_foot_breadth_candidate_blender.py --blend PARENT.blend --expect-sha SHA --out NEW.blend --report JSON
"""
import argparse, hashlib, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
MASTER = 'HGPT_ANATOMICAL_MASTER'
ANSUR_BREADTH = 0.1041
ANSUR_HEEL_BREADTH = 0.0737
HEEL_RAMP = 0.020
HEEL_ZFULL, HEEL_ZZERO = 0.040, 0.080
CORE, FADE = 0.015, 0.045
ZFULL, ZZERO = 0.030, 0.070
BIN = 0.002


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def stations(master):
    out = {}
    for b in master.data.bones:
        n = b.name[5:] if b.name.startswith('anat_') else b.name
        if any(n.startswith(k) for k in ('talus', 'calcaneus', 'navicular', 'cuboid', 'medial_cun', 'intermediate_cun',
                                         'lateral_cun', 'metatarsal', 'hallux', 'toe')):
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


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--expect-sha', '--out', '--report'):
        ap.add_argument(a, required=True)
    ap.add_argument('--heel', action='store_true', help='also solve the heel zone (ambiguous ANSUR landmark; off by default)')
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
    fingerprint = ([tuple(p.vertices) for p in me.polygons], [g.name for g in body.vertex_groups],
                   [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    st = stations(master)
    heads = [st[f'metatarsal_{k}_left:tail'] for k in range(1, 6)]
    assert all(h.x > 0 for h in heads)
    y_ball = sum(h.y for h in heads) / 5.0
    ajc_y = bpy.data.objects['LM_tibia_left__AJC'].matrix_world.translation.y
    foot = [i for i, p in enumerate(P) if p.x > 0.02 and ((p.z < ZZERO and abs(p.y - y_ball) < FADE) or
                                                          (p.z < HEEL_ZZERO and p.y > ajc_y))]
    # per-slice centre of the +X foot (low slices only)
    centre = {}
    for i in foot:
        k = round(P[i].y / BIN)
        lo, hi = centre.get(k, (1.0, -1.0))
        centre[k] = (min(lo, P[i].x), max(hi, P[i].x))
    cx = {k: 0.5 * (a + b) for k, (a, b) in centre.items()}

    def weight(p):
        return (1.0 - smooth((abs(p.y - y_ball) - CORE) / (FADE - CORE))) * (1.0 - smooth((p.z - ZFULL) / (ZZERO - ZFULL)))

    def heel_weight(p):
        return smooth((p.y - ajc_y) / HEEL_RAMP) * (1.0 - smooth((p.z - HEEL_ZFULL) / (HEEL_ZZERO - HEEL_ZFULL)))

    def new_x(i, s, sh=1.0):
        p = P[i]; c = cx[round(p.y / BIN)]
        return c + (p.x - c) * (1.0 + (s - 1.0) * weight(p) + (sh - 1.0) * heel_weight(p))

    ball = [i for i in foot if abs(P[i].y - y_ball) < CORE and P[i].z < 0.04]
    heel_ids = [i for i in foot if P[i].y > ajc_y + HEEL_RAMP and P[i].z < 0.04]   # heel proper (full zone weight)

    def breadth(ids, s, sh):
        xs = [new_x(i, s, sh) for i in ids]
        return max(xs) - min(xs)

    def solve(ids, target, which):
        lo, hi = 0.5, 1.5
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            val = breadth(ids, mid, 1.0) if which == 'ball' else breadth(ids, 1.0, mid)
            lo, hi = (mid, hi) if val < target else (lo, mid)
        return hi
    b0 = breadth(ball, 1.0, 1.0)
    h0 = breadth(heel_ids, 1.0, 1.0)
    s = solve(ball, ANSUR_BREADTH, 'ball')
    sh = solve(heel_ids, ANSUR_HEEL_BREADTH, 'heel') if o.heel else 1.0
    heel_line = [i for i in range(len(P)) if P[i].x > 0.02 and P[i].z < 0.04 and abs(P[i].y - ajc_y) < 0.005]
    heel_at_ajc = (max(P[i].x for i in heel_line) - min(P[i].x for i in heel_line)) if heel_line else None
    disp = {i: new_x(i, s, sh) - P[i].x for i in foot}
    disp = {i: d for i, d in disp.items() if abs(d) > 1e-9}
    kd = KDTree(len(P))
    for i, p in enumerate(P):
        kd.insert(p, i)
    kd.balance()
    full, worst = dict(disp), 0.0
    for i, d in disp.items():
        _, j, dist = kd.find(Vector((-P[i].x, P[i].y, P[i].z)))
        worst = max(worst, dist); full[j] = -d
    assert worst < 1e-6, worst
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    for i, d in full.items():
        me.vertices[i].co.x += d
        for kb in keys:
            kb.data[i].co.x += d
    me.update(); bpy.context.view_layer.update()
    # checks
    Q = [v.co.copy() for v in me.vertices]
    checks = {}
    checks['topology_groups_weights_unchanged'] = fingerprint == ([tuple(p.vertices) for p in me.polygons], [g.name for g in body.vertex_groups],
                                                                  [tuple((g.group, round(g.weight, 7)) for g in v.groups) for v in me.vertices])
    checks['only_x_changed_in_foot_region'] = all((Q[i].y == P[i].y and Q[i].z == P[i].z) for i in range(len(P))) and \
        all(abs(P[i].x) > 0.02 and P[i].z < max(ZZERO, HEEL_ZZERO) for i in full)
    checks['mirror_map_max_error_m'] = worst
    sym = max(abs(-Q[i].x - Q[kd.find(Vector((-P[i].x, P[i].y, P[i].z)))[1]].x) for i in full)
    checks['symmetry_max_m'] = sym
    outside = inside_all(body, st)
    checks['foot_stations_outside_skin'] = outside
    ball_after = [Q[i] for i in range(len(Q)) if Q[i].x > 0.02 and abs(Q[i].y - y_ball) < CORE and Q[i].z < 0.04]
    heel_y = max(q.y for q in Q if q.x > 0.02 and q.z < 0.16)
    heel = [q for q in Q if q.x > 0.02 and q.z < 0.04 and q.y > ajc_y + HEEL_RAMP]
    checks['ball_breadth_mm'] = [round(b0 * 1000, 2), round((max(q.x for q in ball_after) - min(q.x for q in ball_after)) * 1000, 2)]
    checks['heel_breadth_20mm_behind_AJC_mm'] = [round(h0 * 1000, 2), round((max(q.x for q in heel) - min(q.x for q in heel)) * 1000, 2)]
    checks['heel_y_mm'] = round(heel_y * 1000, 2)
    checks['heel_breadth_at_AJC_line_mm_parent'] = round(heel_at_ajc * 1000, 2) if heel_at_ajc else None
    checks['heel_zone_applied'] = o.heel
    ok = (checks['topology_groups_weights_unchanged'] and checks['only_x_changed_in_foot_region'] and sym < 1e-6
          and not outside and abs(checks['ball_breadth_mm'][1] - ANSUR_BREADTH * 1000) < 0.5
          and (not o.heel or abs(checks['heel_breadth_20mm_behind_AJC_mm'][1] - ANSUR_HEEL_BREADTH * 1000) < 0.5))
    checks['verdict'] = 'PASS' if ok else 'FAIL'
    if not ok:
        raise SystemExit('checks failed: ' + json.dumps(checks, default=str))
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    rep = {'schema_version': 1, 'stage': 'ORIGINAL_V1_FOREFOOT_BREADTH_CLAUDE', 'status': 'REVIEW_CANDIDATE_NOT_ACCEPTED',
           'parent': {'path': Path(o.blend).name, 'sha256': parent_sha}, 'output': {'path': Path(o.out).name, 'sha256': sha(o.out)},
           'evidence': {'ansur_breadth_mm': ANSUR_BREADTH * 1000, 'ansur_sd_mm': 4.7, 'ansur_heel_breadth_mm': ANSUR_HEEL_BREADTH * 1000},
           'parameters': {'ball_line_y_mm': round(y_ball * 1000, 2), 'core_m': CORE, 'fade_m': FADE, 'z_full_m': ZFULL, 'z_zero_m': ZZERO,
                          'heel_ramp_m': HEEL_RAMP, 'heel_z_full_m': HEEL_ZFULL, 'heel_z_zero_m': HEEL_ZZERO,
                          'ball_scale_solved': round(s, 5), 'heel_scale_solved': round(sh, 5)},
           'changed_vertices': len(full), 'max_x_displacement_mm': round(max(abs(d) for d in full.values()) * 1000, 3),
           'checks': checks, 'shape_keys_updated': [kb.name for kb in keys]}
    Path(o.report).write_text(json.dumps(rep, indent=1, default=str) + '\n')
    print(json.dumps(rep, indent=1, default=str))


if __name__ == '__main__':
    main()
