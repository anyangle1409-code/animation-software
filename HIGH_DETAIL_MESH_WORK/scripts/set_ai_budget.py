"""Set advisory remaining AI allowance for project routing."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"ai_budget_state.json"

ap=argparse.ArgumentParser()
ap.add_argument("provider",choices=("work","claude"))
ap.add_argument("percent",type=float)
ap.add_argument("--reset-note",default=None)
args=ap.parse_args()
if not 0 <= args.percent <= 100:
    raise SystemExit("Percent must be between 0 and 100.")
data={}
if OUT.is_file():
    try:data=json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:data={}
data[f"{args.provider}_percent"]=args.percent
if args.reset_note is not None:
    data[f"{args.provider}_reset_note"]=args.reset_note
data["updated_utc"]=datetime.now(timezone.utc).isoformat()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
print(json.dumps(data,indent=2))
