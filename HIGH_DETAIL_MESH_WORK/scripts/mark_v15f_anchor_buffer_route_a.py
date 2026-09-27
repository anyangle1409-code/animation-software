"""Record the reviewed visual result of the one bounded Route A proof."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_anchor_buffer_route_a_trial.blend"
AUDIT = ROOT / "reports" / "audit_v15f_anchor_buffer_route_a_trial_blender.json"
GATE = ROOT / "reports" / "v15f_anchor_buffer_route_a_gate.json"
BOARD = ROOT / "renders_v15f_anchor_buffer_route_a" / "V15F_CHECKPOINT004_VS_ROUTE_A_RING_L.jpg"
OUT = ROOT / "reports" / "v15f_anchor_buffer_route_a_visual_decision.json"

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
gate = json.loads(GATE.read_text(encoding="utf-8"))
fingerprint = audit["candidate_topology"]["per_digit_surface"]["ring_L"]["surface_fingerprint_sha256"]
payload = {
    "decision": "FAIL",
    "pass": False,
    "reason": (
        "Numeric fold ratios improved materially, but the matched checkpoint-004 comparison remains "
        "visually near-identical at review scale. The inherited faceted shaft/joint character is still "
        "present, so Route A does not satisfy the required visible-anatomy gate."
    ),
    "candidate": BLEND.name,
    "candidate_sha256": hashlib.sha256(BLEND.read_bytes()).hexdigest(),
    "surface_fingerprint_sha256": fingerprint,
    "numeric_gate": gate["numeric_gate"],
    "board": str(BOARD.relative_to(ROOT)),
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "promotion": "none",
    "next": "Proceed to Route B upstream ring_L topology rebuild from preserved checkpoint 004; do not mirror to ring_R.",
}
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
gate["visual_gate"] = "FAIL"
gate["visual_decision_report"] = str(OUT.relative_to(ROOT))
gate["next"] = payload["next"]
GATE.write_text(json.dumps(gate, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
