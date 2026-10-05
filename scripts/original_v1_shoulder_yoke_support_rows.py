"""Fail-closed validation for the r96 lower axillary support-row declaration."""
from __future__ import annotations

from typing import Any


R95_SHA256 = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"
R96_TOPOLOGY_SHA256 = "6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd"


def _int_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in value
    )


def validate_support_rows_declaration(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1 or data.get("declared_before_edit") is not True:
        errors.append("schema 1 support rows must be declared before edit")
    if data.get("target_revision") != "r96" or data.get("parent_sha256") != R96_TOPOLOGY_SHA256:
        errors.append("exact r96 topology parent is required")
    if data.get("ancestor_r95_sha256") != R95_SHA256:
        errors.append("exact frozen r95 ancestor is required")
    evidence_sha = data.get("localization_evidence_sha256")
    if not isinstance(evidence_sha, str) or len(evidence_sha) != 64:
        errors.append("localization evidence SHA-256 is required")
    if data.get("operation") != "three_closed_quad_support_rows":
        errors.append("only three closed quad support rows are declared")

    seeds = data.get("ring_seed_edge_pairs")
    if not isinstance(seeds, list) or len(seeds) != 3 or not all(_int_list(pair) and len(pair) == 2 for pair in seeds):
        errors.append("exactly three valid seed edge pairs are required")
    rows = data.get("ring_edge_ids")
    if not isinstance(rows, list) or len(rows) != 3 or not all(_int_list(row) for row in rows):
        errors.append("exactly three non-empty edge rows are required")
        flat = [edge for row in rows or [] if isinstance(row, list) for edge in row if isinstance(edge, int)]
    else:
        flat = [edge for row in rows for edge in row]
    if len(flat) != len(set(flat)):
        errors.append("support rows must be edge-disjoint")
    endpoints = data.get("existing_endpoint_vertex_ids")
    if not _int_list(endpoints) or len(endpoints) != len(set(endpoints)):
        errors.append("existing endpoint vertex IDs must be unique")

    expected = data.get("expected_new_vertices")
    existing = data.get("existing_r96_new_vertices")
    cumulative = data.get("cumulative_new_vertices_from_r95")
    ceiling = data.get("maximum_cumulative_new_vertices")
    if not isinstance(expected, int) or expected <= 0 or expected != len(flat):
        errors.append("expected new vertices must equal the declared edge count")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (existing, cumulative, ceiling)):
        errors.append("cumulative topology counts must be integers")
    elif existing < 0 or cumulative != existing + expected or cumulative > ceiling or ceiling > 480:
        errors.append("cumulative new vertices must stay within the original 480-vertex ceiling")
    faces_ceiling = data.get("maximum_cumulative_new_faces")
    if not isinstance(faces_ceiling, int) or not 0 < faces_ceiling <= 960:
        errors.append("cumulative new faces must stay within the original 960-face ceiling")
    if data.get("maximum_new_vertex_influences") != 4:
        errors.append("new support vertices must have at most four deform influences")

    for key in (
        "preserve_original_vertex_ids",
        "preserve_original_positions",
        "preserve_shape_key_original_points",
        "preserve_quads",
        "mirror_symmetric",
        "correctives_disabled_during_gate",
    ):
        if data.get(key) is not True:
            errors.append("support-row declaration must require " + key)
    if data.get("production_approved") is not False:
        errors.append("support-row declaration must remain non-production")
    return errors
