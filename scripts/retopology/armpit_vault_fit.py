"""Fit the armpit cage into the axillary vault of the source (topology fit) - writes a NEW checkpoint.

The Task-4 shoulder cap spans the mouth of the armpit: in the source's rest pose the axilla is a hollow up to ~45 mm
deep between arm and chest, and the cage bridges it (source points INSIDE the cage). Here the cage vertices around
the vault are carried into it: each round, every cage vertex within RADIUS of the vault centre whose own inward ray
(against the vertex normal) meets the source deeper than MIN_GAP is moved a fraction STEP of the way to that hit, then
the moved set is relaxed tangentially (umbrella average with the normal component removed) so the loops spread over
the vault walls instead of bunching at its floor. Stops when the coverage stops improving. Reports coverage of the
source shoulder region, fold defects and self-intersections before / after, so the fit is judged by measurement.

usage: python3.13 armpit_vault_fit.py -- <in .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
RADIUS, MIN_GAP, STEP, ROUNDS, MAX_DEPTH = 0.075, 0.002, 0.5, 25, 0.06
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices])
sb = BVHTree.FromPolygons([Vector(p) for p in SV], [tuple(p.vertices) for p in SRC.data.polygons])
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()


def cage_bvh():
    return BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces])


def inside(cb, p):
    n, o, d = 0, Vector(p), Vector((0.31, 0.17, 0.93)).normalized()
    while True:
        h = cb.ray_cast(o + d * 1e-5, d, 5)
        if h[0] is None:
            return n % 2 == 1
        n += 1; o = h[0]


def coverage(sg):
    cb = cage_bvh(); gh = np.array([0.22 * sg, 0.033, 1.44]); m = (np.linalg.norm(SV - gh, axis=1) < 0.20) & (SV[:, 0] * sg > 0.06)
    d = np.array([cb.find_nearest(Vector(p))[3] for p in SV[m]]) * 1000
    return [round(float(np.percentile(d, q)), 2) for q in (50, 95, 99)] + [round(float(d.max()), 1)]


def intersections():
    tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
    b = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
    return sum(1 for i, j in b.overlap(b) if not set(T[i]) & set(T[j]))


rep = {"method": __doc__.split("usage")[0].strip(), "in": IN.name, "sides": {}}
cov0 = {sg: coverage(sg) for sg in (1, -1)}; inter0 = intersections()
for sg in (1, -1):
    cb = cage_bvh(); gh = np.array([0.22 * sg, 0.033, 1.44]); m = (np.linalg.norm(SV - gh, axis=1) < 0.20) & (SV[:, 0] * sg > 0.06)
    P = SV[m]; far = np.array([p for p in P if cb.find_nearest(Vector(p))[3] > 0.012 and inside(cb, p)])
    if not len(far):
        rep["sides"][sg] = {"vault_points": 0}; continue
    C = Vector(far.mean(0)); verts = [v for v in bm.verts if (v.co - C).length < RADIUS and v.co.x * sg > 0.05]
    hist = []; best = (cov0[sg][1], {v: v.co.copy() for v in verts}); moved_total = 0
    for rnd in range(ROUNDS):
        bm.normal_update(); moved = 0
        for v in verts:
            h = sb.ray_cast(v.co - v.normal * 0.0005, -v.normal, MAX_DEPTH)
            if h[0] is not None and (h[0] - v.co).length > MIN_GAP:
                v.co = v.co.lerp(h[0], STEP); moved += 1
        for _ in range(2):                              # tangential relax of the moved set
            bm.normal_update(); upd = {}
            for v in verts:
                nb = [e.other_vert(v).co for e in v.link_edges]; d = sum(nb, Vector()) / len(nb) - v.co
                upd[v] = v.co + (d - v.normal * d.dot(v.normal)) * 0.5
            for v, p in upd.items():
                v.co = p
        cv = coverage(sg); hist.append((moved, cv[1], cv[3])); moved_total += moved
        if cv[1] < best[0]:
            best = (cv[1], {v: v.co.copy() for v in verts})
        if moved == 0 or (rnd >= 4 and cv[1] >= hist[-4][1]):
            break
    for v, p in best[1].items():
        v.co = p
    rep["sides"]["right" if sg > 0 else "left"] = {"vault_points": int(len(far)), "vault_centre": [round(x, 4) for x in C],
                                                    "cage_vertices_in_play": len(verts), "history_moved_p95_max": hist}
cov1 = {sg: coverage(sg) for sg in (1, -1)}; inter1 = intersections()
bm.to_mesh(body.data); body.data.update()
rep.update(coverage_mm_p50_p95_p99_max_before={"right": cov0[1], "left": cov0[-1]}, coverage_after={"right": cov1[1], "left": cov1[-1]},
           self_intersections_before=inter0, self_intersections_after=inter1)
body["ARMPIT_VAULT_FIT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("VAULT", json.dumps({k: v for k, v in rep.items() if k != "method"}))
