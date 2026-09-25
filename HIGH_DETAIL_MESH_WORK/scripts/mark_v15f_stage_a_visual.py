"""Record explicit visual verdict for the current V15f Stage-A ring/pinky proof."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
BOARD = ROOT / "renders_v15f_stage_a" / "V15F_V13E_STAGE_A_RING_PINKY_PROOF.jpg"
OUT = ROOT / "reports" / "v15f_stage_a_visual_decision.json"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("decision", choices=("pass","fail"))
    ap.add_argument("--notes", default="")
    args=ap.parse_args()
    if not BLEND.is_file():
        raise SystemExit(f"Missing V15f Blend: {BLEND}")
    if not BOARD.is_file():
        raise SystemExit("Missing Stage-A visual board. Run GENERATE_V15F_STAGE_A_VISUAL_PROOF.bat first.")
    stat=BLEND.stat()
    payload={
        "decision":args.decision.upper(),
        "pass":args.decision=="pass",
        "notes":args.notes,
        "blend":BLEND.name,
        "blend_size":stat.st_size,
        "blend_mtime_ns":stat.st_mtime_ns,
        "board":str(BOARD.relative_to(ROOT)),
        "recorded_utc":datetime.now(timezone.utc).isoformat(),
        "criteria":[
            "ring/pinky visibly improved or at minimum not more segmented than V13e",
            "no new pinching or razor creases",
            "joint/shaft volume remains anatomical on both sides",
            "no digit is being accepted on metrics alone",
        ],
        "promotion":"none",
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print(json.dumps(payload,indent=2))

if __name__=="__main__":
    main()
