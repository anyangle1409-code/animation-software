"""Pure selection and constrained diffusion for r96 shoulder-yoke probes."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np

from original_v1_shoulder_yoke_weights import edge_l1

R95_SHA256 = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"


def validate_probe_parent(dump_source_sha256: str, parent: dict) -> bool:
    """Accept exact r95 or an exact declared topology child of r95."""
    if not isinstance(parent, dict) or parent.get("sha256") != dump_source_sha256:
        return False
    if dump_source_sha256 == R95_SHA256:
        return True
    return parent.get("lineage_parent_r95_sha256") == R95_SHA256


def select_safe_mirror_subzone(
    left_ids: Sequence[int],
    right_ids: Sequence[int],
    rows: Sequence[dict[str, float]],
    regions: Sequence[str],
    permitted_regions: set[str],
    permitted_bones: set[str],
    edges: Iterable[tuple[int, int]],
    gradient_threshold: float,
    dilation_rings: int,
) -> dict:
    """Select measured high-gradient pairs without crossing an unsafe pair.

    A pair is eligible only when both vertices are in a permitted anatomical
    region and every existing deform influence is permitted. Seeds are pairs
    incident to an edge whose full deform-weight L1 jump reaches the threshold.
    Dilation follows mesh edges but can visit eligible declared pairs only.
    """
    if len(left_ids) != len(right_ids):
        raise ValueError("left and right declaration lists must have equal length")
    if gradient_threshold <= 0 or dilation_rings < 0:
        raise ValueError("gradient threshold must be positive and rings non-negative")

    pairs = [(int(left), int(right)) for left, right in zip(left_ids, right_ids)]
    pair_of = {vertex: index for index, pair in enumerate(pairs) for vertex in pair}
    if len(pair_of) != 2 * len(pairs):
        raise ValueError("mirror pairs must be disjoint")

    eligible = set()
    excluded_region = 0
    excluded_forbidden = 0
    for index, (left, right) in enumerate(pairs):
        if regions[left] not in permitted_regions or regions[right] not in permitted_regions:
            excluded_region += 1
            continue
        if (set(rows[left]) | set(rows[right])) - permitted_bones:
            excluded_forbidden += 1
            continue
        eligible.add(index)

    incident = [0.0] * len(pairs)
    adjacency = {index: set() for index in eligible}
    for raw_a, raw_b in edges:
        a, b = int(raw_a), int(raw_b)
        gradient = edge_l1(rows[a], rows[b])
        for vertex in (a, b):
            index = pair_of.get(vertex)
            if index in eligible:
                incident[index] = max(incident[index], gradient)
        pair_a, pair_b = pair_of.get(a), pair_of.get(b)
        if pair_a in eligible and pair_b in eligible and pair_a != pair_b:
            adjacency[pair_a].add(pair_b)
            adjacency[pair_b].add(pair_a)

    seeds = {index for index in eligible if incident[index] >= gradient_threshold}
    selected = set(seeds)
    for _ in range(dilation_rings):
        selected.update(neighbour for index in tuple(selected) for neighbour in adjacency[index])

    ordered = sorted(selected, key=lambda index: pairs[index][0])
    return {
        "left_vertex_ids": [pairs[index][0] for index in ordered],
        "right_vertex_ids": [pairs[index][1] for index in ordered],
        "seed_pair_count": len(seeds),
        "selected_pair_count": len(selected),
        "eligible_pair_count": len(eligible),
        "excluded_region_pair_count": excluded_region,
        "excluded_forbidden_pair_count": excluded_forbidden,
        "maximum_incident_l1": max(incident, default=0.0),
    }


def diffuse_permitted_weights(
    weights: np.ndarray,
    edges: np.ndarray,
    zone_ids: Sequence[int],
    permitted_indices: Sequence[int],
    iterations: int,
    lam: float,
    edge_weights: np.ndarray | None = None,
) -> np.ndarray:
    """Diffuse permitted columns while preserving all other values exactly."""
    if iterations < 0 or not 0.0 <= lam <= 1.0:
        raise ValueError("invalid diffusion parameters")
    source = np.asarray(weights, dtype=float)
    result = source.copy()
    edges = np.asarray(edges, dtype=np.int64)
    zone = np.asarray(sorted(set(int(item) for item in zone_ids)), dtype=np.int64)
    permitted = np.asarray(sorted(set(int(item) for item in permitted_indices)), dtype=np.int64)
    if edge_weights is None:
        edge_weights = np.ones(len(edges), dtype=float)
    edge_weights = np.asarray(edge_weights, dtype=float)
    if len(edge_weights) != len(edges) or np.any(edge_weights <= 0):
        raise ValueError("edge weights must be positive and match the edge count")
    if not len(zone) or not len(permitted) or iterations == 0:
        return result

    permitted_mask = np.zeros(result.shape[1], dtype=bool)
    permitted_mask[permitted] = True
    fixed_mass = source[:, ~permitted_mask].sum(axis=1)
    available_mass = 1.0 - fixed_mass
    for _ in range(iterations):
        acc = np.zeros((len(result), len(permitted)), dtype=float)
        den = np.zeros(len(result), dtype=float)
        np.add.at(acc, edges[:, 0], edge_weights[:, None] * result[edges[:, 1]][:, permitted])
        np.add.at(acc, edges[:, 1], edge_weights[:, None] * result[edges[:, 0]][:, permitted])
        np.add.at(den, edges[:, 0], edge_weights)
        np.add.at(den, edges[:, 1], edge_weights)
        mean = acc / np.maximum(den[:, None], 1e-12)
        candidate = (1.0 - lam) * result[zone][:, permitted] + lam * mean[zone]
        totals = candidate.sum(axis=1)
        if np.any(totals <= 1e-12) or np.any(available_mass[zone] < -1e-9):
            raise ValueError("cannot normalise permitted weights")
        candidate *= (available_mass[zone] / totals)[:, None]
        result[np.ix_(zone, permitted)] = candidate
    result[:, ~permitted_mask] = source[:, ~permitted_mask]
    return result


def symmetrise_pairs(
    weights: np.ndarray,
    left_ids: Sequence[int],
    right_ids: Sequence[int],
    swap_indices: Sequence[int],
) -> np.ndarray:
    """Average paired rows after swapping every left/right bone column."""
    if len(left_ids) != len(right_ids):
        raise ValueError("mirror pair lists must have equal length")
    result = np.asarray(weights, dtype=float).copy()
    left = np.asarray(left_ids, dtype=np.int64)
    right = np.asarray(right_ids, dtype=np.int64)
    swap = np.asarray(swap_indices, dtype=np.int64)
    if sorted(swap.tolist()) != list(range(result.shape[1])):
        raise ValueError("bone swap must be a complete permutation")
    average_left = 0.5 * (result[left] + result[right][:, swap])
    result[left] = average_left
    result[right] = average_left[:, swap]
    return result


def limit_influences(weights: np.ndarray, zone_ids: Sequence[int], maximum: int = 4) -> np.ndarray:
    """Keep the largest deterministic influences on zone rows and renormalise."""
    if maximum <= 0:
        raise ValueError("maximum influences must be positive")
    result = np.asarray(weights, dtype=float).copy()
    for vertex in sorted(set(int(item) for item in zone_ids)):
        row = result[vertex]
        nonzero = np.flatnonzero(row > 1e-8)
        if len(nonzero) > maximum:
            # Stable ordering makes equal-weight ties resolve to lower columns.
            keep = nonzero[np.argsort(-row[nonzero], kind="stable")[:maximum]]
            discard = np.ones(len(row), dtype=bool)
            discard[keep] = False
            row[discard] = 0.0
        total = float(row.sum())
        if total <= 1e-12:
            raise ValueError("cannot normalise an empty weight row")
        row /= total
    return result
