"""R121 (candidate, branch claude/r120-surface-candidate-*): finish the R120 clean rebuild.

R120 gave the torso, arms, shoulders and hips a clean, even surface (owner: "It looks terrible" -> "Rebuild clean"), but
  * the seams where the rebuilt surface meets the kept thighs, neck and wrists show as thin lines, and
  * the 6 mm blur that removed the old lumps also flattened the muscle definition.
This step:
  1. seams - HC-Laplacian smoothing (shrink-free, stable on this mesh) over V2_R121_SEAM_RINGS mesh rings either side of
     every rebuilt / kept boundary, fading with ring distance; every shape key moves with the basis;
  2. torso definition - the reference-measured relief of legs_v2_blender.py (rectus rows, linea alba / semilunaris,
     obliques, serratus; back along the fibres; glutes) applied to the rebuilt skin only, along smoothed normals.
     On R120's clean surface there is no older abs detail to erase first.

usage: python3.13 r120_finish_blender.py -- <body_v2_rebuilt.blend> <out dir>
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, OUT = Path(args[0]).resolve(), Path(args[1])
OUT.mkdir(parents=True, exist_ok=True)
HERE = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
REP = {}


def ss(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ 0. repair R120's stitch defects
# R120 left 172 open edges round the thigh seams (zipper triangles refused as duplicates) and ~560 folded triangle
# pairs (neighbours facing opposite ways), mostly in the neck stitch strip: both showed as thin bright lines.
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
bnd_e = [e for e in bm.edges if len(e.link_faces) == 1]
res_ = bmesh.ops.holes_fill(bm, edges=bnd_e, sides=0)
bmesh.ops.triangulate(bm, faces=[f_ for f_ in res_["faces"] if len(f_.verts) > 3])
for f_ in res_["faces"]:
    f_.smooth = True
REP["holes_filled_faces"] = len(res_["faces"])
wire = [e for e in bm.edges if not e.link_faces]
bmesh.ops.delete(bm, geom=wire, context="EDGES")
bm.to_mesh(me); bm.free(); me.update()


def fold_verts():
    bm_ = bmesh.new(); bm_.from_mesh(me); bm_.normal_update()
    out_ = set()
    for e in bm_.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < -0.5:
            for f_ in e.link_faces:
                out_.update(v.index for v in f_.verts)
    nb_ = len(out_); bm_.free()
    return np.array(sorted(out_), dtype=np.int64), nb_


n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
E0 = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E0); E0 = E0.reshape(-1, 2)
A0 = csr_matrix((np.ones(2 * len(E0)), (np.r_[E0[:, 0], E0[:, 1]], np.r_[E0[:, 1], E0[:, 0]])), shape=(n, n))
D0 = 1.0 / np.maximum(np.asarray(A0.sum(1)).ravel(), 1)
fixes = []
for rnd in range(int(os.environ.get("V2_R121_UNFOLD_ROUNDS", "6"))):
    fv, nf = fold_verts(); fixes.append(int(nf))
    if nf == 0:
        break
    m = np.zeros(n); m[fv] = 1.0
    for _ in range(3):                                  # the folded triangles and two rings round them
        m = np.maximum(m, (A0 @ m) * D0 > 0)
    Q = V.copy()
    for _ in range(30):
        Q = Q + 0.6 * m[:, None] * ((A0 @ Q) * D0[:, None] - Q)
    dV = Q - V
    me.vertices.foreach_set("co", Q.ravel())
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + dV).ravel())
    me.update(); V = Q
REP["fold_vertices_per_round"] = fixes
REP["folds_left"] = int(fold_verts()[1])
z0 = float(V[:, 2].min()); H = float(V[:, 2].max()) - z0
attr = me.attributes.get("old_id.001") or me.attributes.get("old_id")
oid = np.empty(n, np.int32); attr.data.foreach_get("value", oid)
NEWR = oid == -2                                        # vertices made by the R120 rebuild
REP["rebuilt_vertices"] = int(NEWR.sum())
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
deg = np.asarray(A.sum(1)).ravel(); Dinv = 1.0 / np.maximum(deg, 1)
mean = lambda X: (A @ X) * (Dinv[:, None] if X.ndim == 2 else Dinv)

GN = [g.name for g in body.vertex_groups]
W = np.zeros((n, len(GN)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
ARMK = ("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky")
ARM = W[:, [i for i, g in enumerate(GN) if any(k in g for k in ARMK)]].sum(1)
HAND = W[:, [i for i, g in enumerate(GN) if any(k in g for k in ("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal"))]].sum(1)

# ------------------------------------------------------------------ 1. seams: ring distance from the boundary
K = int(os.environ.get("V2_R121_SEAM_RINGS", "14"))
bnd = (np.asarray((A @ NEWR.astype(float))).ravel() > 0) & ~NEWR | (np.asarray((A @ (~NEWR).astype(float))).ravel() > 0) & NEWR
hop = np.full(n, 10 ** 6); hop[bnd] = 0; front = bnd.copy()
for h in range(1, K + 1):
    nxt = (np.asarray(A @ front.astype(float)).ravel() > 0) & (hop > h)
    hop[nxt] = h; front = nxt
w = np.where(hop <= K, 1.0 - hop / (K + 1.0), 0.0) * (HAND < 0.5)   # never into the hands
REP["seam_vertices"] = int((w > 0).sum())
O = V.copy(); Q = V.copy()
for _ in range(int(os.environ.get("V2_R121_SEAM_STEPS", "40"))):
    Pm = Q + w[:, None] * (mean(Q) - Q)
    B = Pm - O
    Q = Pm - w[:, None] * (0.6 * B + 0.4 * mean(B))
D = Q - V
REP["seam_max_move_mm"] = round(float(np.linalg.norm(D, axis=1).max() * 1000), 2)

# ------------------------------------------------------------------ 2. torso relief on the rebuilt skin
src = (HERE / "legs_v2_blender.py").read_text()
a = src.index("def _g(x, f, xc, sx, fc, sf, amp):"); b = src.index("if TORSO > 0:")
ns = {"np": np, "ss": ss, "RELIEF": 1.0}
exec(src[a:b], ns)                                       # _g, _win, torso_front, _seg, torso_back - unchanged
TORSO = float(os.environ.get("V2_R121_TORSO", "1.0"))
P1 = V + D
F = np.array([p.vertices[:] for p in me.polygons], dtype=object)
fn = np.zeros_like(P1)
for p in me.polygons:                                    # area-weighted vertex normals of the seam-smoothed surface
    vs = list(p.vertices); a_, b_, c_ = P1[vs[0]], P1[vs[1]], P1[vs[2]]
    nn = np.cross(b_ - a_, c_ - a_)
    for vi in vs:
        fn[vi] += nn
for _ in range(6):
    fn = 0.5 * fn + 0.5 * mean(fn)
fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
ax, f = np.abs(P1[:, 0]) / H, (P1[:, 2] - z0) / H
wf = ss((-fn[:, 1] + 0.05) / 0.40); wb = ss((fn[:, 1] + 0.05) / 0.40)
region = NEWR.astype(float) * ss((ARM < 0.15).astype(float)) * ss((f - 0.425) / 0.02) * ss((0.795 - f) / 0.02)
for _ in range(4):
    region = 0.5 * region + 0.5 * mean(region)
dn = (wf * ns["torso_front"](ax, f) + wb * ns["torso_back"](ax, f)) * region * TORSO
for _ in range(2):
    dn = 0.5 * dn + 0.5 * mean(dn)
D = D + fn * dn[:, None]
REP["torso_relief"] = {"max_mm": round(float(dn.max() * 1000), 1), "min_mm": round(float(dn.min() * 1000), 1)}

# ------------------------------------------------------------------ 3. arm muscles on the rebuilt arms
# R120's 6 mm blur took the R115 arm definition with the lumps.  The same bone-local bumps as R115 (Gray's Anatomy;
# Drake - upper limb surface anatomy; build_body_v2_sculpt_blender.py "R115"), on the rebuilt arm skin only.
ARMDEF = float(os.environ.get("V2_R121_ARMS", "1.0"))
if ARMDEF > 0:
    rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]

    def _seg(bn):
        b_ = rig.data.bones[bn]; return np.array(rig.matrix_world @ b_.head_local), np.array(rig.matrix_world @ b_.tail_local)

    def _frame(Hh, Tt, sgn, P):
        ax_ = Tt - Hh; L = np.linalg.norm(ax_); u = ax_ / L
        t = ((P - Hh) @ u) / L
        dv = P - Hh - np.outer(t * L, u)
        ant = np.array([0.0, -1.0, 0.0]); ant = ant - (ant @ u) * u; ant /= np.linalg.norm(ant)
        lat = np.cross(u, ant); lat *= np.sign(lat[0] * sgn) if lat[0] != 0 else 1.0
        return t, np.degrees(np.arctan2(dv @ lat, dv @ ant))

    def _bump(t, th, t0, t1, thc, thw, amp, pk=1.0):
        x_ = np.clip((t - t0) / (t1 - t0), 0, 1); prof = np.sin(np.pi * x_) ** pk
        dth = (th - thc + 180.0) % 360.0 - 180.0
        return amp * prof * np.exp(-0.5 * (dth / thw) ** 2)

    P2 = V + D
    ha = np.zeros(n)
    for side_ in ("r", "l"):
        uH, uT = _seg(f"upperarm_{side_}"); fH, fT = _seg(f"forearm_{side_}"); sgn = float(np.sign(uH[0]))
        idx = np.nonzero((ARM > 0.2) & NEWR & (np.sign(P2[:, 0]) == sgn))[0]; P = P2[idx]
        tu, thu = _frame(uH, uT, sgn, P); tf, thf = _frame(fH, fT, sgn, P)
        wU = np.clip(1 - ss((tf + 0.04) / 0.10), 0, 1)
        hu = (_bump(tu, thu, -0.05, 0.47, 90, 80, 11.0, 0.8) + 3.0 * ss((tu - 0.1) / 0.1) * ss((0.9 - tu) / 0.1)
              + _bump(tu, thu, 0.05, 0.42, 25, 35, 3.0) + _bump(tu, thu, 0.05, 0.42, 160, 35, 3.0)
              - _bump(tu, thu, 0.38, 0.52, 90, 55, 3.0) + _bump(tu, thu, 0.28, 0.90, 0, 45, 11.0, 1.3)
              + _bump(tu, thu, 0.12, 0.80, 180, 52, 9.0, 1.2) + _bump(tu, thu, 0.22, 0.58, 135, 30, 3.0)
              + _bump(tu, thu, 0.58, 0.92, 70, 22, 3.0) - _bump(tu, thu, 0.40, 0.92, -95, 18, 2.0)
              + _bump(tu, thu, 0.74, 1.10, 40, 30, 4.0))
        hf = (_bump(tf, thf, -0.12, 0.55, 20, 38, 10.0, 0.9) + _bump(tf, thf, -0.02, 0.55, -70, 40, 6.0, 1.1)
              + _bump(tf, thf, 0.04, 0.60, 125, 40, 4.0, 1.1) - _bump(tf, thf, -0.05, 0.12, -10, 22, 2.5))
        hf -= 4.0 * ss((tf - 0.55) / 0.35)
        h_ = np.where(tu > -0.15, hu * wU, 0.0) + np.where((tf > -0.2) & (tf < 1.05), hf * (1 - wU), 0.0)
        ha[idx] += h_ * ss((1.08 - np.clip(tf, 0, None)) / 0.08)
    for _ in range(3):
        ha = 0.5 * ha + 0.5 * mean(ha)
    D = D + fn * (ARMDEF * ha / 1000.0)[:, None]
    REP["arm_muscles"] = {"max_mm": round(float(ha.max()), 2), "min_mm": round(float(ha.min()), 2), "vertices": int((np.abs(ha) > 0.2).sum())}

# ------------------------------------------------------------------ write: basis and every shape key move together
me.vertices.foreach_set("co", (V + D).ravel())
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_r121.blend"), copy=True)
(OUT / "r121_report.json").write_text(json.dumps(REP, indent=1))
print("R121", json.dumps(REP), flush=True)
