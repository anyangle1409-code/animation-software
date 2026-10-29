"""Candidate (new blend): keep the legacy corrective keys' large-scale correction, remove their high-frequency texture.

The legacy families transferred from the old surface carry two things: centimetre-scale corrections that still fit (for
the hip family, e.g., the lower-back fold the skinning makes at the squat bottom) and millimetre-scale texture of the old
surface, which is what adds the roughness (leg_roughness_diag_blender.py: squat p95 0.116 mm plain skinning -> 0.187 mm
with the legacy leg keys).  Neutralising them (neutralize_legacy_shoulder_keys_candidate_blender.py) removes both.
Here each key's rest-space offset field D = key - basis is low-pass filtered instead: ITERS rounds of
D += LAMBDA * (mean_of_neighbours(D) - D) over the mesh edges (characteristic length ~ edge * sqrt(ITERS), ~16 mm for
30 rounds on the ~3 mm body_v2 mesh).  Names, drives and the low-frequency shape stay.

usage: python3.13 smooth_legacy_keys_candidate_blender.py -- <in.blend> <out.blend> [prefix ...]
       env V2_SMOOTH_ITERS (30), V2_SMOOTH_LAMBDA (0.5); default prefixes HGPT_H1_ HGPT_K1_KNEE
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(args[0]), Path(args[1])
PREFIXES = tuple(args[2:]) or ("HGPT_H1_", "HGPT_K1_KNEE")
ITERS = int(os.environ.get("V2_SMOOTH_ITERS", "30")); LAM = float(os.environ.get("V2_SMOOTH_LAMBDA", "0.5"))
if OUT.exists():
    raise ValueError("output must be new")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data; n = len(me.vertices)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
B = np.empty(n * 3); me.shape_keys.reference_key.data.foreach_get("co", B); B = B.reshape(-1, 3)
rep = {"prefixes": PREFIXES, "iters": ITERS, "lambda": LAM, "keys": {}}
for kb in me.shape_keys.key_blocks[1:]:
    if not kb.name.startswith(PREFIXES):
        continue
    c = np.empty(n * 3); kb.data.foreach_get("co", c); D = c.reshape(-1, 3) - B
    D0 = D.copy()
    for _ in range(ITERS):
        D = D + LAM * ((A @ D) * Dinv[:, None] - D)
    kb.data.foreach_set("co", (B + D).ravel())
    m0, m1 = np.linalg.norm(D0, axis=1), np.linalg.norm(D, axis=1)
    rep["keys"][kb.name] = {"max_mm_before": round(float(m0.max() * 1000), 2), "max_mm_after": round(float(m1.max() * 1000), 2),
                            "removed_rms_mm": round(float(np.sqrt(((D0 - D) ** 2).sum(1).mean()) * 1000), 3)}
body["hgpt_r121_legacy_keys_smoothed"] = json.dumps(rep)
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("SMOOTH", json.dumps({"keys": len(rep["keys"])}), flush=True)
