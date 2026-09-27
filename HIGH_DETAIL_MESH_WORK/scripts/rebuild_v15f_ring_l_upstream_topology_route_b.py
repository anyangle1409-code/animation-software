"""Route B proof: rebuild ring_L flow before reapplying conservative freezes.

The accepted contact set remains exact.  All other ring_L vertices receive a
distance-tapered, volume-conscious surface fairing, then suitable triangle
pairs are rebuilt through Blender's UV-aware quad/beauty triangulation path.
No vertices, weights, UV layers, bones, actions or non-ring geometry change.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import sys
from collections import Counter, deque
from pathlib import Path

from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v15_anchor_buffer_policy import route_b_movement_cap_mm

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "checkpoints" / "v15_manual" / "v15f_deep_hand_rebuild_checkpoint_004.blend"
OUTPUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_upstream_topology_route_b_trial.blend"
REPORT = ROOT / "reports" / "v15f_ring_l_upstream_topology_route_b_attempt.json"
if OUTPUT.exists():
    raise SystemExit(f"Refusing to overwrite preserved trial: {OUTPUT.name}")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects["Mike_Freeman"]
mesh = body.data
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()

dlay = bm.verts.layers.deform.active
groups = {g.name: g.index for g in body.vertex_groups}


def members(name: str):
    gid = groups[name]
    return {v for v in bm.verts if v[dlay].get(gid, 0.0) > 0.5}


owned = members("V15_RING_L")
all_direct = members("V15_PROTECTED_PUSHUP")
direct = all_direct & owned
original_positions = {v.index: v.co.copy() for v in bm.verts}
original_weights = {
    v.index: tuple(sorted((int(gid), float(weight)) for gid, weight in v[dlay].items()))
    for v in bm.verts
}
owned_indices = {v.index for v in owned}
direct_indices = {v.index for v in all_direct}
original_ring_edges = {
    tuple(sorted((edge.verts[0].index, edge.verts[1].index)))
    for edge in bm.edges if all(v in owned for v in edge.verts)
}
original_vertex_count = len(bm.verts)
original_face_count = len(bm.faces)

# Whole-mesh distance reproduces the original V15 preparation rule, but only
# graph distance zero remains frozen in this upstream rebuild.
distance = {v: 0 for v in all_direct}
queue = deque(all_direct)
while queue:
    v = queue.popleft()
    if distance[v] >= 4:
        continue
    for edge in v.link_edges:
        other = edge.other_vert(v)
        if other not in distance:
            distance[other] = distance[v] + 1
            queue.append(other)


def cap_for(v) -> float:
    if v in direct:
        return 0.0
    return route_b_movement_cap_mm(distance.get(v, 4)) / 1000.0


def capped_target(v, delta):
    target = v.co + delta
    from_start = target - original_positions[v.index]
    cap = cap_for(v)
    if from_start.length > cap:
        from_start.length = cap
        target = original_positions[v.index] + from_start
    return target


movement_rows = []
for iteration in range(3):
    bm.normal_update()
    updates = {}
    for v in owned:
        if v in direct:
            continue
        neighbours = [edge.other_vert(v) for edge in v.link_edges if edge.other_vert(v) in owned]
        if len(neighbours) < 3:
            continue
        weights = [1.0 / max((other.co - v.co).length, 1e-8) for other in neighbours]
        centroid = sum((other.co * w for other, w in zip(neighbours, weights)), Vector()) / sum(weights)
        lap = centroid - v.co
        normal = v.normal.normalized() if v.normal.length > 1e-12 else Vector()
        normal_delta = normal * lap.dot(normal)
        tangent_delta = lap - normal_delta
        # Normal fairing removes faceted bands; limited tangential motion
        # regularises sampling while retaining joint and shaft volume.
        delta = 0.46 * normal_delta + 0.10 * tangent_delta
        updates[v] = capped_target(v, delta)
    for v, co in updates.items():
        v.co = co
    movement_rows.append({"iteration": iteration + 1, "updated_vertices": len(updates)})

bm.normal_update()

# Rebuild face flow through UV-aware temporary quads.  Direct-contact faces are
# excluded completely.  Blender owns the winding and BEAUTY diagonal choice,
# avoiding the invalid local winding seen in the rejected fixed-anchor flips.
triangles = [
    face for face in bm.faces
    if len(face.verts) == 3 and all(v in owned for v in face.verts) and not (set(face.verts) & direct)
]
joined = bmesh.ops.join_triangles(
    bm,
    faces=triangles,
    cmp_seam=True,
    cmp_sharp=True,
    cmp_uvs=True,
    cmp_vcols=True,
    cmp_materials=True,
    angle_face_threshold=math.radians(60.0),
    angle_shape_threshold=math.radians(75.0),
    topology_influence=0.35,
)
quads = [face for face in joined.get("faces", []) if face.is_valid and len(face.verts) == 4]
if quads:
    bmesh.ops.triangulate(bm, faces=quads, quad_method="BEAUTY", ngon_method="BEAUTY")
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.normal_update()
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

new_ring_edges = {
    tuple(sorted((edge.verts[0].index, edge.verts[1].index)))
    for edge in bm.edges if all(v in owned for v in edge.verts)
}
removed_edges = original_ring_edges - new_ring_edges
added_edges = new_ring_edges - original_ring_edges


def max_move(indices):
    return max(
        (math.dist(tuple(bm.verts[i].co), tuple(original_positions[i])) * 1000.0 for i in indices),
        default=0.0,
    )


direct_max = max_move(direct_indices)
outside_max = max_move(set(original_positions) - owned_indices)
weight_changes = sum(
    tuple(sorted((int(gid), float(weight)) for gid, weight in v[dlay].items())) != original_weights[v.index]
    for v in bm.verts
)
distance_moves = Counter()
for v in owned:
    move = math.dist(tuple(v.co), tuple(original_positions[v.index])) * 1000.0
    if move > 1e-7:
        distance_moves[str(distance.get(v, 4))] += 1

if direct_max != 0.0 or outside_max != 0.0 or weight_changes:
    raise RuntimeError("Route B hard invariant changed before save")
if len(bm.verts) != original_vertex_count or len(bm.faces) != original_face_count:
    raise RuntimeError("Route B unexpectedly changed vertex or face counts")
if not added_edges or not removed_edges:
    raise RuntimeError("Route B did not produce a topology change")

max_ring_move = max_move(owned_indices)
bm.to_mesh(mesh)
bm.free()
mesh.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

payload = {
    "strategy": "Route B upstream ring_L surface and topology rebuild",
    "source": str(SOURCE.relative_to(ROOT)),
    "output": OUTPUT.name,
    "scope": "ring_L only; direct push-up contacts exact",
    "fairing_iterations": movement_rows,
    "moved_vertices_by_contact_distance": dict(sorted(distance_moves.items())),
    "maximum_ring_L_move_mm": max_ring_move,
    "joined_quads": len(quads),
    "removed_ring_edges": len(removed_edges),
    "added_ring_edges": len(added_edges),
    "direct_contact_max_move_mm": direct_max,
    "outside_ring_L_max_move_mm": outside_max,
    "weight_rows_changed": weight_changes,
    "vertices_added_or_removed": 0,
    "faces_added_or_removed": 0,
    "uv_layers_preserved": [layer.name for layer in mesh.uv_layers],
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2), flush=True)
