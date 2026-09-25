"""Record explicit visual verdict for one V15f Stage-B digit."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"reports"/"audit_v15f_deep_hand_rebuild_blender.json"
ALLOWED=("index_L","index_R","middle_L","middle_R")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("digit",choices=ALLOWED)
    ap.add_argument("decision",choices=("pass","fail"))
    ap.add_argument("--notes",default="")
    args=ap.parse_args()
    key=args.digit
    board=ROOT/"renders_v15f_stage_b"/key/f"V15F_V13E_{key.upper()}_PROOF.jpg"
    if not board.is_file():
        raise SystemExit(f"Missing visual board: {board}")
    if not AUDIT.is_file():
        raise SystemExit("Missing current V15f audit. Rerun the Stage-B numeric gate.")
    audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    item=audit.get("candidate_topology",{}).get("per_digit_surface",{}).get(key,{})
    fingerprint=item.get("surface_fingerprint_sha256")
    if not fingerprint:
        raise SystemExit(f"Current audit has no {key} surface fingerprint.")
    payload={
        "digit":key,
        "decision":args.decision.upper(),
        "pass":args.decision=="pass",
        "notes":args.notes,
        "surface_fingerprint_sha256":fingerprint,
        "board":str(board.relative_to(ROOT)),
        "recorded_utc":datetime.now(timezone.utc).isoformat(),
        "criteria":[
            f"{key} visibly improved or at minimum not more segmented than V13e",
            "no new pinching or razor crease",
            "joint/shaft volume remains anatomical",
            "approved ring/pinky appearance remains untouched",
        ],
        "promotion":"none",
    }
    out=ROOT/"reports"/f"v15f_stage_b_{key}_visual_decision.json"
    out.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
