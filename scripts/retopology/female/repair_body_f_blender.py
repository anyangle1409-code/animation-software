"""FEMALE F10a: repair hands, front armpits and the skin under the removable garments. NEW file; input unchanged.

Rest pose, vertex positions only (topology, UVs, weights and textures unchanged, so the bind and the bake stay valid).

Projection target: her FULL source surface (garments fused), first hit from outside along the vertex's own normal,
accepted only when the source normal there agrees with the vertex normal (dot > 0.3). Unlike nearest-point snapping
this cannot pull a finger onto its neighbour or the thumb onto the palm.

Regions:
  * HANDS: palm, fingers, thumb and wrist (t4_part >= 1), both sides;
  * ARMPITS: the front / inner armpit box on each side (torn, overlapping faces at the bra's side edge);
  * COVERED: body skin under the bra / shorts (a ray along the vertex normal meets a garment within 8 mm), plus a
    15 mm margin of uncovered skin round it (the fabric edge lips of the source are fused there).

Under the garments the skin is NOT her source surface (that is fabric). Conservative body: the source surface inset by
INSET(d) along the normal, d = distance (over the mesh) inside the covered area: 1.2 mm at the hem (just inside the
fabric's inner face, the fabric being lifted 0.6 mm and 1.2 mm thick) rising smoothly to 3 mm 20 mm inside, then
low-pass smoothed (Taubin) so strap, band and waistband lips of the fused fabric do not print on the skin; kept between
INSET and INSET + 4 mm below the source and at least 0.6 mm inside each garment's inner face.

Loop (ITER rounds): relax (pure umbrella for crumpled / overlapping vertices, tangential otherwise; region border
feathered over two rings) -> project / inset -> next. Then UNTANGLE: vertices of intersecting non-adjacent face pairs
(+ one ring) are umbrella-smoothed until no pair is left or the count stops falling.

Garments: vertices more than 2 mm off the source (+ lift) are relaxed and re-projected (the spike at the bra's side).

usage: python3.13 repair_body_f_blender.py -- <in .blend> <out NEW .blend> <report .json>
"""
import heapq
import json
import sys
from collections import Counter
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
ITER = 50
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]
src = BVHTree.FromPolygons([v.co.copy() for v in SRC.data.vertices], [tuple(p.vertices) for p in SRC.data.polygons])
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
rep = {"in": IN.name}


def garment_bvh(name):
    o = bpy.data.objects[name]; dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); m = oe.to_mesh()
    t = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [tuple(p.vertices) for p in m.polygons]); oe.to_mesh_clear(); return t


def count_intersections(bm):
    bm.faces.ensure_lookup_table(); t = BVHTree.FromBMesh(bm); bad = []
    for i, j in t.overlap(t):
        if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
            bad.append((i, j))
    return bad


bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
L4 = bm.verts.layers.int["t4_part"]
N = len(bm.verts); P = np.array([v.co[:] for v in bm.verts])
E = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
nbr = [[] for _ in range(N)]
for i, j in E:
    nbr[i].append(j); nbr[j].append(i)
FACES = [[v.index for v in f.verts] for f in bm.faces]
pre_bad = count_intersections(bm)
rep["intersections_before"] = len(pre_bad)


def vnormals(P):
    n = np.zeros_like(P)
    for f in FACES:
        a_, b_, c_ = P[f[0]], P[f[1]], P[f[2]]; fn = np.cross(b_ - a_, c_ - a_)
        if len(f) == 4:
            fn = fn + np.cross(c_ - a_, P[f[3]] - a_)
        n[f] += fn
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


