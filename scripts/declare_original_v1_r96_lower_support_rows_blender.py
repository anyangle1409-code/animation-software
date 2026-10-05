"""Declare three exact lower axillary support rows before any topology edit."""
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


BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
SEEDS = ((859, 6105), (890, 6231), (922, 6290))
EVIDENCE = ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks/r96_axilla_edge_localization/r96_topology_only_edge_localization.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_ring(seed, pair_to_edge):
    pending = [pair_to_edge[tuple(sorted(seed))]]
    seen = set()
    result = []
    while pending:
        edge = pending.pop()
        if edge.index in seen:
            continue
        seen.add(edge.index)
        result.append(edge)
        endpoints = set(edge.verts)
        for face in edge.link_faces:
            if len(face.verts) != 4:
                raise SystemExit("support row crossed a non-quad face")
            opposite = [candidate for candidate in face.edges if not endpoints.intersection(candidate.verts)]
            if len(opposite) != 1:
                raise SystemExit("support row has no unique opposite quad edge")
            if opposite[0].index not in seen:
                pending.append(opposite[0])
    return result


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise SystemExit("declaration output path is required")
    out = Path(args[0]).resolve()
    if out.exists():
        raise SystemExit("refusing to overwrite a support-row declaration")
    source = Path(bpy.data.filepath).resolve()
    if digest(source) != R96_TOPOLOGY_SHA256:
        raise SystemExit("exact r96 topology parent is required")
    if not EVIDENCE.is_file():
        raise SystemExit("committed edge localization evidence is missing")
    body = bpy.data.objects.get(BODY_NAME)
    if body is None or not all(len(face.vertices) == 4 for face in body.data.polygons):
        raise SystemExit("r96 topology body is missing or not all-quad")
    mesh = body.data
    rest = np.asarray([vertex.co[:] for vertex in mesh.vertices], dtype=float)
    mirror_lookup = {tuple(np.round(point, 5)): index for index, point in enumerate(rest)}

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    pair_to_edge = {tuple(sorted(vertex.index for vertex in edge.verts)): edge for edge in bm.edges}
    rows = [edge_ring(seed, pair_to_edge) for seed in SEEDS]
    if [len(row) for row in rows] != [64, 64, 64]:
        raise SystemExit("support rows no longer resolve to three 64-edge rings")
    flat_ids = [edge.index for row in rows for edge in row]
    if len(flat_ids) != len(set(flat_ids)):
        raise SystemExit("support rows overlap")
    edge_pairs = [
        sorted([sorted(vertex.index for vertex in edge.verts) for edge in row])
        for row in rows
    ]
    flat_pairs = {tuple(pair) for row in edge_pairs for pair in row}
    for a, b in flat_pairs:
        ma = mirror_lookup.get(tuple(np.round(rest[a] * [-1.0, 1.0, 1.0], 5)))
        mb = mirror_lookup.get(tuple(np.round(rest[b] * [-1.0, 1.0, 1.0], 5)))
        if ma is None or mb is None or tuple(sorted((ma, mb))) not in flat_pairs:
            raise SystemExit("support rows are not exactly mirror-closed")
    endpoints = sorted({vertex for row in edge_pairs for pair in row for vertex in pair})
    row_records = []
    for seed, row, pairs in zip(SEEDS, rows, edge_pairs):
        midpoints = np.asarray([0.5 * (rest[a] + rest[b]) for a, b in pairs])
        row_records.append({
            "seed_edge_pair": list(seed),
            "edge_count": len(row),
            "edge_ids": sorted(edge.index for edge in row),
            "edge_vertex_pairs": pairs,
            "midpoint_bbox_min_m": [round(float(value), 6) for value in midpoints.min(axis=0)],
            "midpoint_bbox_max_m": [round(float(value), 6) for value in midpoints.max(axis=0)],
        })
    bm.free()

    declaration = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent_candidate": source.name,
        "parent_sha256": R96_TOPOLOGY_SHA256,
        "ancestor_r95_sha256": R95_SHA256,
        "localization_evidence": EVIDENCE.relative_to(ROOT).as_posix(),
        "localization_evidence_sha256": digest(EVIDENCE),
        "operation": "three_closed_quad_support_rows",
        "selection_rule": "closed mirror-symmetric quad edge rings containing exact localized strain seeds 859-6105, 890-6231, and 922-6290",
        "ring_seed_edge_pairs": [list(seed) for seed in SEEDS],
        "ring_edge_ids": [record["edge_ids"] for record in row_records],
        "ring_records": row_records,
        "existing_endpoint_vertex_ids": endpoints,
        "expected_new_vertices": len(flat_ids),
        "existing_r96_new_vertices": 120,
        "cumulative_new_vertices_from_r95": 120 + len(flat_ids),
        "maximum_cumulative_new_vertices": 480,
        "maximum_cumulative_new_faces": 960,
        "maximum_new_vertex_influences": 4,
        "new_vertex_rule": "straight midpoint with shape-key and deform-weight interpolation; retain four strongest normalized deform influences",
        "preserve_original_vertex_ids": True,
        "preserve_original_positions": True,
        "preserve_shape_key_original_points": True,
        "preserve_quads": True,
        "mirror_symmetric": True,
        "correctives_disabled_during_gate": True,
        "stop_conditions": ["parent_identity_mismatch", "out_of_scope_edit", "critical_or_high_defect", "material_regression"],
        "production_approved": False,
    }
    errors = validate_support_rows_declaration(declaration)
    if errors:
        raise SystemExit("invalid support-row declaration: " + "; ".join(errors))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes((json.dumps(declaration, indent=2) + "\n").encode("utf-8"))
    print("R96 LOWER SUPPORT ROWS DECLARED " + json.dumps({"out": str(out), "edge_counts": [len(row) for row in rows], "cumulative_new_vertices": 120 + len(flat_ids)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
