"""Candidate (new blend): make the skin weights left/right symmetric where they are not.

movement_trajectory_test_blender.py (with dominant-bone-checked mirror partners) measured a press-lockout asymmetry of
up to 92 mm at the posterior armpit.  Cause: the weights there differ between the sides (e.g. runtime-right vertices
~0.37 upperarm_r, their left partners ~0.0 upperarm_l with spine_03 instead).  On R121p and L4 about 400 vertex pairs
have a total-variation distance > 0.2 between their weight vector and their mirror partner's (mirrored group names),
mostly the posterior armpit and the hip crease; the asymmetry was inherited from the surface rebuild.

Here every mirror pair (rest positions within PAIR_TOL) whose weights differ by more than TV_MIN gets the mirror
average of the two (each side the mean of its own weights and its partner's mirrored weights), renormalised, repeated
for a few rounds because nearest mirror partners are not always mutual; nothing else changes.  This is neutral (it favours neither side); the corrective keys that cover the changed regions should be
re-authored afterwards.

usage: python3.13 symmetrize_weights_candidate_blender.py -- <in.blend> <out.blend>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.spatial import cKDTree

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
PAIR_TOL, TV_MIN, ROUNDS = 0.002, 0.05, 8
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data; n = len(me.vertices)
GN = [g.name for g in body.vertex_groups]; gi = {g: i for i, g in enumerate(GN)}


def mirror_name(s):
    return s[:-2] + {"_l": "_r", "_r": "_l"}[s[-2:]] if s[-2:] in ("_l", "_r") else s


Wt = np.zeros((n, len(GN)), np.float64)
for v in me.vertices:
    for g in v.groups:
        Wt[v.index, g.group] = g.weight
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
d, MIR = cKDTree(R).query(R * np.array([-1.0, 1.0, 1.0]))
perm = np.array([gi.get(mirror_name(g), i) for i, g in enumerate(GN)])
missing = sorted({mirror_name(g) for g in GN if mirror_name(g) not in gi})
Wm = np.zeros_like(Wt); Wm[:, perm] = Wt                 # each row's weights with the groups mirrored
ok = d < PAIR_TOL
tv0 = 0.5 * np.abs(Wt - Wm[MIR]).sum(1)
W1 = Wt.copy(); hist = []
for _ in range(ROUNDS):                                  # simultaneous mirror-averaging (partners need not be mutual)
    Wm1 = np.zeros_like(W1); Wm1[:, perm] = W1
    tv = 0.5 * np.abs(W1 - Wm1[MIR]).sum(1)
    sel = ok & (tv > TV_MIN)
    hist.append(int(sel.sum()))
    if not sel.any():
        break
    W1[sel] = 0.5 * (W1[sel] + Wm1[MIR[sel]])
    s_ = W1[sel].sum(1, keepdims=True); W1[sel] = W1[sel] / np.maximum(s_, 1e-12)
idx = np.flatnonzero(np.abs(W1 - Wt).max(1) > 1e-6)
new = W1[idx]
tv = tv0
G = body.vertex_groups
for k, vi in enumerate(idx):
    for j in np.flatnonzero((Wt[vi] > 0) | (new[k] > 0)):
        if new[k, j] > 1e-6:
            G[j].add([int(vi)], float(new[k, j]), "REPLACE")
        else:
            G[j].remove([int(vi)])
after = np.zeros((len(idx), len(GN)))
for k, vi in enumerate(idx):
    for g in me.vertices[vi].groups:
        after[k, g.group] = g.weight
rep = {"pair_tol_m": PAIR_TOL, "tv_min": TV_MIN, "pairs_over_tv_min_per_round": hist, "pairs": int(ok.sum()), "changed_vertices": int(len(idx)),
       "tv_gt_0.2_before": int((ok & (tv > 0.2)).sum()), "max_tv_before": round(float(tv[ok].max()), 3),
       "max_weight_change": round(float(np.abs(after - Wt[idx]).max()), 3) if len(idx) else 0.0,
       "groups_without_mirror": missing,
       "region_counts": {"z>1.2 (shoulder / axilla)": int((R[idx, 2] > 1.2).sum()), "z<0.9 (hip / thigh)": int((R[idx, 2] < 0.9).sum())}}
body["hgpt_r121_weight_symmetrize"] = json.dumps(rep)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("WSYM", json.dumps(rep), flush=True)
