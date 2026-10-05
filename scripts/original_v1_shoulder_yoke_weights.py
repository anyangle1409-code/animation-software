"""Pure calculations for declaration-scoped shoulder-yoke weight analysis."""
from __future__ import annotations

import math
from typing import Iterable


def normalise_deform_row(row: dict[str, float], deform_bones: Iterable[str]) -> dict[str, float]:
    allowed = set(deform_bones)
    filtered = {name: float(value) for name, value in row.items() if name in allowed and float(value) > 1e-8}
    if not filtered:
        return {}
    if any(not math.isfinite(value) or value < 0 for value in filtered.values()):
        raise ValueError("deform weights must be finite and non-negative")
    total = sum(filtered.values())
    if total <= 0:
        return {}
    return {name: filtered[name] / total for name in sorted(filtered)}


def classify_vertex(row: dict[str, float], side: str, dominance_limit: float = 0.9, shared_threshold: float = 0.05) -> dict:
    if side not in ("l", "r"):
        raise ValueError("side must be l or r")
    opposite = "_r" if side == "l" else "_l"
    cross_side = sorted(name for name, value in row.items() if name.endswith(opposite) and value > 1e-8)
    dominant_bone, dominant_weight = max(row.items(), key=lambda item: (item[1], item[0])) if row else (None, 0.0)
    meaningful = sorted(name for name, value in row.items() if value >= shared_threshold)
    return {
        "cross_side_bones": cross_side,
        "dominant_bone": dominant_bone,
        "dominant_weight": dominant_weight,
        "excessive_single_bone_dominance": dominant_weight >= dominance_limit,
        "meaningful_bones": meaningful,
        "missing_shared_influence": len(meaningful) < 2,
    }


def _mirror_name(name: str) -> str:
    if name.endswith("_l"):
        return name[:-2] + "_r"
    if name.endswith("_r"):
        return name[:-2] + "_l"
    return name


def compare_mirror_rows(left: dict[str, float], right: dict[str, float]) -> dict:
    names = sorted(set(left) | {_mirror_name(name) for name in right})
    differences = [
        {"bone": name, "left": left.get(name, 0.0), "right_mirrored": right.get(_mirror_name(name), 0.0),
         "absolute_difference": abs(left.get(name, 0.0) - right.get(_mirror_name(name), 0.0))}
        for name in names
    ]
    largest = max(differences, key=lambda item: (item["absolute_difference"], item["bone"]), default=None)
    return {"l1_error": sum(item["absolute_difference"] for item in differences), "largest_difference": largest}


def edge_l1(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(abs(a.get(name, 0.0) - b.get(name, 0.0)) for name in set(a) | set(b))
