"""Pure policy helpers for the V15f Route A anchor-buffer experiment."""
from __future__ import annotations


_CAPS_MM = {
    0: 0.0,   # accepted direct push-up contact
    1: 0.0,   # fixed safety collar around direct contact
    2: 0.25,  # inner transition: small corrective allowance
    3: 0.55,  # outer transition: larger but still sub-millimetre allowance
}


def movement_cap_mm(graph_distance: int) -> float:
    """Return the only permitted displacement for a prepared anchor vertex."""
    return _CAPS_MM.get(int(graph_distance), 0.0)


def route_b_movement_cap_mm(graph_distance: int) -> float:
    """Movement taper for the upstream topology rebuild proof."""
    distance = int(graph_distance)
    if distance <= 0:
        return 0.0
    if distance == 1:
        return 0.12
    if distance == 2:
        return 0.35
    if distance == 3:
        return 0.65
    return 0.90


def report_is_safe(report: dict) -> bool:
    """Confirm that a Route A report preserves every hard invariant."""
    return (
        float(report.get("direct_contact_max_move_mm", 1.0)) == 0.0
        and int(report.get("direct_contact_weight_rows_changed", 1)) == 0
        and int(report.get("eligible_anchor_vertices", 0)) > 0
        and float(report.get("maximum_allowed_move_mm", 99.0)) <= 0.55
        and report.get("topology_changes_allowed") is False
        and report.get("weights_changes_allowed") is False
    )
