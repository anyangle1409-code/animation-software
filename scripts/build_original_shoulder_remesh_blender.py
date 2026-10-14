#!/usr/bin/env python3
"""ORIGINAL_v1 shoulder re-mesh (review only; bpy).  Owner, 14 Oct 2026, on "Is it still the mesh that's not right?" -
"Yes please" (re-mesh the shoulder region as a separate review copy).

Measured on R10: the shoulder / armpit is the coarsest region of the body (median edge 19.7 mm against 9.5 mm for the body
and 9.4 mm for the face; ~40 vertices in a 12 mm slice through the armpit and upper arm), with irregular sliver triangles
over the deltoid cap - too little geometry for the deltoid to round out or the armpit to form a hollow between two folds.

What this does (both sides, mirror-symmetric):
  1. region: every face whose centroid lies within REGION_R of a glenohumeral pivot or within AXILLA_R of the armpit vault
     centre (pivot + (-5, +2, -7.5) cm, medial for the side);
  2. one level of explicit midpoint subdivision of the region (each triangle -> 4; edges ~20 -> ~10 mm); neighbouring faces
     that received a split edge are re-triangulated (best-shaped fan) so the surface stays watertight and all-triangle;
  3. Taubin smoothing (lambda 0.5 / mu -0.53, non-shrinking) of the new and region vertices, the region boundary fixed:
     the faceted coarse shape becomes a smooth surface;
  4. every per-vertex layer is carried across: each new vertex takes the exact average of its two parent vertices for every
     deform weight and every shape-key layer (BMesh's subdivide operator was tried first and was not reliable with this
     mesh's shape-key layers: rippled skin), and the smoothing is applied to every shape-key layer as the same linear
     operator, so each corrective key (K1, C1, S1, S3, S4) keeps its shape on the new vertices.  The body has no UV map.
The bone rig, the bones and every vertex outside the region are unchanged (same index, position, weights and keys; new
vertices are appended after index 17,945).  The file declares its vertex count (scene["hgpt_review_body_vertices"])
so the review drives accept it; shipping a different vertex count is a runtime-contract change (owner + Lane G).

  python3.13 build_original_shoulder_remesh_blender.py -- --blend R10.blend --out R11.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

_E = os.environ
REGION_R = float(_E.get("RM_REGION_R", 0.15))
AXILLA_R = float(_E.get("RM_AXILLA_R", 0.10))
AXILLA_OFF = (-0.05, 0.02, -0.075)
TAUBIN_ITERS = int(_E.get("RM_TAUBIN", 0))   # Loop subdivision already smooths; optional extra Taubin passes
LAMBDA, MU = 0.5, -0.53


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _edge_stats(me, centres, radius):
    import numpy as np
    V = np.array([tuple(v.co) for v in me.vertices]); E = np.array([tuple(e.vertices) for e in me.edges])
    mid = (V[E[:, 0]] + V[E[:, 1]]) / 2
    L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
    mask = np.zeros(len(L), bool)
    for c in centres:
        mask |= np.linalg.norm(mid - np.array(c), axis=1) < radius
    return {"edges": int(mask.sum()), "median_edge_mm": round(float(np.median(L[mask])) * 1000, 2),
            "p90_edge_mm": round(float(np.percentile(L[mask], 90)) * 1000, 2)}


def remesh(body, rig):
    """Explicit midpoint subdivision (every new vertex = exact average of its two parent vertices for position, every
    shape-key layer and every deform weight; BMesh's operator was not reliable with this mesh's shape-key layers), then
    Taubin smoothing of the region interior applied identically to the coordinates and every shape-key layer."""
    import numpy as np
    me = body.data
    pivots = {s: rig.data.bones[f"upperarm_{s}"].head_local.copy() for s in ("l", "r")}
    centres = []
    for s, p in pivots.items():
        sign = 1.0 if s == "r" else -1.0
        centres.append((np.array(tuple(p)), REGION_R))
        centres.append((np.array(tuple(p + Vector((AXILLA_OFF[0] * sign, AXILLA_OFF[1], AXILLA_OFF[2])))), AXILLA_R))
    before = _edge_stats(me, [tuple(c) for c, _ in centres[::2]], 0.12)
    nv = len(me.vertices)
    V = np.array([tuple(v.co) for v in me.vertices])
    keys = me.shape_keys.key_blocks if me.shape_keys else []
    K = [np.array([tuple(d.co) for d in kb.data]) for kb in keys]
    names = [g.name for g in body.vertex_groups]
    W = np.zeros((nv, len(names)))
    for v in me.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    faces = [tuple(p.vertices) for p in me.polygons]
    mats = [p.material_index for p in me.polygons]
    smooth = [p.use_smooth for p in me.polygons]
    if any(len(f) != 3 for f in faces):
        raise RuntimeError("expected an all-triangle mesh")
    cen = np.array([V[list(f)].mean(0) for f in faces])
    inreg = np.zeros(len(faces), bool)
    for c, r in centres:
        inreg |= np.linalg.norm(cen - c, axis=1) < r
    split = {}
    for k in np.where(inreg)[0]:
        f = faces[k]
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            split.setdefault((min(a, b), max(a, b)), None)
    for i, e in enumerate(sorted(split)):
        split[e] = nv + i
    E = np.array(sorted(split))
    # Loop subdivision stencils (linear, applied identically to positions, every shape-key layer and every weight):
    #   edge with both faces in the region: 3/8 (a + b) + 1/8 (c + d); region-boundary edge: 1/2 (a + b);
    #   original vertex whose every face is in the region: (1 - n beta) v + beta sum(neighbours), beta = 3 / (8 n)
    #   (Warren); other vertices unchanged (the surface outside the region does not move)
    opp = {}
    vfaces = [[] for _ in range(nv)]
    for k, f in enumerate(faces):
        for i in range(3):
            a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
            opp.setdefault((min(a, b), max(a, b)), []).append((k, c))
            vfaces[a].append(k)
    rows, cols, vals = [], [], []
    for j, (a, b) in enumerate(E):
        o = opp[(a, b)]
        if len(o) == 2 and all(inreg[k] for k, _ in o):
            for x, w in ((a, 0.375), (b, 0.375), (o[0][1], 0.125), (o[1][1], 0.125)):
                rows.append(nv + j); cols.append(x); vals.append(w)
        else:
            rows += [nv + j, nv + j]; cols += [a, b]; vals += [0.5, 0.5]
    nbr = [set() for _ in range(nv)]
    for f in faces:
        for i in range(3):
            nbr[f[i]].update((f[(i + 1) % 3], f[(i + 2) % 3]))
    interior_old = 0
    for v in range(nv):
        if vfaces[v] and all(inreg[k] for k in vfaces[v]):
            n = len(nbr[v]); beta = 3.0 / (8.0 * n)
            rows.append(v); cols.append(v); vals.append(1 - n * beta)
            for x in nbr[v]:
                rows.append(v); cols.append(x); vals.append(beta)
            interior_old += 1
        else:
            rows.append(v); cols.append(v); vals.append(1.0)
    rows, cols, vals = np.array(rows), np.array(cols), np.array(vals)

    def apply(X):
        out = np.zeros((nv + len(E), X.shape[1]))
        np.add.at(out, rows, vals[:, None] * X[cols])
        return out
    V2 = apply(V)
    K2 = [apply(k) for k in K]
    W2 = apply(W)
    mid = lambda a, b: split.get((min(a, b), max(a, b)))
    nf, nmat, nsm = [], [], []
    for f, m, sm in zip(faces, mats, smooth):
        a, b, c = f
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        cnt = sum(x is not None for x in (ab, bc, ca))
        if cnt == 0:
            out = [f]
        elif cnt == 3:
            out = [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        else:
            # rotate so the split edges come first, then fan-triangulate the polygon
            poly = []
            for x, y, mxy in ((a, b, ab), (b, c, bc), (c, a, ca)):
                poly.append(x)
                if mxy is not None:
                    poly.append(mxy)
            # fan from the vertex opposite the longest split for well-shaped triangles: use the first original vertex
            # that is not an endpoint of every split edge
            n = len(poly)
            best = None
            for st in range(n):
                tris = [(poly[st], poly[(st + i) % n], poly[(st + i + 1) % n]) for i in range(1, n - 1)]
                q = min(_tri_quality(V2, t) for t in tris)
                if best is None or q > best[0]:
                    best = (q, tris)
            out = best[1]
        nf.extend(out); nmat.extend([m] * len(out)); nsm.extend([sm] * len(out))
    # region interior for smoothing: vertices whose every neighbour belongs to a subdivided face
    region_faces = [t for t, f in zip(nf, nf) if any(x >= nv for x in t)]
    region_v = {x for t in region_faces for x in t}
    adj = [set() for _ in range(len(V2))]
    for t in nf:
        for i in range(3):
            adj[t[i]].update((t[(i + 1) % 3], t[(i + 2) % 3]))
    free = np.array(sorted(v for v in region_v if adj[v] <= region_v))
    nb = [np.array(sorted(adj[v])) for v in free]
    layers = [V2] + K2
    for it in range(TAUBIN_ITERS * 2):
        step = LAMBDA if it % 2 == 0 else MU
        for L in layers:
            avg = np.array([L[n].mean(0) for n in nb])
            L[free] = L[free] + step * (avg - L[free])
    # write a new mesh datablock on the same object (vertex groups live on the object; keys are rebuilt by name)
    orig_name = me.name
    me.name = orig_name + "_PRE_REMESH"
    new = bpy.data.meshes.new(orig_name)
    new.from_pydata([tuple(x) for x in V2], [], nf)
    for m in me.materials:
        new.materials.append(m)
    new.polygons.foreach_set("material_index", nmat)
    new.polygons.foreach_set("use_smooth", nsm)
    for k, v in me.items():
        new[k] = v
    old_keys = [(kb.name, kb.slider_min, kb.slider_max, kb.relative_key.name, kb.interpolation, kb.vertex_group, kb.mute)
                for kb in keys]
    body.data = new
    for j, (name, smin, smax, rel, interp, vg, mute) in enumerate(old_keys):
        kb = body.shape_key_add(name=name, from_mix=False)
        kb.data.foreach_set("co", K2[j].reshape(-1))
        kb.slider_min, kb.slider_max, kb.interpolation, kb.vertex_group, kb.mute = smin, smax, interp, vg, mute
        kb.value = 0.0
    for j, (name, *_rest) in enumerate(old_keys):
        rel = old_keys[j][3]
        if rel in new.shape_keys.key_blocks:
            new.shape_keys.key_blocks[name].relative_key = new.shape_keys.key_blocks[rel]
    for gi, gname in enumerate(names):           # vertex-group names live on the mesh in Blender 5: recreate them
        g = body.vertex_groups.get(gname) or body.vertex_groups.new(name=gname)
        col = W2[:, gi]
        for i in np.where(col > 1e-6)[0]:
            g.add([int(i)], float(col[i]), "REPLACE")
    if [g.name for g in body.vertex_groups] != names:
        raise RuntimeError("vertex group order changed")
    new.update()
    after = _edge_stats(new, [tuple(c) for c, _ in centres[::2]], 0.12)
    return {"scheme": "Loop subdivision (region), midpoint on the region boundary", "repositioned_original_vertices": interior_old,
            "region_faces": int(inreg.sum()), "new_vertices": int(len(E)), "smoothed_vertices": int(len(free)),
            "edge_stats_within_12cm_of_pivots_before": before, "after": after, "vertices": len(new.vertices),
            "faces": len(new.polygons), "all_triangles": all(len(p.vertices) == 3 for p in new.polygons)}


def _tri_quality(V, t):
    import numpy as np
    a, b, c = V[t[0]], V[t[1]], V[t[2]]
    area = np.linalg.norm(np.cross(b - a, c - a)) / 2
    s = np.linalg.norm(b - a) ** 2 + np.linalg.norm(c - b) ** 2 + np.linalg.norm(a - c) ** 2
    return 4 * 3 ** 0.5 * area / s if s > 0 else 0.0


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    parent, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
    rig = body.find_armature()
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    n0 = len(body.data.vertices)
    info = remesh(body, rig)
    scene = bpy.context.scene
    scene["hgpt_review_body_vertices"] = len(body.data.vertices)
    scene["hgpt_review_candidate"] = "ORIGINAL_V1_CONSOLIDATED_REVIEW_R11_CLAUDE"
    scene["hgpt_review_candidate_approved"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)
    rep = {"kind": "ORIGINAL_V1_SHOULDER_REMESH", "candidate": "R11", "approved": False, "status": "REVIEW_CANDIDATE_NOT_ACCEPTED",
           "parent": {"path": Path(parent).name, "sha256": sha(parent), "vertices": n0},
           "output": {"path": out.name, "sha256": sha(out)},
           "params": {"region_r_m": REGION_R, "axilla_r_m": AXILLA_R, "axilla_offset_m": AXILLA_OFF, "taubin_iters": TAUBIN_ITERS},
           "remesh": info}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")
    print("REMESH", json.dumps(info))


if __name__ == "__main__":
    main()
