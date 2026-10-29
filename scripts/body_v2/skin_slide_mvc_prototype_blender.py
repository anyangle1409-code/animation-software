"""Prototype (read-only): skin slide by rest mean-value coordinates, measured at the press lockout.

lockout_stretch_diag_blender.py: the lockout stretch is plain skinning (~10,700 edges > 2x with no corrective keys; the
keys change it little) - the arm bones pull the side-chest, lat and back skin up with them.  Real skin slides: the area
the opening axilla needs is drawn from a wide surround.  Earlier tries: a uniform Laplacian slide (evens out vertex
SPACING, so the dense rest armpit got more stretched) and tangential edge springs (fold-overs: nothing stops a vertex
crossing its neighbours).  Here each vertex's rest 1-ring gives positive mean-value weights (Floater 2003) that reproduce
its rest position in its tangent plane exactly; in the posed mesh the skin region is re-solved so every vertex sits, in
its posed tangent plane, at the same weighted barycentre of its neighbours (boundary fixed; normal part of the posed
Laplacian kept: the vertices move only within their tangent planes), then projected back onto the posed surface.  Positive barycentric weights make
this a Tutte-type map: no fold-overs in the planar case, and the rest parametrisation is the fixed point at rest.

usage: python3.13 skin_slide_mvc_prototype_blender.py -- <body.blend> <r57src> <out_dir> [radius_m=0.30] [rounds=3] [damping=1] [pin_m=0]
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import splu

a = sys.argv[sys.argv.index("--") + 1:]; SRC, ROOT, OUT = a[0], a[1], a[2]
RAD = float(a[3]) if len(a) > 3 else 0.30
ROUNDS = int(a[4]) if len(a) > 4 else 3
DAMP = float(a[5]) if len(a) > 5 else 1.0                  # fraction of each linearised tangential step taken
PIN = float(a[6]) if len(a) > 6 else 0.0                   # >0: pin skin with another sheet this near along its normal
METHOD = os.environ.get("V2_SLIDE_METHOD", "mvc")           # mvc (this file) or walk (r57 original_v1_skin_slide)
os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT + "/scripts", ROOT + "/scripts/anatomy_fit", os.path.dirname(os.path.abspath(__file__))]
bpy.ops.wm.open_mainfile(filepath=SRC)
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402
import build_functional_shoulder_correction_blender as correction  # noqa: E402
import functional_shoulder_correction as corr  # noqa: E402
import shoulder_girdle_candidate as girdle  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
AX = {}
for side, name in correction.HUMERI:
    b = rig.data.bones[name]
    AX[name] = corr.humeral_axial_angle_deg(tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
POLY3 = np.array([p.vertices[:3] for p in me.polygons])
ek = {}
for fi, p in enumerate(me.polygons):
    for e_ in p.edge_keys:
        ek.setdefault(e_, []).append(fi)
EF = np.array([(k[0], k[1], f[0], f[1]) for k, f in ek.items() if len(f) == 2])
GN = [g.name for g in body.vertex_groups]
DOM = np.full(n, "", dtype=object); DW = np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.weight > DW[v.index]:
            DW[v.index], DOM[v.index] = g.weight, GN[g.group]
EXCL = np.array([any(k in d for k in ("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal", "forearm",
                                      "head", "neck", "jaw", "eye", "foot", "toe")) for d in DOM])
L0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1)


def normals(P):
    fn = np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]]); vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, TRI[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)


# ---- rest mean-value weights over each vertex's edge 1-ring, in its rest tangent plane
NR = normals(R)
nbr = [[] for _ in range(n)]
for i, j in E:
    nbr[i].append(j); nbr[j].append(i)
rows, cols, vals = [], [], []
bad_ring = 0
for i in range(n):
    J = np.array(nbr[i])
    if len(J) < 3:
        continue
    nn = NR[i]; t1 = np.cross(nn, [1.0, 0, 0] if abs(nn[0]) < 0.9 else [0, 1.0, 0]); t1 /= np.linalg.norm(t1); t2 = np.cross(nn, t1)
    d = R[J] - R[i]; p = np.c_[d @ t1, d @ t2]
    ang = np.arctan2(p[:, 1], p[:, 0]); o = np.argsort(ang); J, p, ang = J[o], p[o], ang[o]
    r = np.maximum(np.linalg.norm(p, axis=1), 1e-12)
    al = np.diff(np.r_[ang, ang[0] + 2 * np.pi])                # angle from neighbour k to k+1
    if (al >= np.pi - 1e-3).any():
        bad_ring += 1
    th = np.tan(np.clip(al, 1e-6, np.pi - 1e-3) / 2)
    w = (th + np.roll(th, 1)) / r                               # tan(a_{k-1}/2) + tan(a_k/2), over |p_k|
    w /= w.sum()
    rows += [i] * len(J); cols += J.tolist(); vals += w.tolist()
W = csr_matrix((vals, (rows, cols)), shape=(n, n))
A_ = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))


def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    P = np.empty(n * 3); m.vertices.foreach_get("co", P); e.to_mesh_clear(); return P.reshape(-1, 3)


def metrics(P, m=None):
    fa, fb, fc = P[POLY3[:, 0]], P[POLY3[:, 1]], P[POLY3[:, 2]]
    fn = np.cross(fb - fa, fc - fa); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
    d = np.einsum("ij,ij->i", fn[EF[:, 2]], fn[EF[:, 3]])
    ok = ~(EXCL[E[:, 0]] | EXCL[E[:, 1]])
    ratio = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-12)
    okf = ~(EXCL[EF[:, 0]] | EXCL[EF[:, 1]])
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    pairs = np.array(bvh.overlap(bvh), dtype=np.int64).reshape(-1, 2)
    if len(pairs):
        pairs = pairs[pairs[:, 0] < pairs[:, 1]]
        ta, tb = TRI[pairs[:, 0]], TRI[pairs[:, 1]]
        pairs = pairs[~(ta[:, :, None] == tb[:, None, :]).any(axis=(1, 2))]
    zc = {}
    if len(pairs):
        cz = R[TRI[pairs[:, 0], 0]]
        for nm, mz in (("axilla", (np.abs(cz[:, 0]) > 0.10) & (np.abs(cz[:, 0]) < 0.24) & (cz[:, 2] > 1.2) & (cz[:, 2] < 1.45)),
                       ("hand_thigh", cz[:, 2] < 1.0)):
            zc[nm] = int(mz.sum())
        zc["other"] = int(len(pairs) - sum(zc.values()))
        oth = cz[~((np.abs(cz[:, 0]) > 0.10) & (np.abs(cz[:, 0]) < 0.24) & (cz[:, 2] > 1.2) & (cz[:, 2] < 1.45)) & (cz[:, 2] >= 1.0)]
        if len(oth):
            zc["other_rest_median_xyz"] = np.round(np.median(np.c_[np.abs(oth[:, 0]), oth[:, 1:]], axis=0), 3).tolist()
    return {"self_intersections_by_zone": zc, "stretch_gt2": int((ok & (ratio > 2)).sum()), "stretch_gt1.5": int((ok & (ratio > 1.5)).sum()),
            "compress_lt0.5": int((ok & (ratio < 0.5)).sum()), "ratio_p99": round(float(np.percentile(ratio[ok], 99)), 3),
            "ratio_max": round(float(ratio[ok].max()), 2),
            "folds_gt90": int((okf & (d < 0)).sum()), "crumple_gt35": int((okf & (d < 0.82)).sum()),
            "self_intersections": int(len(pairs))}, ratio


def frames(N):
    t1 = np.cross(N, np.where(np.abs(N[:, :1]) < 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]]))
    t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-15)
    return t1, np.cross(N, t1)


Lw = (W - csr_matrix((np.ones(n), (np.arange(n), np.arange(n))), shape=(n, n))).tocoo()   # sum_j w_ij x_j - x_i
# vertices whose rest ring the weights do not reproduce (reflex / degenerate rings) are pinned: a Laplacian solve
# spreads even a point residual over centimetres
_D = W @ R - R
RESID = np.linalg.norm(_D - np.einsum("ij,ij->i", _D, NR)[:, None] * NR, axis=1)


REJ = []
INV = []
TRACE = False


def slide(P, free):
    """move the free vertices only within their tangent planes so that, tangentially, each sits at its rest-MVC
    barycentre (linear solve for 2 tangential unknowns per vertex), project onto the posed surface, repeat"""
    free = free & (RESID < 1e-5)
    idx = np.flatnonzero(free); pos = -np.ones(n, int); pos[idx] = np.arange(len(idx)); m = len(idx)
    sel = free[Lw.row] & free[Lw.col]
    ri, ci, wv = pos[Lw.row[sel]], pos[Lw.col[sel]], Lw.data[sel]
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    X = P.copy(); hist = []; REJ.clear()
    for rnd in range(ROUNDS):
        N = normals(X); T1, T2 = frames(N); T = np.stack([T1, T2], axis=2)        # n x 3 x 2
        r = -(Lw.tocsr() @ X)                                                     # want tangential (Lw X) = 0
        # block (i, j) = w_ij T_i^T T_j  (diagonal blocks -I since T_i^T T_i = I)
        Bk = np.einsum("kab,kac->kbc", T[idx[ri]], T[idx[ci]]) * wv[:, None, None]
        rr, cc, vv = [], [], []
        for a_ in range(2):
            for b_ in range(2):
                rr.append(2 * ri + a_); cc.append(2 * ci + b_); vv.append(Bk[:, a_, b_])
        M = csr_matrix((np.concatenate(vv), (np.concatenate(rr), np.concatenate(cc))), shape=(2 * m, 2 * m)).tocsc()
        rhs = np.einsum("kab,ka->kb", T[idx], r[idx]).ravel()
        u = DAMP * splu(M).solve(rhs).reshape(-1, 2)
        Xn = X.copy(); Xn[idx] += np.einsum("kab,kb->ka", T[idx], u)
        rej = 0
        HN = N.copy()                                                            # posed-surface normal under each vertex
        for i in idx:                                                            # back onto the posed surface - but
            hit = bvh.find_nearest(Vector(Xn[i]), 0.03)                          # never onto the opposite sheet of a
            if hit[0] is not None and float(np.dot(hit[1], N[i])) > 0.3:         # crease (its faces face the other way)
                Xn[i] = hit[0]; HN[i] = hit[1]
            else:
                Xn[i] = X[i]; rej += 1
        REJ.append(rej)
        # inversion guard: a triangle whose orientation is reversed against the surface it lies on has tangled -
        # its vertices (and one ring) go back to where they were before this round; repeat until none is left
        for _ in range(20):
            fn = np.cross(Xn[TRI[:, 1]] - Xn[TRI[:, 0]], Xn[TRI[:, 2]] - Xn[TRI[:, 0]])
            inv = np.einsum("ij,ij->i", fn, HN[TRI].sum(1)) <= 0
            inv &= free[TRI].any(1)
            if not inv.any():
                break
            bad = np.zeros(n, bool); bad[TRI[inv].ravel()] = True
            bad = (bad | ((A_ @ bad.astype(float)) > 0)) & free
            Xn[bad] = X[bad]; HN[bad] = N[bad]
            INV.append(int(inv.sum()))
        hist.append(round(float(np.linalg.norm(Xn - X, axis=1).max() * 1000), 2))
        X = Xn
        if TRACE:
            mt, _ = metrics(X)
            print("ROUND", rnd, json.dumps({k: mt[k] for k in ("stretch_gt2", "compress_lt0.5", "folds_gt90", "self_intersections",
                                                             "self_intersections_by_zone")}), flush=True)
    return X, hist


rep = {"method": METHOD, "radius_m": RAD, "rounds": ROUNDS, "damping": DAMP, "contact_pin_m": PIN, "rest_rings_with_reflex_angle": bad_ring, "pinned_rest_residual": int((RESID >= 1e-5).sum())}
bench._reset(rig)
for kb in me.shape_keys.key_blocks[1:]:
    kb.value = 0.0
bpy.context.view_layer.update()
rep["rest_check"], _ = metrics(ev())
girdle.apply_press_pose(rig, 160.0, AX)
for s in ("l", "r"):
    pb = rig.pose.bones[f"forearm_{s}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body); bpy.context.view_layer.update()
P = ev()
gh = [np.array(rig.data.bones[f"upperarm_{s}"].head_local) for s in ("l", "r")]
near = np.zeros(n, bool)
for g in gh:
    near |= np.linalg.norm(R - g, axis=1) < RAD
free = near & ~EXCL & (R[:, 2] > 1.0)
if PIN > 0:                                                 # creases / contacts (posterior axillary fold): both sheets
    NP = normals(P)                                         # would slide along each other - they stay where they are
    bvhp = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    pin = np.zeros(n, bool)
    for i in np.flatnonzero(free):
        o = Vector(P[i] + NP[i] * 2e-4)
        hit = bvhp.ray_cast(o, Vector(NP[i]), PIN)
        if hit[0] is not None:
            pin[i] = True
    for _ in range(3):
        pin |= (A_ @ pin.astype(float)) > 0
    rep["pinned_contact"] = int((pin & free).sum())
    free &= ~pin
# rest fixed point: the slide must leave the rest mesh where it is
Xr, _ = slide(R, free) if METHOD == "mvc" else (R, None)
rep["rest_fixed_point_max_mm"] = round(float(np.linalg.norm(Xr - R, axis=1).max() * 1000), 3)
rep["free_vertices"] = int(free.sum())
rep["before"], r0 = metrics(P)
TRACE = True
if METHOD == "walk":                                        # r57 original_v1_skin_slide: surface-walking, guarded steps
    import time
    import original_v1_skin_slide as walk
    t0 = time.time()
    RIN, ROUT = (float(x) for x in os.environ.get("V2_SLIDE_RR", "0.16,0.26").split(","))
    dmin = np.min([np.linalg.norm(R - g, axis=1) for g in gh], axis=0)
    wfree = np.clip((ROUT - dmin) / max(ROUT - RIN, 1e-6), 0, 1) * free
    idx_w = np.flatnonzero(wfree > 0)
    A0r = np.maximum(0.5 * np.linalg.norm(np.cross(R[TRI[:, 1]] - R[TRI[:, 0]], R[TRI[:, 2]] - R[TRI[:, 0]]), axis=1), 1e-12)
    wlog = []
    X = walk.slide(P, TRI, A0r, idx_w, wfree, iters=int(os.environ.get("V2_SLIDE_ITERS", "60")),
                   eta=float(os.environ.get("V2_SLIDE_ETA", "1.0")), cap=float(os.environ.get("V2_SLIDE_CAP", "0.0015")), log=wlog)
    hist = wlog; rep["walk_seconds"] = round(time.time() - t0, 1); rep["walk_vertices"] = int(len(idx_w))
    rep["walk_rr_m"] = [RIN, ROUT]
else:
    X, hist = slide(P, free)
rep["after"], r1 = metrics(X)
rep["round_moves_mm"] = hist; rep["projection_rejected_per_round"] = list(REJ); rep["inverted_reverted"] = list(INV)
rep["slide_mm_p50_p95_max"] = [round(float(np.percentile(np.linalg.norm(X - P, axis=1)[free], q)) * 1000, 2) for q in (50, 95, 100)]
print("SLIDE", json.dumps(rep), flush=True)
json.dump(rep, open(f"{OUT}/slide_mvc.json", "w"), indent=1)
# renders: shaded before / after (shape check) and stretch heat maps
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH", "CURVE") and ob is not body:
        ob.hide_render = True
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam; cd.ortho_scale = 0.9
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"
sc.render.resolution_x = 600; sc.render.resolution_y = 600
mesh_tmp = bpy.data.meshes.new("SLIDE"); mesh_tmp.from_pydata(P.tolist(), [], [p.vertices[:] for p in me.polygons])
obt = bpy.data.objects.new("SLIDE", mesh_tmp); sc.collection.objects.link(obt); body.hide_render = True
attr = mesh_tmp.color_attributes.new("S", "FLOAT_COLOR", "POINT"); mesh_tmp.color_attributes.active_color = attr
mat = bpy.data.materials.new("M"); mat.diffuse_color = (.72, .55, .45, 1); mesh_tmp.materials.append(mat)
c = Vector((0, 0, float(gh[0][2]) + 0.1))
for tag, Q, rr in (("before", P, r0), ("after", X, r1)):
    mesh_tmp.vertices.foreach_set("co", Q.ravel()); mesh_tmp.update()
    lr = np.log2(np.clip(rr, 0.25, 4.0)); vmax = np.zeros(n); vmin = np.zeros(n)
    np.maximum.at(vmax, E[:, 0], lr); np.maximum.at(vmax, E[:, 1], lr); np.minimum.at(vmin, E[:, 0], lr); np.minimum.at(vmin, E[:, 1], lr)
    t = np.clip(np.where(vmax >= -vmin, vmax, vmin), -1, 1); col = np.ones((n, 4))
    col[:, 0] = np.where(t < 0, 1 + t, 1.0); col[:, 1] = 1 - np.abs(t); col[:, 2] = np.where(t > 0, 1 - t, 1.0)
    attr.data.foreach_set("color", col.ravel())
    for shade in ("heat", "shaded"):
        sc.display.shading.color_type = "VERTEX" if shade == "heat" else "MATERIAL"
        sc.display.shading.show_cavity = shade == "shaded"
        for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0)}.items():
            d = Vector(dv); cam.location = c + d * 3; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = f"{OUT}/{tag}_{shade}_{view}.png"; bpy.ops.render.render(write_still=True)
print("DONE", flush=True)
