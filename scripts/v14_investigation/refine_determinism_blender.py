"""Read-only diagnostic: is body_v2's mesh refinement (scripts/body_v2/refine_torso_blender.py::refine) deterministic?

Loads R41 exactly as build_body_v2_sculpt_blender.py does (r17._setup), runs refine() with the builder's default
arguments (8 mm, no nipple spots, the three R106/R113b/R114 beautify regions) and records two fingerprints of the
result: a geometric one that does not depend on vertex / face order (sorted triangles as rounded coordinates) and an
index-order one.  Nothing is saved; the input .blend is opened read-only and never written.

--sorted runs the same refine() but hands bmesh.ops.subdivide_edges / beautify_fill / triangulate their element
lists sorted by element index instead of in Python-set order (sets of BMesh elements iterate by memory address).

usage: python3.13 refine_determinism_blender.py -- <r57src root> <out.json> [--sorted]
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import bpy
import bmesh
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ROOT, OUTF = Path(args[0]).resolve(), Path(args[1])
SORTED = "--sorted" in args
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"),
                os.environ.get("V14INV_REFINE_DIR", str(HERE.parent / "body_v2"))]   # override: test a patched copy
import build_original_review_candidate_r17_blender as r17
import refine_torso_blender as rt

SRC = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend"
src_sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
res = r17._setup(SRC)
body = res["body"]

if SORTED:
    class _Ops:
        def __getattr__(self, name):
            return getattr(bmesh.ops, name)

        @staticmethod
        def _sort(bm, kw):
            bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
            for k in ("edges", "faces", "verts"):
                if k in kw:
                    kw[k] = sorted(kw[k], key=lambda e: e.index)
            return kw

        def subdivide_edges(self, bm, **kw):
            return bmesh.ops.subdivide_edges(bm, **self._sort(bm, kw))

        def beautify_fill(self, bm, **kw):
            return bmesh.ops.beautify_fill(bm, **self._sort(bm, kw))

        def triangulate(self, bm, **kw):
            return bmesh.ops.triangulate(bm, **self._sort(bm, kw))

    class _BMesh:
        ops = _Ops()

        def __getattr__(self, name):
            return getattr(bmesh, name)
    rt.bmesh = _BMesh()

regions = [((1.44, 1.58, 0.22), 99.0), ((1.16, 1.44, 0.22), 99.0), ((0.03, 1.60, 0.40), 99.0)]
t0 = time.time()
rep, _mi, _mw = rt.refine(body, th_mm=8.0, spots=[], regions=regions)
me = body.data
n = len(me.vertices)
P = np.empty(n * 3); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
T = np.array([p.vertices[:] for p in me.polygons])
# geometric fingerprint: each triangle as its three rounded corner coordinates, sorted; then all triangles sorted
Pr = np.round(P * 1e6).astype(np.int64)
tri_geo = np.sort(Pr[T].reshape(len(T), 3, 3).view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).reshape(len(T), 3), axis=1)
tri_geo = np.sort(tri_geo.view(np.int64).reshape(len(T), 9).view([(f"c{i}", np.int64) for i in range(9)]).ravel())
geo_sha = hashlib.sha256(tri_geo.tobytes()).hexdigest()
vert_set_sha = hashlib.sha256(np.sort(Pr.view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).ravel()).tobytes()).hexdigest()
idx_sha = hashlib.sha256(T.astype(np.int64).tobytes() + Pr.tobytes()).hexdigest()
out = {"mode": "sorted" if SORTED else ("patched module: " + os.environ["V14INV_REFINE_DIR"] if "V14INV_REFINE_DIR" in os.environ else "python-set order (as the builder)"), "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
       "bpy": bpy.app.version_string, "r41_sha256": src_sha, "seconds": round(time.time() - t0, 1),
       "refine_report": {k: rep[k] for k in ("vertices_after", "triangles_after", "rounds_edges_split", "beautify_geom")},
       "sha256_vertex_positions_as_set": vert_set_sha, "sha256_triangles_geometric": geo_sha,
       "sha256_index_order": idx_sha}
OUTF.parent.mkdir(parents=True, exist_ok=True)
OUTF.write_text(json.dumps(out, indent=1))
print("REFINE_DETERMINISM", json.dumps(out), flush=True)
