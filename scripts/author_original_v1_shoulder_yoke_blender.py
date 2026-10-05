"""Author the declared r96 axillary support ring into a new candidate.

Only the committed single-ring topology declaration is accepted. Original
vertices, their weights, and all original shape-key points are audited fixed.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bmesh
import bpy
import numpy as np


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_topology import R95_SHA256, validate_topology_declaration  # noqa: E402


DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_support_ring_declared_before_edit.json"
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise SystemExit("new candidate path is required")
    out = Path(args[0]).resolve()
    receipt = out.with_suffix(".json")
    if out.exists() or receipt.exists():
        raise SystemExit("refusing to overwrite an r96 topology candidate")
    source = Path(bpy.data.filepath).resolve()
    if digest(source) != R95_SHA256:
        raise SystemExit("exact frozen r95 candidate required")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8-sig"))
    errors = validate_topology_declaration(declaration)
    if errors:
        raise SystemExit("invalid support-ring declaration: " + "; ".join(errors))
    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or rig is None or len(rig.data.bones) != 67:
        raise SystemExit("frozen r95 body or 67-bone rig is missing")
    mesh = body.data
    if mesh.shape_keys is None or len(mesh.shape_keys.key_blocks) != 7:
        raise SystemExit("expected Basis plus six frozen r95 corrective keys")

    vertex_count_before = len(mesh.vertices)
    face_count_before = len(mesh.polygons)
    basis_before = np.asarray([vertex.co[:] for vertex in mesh.vertices], dtype=float)
    shape_before = {
        key.name: np.asarray([point.co[:] for point in key.data], dtype=float)
        for key in mesh.shape_keys.key_blocks
    }
    group_names = {group.index: group.name for group in body.vertex_groups}
    weights_before = [
        {group_names[item.group]: float(item.weight) for item in vertex.groups}
        for vertex in mesh.vertices
    ]
    deform = {bone.name for bone in rig.data.bones if bone.use_deform}

    edge_ids = set(declaration["ring_edge_ids"])
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    if max(edge_ids) >= len(bm.edges):
        raise SystemExit("declared edge ID is out of range")
    selected_edges = [bm.edges[index] for index in sorted(edge_ids)]
    endpoint_ids = sorted({vertex.index for edge in selected_edges for vertex in edge.verts})
    if endpoint_ids != declaration["existing_endpoint_vertex_ids"]:
        raise SystemExit("declared ring endpoints do not match the frozen mesh")
    expected_midpoint_pairs = [(edge.verts[0].index, edge.verts[1].index) for edge in selected_edges]
    expected_midpoint_coordinates = np.asarray([
        0.5 * (basis_before[a] + basis_before[b]) for a, b in expected_midpoint_pairs
    ])
    if len({tuple(np.round(point, 7)) for point in expected_midpoint_coordinates}) != len(selected_edges):
        raise SystemExit("declared ring has duplicate rest-space midpoints")
    bm.free()

    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_mesh = bmesh.from_edit_mesh(mesh)
    edit_mesh.edges.ensure_lookup_table()
    for edge in edit_mesh.edges:
        edge.select = edge.index in edge_ids
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    result = bpy.ops.mesh.subdivide(number_cuts=1, smoothness=0.0, ngon=False, quadcorner="STRAIGHT_CUT")
    bpy.ops.object.mode_set(mode="OBJECT")
    if result != {"FINISHED"}:
        raise SystemExit("declared support-ring subdivision failed")
    mesh.update()

    new_ids = list(range(vertex_count_before, len(mesh.vertices)))
    if len(new_ids) != declaration["expected_new_vertices"]:
        raise SystemExit("support ring created an unexpected vertex count")
    if len(mesh.polygons) - face_count_before != declaration["expected_new_faces"]:
        raise SystemExit("support ring created an unexpected face count")
    if not all(len(face.vertices) == 4 for face in mesh.polygons):
        raise SystemExit("support ring did not preserve all-quad topology")
    basis_after = np.asarray([vertex.co[:] for vertex in mesh.vertices], dtype=float)
    original_basis_change = float(np.abs(basis_after[:vertex_count_before] - basis_before).max())
    if original_basis_change != 0.0:
        raise SystemExit("support ring moved an original vertex")

    midpoint_edges = []
    matched_midpoints = set()
    for vertex in new_ids:
        distances = np.linalg.norm(expected_midpoint_coordinates - basis_after[vertex], axis=1)
        match = int(np.argmin(distances))
        if float(distances[match]) > 1e-6 or match in matched_midpoints:
            raise SystemExit(f"new vertex is not a unique declared straight edge midpoint: {float(distances[match])}")
        matched_midpoints.add(match)
        midpoint_edges.append(expected_midpoint_pairs[match])
    shape_original_change = 0.0
    shape_new_midpoint_error = 0.0
    for key in mesh.shape_keys.key_blocks:
        after = np.asarray([point.co[:] for point in key.data], dtype=float)
        before = shape_before[key.name]
        shape_original_change = max(shape_original_change, float(np.abs(after[:vertex_count_before] - before).max()))
        for vertex, (a, b) in zip(new_ids, midpoint_edges):
            shape_new_midpoint_error = max(
                shape_new_midpoint_error,
                float(np.abs(after[vertex] - 0.5 * (before[a] + before[b])).max()),
            )
    if shape_original_change != 0.0 or shape_new_midpoint_error > 1e-6:
        raise SystemExit("support ring did not preserve/interpolate shape keys")

    # Blender interpolates group values. Reduce only the new deform rows to the
    # declared four strongest influences and normalise; all original rows stay fixed.
    groups_by_name = {group.name: group for group in body.vertex_groups}
    for vertex_id in new_ids:
        row = {
            group_names[item.group]: float(item.weight)
            for item in mesh.vertices[vertex_id].groups
            if group_names.get(item.group) in deform and item.weight > 1e-8
        }
        top = sorted(row.items(), key=lambda item: (-item[1], item[0]))[:4]
        total = sum(weight for _, weight in top)
        if total <= 0:
            raise SystemExit("new support vertex has no deform weights")
        for name in deform:
            group = groups_by_name.get(name)
            if group is not None:
                group.remove([vertex_id])
        for name, weight in top:
            groups_by_name[name].add([vertex_id], weight / total, "REPLACE")

    original_weight_change = 0.0
    for vertex_id in range(vertex_count_before):
        after = {group_names[item.group]: float(item.weight) for item in mesh.vertices[vertex_id].groups}
        names = set(after) | set(weights_before[vertex_id])
        original_weight_change = max(
            original_weight_change,
            max((abs(after.get(name, 0.0) - weights_before[vertex_id].get(name, 0.0)) for name in names), default=0.0),
        )
    if original_weight_change != 0.0:
        raise SystemExit("support ring changed an original vertex weight")
    new_rows = [
        [item.weight for item in mesh.vertices[vertex].groups if group_names.get(item.group) in deform and item.weight > 1e-8]
        for vertex in new_ids
    ]
    influence_max = max(len(row) for row in new_rows)
    normalisation_error = max(abs(sum(row) - 1.0) for row in new_rows)
    if influence_max > 4 or normalisation_error > 1e-6:
        raise SystemExit("new support weights violate the four-influence normalized bound")

    scene = bpy.context.scene
    scene["hgpt_candidate_revision"] = out.stem
    scene["hgpt_candidate_parent_sha256"] = R95_SHA256
    scene["hgpt_topology_revision"] = "r96_axillary_support_ring_v1"
    bpy.ops.wm.save_as_mainfile(filepath=str(out), copy=True)
    record = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "r96 declared axillary support topology; weights-only candidate intermediate",
        "source_candidate": source.name,
        "source_sha256": R95_SHA256,
        "declaration": DECLARATION.relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(DECLARATION),
        "candidate": out.name,
        "candidate_sha256": digest(out),
        "vertices_before": vertex_count_before,
        "vertices_after": len(mesh.vertices),
        "faces_before": face_count_before,
        "faces_after": len(mesh.polygons),
        "new_vertex_ids": new_ids,
        "new_vertex_source_edges": [
            {"new_vertex_id": vertex, "endpoint_vertex_ids": [a, b]}
            for vertex, (a, b) in zip(new_ids, midpoint_edges)
        ],
        "original_basis_max_change": original_basis_change,
        "original_weight_max_change": original_weight_change,
        "original_shape_key_point_max_change": shape_original_change,
        "new_shape_key_midpoint_max_error": shape_new_midpoint_error,
        "new_deform_influence_max": influence_max,
        "new_deform_normalisation_max_error": normalisation_error,
        "all_quad": True,
        "rig_bones": len(rig.data.bones),
        "correctives_retained": True,
        "correctives_disabled_during_gate": True,
        "production_approved": False,
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("R96 SUPPORT RING AUTHORED", json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
