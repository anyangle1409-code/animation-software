"""Author the committed three lower axillary support rows into a new probe Blend."""
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
from original_v1_shoulder_yoke_support_rows import (  # noqa: E402
    R95_SHA256,
    R96_TOPOLOGY_SHA256,
    validate_support_rows_declaration,
)


DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_lower_support_rows_declared_before_edit.json"
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("new support-row candidate path is required")
    out = Path(args[0]).resolve()
    receipt_path = out.with_suffix(".json")
    if out.exists() or receipt_path.exists():
        raise SystemExit("refusing to overwrite a support-row candidate")
    source = Path(bpy.data.filepath).resolve()
    if digest(source) != R96_TOPOLOGY_SHA256:
        raise SystemExit("exact declared r96 topology parent is required")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8-sig"))
    errors = validate_support_rows_declaration(declaration)
    if errors:
        raise SystemExit("invalid support-row declaration: " + "; ".join(errors))

    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or rig is None or len(rig.data.bones) != 67:
        raise SystemExit("r96 body or 67-bone rig is missing")
    mesh = body.data
    if mesh.shape_keys is None or len(mesh.shape_keys.key_blocks) != 7:
        raise SystemExit("expected Basis plus six retained corrective keys")
    for key in mesh.shape_keys.key_blocks[1:]:
        key.value = 0.0

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

    edge_ids = {edge_id for row in declaration["ring_edge_ids"] for edge_id in row}
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.edges.ensure_lookup_table()
    if max(edge_ids) >= len(bm.edges):
        raise SystemExit("declared support-row edge ID is out of range")
    selected_edges = [bm.edges[index] for index in sorted(edge_ids)]
    endpoint_ids = sorted({vertex.index for edge in selected_edges for vertex in edge.verts})
    if endpoint_ids != declaration["existing_endpoint_vertex_ids"]:
        raise SystemExit("declared support-row endpoints do not match parent")
    expected_pairs = [(edge.verts[0].index, edge.verts[1].index) for edge in selected_edges]
    expected_midpoints = np.asarray([0.5 * (basis_before[a] + basis_before[b]) for a, b in expected_pairs])
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
        raise SystemExit("declared lower support-row subdivision failed")
    mesh.update()

    new_ids = list(range(vertex_count_before, len(mesh.vertices)))
    expected_new = declaration["expected_new_vertices"]
    if len(new_ids) != expected_new or len(mesh.polygons) - face_count_before != expected_new:
        raise SystemExit("support-row subdivision created unexpected topology counts")
    if not all(len(face.vertices) == 4 for face in mesh.polygons):
        raise SystemExit("support rows did not preserve all-quad topology")
    basis_after = np.asarray([vertex.co[:] for vertex in mesh.vertices], dtype=float)
    original_basis_change = float(np.abs(basis_after[:vertex_count_before] - basis_before).max())
    if original_basis_change != 0.0:
        raise SystemExit("support rows moved an existing vertex")

    matched = set()
    midpoint_pairs = []
    for vertex in new_ids:
        distances = np.linalg.norm(expected_midpoints - basis_after[vertex], axis=1)
        match = int(np.argmin(distances))
        if float(distances[match]) > 1.0e-6 or match in matched:
            raise SystemExit("new support-row vertex is not a unique declared midpoint")
        matched.add(match)
        midpoint_pairs.append(expected_pairs[match])

    shape_original_change = 0.0
    shape_midpoint_error = 0.0
    for key in mesh.shape_keys.key_blocks:
        after = np.asarray([point.co[:] for point in key.data], dtype=float)
        before = shape_before[key.name]
        shape_original_change = max(shape_original_change, float(np.abs(after[:vertex_count_before] - before).max()))
        for vertex, (a, b) in zip(new_ids, midpoint_pairs):
            shape_midpoint_error = max(shape_midpoint_error, float(np.abs(after[vertex] - 0.5 * (before[a] + before[b])).max()))
    if shape_original_change != 0.0 or shape_midpoint_error > 1.0e-6:
        raise SystemExit("support rows did not preserve and interpolate shape keys")

    groups_by_name = {group.name: group for group in body.vertex_groups}
    for vertex_id in new_ids:
        row = {
            group_names[item.group]: float(item.weight)
            for item in mesh.vertices[vertex_id].groups
            if group_names.get(item.group) in deform and item.weight > 1.0e-8
        }
        top = sorted(row.items(), key=lambda item: (-item[1], item[0]))[:4]
        total = sum(weight for _, weight in top)
        if total <= 0.0:
            raise SystemExit("new support-row vertex has no deform weights")
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
        original_weight_change = max(original_weight_change, max((abs(after.get(name, 0.0) - weights_before[vertex_id].get(name, 0.0)) for name in names), default=0.0))
    if original_weight_change != 0.0:
        raise SystemExit("support rows changed an existing vertex weight")
    new_rows = [
        [item.weight for item in mesh.vertices[vertex].groups if group_names.get(item.group) in deform and item.weight > 1.0e-8]
        for vertex in new_ids
    ]
    influence_max = max(len(row) for row in new_rows)
    normalization_error = max(abs(sum(row) - 1.0) for row in new_rows)
    if influence_max > 4 or normalization_error > 1.0e-6:
        raise SystemExit("new support-row weights violate declared bounds")

    scene = bpy.context.scene
    scene["hgpt_candidate_revision"] = out.stem
    scene["hgpt_candidate_parent_sha256"] = R96_TOPOLOGY_SHA256
    scene["hgpt_candidate_ancestor_r95_sha256"] = R95_SHA256
    scene["hgpt_topology_revision"] = "r96_axillary_support_rows_v2"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), copy=True)
    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "r96 declared lower axillary support rows; topology-only probe",
        "source_candidate": source.name,
        "source_sha256": R96_TOPOLOGY_SHA256,
        "ancestor_r95_sha256": R95_SHA256,
        "declaration": DECLARATION.relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(DECLARATION),
        "candidate": out.name,
        "candidate_sha256": digest(out),
        "vertices_before": vertex_count_before,
        "vertices_after": len(mesh.vertices),
        "faces_before": face_count_before,
        "faces_after": len(mesh.polygons),
        "new_vertex_ids": new_ids,
        "original_basis_max_change": original_basis_change,
        "original_weight_max_change": original_weight_change,
        "original_shape_key_point_max_change": shape_original_change,
        "new_shape_key_midpoint_max_error": shape_midpoint_error,
        "new_deform_influence_max": influence_max,
        "new_deform_normalization_max_error": normalization_error,
        "cumulative_new_vertices_from_r95": len(mesh.vertices) - 17946,
        "all_quad": True,
        "rig_bones": len(rig.data.bones),
        "correctives_retained": True,
        "correctives_disabled_during_gate": True,
        "production_approved": False,
    }
    receipt_path.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print("R96 LOWER SUPPORT ROWS AUTHORED " + json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