# ---------------- regions
t4 = np.array([v[L4] for v in bm.verts])
hands = t4 >= 1
ax = np.abs(P[:, 0])
armpit = (ax > 0.10) & (ax < 0.23) & (P[:, 2] > 1.08) & (P[:, 2] < 1.32) & (P[:, 1] > -0.10) & (P[:, 1] < 0.09)
GB = [garment_bvh("HGPT_Female_Bra"), garment_bvh("HGPT_Female_Shorts")]
Nrm = vnormals(P)
covered = np.zeros(N, bool)
for i in range(N):
    if hands[i]:
        continue
    o = Vector(P[i]); d = Vector(Nrm[i])
    for g in GB:
        h = g.ray_cast(o - d * 0.001, d, 0.009)
        if h[0] is not None:
            covered[i] = True; break
rep["covered_vertices"] = int(covered.sum())


def dijkstra(seed_mask, limit):
    dist = np.full(N, np.inf); pq = []
    for i in np.where(seed_mask)[0]:
        dist[i] = 0.0; pq.append((0.0, i))
    heapq.heapify(pq)
    while pq:
        d0, i = heapq.heappop(pq)
        if d0 > dist[i] or d0 > limit:
            continue
        for j in nbr[i]:
            nd = d0 + float(np.linalg.norm(P[i] - P[j]))
            if nd < dist[j]:
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


d_in = dijkstra(~covered, 0.05)          # distance inside the covered area from its border
d_out = dijkstra(covered, 0.03)          # distance outside it
margin = (~covered) & (d_out < 0.025) & ~hands
s = np.clip(d_in / 0.020, 0, 1); INSET = np.where(covered, 0.003 * (s * s * (3 - 2 * s)), 0.0)
region = hands | armpit | covered | margin
fixed_ring = dijkstra(~region, 0.012)     # feather: weight 0 at the region border, 1 two rings (~10 mm) in
W = np.clip(fixed_ring / 0.010, 0, 1)
rep["region_vertices"] = {"hands": int(hands.sum()), "armpits": int(armpit.sum()), "covered": int(covered.sum()), "margin": int(margin.sum())}
P0 = P.copy()
idx = np.where(region)[0]


def umbrella(P, ids):
    return np.array([P[nbr[i]].mean(0) for i in ids])


def crumpled(P, Nrm, ids):
    """vertices whose neighbours' normals disagree with their own (folded / overlapping faces)"""
    c = np.zeros(len(ids), bool)
    for k, i in enumerate(ids):
        c[k] = np.min(Nrm[nbr[i]] @ Nrm[i]) < 0.5
    return c


# armpit: each vertex keeps to its own side of the pit. Label: ARM if its dominant weight is an upper-arm bone, else
# TORSO. In the pit (armpit box, z < 1.27) a torso vertex rejects surface that faces the midline (the arm's inner
# face), an arm vertex rejects surface that faces away from the midline medially of it (the chest wall); a rejected
# hit lets the ray continue to the next surface along it.
vgn = {g.index: g.name for g in body.vertex_groups}
is_arm = np.zeros(N, bool)
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda g: g.weight); is_arm[v.index] = vgn.get(g.group, "").startswith(("upperarm", "forearm"))
pit = armpit & (P[:, 2] < 1.27)


def side_ok(i, hp, hn):
    if not pit[i]:
        return True
    sx = 1.0 if P[i, 0] > 0 else -1.0
    if is_arm[i]:
        return not (sx * hn.x > 0.5 and sx * (hp.x - P[i, 0]) < -0.004)
    return sx * hn.x > -0.3


def project(P, Nrm, ids):
    out = P[ids].copy(); hit = np.zeros(len(ids), bool)
    for k, i in enumerate(ids):
        n = Vector(Nrm[i]); deep = armpit[i]
        o = Vector(P[i]) + n * (0.008 if deep else 0.005); rng = 0.025 if deep else 0.011; h = None
        for _ in range(4):
            h_ = src.ray_cast(o, -n, rng)
            if h_[0] is None:
                break
            if h_[1].dot(n) > 0.3 and side_ok(i, h_[0], h_[1]):
                h = h_; break
            rng -= h_[3] + 0.0005; o = h_[0] - n * 0.0005
            if rng <= 0:
                break
        if h is None:
            h_ = src.find_nearest(Vector(P[i]), 0.012)
            if h_[0] is None or h_[1].dot(n) < 0.5 or not side_ok(i, h_[0], h_[1]):
                continue
            h = h_
        out[k] = np.array(h[0][:]) - Nrm[i] * INSET[i]; hit[k] = True
    return out, hit


