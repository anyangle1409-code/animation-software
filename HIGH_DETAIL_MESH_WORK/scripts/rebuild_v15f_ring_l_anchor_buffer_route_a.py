"""One bounded Route A proof: regularise only ring_L anchor-buffer distance 2/3.

Direct contact and its one-edge collar remain fixed.  The operation preserves
topology and all skin rows and writes a separate experimental candidate.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import sys
from collections import deque
from pathlib import Path

from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v15_anchor_buffer_policy import movement_cap_mm

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "checkpoints" / "v15_manual" / "v15f_deep_hand_rebuild_checkpoint_004.blend"
OUTPUT = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_anchor_buffer_route_a_trial.blend"
REPORT = ROOT / "reports" / "v15f_ring_l_anchor_buffer_route_a_attempt.json"
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
anchors = members("V15_RING_L_ANCHOR") & owned
all_direct = members("V15_PROTECTED_PUSHUP")
direct = all_direct & owned
anchor_only = anchors - direct - (members("V15_PATCH_BOUNDARY") & owned)

distance = {v: 0 for v in all_direct}
queue = deque(all_direct)
while queue:
    v = queue.popleft()
    if distance[v] >= 3:
        continue
    for edge in v.link_edges:
        other = edge.other_vert(v)
        if other not in distance:
            distance[other] = distance[v] + 1
            queue.append(other)

original_positions = {v.index: v.co.copy() for v in bm.verts}
original_weights = {
    v.index: tuple(sorted((int(gid), float(weight)) for gid, weight in v[dlay].items()))
    for v in bm.verts
}
owned_indices = {v.index for v in owned}
direct_indices = {v.index for v in all_direct}
collar_indices = {v.index for v in anchor_only if distance.get(v) == 1}

# Mark the buffer vertices that actually participate in a >35-degree fold,
# either on the edge or in one of its adjacent faces.
severity = {}
for edge in bm.edges:
    if len(edge.link_faces) != 2 or any(v not in owned for v in edge.verts):
        continue
    angle = math.degrees(edge.link_faces[0].normal.angle(edge.link_faces[1].normal))
    if angle <= 35.0:
        continue
    affected = {v for face in edge.link_faces for v in face.verts}
    for v in affected:
        severity[v] = max(severity.get(v, 0.0), angle)

updates = {}
details = []
for v in anchor_only:
    graph_distance = distance.get(v, -1)
    cap_mm = movement_cap_mm(graph_distance)
    if cap_mm <= 0.0 or v not in severity:
        continue
    neighbours = [edge.other_vert(v) for edge in v.link_edges if edge.other_vert(v) in owned]
    if len(neighbours) < 3:
        continue
    # A single constrained surface-fairing step.  The normal component removes
    # the visible fold; a small tangential component improves spacing without
    # becoming another longitudinal profile redistribution.
    centroid = sum((other.co for other in neighbours), Vector()) / len(neighbours)
    laplacian = centroid - v.co
    normal = v.normal.normalized() if v.normal.length > 1e-12 else Vector((0.0, 0.0, 0.0))
    normal_delta = normal * laplacian.dot(normal)
    tangent_delta = laplacian - normal_delta
    strength = min(1.0, 0.35 + max(0.0, severity[v] - 35.0) / 45.0)
    delta = strength * (0.78 * normal_delta + 0.14 * tangent_delta)
    cap = cap_mm / 1000.0
    if delta.length > cap:
        delta.length = cap
    if delta.length <= 1e-8:
        continue
    updates[v] = v.co + delta
    details.append({
        "vertex": v.index,
        "graph_distance_from_direct": graph_distance,
        "incident_or_adjacent_max_angle_deg": severity[v],
        "movement_cap_mm": cap_mm,
        "move_mm": delta.length * 1000.0,
        "normal_component_mm": normal_delta.length * 1000.0,
        "neighbor_count": len(neighbours),
    })

for v, co in updates.items():
    v.co = co
bm.normal_update()

def max_move(indices):
    return max(
        (math.dist(tuple(bm.verts[i].co), tuple(original_positions[i])) * 1000.0 for i in indices),
        default=0.0,
    )

direct_max = max_move(direct_indices)
collar_max = max_move(collar_indices)
outside_max = max_move(set(original_positions) - owned_indices)
weight_changes = sum(
    tuple(sorted((int(gid), float(weight)) for gid, weight in v[dlay].items())) != original_weights[v.index]
    for v in bm.verts
)
if direct_max != 0.0 or collar_max != 0.0 or outside_max != 0.0 or weight_changes:
    raise RuntimeError("Route A hard invariant changed before save")

bm.to_mesh(mesh)
bm.free()
mesh.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

payload = {
    "strategy": "Route A constrained anchor-buffer surface regularisation",
    "source": str(SOURCE.relative_to(ROOT)),
    "output": OUTPUT.name,
    "scope": "ring_L anchor-buffer-only graph distances 2 and 3 adjacent to measured >35-degree folds",
    "moved_vertices": len(updates),
    "maximum_move_mm": max((row["move_mm"] for row in details), default=0.0),
    "distance_two_moved": sum(row["graph_distance_from_direct"] == 2 for row in details),
    "distance_three_moved": sum(row["graph_distance_from_direct"] == 3 for row in details),
    "direct_contact_max_move_mm": direct_max,
    "distance_one_collar_max_move_mm": collar_max,
    "outside_ring_L_max_move_mm": outside_max,
    "weight_rows_changed": weight_changes,
    "topology_changed": False,
    "details": details,
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in payload.items() if k != "details"}, indent=2), flush=True)
