"""Candidate (new blend): copy shape-key offsets from another blend of the same topology, optionally low-pass filtered.

L4 zeroed the legacy shoulder families (S1 / S3 / S5 / S7) to remove the old surface's texture; on the legs the same
families' lesson was that low-pass filtering beats zeroing (it keeps their centimetre-scale correction - T3).  Once a
family has been zeroed its data is gone, so here it is brought back from an earlier blend of the same topology (e.g.
R121p2): for every key whose name starts with one of the prefixes, dst_key = dst_basis + (src_key - src_basis), the
offsets being rest-space, so the small basis differences between the blends (contact passes, a few mm) do not matter.
With V2_TRANSPLANT_SMOOTH_ITERS > 0 the transplanted offset fields are low-pass filtered as in
smooth_legacy_keys_candidate_blender.py (LAMBDA 0.5).

usage: python3.13 transplant_key_offsets_candidate_blender.py -- <src.blend> <dst.blend> <out.blend> prefix [prefix ...]
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

args = sys.argv[sys.argv.index("--") + 1:]
SRC, DST, OUT = Path(args[0]), Path(args[1]), Path(args[2])
PREFIXES = tuple(args[3:])
ITERS = int(os.environ.get("V2_TRANSPLANT_SMOOTH_ITERS", "0")); LAM = 0.5
if OUT.exists() or not PREFIXES:
    raise ValueError("output must be new and prefixes given")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
me = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"].data; n = len(me.vertices)
Bs = np.empty(n * 3); me.shape_keys.reference_key.data.foreach_get("co", Bs); Bs = Bs.reshape(-1, 3)
OFF = {}
for kb in me.shape_keys.key_blocks[1:]:
    if kb.name.startswith(PREFIXES):
        c = np.empty(n * 3); kb.data.foreach_get("co", c); OFF[kb.name] = c.reshape(-1, 3) - Bs
bpy.ops.wm.open_mainfile(filepath=str(DST))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = body.data
if len(me.vertices) != n:
    raise ValueError("topology differs")
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
Bd = np.empty(n * 3); me.shape_keys.reference_key.data.foreach_get("co", Bd); Bd = Bd.reshape(-1, 3)
rep = {"source": SRC.name, "prefixes": PREFIXES, "smooth_iters": ITERS, "keys": {}, "missing_in_dst": []}
for name, D in OFF.items():
    kb = me.shape_keys.key_blocks.get(name)
    if kb is None:
        rep["missing_in_dst"].append(name); continue
    D1 = D.copy()
    for _ in range(ITERS):
        D1 = D1 + LAM * ((A @ D1) * Dinv[:, None] - D1)
    kb.data.foreach_set("co", (Bd + D1).ravel())
    rep["keys"][name] = {"max_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2),
                         "max_mm_after_smoothing": round(float(np.linalg.norm(D1, axis=1).max() * 1000), 2)}
body["hgpt_r121_key_offsets_transplanted"] = json.dumps(rep)
me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
print("TRANSPLANT", json.dumps({"keys": len(rep["keys"]), "missing": len(rep["missing_in_dst"])}), flush=True)
