"""Pure geometry helpers for bounded r96 support-row rest-length probes."""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np


R95_SHA256 = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"
TOPOLOGY_PARENT_SHA256 = "6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd"
MAX_DECLARED_STRENGTH = 0.012
INNER_ZERO_X = 0.08
PEAK_X = 0.18
OUTER_ZERO_X = 0.29


def validate_rest_length_declaration(declaration: dict) -> list[str]:
    """Validate the exact pre-edit contract for the bounded probe family."""
    errors = []
    parent = declaration.get("parent", {})
    if not declaration.get("declared_before_edit"):
        errors.append("declaration must precede every rest-length edit")
    if declaration.get("target_revision") != "r96":
        errors.append("target revision must be r96")
    if parent.get("sha256") != TOPOLOGY_PARENT_SHA256 or parent.get("lineage_parent_r95_sha256") != R95_SHA256:
        errors.append("exact topology parent and r95 lineage are required")
    ids = [int(value) for value in declaration.get("new_support_vertex_ids", [])]
    pairs = declaration.get("mirror_pairs", [])
    flat = [int(value) for pair in pairs if isinstance(pair, list) and len(pair) == 2 for value in pair]
    if not ids or len(ids) != len(set(ids)) or sorted(flat) != sorted(ids):
        errors.append("mirror pair IDs must exactly cover new support vertices")
    strengths = [float(value) for value in declaration.get("probe_strengths_m", [])]
    maximum = float(declaration.get("maximum_displacement_m", -1.0))
    if not strengths or maximum != MAX_DECLARED_STRENGTH or min(strengths) < 0.0 or max(strengths) > maximum:
        errors.append("probe strengths exceed the displacement bound")
    if declaration.get("shape_key_policy") != "same_offset_all_keys":
        errors.append("shape keys must preserve their relative deltas")
    required_preserve = {"original_vertices", "weights", "topology", "rig"}
    if not required_preserve.issubset(set(declaration.get("preserve", []))):
        errors.append("preservation contract is incomplete")
    required_stop = {"critical_or_high_defect", "material_regression"}
    if not required_stop.issubset(set(declaration.get("stop_conditions", []))):
        errors.append("visual and regression stop conditions are required")
    if declaration.get("production_approved") is not False:
        errors.append("probe declaration cannot approve production")
    return errors


def _lateral_taper(abs_x: float) -> float:
    if abs_x <= INNER_ZERO_X or abs_x >= OUTER_ZERO_X:
        return 0.0
    if abs_x <= PEAK_X:
        return (abs_x - INNER_ZERO_X) / (PEAK_X - INNER_ZERO_X)
    return (OUTER_ZERO_X - abs_x) / (OUTER_ZERO_X - PEAK_X)


def build_mirrored_normal_offsets(
    rest: np.ndarray,
    normals: np.ndarray,
    mirror_pairs: Sequence[tuple[int, int]],
    *,
    strength: float,
) -> np.ndarray:
    """Return a mirror-exact, tapered normal offset field for declared pairs."""
    if strength < 0.0 or strength > MAX_DECLARED_STRENGTH:
        raise ValueError("strength exceeds the declared maximum")
    rest = np.asarray(rest, dtype=float)
    normals = np.asarray(normals, dtype=float)
    if rest.shape != normals.shape or rest.ndim != 2 or rest.shape[1] != 3:
        raise ValueError("rest and normals must be matching Nx3 arrays")
    offsets = np.zeros_like(rest)
    for left, right in mirror_pairs:
        mirrored_left = rest[left] * np.array([-1.0, 1.0, 1.0])
        if not np.allclose(mirrored_left, rest[right], atol=1.0e-5, rtol=0.0):
            raise ValueError("pair is not an exact rest-space mirror")
        mirrored_right_normal = normals[right] * np.array([-1.0, 1.0, 1.0])
        direction = normals[left] + mirrored_right_normal
        magnitude = float(np.linalg.norm(direction))
        if magnitude <= 1.0e-12:
            raise ValueError("paired normals do not define a stable direction")
        direction /= magnitude
        amount = strength * _lateral_taper(abs(float(rest[left, 0])))
        offsets[left] = amount * direction
        offsets[right] = offsets[left] * np.array([-1.0, 1.0, 1.0])
    return offsets
