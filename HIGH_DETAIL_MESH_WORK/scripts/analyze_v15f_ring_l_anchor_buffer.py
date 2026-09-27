"""Read-only Route A safety analysis for the V15f left ring-finger buffer.

The accepted push-up contact vertices remain the hard invariant.  This report
separates them from the conservative four-edge modelling buffer added during
V15 preparation and assigns a bounded movement allowance only to graph-distance
two and three buffer vertices.
"""
from __future__ import annotations

import bpy
import bmesh
import json
import math
import sys
from collections import Counter, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v15_anchor_buffer_policy import movement_cap_mm, report_is_safe

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "checkpoints" / "v15_manual" / "v15f_deep_hand_rebuild_checkpoint_004.blend"
OUT_JSON = ROOT / "reports" / "v15f_ring_l_anchor_buffer_route_a.json"
OUT_MD = ROOT / "V15F_RING_L_ANCHOR_BUFFER_ROUTE_A.md"

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
body = bpy.data.objects["Mike_Freeman"]
arm = bpy.data.objects["HomeGymPT_Male_Rig"]
mesh = body.data

bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()

dlay = bm.verts.layers.deform.active
source_layer = bm.verts.layers.int.get("v8_source_id")
tracking_layer = bm.verts.layers.int.get("v15_baseline_vertex_id")
if dlay is None or source_layer is None or tracking_layer is None:
    raise RuntimeError("Candidate lacks required deform/source/tracking layers")

groups = {g.name: g.index for g in body.vertex_groups}


def members(name: str):
    gid = groups[name]
    return {v for v in bm.verts if v[dlay].get(gid, 0.0) > 0.5}


owned = members("V15_RING_L")
anchors = members("V15_RING_L_ANCHOR") & owned
all_direct = members("V15_PROTECTED_PUSHUP")
direct = all_direct & owned
boundaries = members("V15_PATCH_BOUNDARY") & owned
anchor_only = anchors - direct - boundaries

# Recompute the preparation script's whole-mesh distance from the complete
# authoritative contact set. Keep ring-local distance separately for diagnosis.
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

ring_distance = {v: 0 for v in direct}
queue = deque(direct)
while queue:
    v = queue.popleft()
    if ring_distance[v] >= 6:
        continue
    for edge in v.link_edges:
        other = edge.other_vert(v)
        if other in owned and other not in ring_distance:
            ring_distance[other] = ring_distance[v] + 1
            queue.append(other)

to_body = body.matrix_world.inverted() @ arm.matrix_world
bones = arm.data.bones
chain = [to_body @ bones["DEF-f_ring.01.L"].head_local] + [
    to_body @ bones[f"DEF-f_ring.{i:02d}.L"].tail_local for i in (1, 2, 3)
]
lengths = [(b - a).length for a, b in zip(chain[:-1], chain[1:])]
cumulative = [0.0]
for length in lengths:
    cumulative.append(cumulative[-1] + length)


def project(point):
    best = None
    for i, (a, b) in enumerate(zip(chain[:-1], chain[1:])):
        axis = b - a
        length = lengths[i]
        if length <= 1e-12:
            continue
        t = max(0.0, min(1.0, (point - a).dot(axis) / (length * length)))
        foot = a + t * axis
        candidate = ((point - foot).length_squared, cumulative[i] + t * length)
        if best is None or candidate[0] < best[0]:
            best = candidate
    return best[1]


def region(arc: float) -> str:
    pip, dip = cumulative[1], cumulative[2]
    if abs(arc - pip) <= 0.007:
        return "PIP"
    if abs(arc - dip) <= 0.007:
        return "DIP"
    if arc < pip:
        return "proximal_shaft"
    if arc < dip:
        return "middle_shaft"
    return "distal_shaft_tip"


problem_edges = []
problem_touch_count = Counter()
problem_face_count = Counter()
for edge in bm.edges:
    if len(edge.link_faces) != 2 or any(v not in owned for v in edge.verts):
        continue
    angle = math.degrees(edge.link_faces[0].normal.angle(edge.link_faces[1].normal))
    if angle <= 35.0:
        continue
    for v in edge.verts:
        problem_touch_count[v.index] += 1
    for face in edge.link_faces:
        for v in face.verts:
            problem_face_count[v.index] += 1
    problem_edges.append({
        "vertices": [v.index for v in edge.verts],
        "angle_deg": angle,
        "length_mm": edge.calc_length() * 1000.0,
    })

rows = []
for v in sorted(anchor_only, key=lambda item: item.index):
    graph_distance = distance.get(v, -1)
    cap = movement_cap_mm(graph_distance)
    arc = project(v.co)
    rows.append({
        "vertex": v.index,
        "tracking_id": int(v[tracking_layer]),
        "source_id": int(v[source_layer]) - 1 if int(v[source_layer]) > 0 else -1,
        "graph_distance_from_direct": graph_distance,
        "graph_distance_from_ring_L_direct": ring_distance.get(v, -1),
        "arc_mm": arc * 1000.0,
        "region": region(arc),
        "problem_edges_touching": problem_touch_count[v.index],
        "problem_edge_adjacent_face_occurrences": problem_face_count[v.index],
        "movement_cap_mm": cap,
        "eligible_for_route_a": cap > 0.0,
        "original_freeze_reason": "four-edge modelling transition around direct contact",
    })

