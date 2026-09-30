"""Add one supporting edge loop across the shoulder yoke / acromion of an O4 candidate.

blender --background --factory-startup <source O4_bind candidate.blend> --python-exit-code 1 \
        --python scripts/add_original_v1_o4_shoulder_support_loop_blender.py -- <new candidate.blend>

First-party topology repair (Priority 1). Evidence: overhead poses buckle the
deltoid-cap skin into the acromion top, where the ORIGINAL v1 quads are coarse
(crossing edges 12-48 mm). The script finds, from this mesh's own topology, the
closed edge ring that crosses the top of both shoulders (seed: the ring edge
nearest the left deltoid top) and splits it at its midpoint - an ordinary loop
cut, so the mesh stays all-quad and left/right symmetric. New vertices take the
interpolated deform weights of their edge (top 4 bones, renormalised) and the
hgpt_region of the edge's first vertex. Rig, other vertices, shorts and modifiers
are untouched. Refuses to overwrite; writes <new>.json with hashes and counts.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
new_path = Path(args[0])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src_path = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
if len(rig.data.bones) != 63:
    raise SystemExit("Expected the frozen 63-bone v4 rig.")
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
n_before, f_before = len(me.vertices), len(me.polygons)
deform = {b.name for b in rig.data.bones if b.use_deform}
gidx = {g.index: g.name for g in body.vertex_groups}

bm = bmesh.new()
bm.from_mesh(me)
bm.edges.ensure_lookup_table()
if any(len(f.verts) != 4 for f in bm.faces):
    raise SystemExit("Expected an all-quad mesh.")


def ring(start):
    out = [start]
    loop = start.link_loops[0]
    while True:
        opp = loop.link_loop_next.link_loop_next
        if opp.edge == start:
            return out, True
        out.append(opp.edge)
        nxt = opp.link_loop_radial_next
        if nxt == opp:
            return out, False
        loop = nxt


def acceptable(edges, closed):
    mids = [(e.verts[0].co + e.verts[1].co) / 2 for e in edges]
    xs = [m.x for m in mids]
    return (closed and len(edges) == 120 and max(m.z for m in mids) < 1.6 and min(m.z for m in mids) > 1.48
            and abs(max(xs) + min(xs)) < 0.002)


seed_pt = Vector((-0.23, 0.037, 1.52))
near = sorted((e for e in bm.edges if ((e.verts[0].co + e.verts[1].co) / 2 - seed_pt).length < 0.05),
              key=lambda e: ((e.verts[0].co + e.verts[1].co) / 2 - seed_pt).length)
edges, tested = None, set()
for seed in near:
    if seed.index in tested:
        continue
    cand, closed = ring(seed)
    tested.update(e.index for e in cand)
    if acceptable(cand, closed):
        edges = cand
        break
if edges is None:
    raise SystemExit("Shoulder-yoke ring not found (expected closed, 120 edges, symmetric, z 1.48-1.60).")

# remember endpoint weights/regions for the new vertices
dl = bm.verts.layers.deform.active
rl = bm.verts.layers.int.get("hgpt_region")
orig_co = [v.co.copy() for v in bm.verts]
bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
bm.verts.index_update()
bm.verts.ensure_lookup_table()
if any((bm.verts[i].co - orig_co[i]).length > 1e-9 for i in range(n_before)):
    raise SystemExit("Original vertex order/positions changed.")
new_verts = [v for v in bm.verts if v.index >= n_before]      # BMesh appends new vertices
if len(new_verts) != len(edges):
    raise SystemExit(f"Expected {len(edges)} new vertices, got {len(new_verts)}")
for v in new_verts:
    ends = [e.other_vert(v) for e in v.link_edges if e.other_vert(v).index < n_before]
    # the two original endpoints are the old neighbours colinear with v
    a, b = max(((p, q) for p in ends for q in ends if p != q),
               key=lambda pq: ((pq[0].co - v.co).normalized() - (pq[1].co - v.co).normalized()).length)
    w = {}
    for src in (a, b):
        for gi, wt in src[dl].items():
            if gidx.get(gi) in deform:
                w[gi] = w.get(gi, 0.0) + 0.5 * wt
    top = sorted(w.items(), key=lambda t: -t[1])[:4]
    tot = sum(x for _, x in top)
    v[dl].clear()
    for gi, wt in top:
        v[dl][gi] = wt / tot
    v[rl] = a[rl]
if any(len(f.verts) != 4 for f in bm.faces):
    raise SystemExit("Loop cut produced non-quad faces.")
bm.to_mesh(me)
bm.free()
me.update()

scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
scene["hgpt_topology_revision"] = "shoulder_yoke_support_loop_v1"
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate first-party topology repair: shoulder-yoke support loop (not production)",
       "source_candidate": src_path.name, "source_sha256": src_sha,
       "candidate": new_path.name, "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(),
       "vertices_before": n_before, "vertices_after": len(me.vertices),
       "faces_before": f_before, "faces_after": len(me.polygons), "ring_edges_split": len(edges),
       "new_vertex_index_range": [n_before, len(me.vertices) - 1], "rig_bones": len(rig.data.bones),
       "method": "bmesh subdivide_edges(cuts=1, grid fill) on the closed shoulder-yoke edge ring; "
                 "new vertices: averaged endpoint deform weights, top 4, renormalised",
       "inputs": "this candidate's own ORIGINAL v1 mesh/weights and the v4 rig only"}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("LOOP", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "vertices_before", "vertices_after",
                                                "faces_before", "faces_after")}))