for it in range(ITER):
    Nrm = vnormals(P)
    U = umbrella(P, idx); D = U - P[idx]
    cr = crumpled(P, Nrm, idx)
    tang = D - (D * Nrm[idx]).sum(1, keepdims=True) * Nrm[idx]
    # folded vertices: full umbrella; otherwise tangential only, weak on the hands (texture: nails, creases stay put)
    tl = np.where(hands[idx], 0.05, np.where(armpit[idx], 0.6, 0.4))
    step = np.where(cr[:, None], D * 0.5, tang * tl[:, None])
    P[idx] += step * W[idx, None]
    if it < ITER - 3:                      # last rounds: smoothing only under the garments
        Nrm = vnormals(P); tgt, hit = project(P, Nrm, idx)
        blend = np.where(covered[idx], 0.5, 1.0)[:, None] * W[idx, None] * hit[:, None]
        P[idx] = P[idx] + (tgt - P[idx]) * blend
# under the garments: bi-Laplacian low-pass (sparse solve) of covered + margin with the outer ring fixed: removes the
# fused fabric's strap / band / waistband lips (features of ~1-2 cm) and keeps the large forms (breasts, glutes, abdomen)
import scipy.sparse as sp  # noqa: E402
import scipy.sparse.linalg as spl  # noqa: E402
ALPHA = 0.08
# extra low-pass zones on visible skin: the upper back / trapezius band (her source's right back strap is asymmetric
# and left fused lips outside the mirrored bra) and the sternum between the breasts (the fused centre gore's V fold)
upper_back = (P[:, 1] > 0.0) & (P[:, 2] > 1.22) & (P[:, 2] < 1.45) & (np.abs(P[:, 0]) < 0.16)
sternum = (P[:, 1] < 0.0) & (P[:, 2] > 1.17) & (P[:, 2] < 1.31) & (np.abs(P[:, 0]) < 0.05)
extra = (upper_back | sternum) & ~covered & ~hands
margin = margin & ~(armpit & ~covered)
free = (covered | margin | extra) & ~armpit     # the armpits keep the projected loop result (no seam at the bra side)
rep["extra_lowpass_vertices"] = int(extra.sum())
fi = np.where(free)[0]; pos = -np.ones(N, int); pos[fi] = np.arange(len(fi))
rows, cols, vals = [], [], []
for i in range(N):                       # uniform Laplacian over all vertices touching the free set
    if not (free[i] or any(free[j] for j in nbr[i])):
        continue
    rows.append(i); cols.append(i); vals.append(1.0)
    for j in nbr[i]:
        rows.append(i); cols.append(j); vals.append(-1.0 / len(nbr[i]))
Lf = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
A = Lf[:, fi]; Bc = Lf[:, ~free]
wgt = np.where(covered[fi], ALPHA, np.where(margin[fi], ALPHA * (1 + 10 * np.clip(d_out[fi] / 0.025, 0, 1) ** 2), 0.015))   # visible skin: stiffer away from the hem
M = (A.T @ A + sp.diags(wgt)).tocsc()
rhs = -(A.T @ (Bc @ P[~free])) + wgt[:, None] * P[fi]
P[fi] = np.column_stack([spl.spsolve(M, rhs[:, k]) for k in range(3)])
Nrm = vnormals(P)
clamped = 0
for i in np.where(free)[0]:
    n = Vector(Nrm[i])
    h = src.find_nearest(Vector(P[i]))
    if h[0] is not None:
        depth = (h[0] - Vector(P[i])).dot(h[1])     # covered: 1.2-8 mm below her (fabric) surface; visible skin: not above it, <= 3 mm below
        nd = (min(max(depth, -0.003 if d_in[i] > 0.006 else 0.0), 0.008) if covered[i] else min(max(depth, -0.004), 0.006) if sternum[i]
              else min(max(depth, -0.0003), 0.004))
        if abs(nd - depth) > 1e-6:
            P[i] = np.array(h[0][:]) - np.array(h[1][:]) * nd; clamped += 1
    if not covered[i] or d_in[i] < 0.006:          # at the hem the skin meets the fabric edge (no step)
        continue
    for g in GB:                                            # >= 0.5 mm inside the garment's inner face
        gh = g.ray_cast(Vector(P[i]) - n * 0.0005, n, 0.006)
        if gh[0] is not None and gh[3] < 0.001:
            P[i] = P[i] - Nrm[i] * (0.001 - gh[3])
