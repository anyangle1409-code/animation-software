"""FIRST-PARTY clean-up of our Body v2 rest surface: Taubin (lambda / mu) smoothing of the bind shape.

The W12c surface carries small lumps and crinkles (upper arms, upper back, thighs) left by many patch passes.  Taubin
smoothing removes that noise without shrinking the volume; the head, hands and feet are masked out (feathered).
The change is added to the basis AND every shape key, so movement keys keep their offsets.

  usage: python3.13 rest_taubin_smooth_blender.py -- <in .blend> <out dir>
  env:   V2_TAUBIN_ITERS (default 40), V2_TAUBIN_LAMBDA (0.5), V2_TAUBIN_MU (-0.53)
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
IT = int(os.environ.get("V2_TAUBIN_ITERS", "40"))
LAM, MU = float(os.environ.get("V2_TAUBIN_LAMBDA", "0.5")), float(os.environ.get("V2_TAUBIN_MU", "-0.53"))
bpy.ops.wm.open_mainfile(filepath=str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402
bn, rn = character_profile.blender_names()
body = bpy.data.objects[bn]; me = body.data; n = len(me.vertices)
R0 = np.empty(n * 3); me.vertices.foreach_get("co", R0); R0 = R0.reshape(-1, 3)
GN = {g.index: g.name for g in body.vertex_groups}; G = {}
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(n))[v.index] = g.weight
gw = lambda *ks: sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n))
keep = np.clip(gw("head", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal", "foot", "toe"), 0, 1)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
for _ in range(6):                                                 # feather the mask
    keep = 0.5 * keep + 0.5 * (A @ keep) * Dinv
free = 1 - np.clip(keep * 1.5, 0, 1)
X = R0.copy()
for _ in range(IT):
    for f in (LAM, MU):
        L = (A @ X) * Dinv[:, None] - X
        X = X + f * free[:, None] * L
Dl = X - R0
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + Dl).ravel())
me.vertices.foreach_set("co", X.ravel()); me.update()
mv = np.linalg.norm(Dl, axis=1)
rep = {"source": SRC.name, "iters": IT, "lambda": LAM, "mu": MU, "max_move_mm": round(float(mv.max()) * 1000, 2),
       "p99_move_mm": round(float(np.percentile(mv, 99)) * 1000, 2)}
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / SRC.name), copy=True)
(OUT / "taubin_report.json").write_text(json.dumps(rep, indent=1)); print("TAUBIN", json.dumps(rep), flush=True)
