"""Record the reviewed visual result of the Route B topology proof."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_upstream_topology_route_b_trial.blend"
AUDIT = ROOT / "reports" / "audit_v15f_upstream_topology_route_b_trial_blender.json"
GATE = ROOT / "reports" / "v15f_upstream_topology_route_b_gate.json"
BOARD = ROOT / "renders_v15f_upstream_topology_route_b" / "V15F_CHECKPOINT004_VS_ROUTE_B_RING_L.jpg"
OUT = ROOT / "reports" / "v15f_upstream_topology_route_b_visual_decision.json"

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
gate = json.loads(GATE.read_text(encoding="utf-8"))
fingerprint = audit["candidate_topology"]["per_digit_surface"]["ring_L"]["surface_fingerprint_sha256"]
payload = {
    "decision": "PASS",
    "pass": True,
    "reason": (
        "Matched checkpoint-004 and V13e views show a cleaner continuous middle/proximal shaft and "
        "reduced triangular banding, especially in side and oblique views. Joint volume and silhouette "
        "remain intact, with no new pinch or razor crease."
    ),
    "candidate": BLEND.name,
    "candidate_sha256": hashlib.sha256(BLEND.read_bytes()).hexdigest(),
    "surface_fingerprint_sha256": fingerprint,
    "numeric_gate": gate["numeric_gate"],
    "board": str(BOARD.relative_to(ROOT)),
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "promotion": "ring_L proof only; propagation still requires official focused validation",
    "next": "Checkpoint as 005, make it the active V15f ring_L source, then run official focused and deformation/contact validation before propagation.",
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
gate["visual_gate"] = "PASS"
gate["visual_decision_report"] = str(OUT.relative_to(ROOT))
gate["next"] = payload["next"]
GATE.write_text(json.dumps(gate, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
