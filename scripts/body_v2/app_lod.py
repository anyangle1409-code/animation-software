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
    lm.shade_smooth()                       # flat faces would make the exporter split every corner (313k for 52k)
    L = np.empty(nl * 3); lm.vertices.foreach_get("co", L); L = L.reshape(-1, 3)
    # 2. map to the full rest surface
    bvh = BVHTree.FromPolygons(base.tolist(), tris, all_triangles=True)
    T = np.array(tris)
    tri_of = np.empty(nl, np.int64); bary = np.empty((nl, 3)); dist = np.empty(nl)
    # nearest point whose face faces the same way: where surfaces touch at rest (hands on the thighs, the armpit, the
    # inner thighs) the plain nearest point can lie on the OTHER part, whose skinning would then drag the vertex along
    # (seen as long triangles from the hands to the hips when the arms rise)
    NL = np.empty(nl * 3); lm.vertices.foreach_get("normal", NL); NL = NL.reshape(-1, 3)
    FN = np.cross(base[T[:, 1]] - base[T[:, 0]], base[T[:, 2]] - base[T[:, 0]])
    FN /= np.maximum(np.linalg.norm(FN, axis=1, keepdims=True), 1e-15)
    flipped = 0
    for i, p in enumerate(L):
        loc, _, fi, d = bvh.find_nearest(p)
        if FN[fi] @ NL[i] < 0.3:
            best = None
            for loc2, _, fi2, d2 in bvh.find_nearest_range(p, max(0.006, 2 * d)):
                if FN[fi2] @ NL[i] >= 0.3 and (best is None or d2 < best[3]):
                    best = (loc2, None, fi2, d2)
            if best is not None:
                loc, _, fi, d = best; flipped += 1
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
    # barycentric blending mixes three corners' bone sets; past `influences` bones the cut drops real weight exactly
    # where weights change fastest (elbow crease with the twist bones, hip crease) and the deep bends then pull those
    # vertices up to ~4 cm off.  There the nearest corner's own binding is used (its top 8 are within 0.38 mm).
    over = (Wl > 1e-6).sum(1) > influences
    near = T[tri_of, np.argmax(bary, 1)]
    Wl[over] = Wf[near[over]].toarray()
    order = np.argsort(-Wl, 1)[:, :influences]
    keep = np.zeros_like(Wl, bool); np.put_along_axis(keep, order, True, 1)
    dropped = np.where(keep, 0.0, Wl).sum(1) / np.maximum(Wl.sum(1), 1e-12)
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
    # 4. clip morphs, fitted in POSED space: for every baked frame the full model is evaluated and mapped onto the LOD's
    #    surface points (the target), the LOD's own skinning response is measured (finite differences through a temporary
    #    key), and the rest-space offset that lands the LOD exactly on the target is solved per vertex.  (Interpolating the
    #    full keys' rest offsets instead breaks in contact creases: those offsets were solved through near-singular crease
    #    skinning and only work with each full vertex's exact weights - the curl peak and squat bottom were 45 mm off.)
    #    The per-frame offsets are then factored by SVD into the fewest components within `tol`.
    clips = list(bake.keys())
    dg = bpy.context.evaluated_depsgraph_get()
    lo.shape_key_add(name="Basis", from_mix=False); tmpk = lo.shape_key_add(name="HGPT_TMP_FD", from_mix=False)
    Ml = np.array(lo.matrix_world); Mb = np.array(body.matrix_world)

    def ev(ob, M):
        e = ob.evaluated_get(dg); m_ = e.to_mesh(); P = np.empty(len(m_.vertices) * 3)
        m_.vertices.foreach_get("co", P); e.to_mesh_clear()
        return P.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    C3 = T[tri_of]
    rows, frame_of, cond_max = [], [], 0.0
    CHECK = {}
    for c in clips:
        for f, (mats, vals) in enumerate(bake[c]):
            for pb in rig.pose.bones:
                pb.matrix_basis = mats[pb.name]
            for kb_, v in zip(kbs, vals):
                if kb_ != key.reference_key:
                    kb_.value = v
            tmpk.value = 0.0; bpy.context.view_layer.update()
            Pf = ev(body, Mb); target = np.einsum("nk,nkj->nj", bary, Pf[C3])
            P0 = ev(lo, Ml)
            Mv = np.zeros((nl, 3, 3)); tmpk.value = 1.0
            for j in range(3):
                d = np.zeros((nl, 3)); d[:, j] = 1e-3
                tmpk.data.foreach_set("co", (L + d).ravel()); lm.update(); bpy.context.view_layer.update()
                Mv[:, :, j] = (ev(lo, Ml) - P0) / 1e-3
            tmpk.value = 0.0; tmpk.data.foreach_set("co", L.ravel()); lm.update()
            sv = np.linalg.svd(Mv, compute_uv=False); cond_max = max(cond_max, float((sv[:, 0] / np.maximum(sv[:, 2], 1e-9)).max()))
            sol = np.linalg.solve(Mv, (target - P0)[:, :, None])[:, :, 0]
            rows.append(sol.ravel()); frame_of.append((c, f))
            if f == (len(bake[c]) - 1) // 2:                                  # check the solve lands on the target
                tmpk.data.foreach_set("co", (L + sol).ravel()); lm.update(); tmpk.value = 1.0
                bpy.context.view_layer.update()
                resid = float(np.linalg.norm(ev(lo, Ml) - target, axis=1).max() * 1000)
                tmpk.value = 0.0; tmpk.data.foreach_set("co", L.ravel()); lm.update()
                CHECK[f"{c}_{f}"] = {"posed_residual_mm": round(resid, 4), "target": target.astype(np.float32)}
    for kb_ in kbs[1:]:
        kb_.value = 0.0
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    lo.shape_key_remove(tmpk)
    D = np.array(rows)                                                         # (F, 3 nl), rest space
    used = np.nonzero(np.abs(np.array([vals[1:] for c in clips for _, vals in bake[c]])).max(0) > 1e-5)[0]
    U, S, Vt = np.linalg.svd(D, full_matrices=False)
    r_keep = len(S)
    for r_ in range(1, len(S) + 1):
        E = D - (U[:, :r_] * S[:r_]) @ Vt[:r_]
        if np.linalg.norm(E.reshape(len(D), nl, 3), axis=2).max() * 1000 <= tol_mm:
            r_keep = r_; break
    E = D - (U[:, :r_keep] * S[:r_keep]) @ Vt[:r_keep]
    err_mm = float(np.linalg.norm(E.reshape(len(D), nl, 3), axis=2).max() * 1000)
    scale = np.abs(U[:, :r_keep]).max(0) + 1e-12                               # weights in [-1, 1]
    for j in range(r_keep):
        kb = lo.shape_key_add(name=f"HGPT_CLIP_PC_{j:02d}", from_mix=False)
        kb.slider_min, kb.slider_max = -1.0, 1.0     # component weights are signed (a 0..1 slider clamped them)
        kb.data.foreach_set("co", (L + (S[j] * scale[j] * Vt[j]).reshape(-1, 3)).ravel())
    coef = U[:, :r_keep] / scale                                               # (F, r)
    weights, f0 = {}, 0
    for c in clips:
        weights[c] = coef[f0:f0 + len(bake[c])].tolist(); f0 += len(bake[c])
    lm.update()
    rep = {"lod_vertices": nl, "remapped_to_same_facing_surface": flipped, "lod_triangles": len(lm.polygons), "full_vertices": n, "decimate_ratio": ratio,
           "rest_surface_distance_mm": {"max": round(float(dist.max() * 1000), 3), "p99": round(float(np.percentile(dist, 99) * 1000), 3)},
           "influences": influences, "vertices_given_nearest_corner_binding": int(over.sum()),
           "max_weight_share_dropped": round(float(dropped.max()), 4), "corrective_targets_used_by_clips": int(len(used)),
           "clip_components": int(r_keep), "clip_component_max_error_mm": round(err_mm, 4), "tolerance_mm": tol_mm,
           "clip_morphs": "posed-space fit to the full model at every baked frame",
           "lod_skinning_condition_max": round(cond_max, 1),
           "frames": int(len(D))}
    rep["fit_check_posed_residual_mm"] = {k: v["posed_residual_mm"] for k, v in CHECK.items()}
    rep["_map"] = {"corners": T[tri_of], "bary": bary, **{f"target_{k}": v["target"] for k, v in CHECK.items()}}                      # for exact LOD-vs-full checks
    return lo, weights, rep
