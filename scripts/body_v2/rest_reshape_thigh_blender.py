"""CANDIDATE (review only): widen the lower thigh of a Body v2 blend, in the rest shape, on a copy.

Why: against the owner's reference (3 Nov 2026), at 0.37 of stature the thigh is 0.081 of stature wide in the front view
(reference 0.091, about 11 % thin).  The knee, calf and ankle match (docs/ANATOMICAL_DEFECT_LIST_20261103.md, 1.3).
The skeleton is frozen and is not touched; only the skin moves.

What, per side, in the thigh frame (the rig's thigh_<s>, hip -> knee):
  * skin is pushed out from the thigh axis, in the horizontal plane, by up to V2_THIGH_MM at the level of
    V2_THIGH_PEAK (fraction of stature).  The level profile rises from 0 at V2_THIGH_LO[0] to 1 at V2_THIGH_LO[1]
    (the knee stays), holds, and fades out between V2_THIGH_HI[0] and V2_THIGH_HI[1] (below the leg join);
  * the direction weight favours the medial and lateral sides (vastus medialis / lateralis, which make the front
    width), a little of the front (rectus femoris), none of the back (hamstrings, seen only from the side);
  * only skin weighted to the thigh (thigh group weight > 0.5) moves: the hands that hang beside it do not;
  * clearance guard: no thigh vertex comes closer than min(its rest clearance, V2_THIGH_GAP_MM) to the hand / forearm
    skin or the other leg (as R76i does for the arms);
  * the field is Laplacian-smoothed V2_THIGH_SMOOTH rounds.
The change is added to the basis AND to every shape key (keys hold absolute positions, so every corrective keeps its
offset).  Weights, groups and drive data are unchanged.  Object names come from the character profile
(character_profile.py; default the male).

usage: python3.13 rest_reshape_thigh_blender.py -- <src.blend> <out dir>
       (refuses an existing <out dir>/body_v2_r121_arms.blend)
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
MM = float(os.environ.get("V2_THIGH_MM", "9"))
LO = [float(x) for x in os.environ.get("V2_THIGH_LO", "0.30,0.35").split(",")]
HI = [float(x) for x in os.environ.get("V2_THIGH_HI", "0.40,0.445").split(",")]
FRONT = float(os.environ.get("V2_THIGH_FRONT", "0.4"))
GAP = float(os.environ.get("V2_THIGH_GAP_MM", "4")) / 1000.0
SMOOTH = int(os.environ.get("V2_THIGH_SMOOTH", "10"))
out_blend = OUT / "body_v2_r121_arms.blend"
if out_blend.exists():
    raise SystemExit(f"{out_blend} exists; refusing to overwrite")
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC))
BODY, RIG = character_profile.blender_names()
body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
me = body.data; n = len(me.vertices)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
z0 = float(R[:, 2].min()); H = float(R[:, 2].max()) - z0
h = (R[:, 2] - z0) / H
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
GN = [g.name for g in body.vertex_groups]
W = {}
for v in me.vertices:
    for g in v.groups:
        W.setdefault(GN[g.group], np.zeros(n))[v.index] = g.weight


def gsum(*keys):
    out = np.zeros(n)
    for name, w_ in W.items():
        if any(k in name for k in keys):
            out += w_
    return out


def ramp(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)


def front_width(P, side_sign, level):
    sel = (np.abs((P[:, 2] - z0) / H - level) < 0.004) & (np.sign(P[:, 0]) == side_sign) & (thigh_any > 0.5)
    return float(P[sel, 0].max() - P[sel, 0].min()) / H if sel.any() else None


inv = body.matrix_world.inverted()
arm_skin = gsum("hand", "metacarpal", "thumb", "index", "middle", "ring", "pinky", "forearm") > 0.3
thigh_any = np.zeros(n)
D = np.zeros_like(R)
rep = {"source": SRC.name, "character": character_profile.load()["id"], "mm": MM, "level_rise": LO, "level_fade": HI,
       "front_weight": FRONT, "gap_mm": GAP * 1000, "smooth_rounds": SMOOTH, "stature_m": round(H, 4), "sides": {}}
for s in ("l", "r"):
    b = rig.data.bones[f"thigh_{s}"]
    hip = np.array(inv @ (rig.matrix_world @ b.head_local)); knee = np.array(inv @ (rig.matrix_world @ b.tail_local))
    sg = np.sign(hip[0])
    wt = gsum(f"thigh_{s}")
    thigh_any += wt
    ax = (knee - hip) / np.linalg.norm(knee - hip)
    rel = R - hip
    rad = rel - np.outer(rel @ ax, ax); rad[:, 2] = 0.0          # horizontal push
    rdir = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
    lat = rdir[:, 0] * sg                                         # +1 lateral, -1 medial
    fwd = -rdir[:, 1]                                             # +1 front (-y)
    w_dir = np.clip(np.abs(lat) + FRONT * np.clip(fwd, 0, 1), 0, 1) * (1 - ramp(-fwd, 0.3, 0.8))
    w_lvl = ramp(h, LO[0], LO[1]) * (1 - ramp(h, HI[0], HI[1]))
    w = w_dir * w_lvl * ramp(wt, 0.5, 0.8) * (np.sign(R[:, 0]) == sg)
    D += (MM / 1000.0) * w[:, None] * rdir
    rep["sides"][s] = {"hip_m": [round(float(x), 4) for x in hip], "knee_m": [round(float(x), 4) for x in knee],
                       "moved_vertices": int((w > 0.05).sum())}
for _ in range(SMOOTH):
    D = 0.5 * D + 0.5 * (A @ D) * Dinv[:, None]
D[thigh_any < 0.3] = 0.0
# clearance guard: the hands / forearms and the other leg
mv = np.linalg.norm(D, axis=1) > 1e-5
idx = np.nonzero(mv)[0]
cap = np.ones(n)
for s in ("l", "r"):
    sg = np.sign(np.array(inv @ (rig.matrix_world @ rig.data.bones[f"thigh_{s}"].head_local))[0])
    mine = idx[np.sign(R[idx, 0]) == sg]
    others = np.nonzero(arm_skin | ((np.sign(R[:, 0]) != sg) & (thigh_any > 0.3)))[0]
    tree = cKDTree(R[others])
    d0, _ = tree.query(R[mine]); d1, _ = tree.query(R[mine] + D[mine])
    allowed = np.minimum(d0, GAP)
    bad = d1 < allowed
    # shrink the push where it would close the gap: ratio of what is allowed to what was asked
    need = np.linalg.norm(D[mine], axis=1)
    ratio = np.clip(1.0 - (allowed - d1) / np.maximum(need, 1e-9), 0, 1)
    cap[mine[bad]] = ratio[bad]
    rep["sides"][s]["clearance_limited_vertices"] = int(bad.sum())
for _ in range(SMOOTH // 2):                                    # soft cut-back
    cap = np.minimum(cap, 0.5 * cap + 0.5 * (A @ cap) * Dinv)
D *= cap[:, None]
P = R + D
for s in ("l", "r"):
    sgn = np.sign(np.array(inv @ (rig.matrix_world @ rig.data.bones[f"thigh_{s}"].head_local))[0])
    rep["sides"][s]["front_width_037_before"] = round(front_width(R, sgn, 0.37), 4)
    rep["sides"][s]["front_width_037_after"] = round(front_width(P, sgn, 0.37), 4)
    rep["sides"][s]["front_width_033_after"] = round(front_width(P, sgn, 0.33), 4)
    rep["sides"][s]["front_width_042_after"] = round(front_width(P, sgn, 0.42), 4)
others = np.nonzero(arm_skin)[0]
dmin = cKDTree(P[others]).query(P[idx])[0]
rep["min_clearance_to_hands_forearms_mm"] = round(float(dmin.min()) * 1000, 2)
rep["max_move_mm"] = round(float(np.linalg.norm(D, axis=1).max()) * 1000, 2)
rep["moved_over_1mm"] = int((np.linalg.norm(D, axis=1) > 1e-3).sum())
kbs = me.shape_keys.key_blocks if me.shape_keys else []
for kb in kbs:
    c = np.empty(n * 3); kb.data.foreach_get("co", c)
    kb.data.foreach_set("co", (c.reshape(-1, 3) + D).ravel())
me.vertices.foreach_set("co", P.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), copy=True)
(OUT / "rest_reshape_thigh_report.json").write_text(json.dumps(rep, indent=1))
print("THIGH", json.dumps(rep), flush=True)
