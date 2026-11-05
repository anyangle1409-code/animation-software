"""Topology + shape audit for the Task 3 shell (read-only).

Reports (mirrored, i.e. full-body evaluated mesh, and the half-body source mesh):
  * faces by type, boundary edges classified (mirror seam / planned openings / unexpected), wire edges, loose verts,
    non-manifold edges, vertex valence histogram (poles), connected components;
  * quad shape by region: aspect (longest / shortest side), corner angles, count of poor quads;
  * shape capture: distance from the source surface (proxy points inside the covered region) to the cage, raw and
    after one Catmull-Clark level re-projected (what a subdivided, shrinkwrapped cage would show), in mm.

usage: python3.13 audit_task3_shell.py -- <blend> <out .json> [shell object] [source object]
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
BL, OUT = Path(a[0]), Path(a[1]); SH = a[2] if len(a) > 2 else "HGPT_Male_Task3_Shell"; SRC = a[3] if len(a) > 3 else "HGPT_SOURCE_PROXY_Mesh_0"
bpy.ops.wm.open_mainfile(filepath=str(BL), load_ui=False)
ob = bpy.data.objects[SH]; src = bpy.data.objects[SRC]
design = json.loads(ob.get("TASK3_SHELL_DESIGN", "{}"))


def region(c):
    z = c[2]
    if z > 1.74:
        return "crown"
    if z > 1.565:
        return "head_neck"
    if z > 1.492:
        return "trapezius_band"
    if z > 1.27:
        return "socket_band"
    return "torso"


def topo(bm, mirrored):
    r = {"vertices": len(bm.verts), "faces": len(bm.faces), "face_sizes": dict(Counter(len(f.verts) for f in bm.faces)),
         "wire_edges": sum(e.is_wire for e in bm.edges), "loose_vertices": sum(not v.link_edges for v in bm.verts),
         "non_manifold_edges": sum(len(e.link_faces) > 2 for e in bm.edges)}
    # boundary edges grouped into connected loops; each loop is classified by where it lies
    bnd = [e for e in bm.edges if e.is_boundary]
    seam = [e for e in bnd if not mirrored and all(abs(v.co.x) < 1e-6 for v in e.verts)]
    rest = [e for e in bnd if e not in set(seam)]
    vp = {}
    for e in rest:
        for v in e.verts:
            vp.setdefault(v.index, []).append(e)
    seen, loops = set(), []
    for e in rest:
        if e.index in seen:
            continue
        stack, comp = [e], []
        while stack:
            x = stack.pop()
            if x.index in seen:
                continue
            seen.add(x.index); comp.append(x)
            for v in x.verts:
                stack += [y for y in vp[v.index] if y.index not in seen]
        loops.append(comp)
    cls = Counter({"mirror_seam": len(seam)}) if not mirrored else Counter()
    detail = []
    for comp in loops:
        C = np.array([((x.verts[0].co + x.verts[1].co) / 2)[:] for x in comp]); c = C.mean(0); zr = (C[:, 2].min(), C[:, 2].max())
        if zr[1] < design.get("open_pelvis_z", 0.0) + 0.003:
            lab = "open_pelvis"
        elif 1.2 < c[2] < 1.55 and abs(c[0]) > 0.12:
            lab = "arm_socket"
        elif 1.62 < c[2] < 1.73 and abs(c[0]) > 0.05 and -0.04 < c[1] < 0.05:
            lab = "ear_opening"
        elif 1.55 < c[2] < 1.73 and c[1] < -0.03:
            lab = "face_opening"
        else:
            lab = "unexpected"
        cls[lab] += len(comp); detail.append({"label": lab, "edges": len(comp), "centre": [round(float(x), 3) for x in c],
                                              "z_range": [round(float(zr[0]), 3), round(float(zr[1]), 3)]})
    r["boundary_edges"] = dict(cls); r["boundary_loops"] = detail
    val = Counter(len(v.link_edges) for v in bm.verts if not v.is_boundary)
    r["interior_valence"] = {str(k): val[k] for k in sorted(val)}
    par = list(range(len(bm.verts)))

    def f(k):
        while par[k] != k:
            par[k] = par[par[k]]; k = par[k]
        return k
    for e in bm.edges:
        x, y = f(e.verts[0].index), f(e.verts[1].index)
        if x != y:
            par[x] = y
    r["components"] = len({f(v.index) for v in bm.verts})
    return r


def quality(bm):
    by = {}
    for fc in bm.faces:
        L = [e.calc_length() for e in fc.edges]; ang = [math.degrees(lp.calc_angle()) for lp in fc.loops]
        by.setdefault(region(fc.calc_center_median()), []).append((max(L) / max(min(L), 1e-12), min(ang), max(ang)))
    out = {}
    for k, q in sorted(by.items()):
        q = np.array(q)
        out[k] = {"faces": len(q), "aspect_p50": round(float(np.median(q[:, 0])), 2), "aspect_p95": round(float(np.percentile(q[:, 0], 95)), 2),
                  "aspect_max": round(float(q[:, 0].max()), 2), "min_angle_p5": round(float(np.percentile(q[:, 1], 5)), 1),
                  "min_angle_min": round(float(q[:, 1].min()), 1), "max_angle_max": round(float(q[:, 2].max()), 1),
                  "poor_quads(aspect>4|angle<30|>150)": int(((q[:, 0] > 4) | (q[:, 1] < 30) | (q[:, 2] > 150)).sum())}
    return out


half = bmesh.new(); half.from_mesh(ob.data)
dg = bpy.context.evaluated_depsgraph_get(); me_full = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
full = bmesh.new(); full.from_mesh(me_full)
rep = {"blend": str(BL), "object": SH, "source": SRC, "half": topo(half, False), "mirrored": topo(full, True), "quad_quality": quality(full)}
# shape capture
SV = np.array([v.co[:] for v in src.data.vertices]); bvh_src = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(p.vertices) for p in src.data.polygons])


def capture(bm_):
    """distance from source points to the cage, counted only where the nearest cage face is away from every opening
    (no boundary vertex within two face rings), so the openings do not pollute the shape measurement"""
    bm_.faces.ensure_lookup_table()
    near_open = set()
    for fc in bm_.faces:
        if any(v.is_boundary and not (abs(v.co.x) < 1e-6) for v in fc.verts):
            near_open.add(fc.index)
    for _ in range(2):
        grow = set()
        for i in near_open:
            for v in bm_.faces[i].verts:
                grow |= {f.index for f in v.link_faces}
        near_open |= grow
    cage = BVHTree.FromBMesh(bm_)
    lo = design.get("open_pelvis_z", 0.915) + 0.01
    sel = SV[(SV[:, 2] > lo) & (np.abs(SV[:, 0]) < 0.30)]
    sel = sel[::7]
    d = []
    for p in sel:
        loc, nrm, idx, dist = cage.find_nearest(p)
        if dist is not None and dist < 0.03 and idx not in near_open:
            d.append(dist)
    d = np.array(d) * 1000
    return {"samples": len(d), "median_mm": round(float(np.median(d)), 2), "p95_mm": round(float(np.percentile(d, 95)), 2), "max_mm": round(float(d.max()), 2)}


rep["shape_capture_raw_cage"] = capture(full)
sub = full.copy(); bmesh.ops.subdivide_edges(sub, edges=sub.edges[:], cuts=1, use_grid_fill=True, smooth=1.0)
for v in sub.verts:                                    # re-project (shrinkwrap equivalent)
    v.co = bvh_src.find_nearest(v.co)[0]
rep["shape_capture_subdivided_projected"] = capture(sub)
OUT.write_text(json.dumps(rep, indent=1)); print("AUDIT", json.dumps(rep))
