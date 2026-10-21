"""Body v2: refine the coarse torso / pelvis / glute / neck mesh (Claude, 21 Oct 2026).  Review candidate only.

Owner (21 Oct), after draft v4b ("This is how the pelvis and groin and legs should look" - belly button, inguinal V,
pubic wedge, gluteal fold): the R41 body has 13-15 mm edges on the belly and groin (3.5-4 mm on the arms and thighs),
too coarse for any of those to form; owner chose "Refine the torso mesh".

refine(body): in the region rest z [zlo, zhi], triangles whose longest edge is over th_mm are split at the edge midpoints
(bmesh subdivide, grid fill, then triangulated), repeated until none are left.  Linear subdivision interpolates every
per-vertex layer - skin weights and all shape keys (the correctives) - so the new vertices deform exactly as the old
surface did.  Then the new vertices are placed by Phong tessellation on their old triangles (old vertices unchanged) to round the
facets; the same rest
displacement is added to every shape key, so the correctives' deltas stay the interpolated ones.
Also returns the exact linear map of the new mesh from the old one (each vertex = weights over an old triangle), used
to carry 21,600-vertex arrays (dense correctives, earlier offsets) over to the refined mesh.
"""
import bmesh
import bpy
import numpy as np
from mathutils.bvhtree import BVHTree


def refine(body, th_mm=8.0, zlo=-1.0, zhi=1.95, phong_alpha=0.75, max_rounds=6, spots=()):
    """spots: extra (centre xyz, radius m, threshold mm) discs refined further, after the main pass (R103: the nipples -
    ~8 mm edges cannot carry a nipple a few mm across)"""
    me = body.data
    n0 = len(me.vertices)
    old = np.array([v.co[:] for v in me.vertices])
    old_tris = [tuple(p.vertices) for p in me.polygons]
    assert all(len(t) == 3 for t in old_tris), "R41 body is expected to be all triangles"
    bm = bmesh.new(); bm.from_mesh(me)
    th = th_mm / 1000.0
    rounds = []
    for _ in range(max_rounds):
        bm.faces.ensure_lookup_table()
        edges = set()
        for f in bm.faces:
            c = sum((v.co for v in f.verts), f.verts[0].co * 0) / len(f.verts)
            if zlo < c.z < zhi and max(e.calc_length() for e in f.edges) > th:
                # all three edges (splitting only the long ones left degenerate triangles that never converged, v5k)
                edges.update(f.edges)
        if not edges:
            break
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True, smooth=0.0)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        rounds.append(len(edges))
    from mathutils import Vector as _V
    for c_, r_, t_ in spots:
        c_ = _V(c_)
        for _ in range(max_rounds):
            bm.faces.ensure_lookup_table()
            edges = set()
            for f in bm.faces:
                c = sum((v.co for v in f.verts), f.verts[0].co * 0) / len(f.verts)
                if (c - c_).length < r_ and max(e.calc_length() for e in f.edges) > t_ / 1000.0:
                    edges.update(f.edges)
            if not edges:
                break
            bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True, smooth=0.0)
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
            rounds.append(len(edges))
    bm.to_mesh(me); bm.free(); me.update()
    nv = len(me.vertices)
    P = np.array([v.co[:] for v in me.vertices])
    assert np.allclose(P[:n0], old), "old vertices must keep their index and position"
    # exact linear map: every vertex lies on an old triangle (subdivision was linear)
    tree = BVHTree.FromPolygons([tuple(v) for v in old], old_tris, all_triangles=True)
    map_idx = np.zeros((nv, 3), np.int64); map_w = np.zeros((nv, 3))
    map_idx[:n0, 0] = np.arange(n0); map_w[:n0, 0] = 1.0
    OT = np.array(old_tris)
    for i in range(n0, nv):
        loc, _, fi, _ = tree.find_nearest(P[i])
        a, b, c = old[OT[fi]]
        v0, v1, v2 = b - a, c - a, np.array(loc) - a
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den
        map_idx[i] = OT[fi]; map_w[i] = (1 - w1 - w2, w1, w2)
    map_err = float(np.abs((old[map_idx] * map_w[..., None]).sum(1) - P).max())
    # round the facets: Phong tessellation (Boubekeur & Alexa 2008) of each new vertex on its old triangle, from the old
    # corner positions and area-weighted vertex normals - exact and local: old vertices stay, nothing slides sideways.
    # (Taubin relaxing on R41's long thin triangles - up to 30-40 mm long - left ripples and neck pleats, v5c.)
    OT = np.array(old_tris)
    fn = np.cross(old[OT[:, 1]] - old[OT[:, 0]], old[OT[:, 2]] - old[OT[:, 0]])
    vn = np.zeros_like(old); np.add.at(vn, OT.ravel(), np.repeat(fn, 3, axis=0))
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    plin = (old[map_idx] * map_w[..., None]).sum(1)
    Pj, Nj = old[map_idx], vn[map_idx]
    proj = plin[:, None, :] - ((plin[:, None, :] - Pj) * Nj).sum(2)[..., None] * Nj
    pph = (proj * map_w[..., None]).sum(1)
    Q = (1 - phong_alpha) * plin + phong_alpha * pph
    Q[:n0] = old
    tris = np.array([p.vertices[:] for p in me.polygons])
    D = Q - P
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            co = np.empty(nv * 3); kb.data.foreach_get("co", co)
            kb.data.foreach_set("co", (co.reshape(-1, 3) + D).ravel())
    co = np.empty(nv * 3); me.vertices.foreach_get("co", co); me.vertices.foreach_set("co", (co.reshape(-1, 3) + D).ravel())
    me.update()
    E = np.concatenate([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    L = np.linalg.norm(Q[E[:, 0]] - Q[E[:, 1]], axis=1); mz = 0.5 * (Q[E[:, 0], 2] + Q[E[:, 1], 2])
    inreg = (mz > zlo) & (mz < zhi)
    report = {"vertices_before": n0, "vertices_after": nv, "triangles_after": len(tris), "rounds_edges_split": rounds,
              "threshold_mm": th_mm, "region_z": [zlo, zhi], "linear_map_max_err_mm": round(map_err * 1000, 4),
              "max_smoothing_move_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2),
              "region_edge_mm_median_max": [round(float(np.median(L[inreg]) * 1000), 2), round(float(L[inreg].max() * 1000), 2)]}
    return report, map_idx, map_w
