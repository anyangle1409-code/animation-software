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


n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
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

# ------------------------------------------------------------------ write: basis and every shape key move together
me.vertices.foreach_set("co", (V + D).ravel())
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_r121.blend"), copy=True)
(OUT / "r121_report.json").write_text(json.dumps(REP, indent=1))
print("R121", json.dumps(REP), flush=True)
