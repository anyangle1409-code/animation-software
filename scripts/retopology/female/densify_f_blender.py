"""FEMALE densify-and-fit: subdivide the closed cage once (face region twice) and put every NEW vertex on her source.

Method (as the male densify_project_blender.py, without a rig at this stage):
  * every edge is cut once (bmesh subdivide_edges, grid fill: a quad becomes 4 quads);
  * every NEW vertex is moved onto her projection target (her source minus the hanging ponytail and fabric-covered
    skin) by a ray along its own normal, both directions, within SNAP_MAX, accepting only a surface facing the same way
    (never the opposite wall of a narrow gap: armpit, crotch, between fingers / toes);
  * symmetry guard: where a new vertex's snap differs from its mirror twin's by more than SYM_MM, both keep the smaller
    offset (her source is symmetric to < 1 mm almost everywhere; a one-sided offset is a source defect);
  * with "face" the front of the head (above the jaw) is cut a second time: eyes, lids, lips, nose;
  * original vertices are not moved: proportions cannot change (every vertex is an original cage vertex or a point
    of her source surface).
The cage's chords that cut under the surface (nose tip, under the chin, the bra band's lower lip) are lifted because
the new mid-edge / mid-face vertices land on the surface.

usage: python3.13 densify_f_blender.py -- <in .blend> <out NEW .blend> <report .json> [face]
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]); FACE = len(a) > 3 and a[3] == "face"
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
TGT = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]; body = bpy.data.objects["HGPT_Female_Body"]
bvh = BVHTree.FromPolygons([v.co.copy() for v in TGT.data.vertices], [tuple(p.vertices) for p in TGT.data.polygons])
SNAP_MAX = float(__import__("os").environ.get("SNAP_MAX", "0.006")); SYM_MM = 2.5


def snap(p, n):
    """nearest same-facing surface point along +-n within SNAP_MAX, else None"""
    best = None
    for d in (n, -n):
        h = bvh.ray_cast(p - d * 0.0002, d, SNAP_MAX)
        if h[0] is not None and h[1].dot(n) > 0.5 and (best is None or h[3] < best[1]):
            best = (h[0], h[3])
    return best[0] if best else None


def face_region(v):
    p = v.co
    return p.z > 1.40 and p.y < -0.02 and abs(p.x) < 0.075


def level(bm, edges, tag):
    old = set(bm.verts)
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    bm.normal_update()
    new = [v for v in bm.verts if v not in old]
    off = {}
    for v in new:
        h = snap(v.co.copy(), v.normal.copy())
        off[v] = (h - v.co) if h is not None else Vector()
    # symmetry guard
    kd = KDTree(len(new))
    for i, v in enumerate(new):
        kd.insert(Vector((v.co.x, v.co.y, v.co.z)), i)
    kd.balance(); sym_fix = 0
    for i, v in enumerate(new):
        if v.co.x <= 0.002:
            continue
        q, j, d = kd.find(Vector((-v.co.x, v.co.y, v.co.z)))
        if d > 0.002:
            continue
        w = new[j]
        if abs(off[v].length - off[w].length) * 1000 > SYM_MM:
            s = off[v] if off[v].length < off[w].length else off[w]
            mag = s.length
            off[v] = off[v].normalized() * mag if off[v].length > 1e-9 else Vector()
            off[w] = off[w].normalized() * mag if off[w].length > 1e-9 else Vector()
            sym_fix += 1
    snapped = 0
    for v in new:
        if off[v].length > 0:
            v.co += off[v]; snapped += 1
    return {"level": tag, "new_vertices": len(new), "snapped": snapped, "symmetry_guarded": sym_fix,
            "offset_mm_p50_p95_max": [round(float(np.percentile([o.length for o in off.values()], q)) * 1000, 2) for q in (50, 95, 100)]}


bm = bmesh.new(); bm.from_mesh(body.data); bm.normal_update()
info = [level(bm, list(bm.edges), "whole body")]
if FACE:
    fe = [e for e in bm.edges if all(face_region(v) for v in e.verts)]
    info.append(level(bm, fe, "face (second level)"))
# remove loose / degenerate
nq = sum(len(f.verts) != 4 for f in bm.faces)
bm.to_mesh(body.data); body.data.update()
tris = bm.calc_loop_triangles(); T = [tuple(l.vert.index for l in t) for t in tris]
sb = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], T, all_triangles=True)
inter = sum(1 for i, j in sb.overlap(sb) if not set(T[i]) & set(T[j]))
L = np.array([e.calc_length() for e in bm.edges])
rep = {"in": IN.name, "levels": info, "vertices": len(bm.verts), "faces": len(bm.faces), "non_quads": nq,
       "boundary_edges": sum(e.is_boundary for e in bm.edges), "intersecting_pairs": inter,
       "edge_mm_p5_p50_p95": [round(float(np.percentile(L, q)) * 1000, 2) for q in (5, 50, 95)]}
body["DENSIFY"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("DENSIFY", json.dumps(rep))
