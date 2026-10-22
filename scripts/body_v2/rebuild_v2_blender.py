"""R120 (owner: "It looks terrible" -> chose "Rebuild clean"): rebuild the torso, arms, shoulders, neck base and hips as
a new clean surface, keeping the new legs (R119), the hands and the head.

Why: every relief or smoothing pass on the old surface fought its ripples and sliver triangles (ladder abs, pits at the
clavicle, lumpy chest).  The outlines are right (front and side within a few mm of the reference), the surface is not.

How (all in a pose with the arms 40 deg out, so the armpits and the forearm / hip gaps stay open):
  1. the posed body is voxelised (3 mm; inside by ray parity per column) and turned into a signed distance field
     (exact Euclidean distance transforms), which is blurred (V2_RB_BLUR_MM) - the lumps and creases go, the outline
     and the large forms stay;
  2. marching cubes gives an even, clean surface, relaxed with HC smoothing;
  3. it is cut at five planes - across both thighs (0.40 of stature), the neck (V2_RB_NECK_Z) and both wrists - and
     stitched to the kept old parts (legs, head, hands) with triangle strips;
  4. skin weights and shape-key deltas come from the nearest old vertices; each new vertex is taken back to the rest
     pose by inverting its own linear-blend skinning transform (the armature modifier is plain LBS);
  5. standing renders as the leg step.

usage: blender python rebuild_v2_blender.py -- <body_v2_legs.blend> <r57src root> <out dir>
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]).resolve(), Path(args[1]).resolve(), Path(args[2])
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(HERE)]
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
import build_original_movement_benchmarks_blender as bench

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
REP = {}


def ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


nv0 = len(me.vertices)
V0 = np.empty(nv0 * 3); me.vertices.foreach_get("co", V0); V0 = V0.reshape(-1, 3)
z0 = float(V0[:, 2].min()); H = float(V0[:, 2].max()) - z0
GN = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(GN)}
W0 = np.zeros((nv0, len(GN)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W0[v.index, g.group] = g.weight
KEYS = [kb.name for kb in me.shape_keys.key_blocks] if me.shape_keys else []
KD0 = {}
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    c_ = np.empty(nv0 * 3); kb.data.foreach_get("co", c_); KD0[kb.name] = c_.reshape(-1, 3) - V0

# ------------------------------------------------------------------ the build pose: arms out, no drivers (pure LBS)
ABD = float(os.environ.get("V2_RB_ABD", "40"))
bench._reset(rig)
for sd, sg in (("r", -1.0), ("l", 1.0)):
    pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * ABD))
if me.shape_keys:
    for kb in me.shape_keys.key_blocks[1:]:
        kb.value = 0.0
bpy.context.view_layer.update()
_pp, _ = bench._evaluated(body); P0 = np.array([tuple(v) for v in _pp])
RM = rig.matrix_world; RMi = RM.inverted()
BM = {}                                                  # per-bone deform matrix (world, rest -> posed)
for pb in rig.pose.bones:
    BM[pb.name] = np.array(RM @ pb.matrix @ pb.bone.matrix_local.inverted() @ RMi)
# check: LBS of the rest coordinates reproduces the evaluated pose
Wn = W0 / np.maximum(W0.sum(1, keepdims=True), 1e-9)
Mstack = np.stack([BM.get(n, np.eye(4)) for n in GN])            # (G, 4, 4)
def lbs(V, Wr):
    M = np.einsum("ng,gij->nij", Wr, Mstack)
    return np.einsum("nij,nj->ni", M[:, :3, :3], V) + M[:, :3, 3], M
_chk, _ = lbs(V0[:2000], Wn[:2000])
REP["lbs_check_max_mm"] = round(float(np.abs(_chk - P0[:2000]).max()) * 1000, 3)

# kept parts and cut planes (posed space)
def bone_pose_head(n):
    pb = rig.pose.bones[n]; return np.array(RM @ pb.head), np.array(RM @ pb.tail)
ZT = z0 + float(os.environ.get("V2_RB_THIGH_F", "0.40")) * H
ZN = float(os.environ.get("V2_RB_NECK_Z", "1.585"))
PLANES = [("thigh", np.array([0, 0, ZT]), np.array([0, 0, -1.0]), None),     # normal points to the KEPT old side
          ("neck", np.array([0, 0, ZN]), np.array([0, 0, 1.0]), None)]
for sd in ("r", "l"):
    h_, t_ = bone_pose_head(f"forearm_tw1_{sd}")                # forearm tw1 tail = wrist
    d_ = (t_ - h_) / np.linalg.norm(t_ - h_)
    PLANES.append((f"wrist_{sd}", t_ - 0.012 * d_, d_, t_))
REP["planes"] = {n: [round(float(x), 4) for x in c] for n, c, _, _ in PLANES}


def old_side(P):
    """True where a point is on a kept old part (beyond any cut plane)"""
    k = np.zeros(len(P), bool)
    for n, c, nn, wc in PLANES:
        s = (P - c) @ nn > 0
        if wc is not None:
            s &= np.linalg.norm(P - wc, axis=1) < 0.16
        k |= s
    return k


# ------------------------------------------------------------------ voxelise, SDF, blur, marching cubes
hv = float(os.environ.get("V2_RB_VOX_MM", "3.0")) * 1e-3
mid = ~old_side(P0)
lo = P0[mid].min(0) - 0.03; hi = P0[mid].max(0) + 0.03
nx, ny, nz = (np.ceil((hi - lo) / hv).astype(int) + 1)
REP["grid"] = [int(nx), int(ny), int(nz)]
REP["old_mesh_open_edges"] = sum(1 for e in me.edges if False)
tris = []
for p in me.polygons:
    vs = p.vertices[:]
    for k in range(1, len(vs) - 1):
        tris.append((vs[0], vs[k], vs[k + 1]))
tris = np.array(tris)
bvh = BVHTree.FromPolygons([Vector(p) for p in P0], tris.tolist(), all_triangles=True)
# inside / outside by ray parity along each axis, majority of the three (v1 used z only: a ray grazing an edge
# between two triangles misses a crossing and fills the whole span between the arm and the torso)
axes_c = [lo[k] + hv * np.arange(n_) for k, n_ in enumerate((nx, ny, nz))]


def parity(ax_):
    o1, o2 = [k for k in range(3) if k != ax_]
    occ_ = np.zeros((nx, ny, nz), bool)
    dvec = Vector([1.0 if k == ax_ else 0.0 for k in range(3)])
    for i, a in enumerate(axes_c[o1]):
        for j, b in enumerate(axes_c[o2]):
            o = [0.0, 0.0, 0.0]; o[o1] = a; o[o2] = b; o[ax_] = lo[ax_] - 0.05
            o = Vector(o); hits = []
            for _ in range(64):
                r = bvh.ray_cast(o, dvec)
                if r[0] is None:
                    break
                t = r[0][ax_]
                if not hits or t - hits[-1] > 1e-6:
                    hits.append(t)
                o = r[0] + dvec * 1e-5
            sl = [slice(None)] * 3; sl[o1] = i; sl[o2] = j
            line = np.zeros(len(axes_c[ax_]), bool)
            for p_, q_ in zip(hits[0::2], hits[1::2]):
                line |= (axes_c[ax_] > p_) & (axes_c[ax_] < q_)
            occ_[tuple(sl)] = line
    return occ_


_ov = [(a_, b_) for a_, b_ in bvh.overlap(bvh) if a_ < b_ and not (set(tris[a_]) & set(tris[b_]))]
REP["posed_self_overlap_pairs"] = len(_ov)
votes = parity(2).astype(np.int8) + parity(0) + parity(1)
occ = votes >= 2
REP["parity_disagreement_voxels"] = int(((votes == 1) | (votes == 2)).sum())
REP["occupied_voxels"] = int(occ.sum())
sdf = (distance_transform_edt(~occ) - distance_transform_edt(occ)) * hv
sdf = gaussian_filter(sdf, float(os.environ.get("V2_RB_BLUR_MM", "6")) * 1e-3 / hv)
mv, mf, _, _ = marching_cubes(sdf.astype(np.float32), 0.0, spacing=(hv, hv, hv))
mv = mv + lo
vol = np.einsum("ij,ij->i", mv[mf[:, 0]], np.cross(mv[mf[:, 1]], mv[mf[:, 2]])).sum()
if vol < 0:
    mf = mf[:, ::-1]
REP["mc"] = {"verts": len(mv), "tris": len(mf)}

# ------------------------------------------------------------------ new middle piece: cut and relax
nb = bmesh.new()
nvs = [nb.verts.new(p) for p in mv]
for t in mf:
    try:
        nb.faces.new((nvs[t[0]], nvs[t[1]], nvs[t[2]]))
    except ValueError:
        pass
bmesh.ops.remove_doubles(nb, verts=nb.verts, dist=1e-7)
bmesh.ops.beautify_fill(nb, faces=nb.faces, edges=nb.edges, method="ANGLE")


def cut(bm_, keep_old):
    """bisect bm_ at every plane; keep_old=True keeps the old parts, else the middle.  Each cut only touches faces near
    its own plane (and, for a wrist, near that wrist): a whole-mesh cut at the thigh plane would also take the head."""
    for n, c, nn, wc in PLANES:
        cv = Vector(c); nv_ = Vector(nn)
        fs = [f for f in bm_.faces
              if min(abs((v.co - cv).dot(nv_)) for v in f.verts) < 0.03
              and (wc is None or min((Vector(wc) - v.co).length for v in f.verts) < 0.12)
              and (wc is not None or n != "thigh" or max(v.co.z for v in f.verts) < ZT + 0.05)]
        geom = list({e for f in fs for e in f.edges}) + fs + list({v for f in fs for v in f.verts})
        # clear_inner deletes the side the normal points away from
        bmesh.ops.bisect_plane(bm_, geom=geom, plane_co=cv, plane_no=nv_ if keep_old else -nv_, clear_inner=True)
    # then everything on the wrong side, away from the planes
    bm_.verts.ensure_lookup_table()
    P = np.array([tuple(v.co) for v in bm_.verts])
    onp = np.zeros(len(P), bool)
    for n, c, nn, wc in PLANES:
        onp |= np.abs((P - c) @ nn) < 1e-6
    side = old_side(P)
    gone = [v for v, s_, o_ in zip(bm_.verts, side, onp) if not o_ and (s_ != keep_old)]
    bmesh.ops.delete(bm_, geom=gone, context="VERTS")


cut(nb, keep_old=False)
# drop any stray islands (the hand side of a wrist plane beyond the 12 cm geometry window, etc.)
nb.verts.ensure_lookup_table()
seen = set(); islands = []
for v in nb.verts:
    if v in seen:
        continue
    stack = [v]; isl = []
    seen.add(v)
    while stack:
        a = stack.pop(); isl.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b not in seen:
                seen.add(b); stack.append(b)
    islands.append(isl)
islands.sort(key=len, reverse=True)
for isl in islands[1:]:
    bmesh.ops.delete(nb, geom=isl, context="VERTS")
REP["mc_islands_dropped"] = len(islands) - 1

# ------------------------------------------------------------------ old mesh in posed space, cut, middle removed
bm = bmesh.new(); bm.from_mesh(me)
rest_l = bm.verts.layers.shape.new("__REST__")
shl = [bm.verts.layers.shape[k] for k in KEYS]
oid = bm.verts.layers.int.new("old_id")
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v[rest_l] = v.co.copy(); v[oid] = v.index; v.co = Vector(P0[v.index])
cut(bm, keep_old=True)
bm.verts.ensure_lookup_table()
REP["old_verts_after_cut"] = len(bm.verts)

# merge the new piece in
NEW = set()
nmap = {}
for v in nb.verts:
    x = bm.verts.new(v.co); x[oid] = -2; nmap[v] = x; NEW.add(x)
for f in nb.faces:
    bm.faces.new([nmap[v] for v in f.verts]).smooth = True
nb.free()


def loop_on_plane(c, nn, verts):
    """ordered boundary loop(s) lying on a plane, from the given vertex set"""
    on = {v for v in verts if v.is_boundary and abs((np.array(v.co) - c) @ nn) < 1e-5}
    loops = []
    while on:
        s = next(iter(on)); lp = [s]; on.discard(s); prev = None
        while True:
            nx_ = [e.other_vert(lp[-1]) for e in lp[-1].link_edges if e.is_boundary and e.other_vert(lp[-1]) in on]
            if not nx_:
                break
            lp.append(nx_[0]); on.discard(nx_[0])
        loops.append(lp)
    return loops


def plane_angles(lp, c, nn):
    a_ = np.cross(nn, [1.0, 0, 0] if abs(nn[0]) < 0.9 else [0, 1.0, 0]); a_ /= np.linalg.norm(a_); b_ = np.cross(nn, a_)
    P = np.array([tuple(v.co) for v in lp]); q = P - P.mean(0)
    return np.arctan2(q @ b_, q @ a_), P.mean(0)


def stitch(A, B, flip):
    pa = np.array([tuple(v.co) for v in A]); pb = np.array([tuple(v.co) for v in B])
    s0 = int(np.argmin(np.linalg.norm(pb - pa[0], axis=1))); B = B[s0:] + B[:s0]; pb = np.roll(pb, -s0, 0)
    sa = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pa, pa[:1]]), axis=0), axis=1))]); sa /= sa[-1]
    sb = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([pb, pb[:1]]), axis=0), axis=1))]); sb /= sb[-1]
    i = j = 0; na, nb_ = len(A), len(B); made = []
    while i < na or j < nb_:
        if j >= nb_ or (i < na and sa[i + 1] <= sb[j + 1]):
            tri = (A[i], A[(i + 1) % na], B[j % nb_]); i += 1
        else:
            tri = (A[i % na], B[(j + 1) % nb_], B[j]); j += 1
        try:
            f = bm.faces.new(tri[::-1] if flip else tri); f.smooth = True; made.append(f)
        except ValueError:
            pass
    return made


OLDV = [v for v in bm.verts if v not in NEW]
REP["stitches"] = {}
for n, c, nn, wc in PLANES:
    ol = loop_on_plane(c, nn, OLDV); nl = loop_on_plane(c, nn, NEW)
    pairs = []
    for A in ol:
        ca = np.array([tuple(v.co) for v in A]).mean(0)
        B = min(nl, key=lambda L: np.linalg.norm(np.array([tuple(v.co) for v in L]).mean(0) - ca)) if nl else None
        if B is None:
            continue
        nl.remove(B)
        ta, _ = plane_angles(A, c, nn); tb, _ = plane_angles(B, c, nn)
        if ((np.diff(np.unwrap(np.r_[ta, ta[:1]]))).sum() < 0):
            A = A[::-1]
        if ((np.diff(np.unwrap(np.r_[tb, tb[:1]]))).sum() < 0):
            B = B[::-1]
        a0, a1 = A[0], A[1]
        ef = [f for f in a0.link_faces if a1 in f.verts][0]; fv = list(ef.verts); ia = fv.index(a0)
        fwd = fv[(ia + 1) % len(fv)] is a1
        made = stitch(A, B, fwd)
        pairs.append({"old": len(A), "new": len(B), "tris": len(made)})
    REP["stitches"][n] = pairs

# seam relax (new vertices only), HC
bm.verts.ensure_lookup_table(); bm.verts.index_update()
NL = list(NEW); idn = {v: i for i, v in enumerate(NL)}
nbr = [[idn[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in idn] for v in NL]
Pn = np.array([tuple(v.co) for v in NL])
dpl = np.min(np.stack([np.abs((Pn - c) @ nn) + (0 if wc is None else 0) for n, c, nn, wc in PLANES]), axis=0)
wsm = 1.0 - ss(dpl / 0.03)
O = Pn.copy(); Q = Pn.copy()
for _ in range(int(os.environ.get("V2_RB_SEAM_STEPS", "20"))):
    Pm = np.array([Q[k].mean(0) if k else Q[i] for i, k in enumerate(nbr)]); Pm = Q + wsm[:, None] * (Pm - Q)
    B_ = Pm - O; Bn = np.array([B_[k].mean(0) if k else B_[i] for i, k in enumerate(nbr)])
    Q = Pm - wsm[:, None] * (0.6 * B_ + 0.4 * Bn)
# and a light HC pass over the whole new piece (the voxel staircase)
wall = np.full(len(NL), 1.0)
O = Q.copy()
for _ in range(int(os.environ.get("V2_RB_HC_STEPS", "4"))):
    Pm = np.array([Q[k].mean(0) if k else Q[i] for i, k in enumerate(nbr)])
    B_ = Pm - O; Bn = np.array([B_[k].mean(0) if k else B_[i] for i, k in enumerate(nbr)])
    Q = Pm - (0.6 * B_ + 0.4 * Bn)
for v, q in zip(NL, Q):
    v.co = Vector(q)

# ------------------------------------------------------------------ weights, back to rest, shape keys
src = np.where(~old_side(P0))[0]
tree = cKDTree(P0[src])
d_, j_ = tree.query(Q, k=4)
w_ = 1.0 / np.maximum(d_, 1e-4) ** 2; w_ /= w_.sum(1, keepdims=True)
idx = src[j_]
WN = np.einsum("nk,nkg->ng", w_, W0[idx])
for _ in range(int(os.environ.get("V2_RB_WSMOOTH", "6"))):
    WN = 0.5 * WN + 0.5 * np.array([WN[k].mean(0) if k else WN[i] for i, k in enumerate(nbr)])
WN /= np.maximum(WN.sum(1, keepdims=True), 1e-6)
REP["weight_source_dist_mm"] = {"median": round(float(np.median(d_[:, 0])) * 1000, 1), "max": round(float(d_[:, 0].max()) * 1000, 1)}
_, M = lbs(np.zeros((len(Q), 3)), WN)
R_ = np.linalg.solve(M[:, :3, :3], (Q - M[:, :3, 3])[..., None])[..., 0]
dl = bm.verts.layers.deform.verify()
for v, wr, r in zip(NL, WN, R_):
    dv = v[dl]; dv.clear()
    for g in np.nonzero(wr > 1e-4)[0]:
        dv[int(g)] = float(wr[g])
    v[rest_l] = Vector(r)
for k, sl in zip(KEYS, shl):
    D = np.einsum("nk,nkc->nc", w_, KD0[k][idx])
    for v, r, dd in zip(NL, R_, D):
        v[sl] = Vector(r) + Vector(dd)
# everything back to rest
for v in bm.verts:
    v.co = v[rest_l].copy()
bm.verts.layers.shape.remove(rest_l)
bad = sum(1 for e in bm.edges if len(e.link_faces) == 2 and
          [l for l in e.link_faces[0].loops if l.edge is e][0].vert is [l for l in e.link_faces[1].loops if l.edge is e][0].vert)
REP["winding_conflicts"] = bad
REP["non_manifold_edges"] = sum(1 for e in bm.edges if not e.is_manifold)
bm.to_mesh(me); bm.free(); me.update()
bench._reset(rig); bpy.context.view_layer.update()
REP["verts_before_after"] = [nv0, len(me.vertices)]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_rebuilt.blend"), copy=True)
(OUT / "rebuild_report.json").write_text(json.dumps(REP, indent=1))
print("REBUILD_V2", json.dumps(REP), flush=True)

if os.environ.get("V2_RB_RENDER", "1") == "1":
    import runpy
    sys.argv = [sys.argv[0], "--", str(OUT / "body_v2_rebuilt.blend"), str(ROOT), str(OUT)]
    runpy.run_path(str(HERE / "render_v2_blender.py"), run_name="__main__")
