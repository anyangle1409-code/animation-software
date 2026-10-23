"""Read-only diagnostic: the V14 leg step's cut (scripts/body_v2/legs_v2_blender.py, "cut the old legs"), replayed on a
W8 body_v2.blend and accounted for vertex by vertex.  Nothing is saved; the input is never written.

The selection, plane and bisect below are copied from legs_v2_blender.py (the R119 v10-v18 versions are identical up
to here).  For each leg it records: stature measures (z0, H, cut height zc), the faces handed to bisect_plane, the old
vertices it removes, the vertices it creates (= the cut loop), and fingerprints of the skin around the cut - vertex
positions and triangle connectivity in a 2 cm band - so two W8 files can be told apart as "same vertices, different
triangles" or "different vertices".

The leg step's final vertex count is then
    final = W8 vertices - removed (both legs) + cut loop (both) + ring vertices + foot vertices
and the ring / foot counts depend only on the loop perimeter and the foot model (compare legs_v2_report.json).

usage: python3.13 cut_accounting_blender.py -- <body_v2.blend> <out.json>
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, OUTF = Path(args[0]).resolve(), Path(args[1])
src_sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
nv0 = len(me.vertices)
V0 = np.empty(nv0 * 3); me.vertices.foreach_get("co", V0); V0 = V0.reshape(-1, 3)
z0 = float(V0[:, 2].min()); H = float(V0[:, 2].max()) - z0
GN = [g.name for g in body.vertex_groups]
W0 = np.zeros((nv0, len(GN)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W0[v.index, g.group] = g.weight
gi = {n: i for i, n in enumerate(GN)}
ARMK = ("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "finger", "wrist", "clav")
ARM = W0[:, [i for i, n in enumerate(GN) if any(k in n.lower() for k in ARMK)]].sum(1)
SIDES = (("r", 1.0), ("l", -1.0))
LEGW = {sd: sum(W0[:, gi[f"{b}_{sd}"]] for b in ("thigh", "shin", "foot", "toe") if f"{b}_{sd}" in gi) for sd, _ in SIDES}
CUT = float(os.environ.get("V2_LEGS_CUT", "0.45"))
zc = z0 + CUT * H
T0 = np.array([p.vertices[:] for p in me.polygons])


def band_fingerprint(sg):
    """skin of one leg within 1 cm of the cut: vertex positions (as a set) and triangles (as sets of positions)"""
    P = np.round(V0 * 1e6).astype(np.int64)
    inb = (np.abs(V0[:, 2] - zc) < 0.01) & (V0[:, 0] * sg > 0) & (ARM < 0.3)
    vs = P[inb]; vs = vs[np.lexsort(vs.T[::-1])]
    tri_in = inb[T0].all(1)
    tr = np.sort(P[T0[tri_in]].reshape(-1, 3, 3).view([("a", np.int64), ("b", np.int64), ("c", np.int64)]).reshape(-1, 3), axis=1)
    tr = np.sort(tr.view(np.int64).reshape(-1, 9).view([(f"k{i}", np.int64) for i in range(9)]).ravel())
    return {"band_vertices": int(inb.sum()), "band_triangles": int(tri_in.sum()),
            "sha256_band_vertex_positions": hashlib.sha256(vs.tobytes()).hexdigest(),
            "sha256_band_triangles": hashlib.sha256(tr.tobytes()).hexdigest()}


bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
oid = bm.verts.layers.int.new("old_id")
for v in bm.verts:
    v[oid] = v.index
out = {"input": str(SRC.name), "input_sha256": src_sha, "bpy": bpy.app.version_string, "vertices": nv0,
       "z0_m": z0, "stature_m": H, "cut_fraction": CUT, "zc_m": zc, "sides": {}}
for sd, sg in SIDES:
    fp = band_fingerprint(sg)
    legv = (LEGW[sd] > 0.5) & (V0[:, 0] * sg > 0) & (ARM < 0.3)
    faces = [f for f in bm.faces if all(legv[v[oid]] if v[oid] >= 0 else True for v in f.verts)
             and min(v.co.z for v in f.verts) < zc + 0.03]
    geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
    pre = set(bm.verts)
    old_before = {v[oid] for v in bm.verts if v[oid] >= 0}
    # edges that will be cut: one endpoint strictly above, one strictly below (exactly-on-plane endpoints noted)
    fe = {e for f in faces for e in f.edges}
    cross = [e for e in fe if (e.verts[0].co.z - zc) * (e.verts[1].co.z - zc) < 0]
    onp = [v for v in {v for f in faces for v in f.verts} if abs(v.co.z - zc) < 1e-9]
    near = sorted(abs(v.co.z - zc) for v in {v for f in faces for v in f.verts})[:5]
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zc), plane_no=(0, 0, 1), clear_inner=True)
    cutv = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMVert)]
    created = [v for v in cutv if v not in pre]
    for v in created:
        v[oid] = -1
    old_after = {v[oid] for v in bm.verts if v[oid] >= 0}
    removed = sorted(old_before - old_after)
    bset = {v for v in cutv if v.is_boundary}
    out["sides"][sd] = {"faces_selected": len(faces), "edges_crossing_plane": len(cross),
                        "old_vertices_exactly_on_plane": len(onp), "closest_vertex_to_plane_mm": [round(x * 1000, 6) for x in near],
                        "vertices_created_by_bisect": len(created), "cut_loop_boundary_vertices": len(bset),
                        "old_vertices_removed": len(removed),
                        "sha256_removed_old_indices": hashlib.sha256(np.array(removed, np.int64).tobytes()).hexdigest(),
                        **fp}
out["net_change_from_cut"] = sum(s["vertices_created_by_bisect"] - s["old_vertices_removed"] for s in out["sides"].values())
OUTF.parent.mkdir(parents=True, exist_ok=True)
OUTF.write_text(json.dumps(out, indent=1))
print("CUT_ACCOUNTING", json.dumps(out), flush=True)
