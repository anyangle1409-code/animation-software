"""Pure fail-closed validation for the r96 shoulder support-ring declaration."""
from __future__ import annotations

from typing import Any


R95_SHA256 = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"


def _ids(value: Any) -> list[int] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in value):
        return None
    return value


def validate_topology_declaration(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1 or data.get("declared_before_edit") is not True:
        errors.append("schema 1 declaration must be recorded before edit")
    if data.get("target_revision") != "r96" or data.get("parent_sha256") != R95_SHA256:
        errors.append("exact r95 parent is required for target r96")
    maximum_sha = data.get("maximum_declaration_sha256")
    if not isinstance(maximum_sha, str) or len(maximum_sha) != 64:
        errors.append("maximum declaration SHA-256 is required")
    if data.get("operation") != "single_closed_quad_support_ring":
        errors.append("only one closed quad support ring is declared")

    edges = _ids(data.get("ring_edge_ids"))
    endpoints = _ids(data.get("existing_endpoint_vertex_ids"))
    centerline = _ids(data.get("centerline_bridge_vertex_ids"))
    if edges is None or len(set(edges)) != len(edges):
        errors.append("ring edge IDs must be unique non-negative integers")
    if endpoints is None or len(set(endpoints)) != len(endpoints):
        errors.append("endpoint vertex IDs must be unique non-negative integers")
    if centerline is None or endpoints is None or not set(centerline).issubset(endpoints):
        errors.append("centerline bridge IDs must be a non-empty endpoint subset")

    expected = data.get("expected_new_vertices")
    max_vertices = data.get("maximum_new_vertices")
    max_faces = data.get("maximum_new_faces")
    if (
        not isinstance(expected, int) or expected <= 0
        or not isinstance(max_vertices, int) or not expected <= max_vertices <= 480
    ):
        errors.append("expected and maximum new vertices must be finite and within 480")
    elif edges is not None and expected != len(edges):
        errors.append("expected new vertices must equal the split edge count")
    if not isinstance(max_faces, int) or not 0 < max_faces <= 960:
        errors.append("maximum new faces must be finite and within 960")

    for key in (
        "preserve_original_vertex_ids", "preserve_original_positions",
        "preserve_shape_key_original_points", "preserve_quads", "mirror_symmetric",
    ):
        if data.get(key) is not True:
            errors.append("topology declaration must require " + key)
    if data.get("production_approved") is not False:
        errors.append("topology declaration must remain non-production")
    return errors