rep["covered_depth_clamped"] = clamped
# ---------------- armpit pleats: excess mesh area folded into a lip (her left pit, where the coarse torso shell
# meets the dense arm). Faces whose normal disagrees with her surface (dot < 0.3) or that fold against a neighbour
# seed a patch (+ 25 mm over the mesh); the patch becomes a biharmonic membrane (outer ring fixed: smooth, one sheet,
# no fold) and is then projected back onto her surface along the membrane normal (own side of the pit only).
Nrm = vnormals(P)
seed = np.zeros(N, bool)
for f in FACES:
    if not armpit[f[0]]:
        continue
    c = P[f].mean(0); fn = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]]); ln = np.linalg.norm(fn)
    if ln < 1e-12:
        seed[f] = True; continue
    h = src.find_nearest(Vector(c))
    if h[0] is not None and np.dot(fn / ln, h[1][:]) < 0.3:
        seed[f] = True
seed &= armpit
patch = (dijkstra(seed, 0.03) < 0.025) & armpit if seed.any() else seed
rep["pleat_seed_vertices"] = int(seed.sum()); rep["pleat_patch_vertices"] = int(patch.sum())


def membrane_patch(patch, out_off, rng0, iters, agree):
    """biharmonic membrane over the patch (outer ring fixed), then relax + project along the membrane normal"""
    global P
    pi_ = np.where(patch)[0]
    rows, cols, vals = [], [], []
    for i in range(N):
        if not (patch[i] or any(patch[j] for j in nbr[i])):
            continue
        rows.append(i); cols.append(i); vals.append(1.0)
        for j in nbr[i]:
            rows.append(i); cols.append(j); vals.append(-1.0 / len(nbr[i]))
    Lp = sp.csr_matrix((vals, (rows, cols)), shape=(N, N)); Ap = Lp[:, pi_]; Bp = Lp[:, ~patch]
    Mp = (Ap.T @ Ap + sp.identity(len(pi_)) * 1e-6).tocsc(); rp = -(Ap.T @ (Bp @ P[~patch]))
    P[pi_] = np.column_stack([spl.spsolve(Mp, rp[:, k]) for k in range(3)])
    for _ in range(iters):
        Nrm = vnormals(P)
        D = umbrella(P, pi_) - P[pi_]
        P[pi_] += (D - (D * Nrm[pi_]).sum(1, keepdims=True) * Nrm[pi_]) * 0.5
        Nrm = vnormals(P)
        for i in pi_:
            n = Vector(Nrm[i]); o = Vector(P[i]) + n * out_off; rng = rng0
            for _k in range(5):
                h = src.ray_cast(o, -n, rng)
                if h[0] is None:
                    break
                if h[1].dot(n) > agree and side_ok(i, h[0], h[1]):
                    P[i] = np.array(h[0][:]) - Nrm[i] * INSET[i]; break
                rng -= h[3] + 0.0005; o = h[0] - n * 0.0005
                if rng <= 0:
                    break


if patch.any():
    membrane_patch(patch, 0.015, 0.04, 8, 0.2)
