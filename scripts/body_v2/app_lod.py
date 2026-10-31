"""App LOD + clip-morph compression for the review-candidate GLB (in memory; nothing is saved to a .blend).

Why: the full candidate (347,917 vertices, 141 shape keys) cannot play on a phone - three.js keeps every morph target
of a mesh on the GPU as one texture (347,917 x 140 targets ~ 780 MB), and PT-App's intake preflight accepts dense
accessors only (dense, the 100 targets the press / curl / squat clips use would be ~ 470 MB).

What:
  1. LOD: the rest mesh decimated (collapse, mirrored in X so left and right stay alike).
  2. Every LOD vertex is mapped to its nearest point on the full rest surface (triangle + barycentric weights).
  3. Skin weights: the full binding interpolated there, the 8 largest kept (two glTF joint sets; see the ledger).
  4. Correctives: the baked clips only ever show sum_k w_k(frame) * target_k.  Over every baked frame of every clip
     that sum, sampled at the LOD vertices, is factored by SVD; the fewest components that reproduce every frame to
     within `tol` (max vertex error) become the LOD's shape keys ("HGPT_CLIP_PC_nn") and their coefficients the per-frame
     weights.  Exact for the baked clips up to `tol`; a new exercise needs the full key set and the drive rules.
Returns (lod object, per-clip per-frame component weights, report).
"""
from __future__ import annotations

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree


def _tris(me):
    return [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)]


