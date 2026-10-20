"""R68 fix at the source: rebuild the rear-shoulder part of each S7 deltoid corrective (Claude, 20 Oct 2026).  Review only.

Finding (diagnose_shoulder_skinning_blender.py, R41 model): the posterior deltoid / posterior axillary fold is flattened and
pinched mainly by the S7 deltoid correctives (HGPT_S7_DELT_<side>_<deg>): switching S7 off cuts the rear-shoulder
triangles compressed below half their rest area from 425 to 63 at 135.6 deg and from 375 to 109 at 156 deg; the other
families (S1/S3/S5/H1/C1) barely change it.  S7 was fitted to the approved R47/R48 outline, which is measured only in the
lateral (+-x) and front-lateral ((+-x,-y)/sqrt2) directions at heights 1.18-1.62 m - the rear surface is not part of it.

For each S7 key (at its own elevation, both sides):
  B = posed skin with S7 off (natural rear deltoid, measured), P = posed skin with S7 on.
  Rear region R per side: rest within --radius of the upper-arm head and posterior (y > head - 1 cm).  Pinned: every
  vertex on the approved-outline support (Work's silhouette(), both directions, 1.18-1.62 m) and its one-ring, so the
  outline the owner approved cannot move.
  Laplacian editing on R: keep P outside R and on the pins, and inside R take B's surface detail (uniform-graph Laplacian
  coordinates) -> x.  The posed change x - P is mapped back to the key's rest-space offsets with each vertex's exact
  linear-skinning matrix (measured with a probe key), so the corrected key works through the whole blend.
Writes the corrected key coordinates to an .npz (nothing saved to a .blend).
  blender --background --python rear_restore_s7_blender.py -- <R57 root> <out.npz> [radius] [blend]
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

args = sys.argv[sys.argv.index("--") + 1:]
ROOT = Path(args[0]).resolve(); OUT = Path(args[1])
RADIUS = float(args[2]) if len(args) > 2 else 0.15
BLEND = float(args[3]) if len(args) > 3 else 1.0           # 1 = full B detail on R; <1 mixes with P's own detail
CORE_R = float(args[4]) if len(args) > 4 else 0.0          # R68b: >0 = smooth falloff (m) around the rear deltoid / posterior fold
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
os.environ["S7_LOCKOUT_HT"] = "166"
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px
from original_review_r48_outline import silhouette

MODEL = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend"
if hashlib.sha256(MODEL.read_bytes()).hexdigest() != "4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e":
    raise ValueError("Original Blender model bytes changed")
res = r17._setup(MODEL)
rig, body = res["runtime"], res["body"]
keys = body.data.shape_keys.key_blocks
s7 = [k for k in keys if k.name.startswith("HGPT_S7_DELT_")]
mw = body.matrix_world
nv = len(body.data.vertices)
tri = []
for p in body.data.polygons:
    v = p.vertices[:]
    tri += [(v[0], v[i], v[i + 1]) for i in range(1, len(v) - 1)]
faces = np.array(tri)
e = np.unique(np.sort(np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1), axis=0)
Adj = sparse.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(nv, nv)).tocsr()
L = (sparse.diags(np.asarray(Adj.sum(1)).ravel()) - Adj).tocsr()


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    m = ev.to_mesh()
    co = np.array([mw @ v.co for v in m.vertices])
    ev.to_mesh_clear()
    return co


def pose(ht):
    bench._reset(rig)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if px.press_state(mid)[0] < ht else (lo, mid)
    px.pose_press_full(res, 0.5 * (lo + hi))
    drives.drive(rig, body)
    bpy.context.view_layer.update()


bench._reset(rig); bpy.context.view_layer.update()
for k in keys:
    if k.name != "Basis":
        k.value = 0.0
REST = evaluated()
head = {s: np.array(rig.matrix_world @ rig.pose.bones[f"upperarm_{s}"].head) for s in "lr"}
region = np.zeros(nv, bool)
for s in "lr":
    region |= (np.linalg.norm(REST - head[s], axis=1) < RADIUS) & (REST[:, 1] > head[s][1] - 0.01)
# R68b: smooth application weight.  R68a (hard region) left a crease where the region edge met the shoulder top (the
# S7-off skin has its own linear-skinning crease there) - so the change is applied with a weight that is 1 on the rear
# deltoid / posterior axillary fold (rest centre: 4 cm behind and 7 cm below the upper-arm head) and fades to 0 by
# CORE_R, and fades out above the upper-arm head height (shoulder top / trapezius keep the current shape).
wgt = np.ones(nv)
if CORE_R > 0:
    def sm(x):
        x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
    wgt = np.zeros(nv)
    for s_ in "lr":
        # R68d: centred on where the pinch actually is (measured: rest centroid of the rear triangles compressed < 50 %
        # at 120-166 deg = (0.234, 0.07, 1.49), the back of the shoulder cap / posterior deltoid, 3 cm above the
        # upper-arm head), no height fade
        c = np.array([0.234 * (1 if s_ == "r" else -1), 0.07, 1.49])
        wgt = np.maximum(wgt, sm(1.0 - np.linalg.norm(REST - c, axis=1) / CORE_R))
probe = body.shape_key_add(name="R68_PROBE", from_mix=False)
basis_co = np.array([v.co for v in keys["Basis"].data])
H = 0.01
by_deg = {}
for k in s7:
    m = re.match(r"HGPT_S7_DELT_([lr])_(\d+)", k.name)
    by_deg.setdefault(int(m.group(2)), []).append(k)
report = {"radius_m": RADIUS, "blend": BLEND, "core_m": CORE_R, "keys": {}}
new_co = {}
for deg, ks in sorted(by_deg.items()):
    pose(float(deg))
    for k in s7:
        k.value = 1.0 if k in ks else 0.0
    probe.value = 0.0
    bpy.context.view_layer.update()
    P = evaluated()
    for k in ks:
        k.value = 0.0
    bpy.context.view_layer.update()
    B = evaluated()
    for k in ks:
        k.value = 1.0
    # exact per-vertex linear skinning matrix (shape offsets are skinned linearly): probe columns
    Acol = []
    for ax in range(3):
        off = basis_co.copy(); off[:, ax] += H
        probe.data.foreach_set("co", off.ravel())
        probe.value = 1.0
        bpy.context.view_layer.update()
        Acol.append((evaluated() - P) / H)
        probe.value = 0.0
    probe.data.foreach_set("co", basis_co.ravel())
    A = np.stack(Acol, axis=2)                                    # (nv, 3, 3): column ax = d posed / d rest_ax
    pins = set()
    for sign, side in ((-1, "l"), (1, "r")):
        for n in (np.array([sign, 0.0, 0.0]), np.array([sign, -1.0, 0.0]) / np.sqrt(2.0)):
            for h in np.arange(1.18, 1.62, 0.005):
                pins.update(silhouette(P, faces, side, n, h)[1].tolist())
    pin = np.zeros(nv, bool); pin[list(pins)] = True
    pin = pin | (Adj @ pin.astype(float) > 0)
    free = np.flatnonzero(region & ~pin)
    fixed = np.setdiff1d(np.arange(nv), free)
    target_delta = L @ (BLEND * B + (1 - BLEND) * P)
    LFF = L[free][:, free].tocsc(); LFC = L[free][:, fixed]
    x = P.copy()
    for ax in range(3):
        rhs = target_delta[free, ax] - LFC @ P[fixed, ax]
        x[free, ax] = spsolve(LFF, rhs)
    dpos = (x - P) * wgt[:, None]
    drest = np.linalg.solve(A[free], dpos[free][..., None])[..., 0]
    for k in ks:
        co = np.array([v.co for v in k.data])
        side = re.match(r"HGPT_S7_DELT_([lr])_", k.name).group(1)
        sel = free[(REST[free, 0] > 0) == (side == "r")]
        idx = np.searchsorted(free, sel)
        co[sel] += drest[idx]
        new_co[k.name] = co
        report["keys"][k.name] = {"vertices_changed": int(len(sel)), "max_posed_change_mm": round(float(np.linalg.norm(dpos[sel], axis=1).max() * 1000), 2),
                                  "pins": int(pin.sum())}
    print("R68R", deg, json.dumps({k.name: report["keys"][k.name] for k in ks}), flush=True)
body.shape_key_remove(probe)
np.savez_compressed(OUT, **new_co)
Path(str(OUT) + ".json").write_text(json.dumps(report, indent=1))
print("R68R_DONE", flush=True)