# thumb junctions: the thumb tube (t4_part 20 / 21) meets the palm across a gash (palm and back of the hand). Patch:
# thumb base ring (part 20) + 18 mm round it over the hand (not the fingers); rays stay short (no jump to the index)
tb = t4 == 20
dtb = dijkstra(tb, 0.045)
tpatch = (dtb < 0.035) & ~np.isin(t4, (10, 11, 12, 13)) & (hands | (dtb < 0.03))
tpatch &= ~((t4 == 21) & (dtb > 0.015))           # the thumb itself only near its base
rep["thumb_junction_patch_vertices"] = int(tpatch.sum())
if tpatch.any():
    membrane_patch(tpatch, 0.010, 0.022, 12, 0.3)
# thumb collar through the palm: the thumb's base ring (part 20) is plugged into the hand from the front and palm
# faces cross it. Palm vertices inside the thumb's base cylinder (axis: principal direction of the thumb, from the
# collar's centre; radius: the collar's) are pushed radially out to 1.08 x that radius (they become the rim), then
# lightly relaxed.
pushed = 0
for sgn in (1, -1):
    C = np.where((t4 == 20) & (np.sign(P[:, 0]) == sgn))[0]; T = np.where((t4 == 21) & (np.sign(P[:, 0]) == sgn))[0]
    if len(C) < 8 or len(T) < 8:
        continue
    o = P[C].mean(0); X = np.vstack([P[C], P[T]]) - o
    d = np.linalg.svd(X, full_matrices=False)[2][0]
    if np.dot(P[T].mean(0) - o, d) < 0:
        d = -d
    rc = np.median(np.linalg.norm((P[C] - o) - np.outer((P[C] - o) @ d, d), axis=1))
    cand = np.where((t4 == 1) & (np.sign(P[:, 0]) == sgn))[0]
    for _ in range(3):
        R = P[cand] - o; ta = R @ d; radial = R - np.outer(ta, d); r = np.linalg.norm(radial, axis=1)
        m = (ta > -0.015) & (ta < 0.012) & (r < rc * 1.08) & (r > 1e-6)
        ids = cand[m]; P[ids] = o + np.outer(ta[m], d) + radial[m] / r[m, None] * rc * 1.08; pushed += int(m.sum())
        ring = np.array(sorted({j for i in ids for j in nbr[i]} - set(C.tolist()) - set(T.tolist())), int)
        if len(ring):
            P[ring] += (umbrella(P, ring) - P[ring]) * 0.3
    rep[f"thumb_{'left' if sgn > 0 else 'right'}_collar_radius_mm"] = round(float(rc) * 1000, 1)
rep["palm_vertices_pushed_out_of_thumb"] = pushed
# palm fold on the thumb side: the palm surface folds inward (two layers inside her hand) where the collar attaches.
# Palm / collar / thumb-base vertices (+ wrist within 30 mm of the collar): relax (tangential, full umbrella where
# folded) and snap to the nearest point of her surface (within 12 mm; no fingers in the set, so no digit can fuse).
dcol = dijkstra(t4 == 20, 0.04)
fold = (np.isin(t4, (1, 20)) | ((t4 == 21) & (dcol < 0.015)) | ((t4 == 0) & (dcol < 0.03)))
fi_ = np.where(fold)[0]; fw = np.clip(dijkstra(~fold, 0.01)[fi_] / 0.006, 0, 1)
for it_ in range(45):
    Nrm = vnormals(P); D = umbrella(P, fi_) - P[fi_]; cr = crumpled(P, Nrm, fi_)
    tang = D - (D * Nrm[fi_]).sum(1, keepdims=True) * Nrm[fi_]
    P[fi_] += np.where(cr[:, None], D * 0.6, tang * 0.7) * fw[:, None]
    if it_ % 3 and it_ < 44:                     # snap every third round (and the last) only: the excess area spreads out first
        continue
    for k, i in enumerate(fi_):
        h = src.find_nearest(Vector(P[i]), 0.012)
        if h[0] is not None:
            P[i] = P[i] + (np.array(h[0][:]) - P[i]) * fw[k]
