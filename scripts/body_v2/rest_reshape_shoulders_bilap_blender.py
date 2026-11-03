"""CANDIDATE (review only): lower and slim the shoulders in the rest shape with a smooth handle deformation, on a copy.

The first rest reshape (rest_reshape_shoulders_blender.py, ST_a 3 Nov) chose the moving skin by its normal (only skin
facing up was lowered) and pulled the deltoid cap radially towards the joint: at 20 / 22 mm that left a hard ridge
along the top of each shoulder where the lowering stopped, and the cap's relief was packed into crinkles.

Here only two small HANDLE regions per side are prescribed, and every other vertex near the shoulder is solved for the
smoothest displacement field that meets them (bi-Laplacian: minimise |L d|^2, uniform Laplacian), so nothing stops at
an edge:
  * trapezius crest: skin on the top of the shoulder between the neck and the acromion, lowered by up to V2_BILAP_TRAP_MM
    (a smooth bell across that span, peak midway);
  * deltoid: skin around the most lateral point of the cap (within V2_BILAP_CAP_R m), moved inwards by up to
    V2_BILAP_DELT_MM, a little downwards (V2_BILAP_DELT_DOWN, fraction);
  * fixed (no motion): everything farther than V2_BILAP_R m from the joint centre, the midline (|x| < 4.5 cm: neck,
    sternum, spine) and the head above the jaw;
  * the rest of the ball is free.
The displacement is added to the basis AND to every shape key (keys hold absolute positions).  Weights, groups and
drive data are unchanged; the skeleton is not touched.  Object names come from the character profile.

usage: python3.13 rest_reshape_shoulders_bilap_blender.py -- <src.blend> <out dir>
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import splu

sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
TRAP = float(os.environ.get("V2_BILAP_TRAP_MM", "18")) / 1000.0
DELT = float(os.environ.get("V2_BILAP_DELT_MM", "14")) / 1000.0
DOWN = float(os.environ.get("V2_BILAP_DELT_DOWN", "0.3"))
RAD = float(os.environ.get("V2_BILAP_R", "0.22"))
CAP_R = float(os.environ.get("V2_BILAP_CAP_R", "0.035"))
out_blend = OUT / "body_v2_r121_arms.blend"
if out_blend.exists():
    raise SystemExit(f"{out_blend} exists; refusing to overwrite")
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC))
BODY, RIG = character_profile.blender_names()
body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
me = body.data; n = len(me.vertices)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
deg = np.asarray(A.sum(1)).ravel()
Ls = (A - diags(deg)).tocsr()                                    # symmetric uniform Laplacian (graph)
K = (Ls.T @ diags(1.0 / np.maximum(deg, 1)) @ Ls).tocsr()        # bi-Laplacian energy |D^-1 Ls d|^2_D
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
known = np.zeros(n, bool)
rep = {"source": SRC.name, "character": character_profile.load()["id"], "trap_mm": TRAP * 1000, "delt_mm": DELT * 1000,
       "delt_down": DOWN, "radius_m": RAD, "cap_handle_r_m": CAP_R, "sides": {}}
for s in ("l", "r"):
    c = np.array(inv @ (rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local)); sg = np.sign(c[0])
    side = np.sign(R[:, 0]) == sg
    r = np.linalg.norm(R - c, axis=1)
    ax = np.abs(R[:, 0]); cx = abs(c[0])
    # fixed: outside the ball, the midline, the head
    fixed = side & ((r > RAD) | (ax < 0.045) | (R[:, 2] > c[2] + 0.15))
    # trapezius crest handle: top-facing skin between the neck and the acromion, near the crest's front-back middle
    span = (ax > 0.07) & (ax < cx - 0.02) & (R[:, 2] > c[2] + 0.02) & (np.abs(R[:, 1] - (c[1] + 0.01)) < 0.035) & (N[:, 2] > 0.75)
    t = np.clip((ax - 0.07) / max(cx - 0.02 - 0.07, 1e-6), 0, 1)
    bell = np.sin(np.pi * t) ** 1.2 * 0.75 + 0.25 * t               # peak midway, still lowered at the acromion end
    th = side & span & ~fixed
    D[th, 2] = -TRAP * bell[th]
    # deltoid handle: around the most lateral point of the cap
    lat = np.nonzero(side & (np.abs(R[:, 2] - c[2]) < 0.015) & (np.abs(R[:, 1] - c[1]) < 0.03))[0]
    pl = R[lat[np.argmax(ax[lat])]]
    dl = np.linalg.norm(R - pl, axis=1)
    ch = side & (dl < CAP_R) & ~fixed
    w = 1.0 - ramp(dl, 0.0, CAP_R)                                   # full at the point, 0 at the handle's rim
    D[ch, 0] = -sg * DELT * (0.35 + 0.65 * w[ch])
    D[ch, 2] = -DOWN * DELT * (0.35 + 0.65 * w[ch])
    known |= fixed | th | ch
    rep["sides"][s] = {"gh_centre_m": [round(float(x), 4) for x in c], "lateral_point_skin_mm": round(float(abs(pl[0] - c[0])) * 1000, 1),
                       "trap_handle_vertices": int(th.sum()), "cap_handle_vertices": int(ch.sum()),
                       "fixed_in_side": int(fixed.sum())}
# free: everything within the side's ball that is not prescribed; everything else is known (fixed at 0 outside the
# balls).  One sparse direct solve per side (the two balls do not touch)
rep["free_vertices"] = 0
for s in ("l", "r"):
    c = np.array(inv @ (rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local))
    free = (np.sign(R[:, 0]) == np.sign(c[0])) & (np.linalg.norm(R - c, axis=1) <= RAD) & ~known
    fi = np.nonzero(free)[0]
    Kf = K[fi]; Kff = Kf[:, fi].tocsc()
    rhs = -(Kf @ D) + Kff @ D[fi]                                # -(K_fk d_k): the free columns' own share removed
    lu = splu(Kff, permc_spec="MMD_AT_PLUS_A")
    for j in range(3):
        D[fi, j] = lu.solve(rhs[:, j])
    rep["free_vertices"] += int(len(fi))
P = R + D
for s in ("l", "r"):
    c = np.array(inv @ (rig.matrix_world @ rig.data.bones[f"upperarm_{s}"].head_local))
    lat = np.nonzero((np.sign(P[:, 0]) == np.sign(c[0])) & (np.abs(P[:, 2] - c[2]) < 0.015) & (np.abs(P[:, 1] - c[1]) < 0.03))[0]
    up = np.nonzero((np.abs(P[:, 0] - c[0]) < 0.02) & (np.abs(P[:, 1] - c[1]) < 0.03) & (P[:, 2] > c[2]))[0]
    rep["sides"][s]["after_lateral_mm"] = round(float(np.abs(P[lat, 0] - c[0]).max() * 1000), 1)
    rep["sides"][s]["after_above_mm"] = round(float((P[up, 2].max() - c[2]) * 1000), 1)
mv = np.linalg.norm(D, axis=1)
rep["moved_over_1mm"] = int((mv > 1e-3).sum()); rep["max_move_mm"] = round(float(mv.max()) * 1000, 2)
# strain check: the largest edge-length change (compression packs relief into crinkles)
l0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1); l1 = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
ratio = l1 / np.maximum(l0, 1e-9); mvd = (mv[E[:, 0]] > 1e-4) | (mv[E[:, 1]] > 1e-4)
rep["edge_ratio_p01_p99"] = [round(float(np.percentile(ratio[mvd], 1)), 3), round(float(np.percentile(ratio[mvd], 99)), 3)]
kbs = me.shape_keys.key_blocks if me.shape_keys else []
for kb in kbs:
    cc = np.empty(n * 3); kb.data.foreach_get("co", cc)
    kb.data.foreach_set("co", (cc.reshape(-1, 3) + D).ravel())
me.vertices.foreach_set("co", P.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), copy=True)
(OUT / "rest_reshape_shoulders_bilap_report.json").write_text(json.dumps(rep, indent=1))
print("BILAP", json.dumps(rep), flush=True)
