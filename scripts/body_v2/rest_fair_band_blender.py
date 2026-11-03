"""CANDIDATE (review only): fair the leg-join band (the R119 leg cut at 0.45 of stature) in the rest shape, on a copy.

Defect 1.4 (docs/ANATOMICAL_DEFECT_LIST_20261103.md): a horizontal tone line around the top of both thighs at 0.44 -
0.45 of stature, where a strip of long thin triangles joins the rebuilt leg rings to the original mesh.  Standing, it
reads as a band around the thighs and buttocks.

What: inside the band (|height - V2_BAND_H| < V2_BAND_W, fractions of stature, smooth bell weight), the surface's
fine relief along the normal is removed: each pass moves a vertex along its normal by the weighted normal component of
(Laplacian-smoothed surface - surface), V2_BAND_ROUNDS smoothing rounds per pass, V2_BAND_PASSES passes.  Movement is
along the normal only (no vertex slides within the surface: S1b showed that sliding breaks the shape keys); hands and
forearms are held.  Added to the basis and to every key.  Object names from the character profile.

usage: python3.13 rest_fair_band_blender.py -- <src.blend> <out dir>
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
H0 = float(os.environ.get("V2_BAND_H", str(character_profile.region("legs_v2_blender.py", "V2_LEGS_CUT", 0.45))))
W = float(os.environ.get("V2_BAND_W", "0.02"))
ROUNDS = int(os.environ.get("V2_BAND_ROUNDS", "6"))
PASSES = int(os.environ.get("V2_BAND_PASSES", "3"))
out_blend = OUT / "body_v2_r121_arms.blend"
if out_blend.exists():
    raise SystemExit(f"{out_blend} exists; refusing to overwrite")
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
BODY, RIG = character_profile.blender_names()
body = bpy.data.objects[BODY]; me = body.data; n = len(me.vertices)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
z0 = float(R[:, 2].min()); H = float(R[:, 2].max()) - z0; h = (R[:, 2] - z0) / H
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
GN = [g.name for g in body.vertex_groups]
held = np.zeros(n)
hk = ("hand", "metacarpal", "thumb", "index", "middle", "ring", "pinky", "forearm")
for v in me.vertices:
    for g in v.groups:
        if any(k in GN[g.group] for k in hk):
            held[v.index] += g.weight


def vnormals(P):
    fn = np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]]); vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, TRI[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)


def edge_dihedral_p99(P, sel):
    """99th percentile of the angle between neighbouring vertex normals over the band (a crease / ledge measure)"""
    nn = vnormals(P); m = sel[E[:, 0]] & sel[E[:, 1]]
    c = np.clip(np.einsum("ij,ij->i", nn[E[m, 0]], nn[E[m, 1]]), -1, 1)
    return round(float(np.degrees(np.arccos(np.percentile(c, 1)))), 2)


t = np.clip(1 - np.abs(h - H0) / W, 0, 1)
w = t * t * (3 - 2 * t) * (held < 0.3)
band = w > 0.05
P = R.copy()
before = edge_dihedral_p99(P, band)
for _ in range(PASSES):
    Q = P.copy()
    for _ in range(ROUNDS):
        Q = 0.5 * Q + 0.5 * (A @ Q) * Dinv[:, None]
    nn = vnormals(P)
    hn = np.einsum("ij,ij->i", Q - P, nn)
    P = P + (w * hn)[:, None] * nn
D = P - R
rep = {"source": SRC.name, "character": character_profile.load()["id"], "band_h": H0, "band_w": W, "rounds": ROUNDS,
       "passes": PASSES, "band_vertices": int(band.sum()), "max_move_mm": round(float(np.linalg.norm(D, axis=1).max()) * 1000, 3),
       "normal_angle_p99_deg_before": before, "normal_angle_p99_deg_after": edge_dihedral_p99(P, band)}
kbs = me.shape_keys.key_blocks if me.shape_keys else []
for kb in kbs:
    c = np.empty(n * 3); kb.data.foreach_get("co", c)
    kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.vertices.foreach_set("co", P.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), copy=True)
(OUT / "rest_fair_band_report.json").write_text(json.dumps(rep, indent=1))
print("BAND", json.dumps(rep), flush=True)