rep["hand_fold_vertices"] = int(fold.sum())
# thumb collar too narrow (a pinch where the thumb meets the hand): the collar ring (part 20) is scaled radially about
# the thumb axis to the radius of the thumb's own base (part 21 within 15 mm of the collar)
for sgn in (1, -1):
    C = np.where((t4 == 20) & (np.sign(P[:, 0]) == sgn))[0]; T = np.where((t4 == 21) & (np.sign(P[:, 0]) == sgn))[0]
    if len(C) < 8 or len(T) < 8:
        continue
    dc_ = dijkstra((t4 == 20) & (np.sign(P[:, 0]) == sgn), 0.02); TB = T[dc_[T] < 0.015]
    o = P[C].mean(0); d = np.linalg.svd(np.vstack([P[C], P[T]]) - o, full_matrices=False)[2][0]
    if np.dot(P[T].mean(0) - o, d) < 0:
        d = -d
    def rad(ix):
        R = P[ix] - o; return R - np.outer(R @ d, d)
    rC = np.median(np.linalg.norm(rad(C), axis=1)); rT = np.median(np.linalg.norm(rad(TB), axis=1)) if len(TB) else rC
    if rT > rC * 1.1:
        R = rad(C); P[C] += R * (rT / rC - 1.0)
    rep[f"thumb_{'left' if sgn > 0 else 'right'}_collar_radius_mm_before_after"] = [round(float(rC) * 1000, 1), round(float(max(rT, rC)) * 1000, 1)]
# thumb-side crease: her source has a deep groove where the adducted thumb presses on the palm; snapping folds the
# palm into it (edges folded up to 170 deg from the wrist to the thumb base). Vertices of hand / wrist edges folded
# more than 60 deg, + 10 mm round them (fingers excluded), are umbrella-smoothed WITHOUT projection (taper to 0 at the
# zone edge): a rounded thenar web instead of a cut. Local deviation from her surface is reported.
def sharp_verts():
    out = set()
    Nf = {}
    for k, f in enumerate(FACES):
        if hands[f[0]] or (t4[f[0]] == 0 and abs(P[f[0], 0]) > 0.36 and P[f[0], 2] < 0.95):
            n_ = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]]); l_ = np.linalg.norm(n_)
            if l_ > 0:
                Nf[k] = n_ / l_
    for e in bm.edges:
        lf = [g.index for g in e.link_faces]
        if len(lf) == 2 and lf[0] in Nf and lf[1] in Nf and np.dot(Nf[lf[0]], Nf[lf[1]]) < 0.5:
            out.update(v.index for v in e.verts)
    return out


bm.faces.ensure_lookup_table(); P_c0 = P.copy(); seeds = []; fil_all = set()
for _round in range(3):
    sv = sharp_verts(); smask = np.zeros(N, bool); smask[list(sv)] = True
    smask &= ~np.isin(t4, (10, 11, 12, 13)); seeds.append(int(smask.sum()))
    if not smask.any():
        break
    dsh = dijkstra(smask, 0.015); fil = np.where((dsh < 0.010) & ~np.isin(t4, (10, 11, 12, 13)))[0]
    fwt = (1 - dsh[fil] / 0.010) ** 0.5; fil_all.update(fil.tolist())
    for _ in range(30):
        P[fil] += (umbrella(P, fil) - P[fil]) * (0.5 * fwt)[:, None]
fil = np.array(sorted(fil_all), int); dv = np.linalg.norm(P[fil] - P_c0[fil], axis=1) * 1000
rep["hand_crease_seed_vertices"] = seeds; rep["hand_crease_smoothed_vertices"] = int(len(fil))
rep["hand_crease_moved_mm_p95_max"] = [round(float(np.percentile(dv, 95)), 2), round(float(dv.max()), 2)] if len(fil) else []
# the pit itself: her source carries the bra side panel's fused edge lip down into the pit; a light Taubin low-pass
# (pit vertices, feathered) keeps it from printing on the skin
pit_ids = np.where(pit)[0]; pw = W[pit_ids]
for _ in range(15):
    for f_ in (0.5, -0.53):
        P[pit_ids] += (umbrella(P, pit_ids) - P[pit_ids]) * (f_ * pw)[:, None]