distance_counts = dict(sorted(Counter(row["graph_distance_from_direct"] for row in rows).items()))
eligible = [row for row in rows if row["eligible_for_route_a"]]
eligible_problem = [row for row in eligible if row["problem_edges_touching"] or row["problem_edge_adjacent_face_occurrences"]]

summary = {
    "candidate": str(CANDIDATE.relative_to(ROOT)),
    "scope": "read-only Route A classification; no geometry saved",
    "decision": "ROUTE_A_SAFE_FOR_ONE_BOUNDED_EXPERIMENT",
    "direct_contact_vertices_ring_L": len(direct),
    "anchor_buffer_only_vertices": len(anchor_only),
    "anchor_buffer_distance_counts": distance_counts,
    "eligible_anchor_vertices": len(eligible),
    "eligible_anchor_vertices_near_problem_edges": len(eligible_problem),
    "fixed_distance_one_safety_collar_vertices": sum(row["graph_distance_from_direct"] == 1 for row in rows),
    "maximum_allowed_move_mm": max((row["movement_cap_mm"] for row in rows), default=0.0),
    "direct_contact_max_move_mm": 0.0,
    "direct_contact_weight_rows_changed": 0,
    "topology_changes_allowed": False,
    "weights_changes_allowed": False,
    "hard_invariants": [
        "all direct protected coordinates remain bit-identical",
        "all original bone-weight rows remain exact",
        "distance-one contact collar remains fixed",
        "no topology, UV, rig, hierarchy, exercise, grip or equipment changes",
        "all non-ring_L positions remain exact",
        "trial is a separate candidate and never replaces checkpoint 004 unless all gates pass",
    ],
    "movement_policy_mm": {"distance_0": 0.0, "distance_1": 0.0, "distance_2": 0.25, "distance_3": 0.55},
    "policy_basis": (
        "The V15 audit permits up to 10 mm for digit-owned source vertices, but Route A uses only "
        "2.5% and 5.5% of that ceiling. Distance one stays fixed as a safety collar. The experiment "
        "can therefore test the conservative modelling freeze without weakening accepted contact."
    ),
    "problem_edges_gt35": len(problem_edges),
}
summary["policy_safe"] = report_is_safe(summary)
if len(anchor_only) != 390:
    raise RuntimeError(f"Expected 390 anchor-only ring_L vertices, found {len(anchor_only)}")
if not summary["policy_safe"]:
    raise RuntimeError("Route A policy did not satisfy the hard-invariant contract")

payload = dict(summary)
payload["anchor_buffer_vertices"] = rows
payload["problem_edges"] = problem_edges
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

lines = [
    "# V15f ring_L Route A anchor-buffer analysis", "",
    f"- Candidate: `{summary['candidate']}`",
    "- Operation: read-only; no geometry was saved",
    f"- Decision: **{summary['decision']}**", "",
    "## Evidence", "",
    f"- Direct protected ring_L vertices: {len(direct)} (movement allowance 0.00 mm)",
    f"- Anchor-buffer-only vertices: {len(anchor_only)}",
    f"- Distance distribution: {distance_counts}",
    f"- Eligible distance-two/three vertices: {len(eligible)}",
    f"- Eligible vertices touching or face-adjacent to a >35 degree edge: {len(eligible_problem)}",
    f"- Fixed distance-one safety collar: {summary['fixed_distance_one_safety_collar_vertices']} vertices",
    f"- Maximum Route A movement: {summary['maximum_allowed_move_mm']:.2f} mm", "",
    "The accepted direct-contact set and its skin rows remain exact. The wider anchor group was created by",
    "the V15 preparation script as a four-edge modelling transition; it is not part of the accepted contact",
    "guard. Route A can therefore test only distance-two and distance-three buffer vertices while keeping",
    "the direct set and a one-edge safety collar fixed.", "",
    "## Movement envelope", "",
    "- graph distance 0: 0.00 mm (direct contact)",
    "- graph distance 1: 0.00 mm (fixed safety collar)",
    "- graph distance 2: 0.25 mm",
    "- graph distance 3: 0.55 mm", "",
    "These caps are 2.5% and 5.5% of the existing 10 mm digit-source audit ceiling. The trial must still",
    "prove zero direct-contact movement, zero weight-row changes, exact non-ring geometry, numeric PASS and",
    "a visible improvement in the matched V13e comparison. The full per-vertex classification is in",
    f"`{OUT_JSON.relative_to(ROOT)}`.", "",
]
OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(json.dumps(summary, indent=2), flush=True)
bm.free()
