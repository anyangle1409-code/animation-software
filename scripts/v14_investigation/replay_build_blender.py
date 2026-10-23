"""Replay a preserved W8 triangulation: run build_body_v2_sculpt_blender.py unchanged, except that right after its
mesh refinement the refined mesh is given the preserved build's vertex order and triangles.

Why: refine() is not deterministic (V14 investigation, 2026-10-23) - every build has the same refined vertex
positions but a different triangulation and vertex order.  The archived V14 was built on build "L0"; its refined rest
positions and triangles are preserved in evidence/build_L0/refined_mesh_and_offsets.npz.  This wrapper:
  1. runs the original refine() (Blender interpolates every skin weight and shape key onto the new vertices);
  2. matches every refined vertex to the preserved one at the same position (the vertex SET is identical - checked,
     the run stops if not), re-orders the vertices into the preserved order, and replaces the triangles with the
     preserved triangles (R41 has no UVs or other face data; every face is smooth-shaded, one material);
  3. returns the preserved refine map, so the builder continues exactly as in that build.
The builder script itself is not modified; it is run in-process with runpy.  The output is a NEW W8 under <out>.

usage: python3.13 replay_build_blender.py -- <r57src root> <out dir> <gain> <refined_mesh_and_offsets.npz>
       (same environment variables as the builder, e.g. V2_SAVE_BLEND=1)
"""
import json
import runpy
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ROOT, OUT, GAIN, NPZ = args[0], args[1], args[2], Path(args[3]).resolve()
HERE = Path(__file__).resolve().parent
BUILDER = HERE.parent / "body_v2" / "build_body_v2_sculpt_blender.py"
sys.path[:0] = [str(HERE.parent / "body_v2")]
import refine_torso_blender as rt

PRE = np.load(NPZ)
_orig_refine = rt.refine
REPLAY = {}


def replay_refine(body, **kw):
    rep, _mi, _mw = _orig_refine(body, **kw)
    me = body.data
    n = len(me.vertices)
    tgt = PRE["rest"].astype(np.float64)
    assert len(tgt) == n, f"vertex count {n} != preserved {len(tgt)}"
    P = np.empty(n * 3); me.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
    from scipy.spatial import cKDTree
    d, j = cKDTree(tgt).query(P)
    REPLAY["match_max_dist_mm"] = float(d.max() * 1000)
    REPLAY["match_is_bijection"] = bool(len(np.unique(j)) == n)
    assert REPLAY["match_is_bijection"] and d.max() < 1e-6, f"vertex sets differ: max {d.max()} m, unique {len(np.unique(j))}"
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    newidx = {v: int(j[v.index]) for v in bm.verts}
    bmesh.ops.delete(bm, geom=list(bm.edges), context="EDGES_FACES")       # keeps the vertices and their layers
    bm.verts.sort(key=lambda v: newidx[v])
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    for t in PRE["tris"]:
        f = bm.faces.new((bm.verts[int(t[0])], bm.verts[int(t[1])], bm.verts[int(t[2])]))
        f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
    P2 = np.empty(n * 3); me.vertices.foreach_get("co", P2); P2 = P2.reshape(-1, 3)
    REPLAY["positions_equal_preserved_max_mm"] = float(np.abs(P2 - tgt).max() * 1000)
    T2 = np.array([p.vertices[:] for p in me.polygons])
    REPLAY["triangles_equal_preserved"] = bool(np.array_equal(T2, PRE["tris"]))
    rep = dict(rep); rep["replayed_from"] = str(NPZ.name); rep["replay"] = dict(REPLAY)
    print("V2_REPLAY", json.dumps(REPLAY), flush=True)
    return rep, PRE["refine_idx"].astype(np.int64), PRE["refine_w"].astype(np.float64)


rt.refine = replay_refine
sys.argv = [str(BUILDER), "--", ROOT, OUT, GAIN]
runpy.run_path(str(BUILDER), run_name="__main__")