for v in bm.verts:
    v.co = Vector(P[v.index])
# ---------------- untangle
hist = []
for rnd in range(60):
    bad = count_intersections(bm); hist.append(len(bad))
    if not bad or (rnd > 10 and len(bad) >= min(hist[:-1])):
        if not bad:
            break
    vs = set()
    for i, j in bad:
        for f in (bm.faces[i], bm.faces[j]):
            for v in f.verts:
                vs.add(v.index); vs.update(nbr[v.index])
    ids = np.array(sorted(vs)); P = np.array([v.co[:] for v in bm.verts])
    P[ids] += (umbrella(P, ids) - P[ids]) * 0.5
    for v in bm.verts:
        v.co = Vector(P[v.index])
    if rnd > 25 and hist[-1] >= hist[-6]:
        break
rep["untangle_rounds"] = hist
post_bad = count_intersections(bm)
c = Counter()
for i, j in post_bad:
    f = bm.faces[i]; p = max(v[L4] for v in f.verts); c["hand" if p >= 1 else ("covered" if covered[f.verts[0].index] else "other")] += 1
rep["intersections_after"] = len(post_bad); rep["intersections_after_by_region"] = dict(c)
P = np.array([v.co[:] for v in bm.verts]); mv = np.linalg.norm(P - P0, axis=1) * 1000
rep["moved_mm"] = {k: [round(float(np.percentile(mv[m], q)), 2) for q in (50, 95, 100)] for k, m in
                   (("hands", hands), ("armpits", armpit), ("covered", covered), ("margin", margin), ("rest", ~region))}
bm.to_mesh(me); me.update(); bm.free()
import os  # noqa: E402
if os.environ.get("F10_DEBUG"):
    ca = me.color_attributes.new("F10_region", "FLOAT_COLOR", "POINT")
    cl = {0: (0.8, 0.8, 0.8, 1), 1: (0.2, 0.8, 0.2, 1), 2: (0.9, 0.2, 0.2, 1), 3: (0.2, 0.3, 0.9, 1), 4: (0.9, 0.8, 0.1, 1)}
    for i in range(N):
        k = 4 if hands[i] else 2 if covered[i] else 1 if margin[i] else 3 if armpit[i] else 0
        ca.data[i].color = cl[k]
# ---------------- garments: spikes / folds off the source
for name in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[name]; gm = o.data; g = bmesh.new(); g.from_mesh(gm); g.verts.ensure_lookup_table()
    GP = np.array([v.co[:] for v in g.verts]); gn = [[] for _ in GP]
    for e in g.edges:
        gn[e.verts[0].index].append(e.verts[1].index); gn[e.verts[1].index].append(e.verts[0].index)
    off = np.array([abs(src.find_nearest(Vector(p))[3] - 0.0006) for p in GP]); bad = np.where(off > 0.002)[0]
    grow = set(bad.tolist())
    for _ in range(2):
        grow |= {j for i in list(grow) for j in gn[i]}
    gi = np.array(sorted(grow), int)
    for _ in range(12):
        if len(gi) == 0:
            break
        bnd = np.array([g.verts[i].is_boundary for i in gi])
        U = np.array([GP[gn[i]].mean(0) for i in gi]); GP[gi] += (U - GP[gi]) * np.where(bnd, 0.3, 0.6)[:, None]
        for k, i in enumerate(gi):
            h = src.find_nearest(Vector(GP[i]))
            if h[0] is not None:
                GP[i] = np.array(h[0][:]) + np.array(h[1][:]) * 0.0006
    for v in g.verts:
        v.co = Vector(GP[v.index])
    g.to_mesh(gm); gm.update(); g.free()
    rep[name + "_vertices_off_source_fixed"] = int(len(bad))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("REPAIR", json.dumps(rep))
