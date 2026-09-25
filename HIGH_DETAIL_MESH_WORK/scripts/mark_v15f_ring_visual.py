"""Record the explicit visual verdict for the current V15f ring-left proof.

Usage:
  python scripts/mark_v15f_ring_visual.py pass
  python scripts/mark_v15f_ring_visual.py fail --notes "still segmented at PIP"

The verdict is bound to the current V15f Blend mtime/size. Any later save makes
it stale and V15F_STATUS will require a new visual review.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
BOARD = ROOT / "renders_v15f_ring_proof" / "V15F_V13E_RING_L_PROOF.jpg"
OUT = ROOT / "reports" / "v15f_ring_visual_decision.json"
AUDIT = ROOT / "reports" / "audit_v15f_deep_hand_rebuild_blender.json"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decision", choices=("pass", "fail"))
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    if not BLEND.is_file():
        raise SystemExit(f"Missing V15f Blend: {BLEND}")
    if not BOARD.is_file():
        raise SystemExit(
            "Missing visual board. Run GENERATE_V15F_RING_VISUAL_PROOF.bat first."
        )

    if not AUDIT.is_file():
        raise SystemExit("Missing current V15f Blender audit. Rerun AUDIT_V15F_RING_PROOF.bat.")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    ring = (
        audit.get("candidate_topology", {})
        .get("per_digit_surface", {})
        .get("ring_L", {})
    )
    fingerprint = ring.get("surface_fingerprint_sha256")
    if not fingerprint:
        raise SystemExit("Current audit has no ring_L surface fingerprint. Rerun the ring proof.")

    stat = BLEND.stat()
    payload = {
        "decision": args.decision.upper(),
        "pass": args.decision == "pass",
        "notes": args.notes,
        "blend": BLEND.name,
        "blend_size": stat.st_size,
        "blend_mtime_ns": stat.st_mtime_ns,
        "surface_fingerprint_sha256": fingerprint,
        "board": str(BOARD.relative_to(ROOT)),
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "criteria": [
            "ring_L visibly less segmented/faceted than V13e",
            "no new pinching or razor crease",
            "shaft/joint volume remains anatomical",
            "improvement is topology/silhouette, not only smoothing/shading",
        ],
        "promotion": "none",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
