"""CANDIDATE (review only): lower and slim the shoulders of a Body v2 blend, in the rest shape, on a copy.

Why: against the owner's reference (3 Nov 2026) the model's shoulders are high and square.
  * the shoulder line starts widening ~4 cm higher;
  * at 80 % of stature the silhouette is 0.31-0.32 of stature wide (reference 0.24-0.26);
  * the skin stands ~81 mm above and ~82 mm lateral of the glenohumeral (GH) centre, where an adult male shoulder is
    ~40-50 mm above (acromion + skin) and ~55-65 mm lateral (humeral head + deltoid + skin).
The skeleton is frozen and is not touched; only the skin moves.

What, per side, in the GH-centred frame (rest pose, the rig's upperarm_<s> head):
  * deltoid cap: skin in the lateral-superior direction from the GH centre is moved towards it by up to
    V2_SHAPE_DELT_MM at the most lateral point.  The weight is (direction . lateral-superior axis)^2, faded out
    between 9 and 14 cm from the centre.  Points on the armpit side (direction . axis <= 0) do not move.
  * trapezius: the top surface between the neck and the acromion is lowered by up to V2_SHAPE_TRAP_MM.  The weight
    peaks midway, fades to 0 at the neck (|x| 6 cm) and blends into the cap at the acromion.  Only skin whose normal
    points up moves; the front of the chest and the back below the scapular spine stay.
  * the displacement field is smoothed (V2_SHAPE_SMOOTH Laplacian rounds), so no new crease is made.
The change is added to the basis AND to every shape key.  Keys store absolute positions, so every corrective keeps
its offset exactly.  Weights, groups and drive data are unchanged.

usage: python3.13 rest_reshape_shoulders_blender.py -- <src.blend> <out dir>
       (refuses an existing <out dir>/body_v2_r121_arms.blend)
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
DELT_MM = float(os.environ.get("V2_SHAPE_DELT_MM", "16"))
TRAP_MM = float(os.environ.get("V2_SHAPE_TRAP_MM", "14"))
SMOOTH = int(os.environ.get("V2_SHAPE_SMOOTH", "12"))
RELAX = int(os.environ.get("V2_SHAPE_RELAX", "0"))             # tangential relaxation rounds in the moved region
DETAIL = float(os.environ.get("V2_SHAPE_DETAIL", "1.0"))       # fine relief kept where the skin moved (1 = all)
YRAMP = [float(x) for x in os.environ.get("V2_SHAPE_TRAP_YRAMP", "0.09,0.04").split(",")]   # trapezius front fade (m
# in front of the GH centre: full lowering behind -YRAMP[1], none in front of -YRAMP[0])
out_blend = OUT / "body_v2_r121_arms.blend"
if out_blend.exists():
    raise SystemExit(f"{out_blend} exists; refusing to overwrite")
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])


def vnormals(P):
    fn = np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]]); vn = np.zeros_like(P)
    for k in range(3):
        np.add.at(vn, TRI[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-15)


def ramp(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)


inv = body.matrix_world.inverted()
N = vnormals(R)
D = np.zeros_like(R)
rep = {"source": SRC.name, "delt_mm": DELT_MM, "trap_mm": TRAP_MM, "smooth_rounds": SMOOTH, "sides": {}}
for s in ("l", "r"):
    gh = np.array(inv @ (rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local))
    sg = np.sign(gh[0])
    rel = R - gh; r = np.linalg.norm(rel, axis=1); dirn = rel / np.maximum(r[:, None], 1e-9)
    side = np.sign(R[:, 0]) == sg
    # deltoid cap
    u = np.array([0.85 * sg, 0.0, 0.53]); u /= np.linalg.norm(u)
    w_dir = np.clip(dirn @ u, 0, 1) ** 2
    w_rad = 1 - ramp(r, 0.09, 0.14)
    w_cap = w_dir * w_rad * side
    lat = np.nonzero(side & (np.abs(R[:, 2] - gh[2]) < 0.015) & (np.abs(R[:, 1] - gh[1]) < 0.03))[0]
    i_lat = lat[np.argmax(np.abs(R[lat, 0]))]
    w_cap = w_cap / max(w_cap[i_lat], 1e-6)
    D += -(DELT_MM / 1000.0) * np.clip(w_cap, 0, 1.2)[:, None] * dirn
    # trapezius top line: neck (|x| 6 cm) -> acromion, posterior-superior skin with upward normals
    ax = np.abs(R[:, 0])
    w_x = ramp(ax, 0.06, 0.11) * (1 - ramp(ax, abs(gh[0]) - 0.03, abs(gh[0]) + 0.01))
    w_z = ramp(R[:, 2], gh[2] - 0.01, gh[2] + 0.03)
    w_up = ramp(N[:, 2], 0.25, 0.6)
    w_y = ramp(R[:, 1], gh[1] - YRAMP[0], gh[1] - YRAMP[1])  # not the front of the chest
    w_tr = w_x * w_z * w_up * w_y * side
    D[:, 2] += -(TRAP_MM / 1000.0) * w_tr
    rep["sides"][s] = {"gh_centre_m": [round(float(x), 4) for x in gh], "lateral_point_skin_mm": round(float(np.abs(R[i_lat, 0] - gh[0]) * 1000), 1),
                       "cap_vertices": int((w_cap > 0.05).sum()), "trap_vertices": int((w_tr > 0.05).sum())}
for _ in range(SMOOTH):
    D = 0.5 * D + 0.5 * (A @ D) * Dinv[:, None]
# S1 (16 / 14 mm, no relax) packed the cap's sculpted fine relief ~30 % tighter (visible crinkles): optionally even out
# the spacing in the moved region by sliding vertices within the surface, and attenuate its finest relief
wm = np.clip(np.linalg.norm(D, axis=1) / 0.002, 0, 1)
for _ in range(SMOOTH // 2):
    wm = np.maximum(wm, 0.85 * (A @ wm) * Dinv)
P = R + D
for _ in range(RELAX):
    nP = vnormals(P); L = (A @ P) * Dinv[:, None] - P
    L -= np.einsum("ij,ij->i", L, nP)[:, None] * nP
    P = P + 0.5 * wm[:, None] * L
if DETAIL < 1.0:
    Q = P.copy()
    for _ in range(3):
        Q = 0.5 * Q + 0.5 * (A @ Q) * Dinv[:, None]
    P = Q + (1.0 - (1.0 - DETAIL) * wm)[:, None] * (P - Q)
D = P - R
rep.update({"relax_rounds": RELAX, "detail_kept": DETAIL, "trap_front_fade_m": YRAMP})
mv = np.linalg.norm(D, axis=1)
rep["moved_over_1mm"] = int((mv > 1e-3).sum()); rep["max_move_mm"] = round(float(mv.max()) * 1000, 2)

# apply to the mesh, the basis and every key (keys hold absolute positions: each keeps its offset)
kbs = me.shape_keys.key_blocks if me.shape_keys else []
for kb in kbs:
    c = np.empty(n * 3); kb.data.foreach_get("co", c)
    kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.vertices.foreach_set("co", (R + D).ravel()); me.update()
for s in ("l", "r"):
    gh = np.array(inv @ (rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local))
    P = R + D
    lat = np.nonzero((np.sign(P[:, 0]) == np.sign(gh[0])) & (np.abs(P[:, 2] - gh[2]) < 0.015) & (np.abs(P[:, 1] - gh[1]) < 0.03))[0]
    up = np.nonzero((np.abs(P[:, 0] - gh[0]) < 0.02) & (np.abs(P[:, 1] - gh[1]) < 0.03) & (P[:, 2] > gh[2]))[0]
    rep["sides"][s]["after_lateral_mm"] = round(float(np.abs(P[lat, 0] - gh[0]).max() * 1000), 1)
    rep["sides"][s]["after_above_mm"] = round(float((P[up, 2].max() - gh[2]) * 1000), 1)
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), copy=True)
(OUT / "rest_reshape_shoulders_report.json").write_text(json.dumps(rep, indent=1))
print("RESHAPE", json.dumps(rep), flush=True)
