"""Declare one measured axillary support ring on exact r95 without editing it."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bmesh
import bpy


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_topology import R95_SHA256, validate_topology_declaration  # noqa: E402


MAX_DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/shoulder_yoke_declared_before_edit.json"
WEIGHT_SCREEN = ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks/r96_weights_only_screening/README.md"
DEFAULT_OUT = MAX_DECLARATION.with_name("r96_support_ring_declared_before_edit.json")
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_ring(start):
    result = [start]
    loop = start.link_loops[0]
    seen = {start.index}
    while True:
        opposite = loop.link_loop_next.link_loop_next
        if opposite.edge == start:
            return result, True
        if opposite.edge.index in seen:
            return result, False
        seen.add(opposite.edge.index)
        result.append(opposite.edge)
        next_loop = opposite.link_loop_radial_next
        if next_loop == opposite:
            return result, False
        loop = next_loop


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(args[0]).resolve() if args else DEFAULT_OUT.resolve()
    markdown = out.with_name("SUPPORT_RING_DECLARATION.md")
    if out.exists() or markdown.exists():
        raise SystemExit("refusing to overwrite the r96 support-ring declaration")
    source = Path(bpy.data.filepath).resolve()
    if digest(source) != R95_SHA256:
        raise SystemExit("exact frozen r95 candidate required")
    body = bpy.data.objects.get(BODY_NAME)
    if body is None or body.type != "MESH":
        raise SystemExit("frozen r95 body is missing")
    maximum = json.loads(MAX_DECLARATION.read_text(encoding="utf-8-sig"))
    declared = set(maximum["zone"]["left_vertex_ids"]) | set(maximum["zone"]["right_vertex_ids"])
    names = json.loads(bpy.context.scene["hgpt_region_names"])
    region_attr = body.data.attributes["hgpt_region"]

    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.edges.ensure_lookup_table()
    candidates = []
    seen = set()
    for seed in bm.edges:
        midpoint = (seed.verts[0].co + seed.verts[1].co) / 2
        if not (-0.30 < midpoint.x < -0.04 and 1.40 < midpoint.z < 1.43):
            continue
        ring, closed = trace_ring(seed)
        key = frozenset(edge.index for edge in ring)
        if key in seen:
            continue
        seen.add(key)
        mids = [(edge.verts[0].co + edge.verts[1].co) / 2 for edge in ring]
        xs = [point.x for point in mids]
        zs = [point.z for point in mids]
        if closed and len(ring) == 120 and 1.410 < min(zs) < max(zs) < 1.420 and abs(max(xs) + min(xs)) < 1e-5:
            candidates.append(ring)
    if len(candidates) != 1:
        raise SystemExit(f"expected one measured axillary support ring, found {len(candidates)}")
    ring = candidates[0]
    edge_ids = sorted(edge.index for edge in ring)
    endpoint_ids = sorted({vertex.index for edge in ring for vertex in edge.verts})
    centerline = [vertex for vertex in endpoint_ids if abs(body.data.vertices[vertex].co.x) <= 1e-8]
    outside = [vertex for vertex in endpoint_ids if vertex not in declared]
    if outside != centerline or len(centerline) != 4:
        raise SystemExit("ring may escape the maximum declaration only through four self-mirror centerline bridges")
    if any(names[region_attr.data[vertex].value] != "shoulder" for vertex in centerline):
        raise SystemExit("centerline bridge is not shoulder-region skin")
    mids = [(edge.verts[0].co + edge.verts[1].co) / 2 for edge in ring]
    bm.free()

    record = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent_sha256": R95_SHA256,
        "parent_candidate": maximum["parent"]["candidate_path"],
        "maximum_declaration": MAX_DECLARATION.relative_to(ROOT).as_posix(),
        "maximum_declaration_sha256": digest(MAX_DECLARATION),
        "evidence": WEIGHT_SCREEN.relative_to(ROOT).as_posix(),
        "evidence_sha256": digest(WEIGHT_SCREEN),
        "operation": "single_closed_quad_support_ring",
        "selection_rule": "the unique closed 120-edge quad ring with midpoint z 1.410..1.420 m, bilateral x symmetry and a seed midpoint in the left shoulder/axilla",
        "ring_edge_ids": edge_ids,
        "existing_endpoint_vertex_ids": endpoint_ids,
        "centerline_bridge_vertex_ids": centerline,
        "centerline_bridge_rule": "the only endpoints outside the strict-pair maximum zone are four x=0 self-mirror shoulder vertices required to keep the ring continuous and all-quad; their positions and existing weights remain unchanged",
        "expected_new_vertices": len(edge_ids),
        "expected_new_faces": len(edge_ids),
        "maximum_new_vertices": maximum["topology_intent"]["maximum_new_vertices"],
        "maximum_new_faces": maximum["topology_intent"]["maximum_new_faces"],
        "ring_midpoint_bbox_min_m": [round(min(float(point[i]) for point in mids), 6) for i in range(3)],
        "ring_midpoint_bbox_max_m": [round(max(float(point[i]) for point in mids), 6) for i in range(3)],
        "new_vertex_rule": "straight midpoint subdivision; every new shape-key point and vertex-group value is Blender's interpolation of the two existing endpoints",
        "existing_vertex_weight_change": False,
        "preserve_original_vertex_ids": True,
        "preserve_original_positions": True,
        "preserve_shape_key_original_points": True,
        "preserve_quads": True,
        "mirror_symmetric": True,
        "correctives_retained_but_disabled_for_gate": True,
        "stop_conditions": maximum["stop_conditions"],
        "production_approved": False,
    }
    errors = validate_topology_declaration(record)
    if errors:
        raise SystemExit("invalid r96 support-ring declaration: " + "; ".join(errors))
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# r96 axillary support-ring declaration\n\n"
        "Declared before topology editing on exact frozen r95.\n\n"
        f"- One closed all-quad ring: {len(edge_ids)} split edges / {len(edge_ids)} expected new vertices and faces\n"
        f"- Existing endpoints: {len(endpoint_ids)}; {len(endpoint_ids) - len(centerline)} inside the maximum paired zone plus {len(centerline)} self-mirror shoulder centerline bridges\n"
        "- Original vertex IDs, positions, weights, and all original shape-key points remain fixed\n"
        "- Correctives are retained but disabled during the weights-only gate\n"
        "- Production approval remains false\n",
        encoding="utf-8",
    )
    print("R96 SUPPORT RING DECLARED", out, len(edge_ids), "edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
