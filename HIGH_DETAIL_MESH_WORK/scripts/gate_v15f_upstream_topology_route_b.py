"""Compare the Route B topology proof with active checkpoint 004."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports" / "audit_v15f_deep_hand_rebuild_blender.json"
TRIAL = ROOT / "reports" / "audit_v15f_upstream_topology_route_b_trial_blender.json"
ATTEMPT = ROOT / "reports" / "v15f_ring_l_upstream_topology_route_b_attempt.json"
OUT = ROOT / "reports" / "v15f_upstream_topology_route_b_gate.json"

base = json.loads(BASE.read_text(encoding="utf-8"))
trial = json.loads(TRIAL.read_text(encoding="utf-8"))
attempt = json.loads(ATTEMPT.read_text(encoding="utf-8"))
b = base["candidate_topology"]["per_digit_surface"]["ring_L"]
t = trial["candidate_topology"]["per_digit_surface"]["ring_L"]
checks = {
    "general_invariants_pass": bool(trial.get("pass")),
    "direct_contacts_exact": float(trial["protected_max_move_mm"]) == 0.0,
    "weights_exact": int(trial["original_digit_weight_rows_changed"]) == 0,
    "outside_ring_L_exact": all(
        float(row["max_move_mm"]) <= 1e-6
        for key, row in trial["per_digit_original_movement_vs_v13e"].items()
        if key != "ring_L"
    ),
    "topology_rebuilt": int(attempt["removed_ring_edges"]) > 0 and int(attempt["added_ring_edges"]) > 0,
    "vertex_and_face_counts_preserved": int(attempt["vertices_added_or_removed"]) == 0 and int(attempt["faces_added_or_removed"]) == 0,
    "ring_L_gt35_improved": float(t["sharp_length_ratio_gt_35"]) < float(b["sharp_length_ratio_gt_35"]),
    "ring_L_gt50_improved": float(t["sharp_length_ratio_gt_50"]) < float(b["sharp_length_ratio_gt_50"]),
    "ring_L_gt100_not_worse": int(t["dihedral_edge_count_gt_deg"]["100"]) <= int(b["dihedral_edge_count_gt_deg"]["100"]),
    "no_new_boundaries": int(t["boundary_edges"]) <= int(b["boundary_edges"]),
}
report = {
    "candidate": trial["candidate"],
    "comparison": base["candidate"],
    "numeric_gate": "PASS" if all(checks.values()) else "FAIL",
    "checkpoint_004": {
        "ring_L_gt35": b["sharp_length_ratio_gt_35"],
        "ring_L_gt50": b["sharp_length_ratio_gt_50"],
        "ring_L_gt100": b["dihedral_edge_count_gt_deg"]["100"],
    },
    "route_b_trial": {
        "ring_L_gt35": t["sharp_length_ratio_gt_35"],
        "ring_L_gt50": t["sharp_length_ratio_gt_50"],
        "ring_L_gt100": t["dihedral_edge_count_gt_deg"]["100"],
        "maximum_move_mm": attempt["maximum_ring_L_move_mm"],
        "removed_ring_edges": attempt["removed_ring_edges"],
        "added_ring_edges": attempt["added_ring_edges"],
    },
    "checks": checks,
    "visual_gate": "PENDING",
    "next": "Render matched checkpoint-004 and V13e comparisons; accept only if anatomy is visibly cleaner without pinching.",
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