def build(rig, body, bake, ratio=0.15, tol_mm=0.05, influences=8):
    me = body.data; key = me.shape_keys; kbs = key.key_blocks; n = len(me.vertices)
    base = np.empty(n * 3); kbs[0].data.foreach_get("co", base); base = base.reshape(-1, 3)
    tris = _tris(me)
    # 1. decimated copy of the rest mesh (no shape keys on the copy, so the modifier can run)
    tmp = bpy.data.meshes.new("HGPT_LOD_TMP"); tmp.from_pydata(base.tolist(), [], [tuple(p.vertices) for p in me.polygons])
    tmp.update()
    to = bpy.data.objects.new("HGPT_LOD_TMP", tmp); bpy.context.scene.collection.objects.link(to)
    mod = to.modifiers.new("decimate", "DECIMATE"); mod.decimate_type = "COLLAPSE"; mod.ratio = ratio
    mod.use_symmetry = True; mod.symmetry_axis = "X"; mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get(); ev = to.evaluated_get(dg)
    lm = bpy.data.meshes.new_from_object(ev); lm.name = "HGPT_BODY_APP_LOD"
    bpy.data.objects.remove(to); bpy.data.meshes.remove(tmp)
    nl = len(lm.vertices)
    L = np.empty(nl * 3); lm.vertices.foreach_get("co", L); L = L.reshape(-1, 3)
    # 2. map to the full rest surface
    bvh = BVHTree.FromPolygons(base.tolist(), tris, all_triangles=True)
    T = np.array(tris)
    tri_of = np.empty(nl, np.int64); bary = np.empty((nl, 3)); dist = np.empty(nl)
    for i, p in enumerate(L):
        loc, _, fi, d = bvh.find_nearest(p)
        a, b_, c = base[T[fi]]; v0, v1, v2 = b_ - a, c - a, np.array(loc) - a
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01 or 1e-30
        v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
        bary[i] = (1 - v - w, v, w); tri_of[i] = fi; dist[i] = d
    from scipy.sparse import csr_matrix
    Am = csr_matrix((bary.ravel(), (np.repeat(np.arange(nl), 3), T[tri_of].ravel())), shape=(nl, n))
    # 3. skin weights (deform groups), top `influences`, renormalised
    deform = [b.name for b in rig.data.bones if b.use_deform]
    gidx = {g.index: g.name for g in body.vertex_groups}; col = {nm: j for j, nm in enumerate(deform)}
    vi, bj, ww = [], [], []
    for v in me.vertices:
        for g in v.groups:
            nm = gidx.get(g.group)
            if nm in col and g.weight > 0:
                vi.append(v.index); bj.append(col[nm]); ww.append(g.weight)
    Wf = csr_matrix((np.array(ww), (np.array(vi), np.array(bj))), shape=(n, len(deform)))
    Wl = (Am @ Wf).toarray()
    order = np.argsort(-Wl, 1)[:, :influences]
    keep = np.zeros_like(Wl, bool); np.put_along_axis(keep, order, True, 1)
    Wl = np.where(keep & (Wl > 1e-6), Wl, 0.0); Wl /= np.maximum(Wl.sum(1, keepdims=True), 1e-12)
    lo = bpy.data.objects.new("HGPT_BODY_APP_LOD", lm); bpy.context.scene.collection.objects.link(lo)
    lo.parent = rig; lo.matrix_world = body.matrix_world.copy()      # skinned child of the rig, rest transform kept
    for j, nm in enumerate(deform):
        rows = np.nonzero(Wl[:, j])[0]
        if len(rows):
            g = lo.vertex_groups.new(name=nm)
            for r in rows:
                g.add([int(r)], float(Wl[r, j]), "REPLACE")
    am = lo.modifiers.new("Armature", "ARMATURE"); am.object = rig
    # 4. clip morphs: SVD of every baked frame's corrective sum at the LOD vertices
    clips = list(bake.keys())
    Wk = np.array([vals[1:] for c in clips for _, vals in bake[c]])            # (F, K): key values (no Basis)
    used = np.nonzero(np.abs(Wk).max(0) > 1e-5)[0]
    co = np.empty(n * 3)
    TL = np.zeros((len(used), nl * 3))
    for r, k in enumerate(used):
        kbs[int(k) + 1].data.foreach_get("co", co)
        TL[r] = (Am @ (co.reshape(-1, 3) - base)).ravel()
    D = Wk[:, used] @ TL                                                       # (F, 3 nl)
    U, S, Vt = np.linalg.svd(D, full_matrices=False)
    r_keep = len(S)
    for r_ in range(1, len(S) + 1):
        E = D - (U[:, :r_] * S[:r_]) @ Vt[:r_]
        if np.linalg.norm(E.reshape(len(D), nl, 3), axis=2).max() * 1000 <= tol_mm:
            r_keep = r_; break
    E = D - (U[:, :r_keep] * S[:r_keep]) @ Vt[:r_keep]
    err_mm = float(np.linalg.norm(E.reshape(len(D), nl, 3), axis=2).max() * 1000)
    lo.shape_key_add(name="Basis", from_mix=False)
    scale = np.abs(U[:, :r_keep]).max(0) + 1e-12                               # weights in [-1, 1]
    for j in range(r_keep):
        kb = lo.shape_key_add(name=f"HGPT_CLIP_PC_{j:02d}", from_mix=False)
        kb.data.foreach_set("co", (L + (S[j] * scale[j] * Vt[j]).reshape(-1, 3)).ravel())
    coef = U[:, :r_keep] / scale                                               # (F, r)
    weights, f0 = {}, 0
    for c in clips:
        weights[c] = coef[f0:f0 + len(bake[c])].tolist(); f0 += len(bake[c])
    lm.update()
    rep = {"lod_vertices": nl, "lod_triangles": len(lm.polygons), "full_vertices": n, "decimate_ratio": ratio,
           "rest_surface_distance_mm": {"max": round(float(dist.max() * 1000), 3), "p99": round(float(np.percentile(dist, 99) * 1000), 3)},
           "influences": influences, "corrective_targets_used_by_clips": int(len(used)),
           "clip_components": int(r_keep), "clip_component_max_error_mm": round(err_mm, 4), "tolerance_mm": tol_mm,
           "frames": int(len(D))}
    return lo, weights, rep
