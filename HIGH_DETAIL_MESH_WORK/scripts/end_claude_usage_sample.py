"""Finish active Claude usage sample and update stored allowance."""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/"reports"/"active_claude_usage_sample.json"
LOGGER=ROOT/"scripts"/"log_claude_usage.py"
SET=ROOT/"scripts"/"set_ai_budget.py"

ap=argparse.ArgumentParser()
ap.add_argument("after",type=float)
ap.add_argument("--notes",default="")
args=ap.parse_args()
if not ACTIVE.is_file():
    raise SystemExit("No active Claude usage sample.")
data=json.loads(ACTIVE.read_text(encoding="utf-8"))
started=datetime.fromisoformat(data["started_utc"])
minutes=max(.1,(datetime.now(timezone.utc)-started).total_seconds()/60)
notes="; ".join(x for x in (data.get("notes",""),args.notes) if x)

subprocess.run([sys.executable,str(SET),"claude",str(args.after)],cwd=ROOT,check=True)
cmd=[
    sys.executable,str(LOGGER),data["task_class"],data["model_family"],
    str(data["before_percent"]),str(args.after),f"{minutes:.2f}",
    "--effort",data.get("effort","low")
]
if notes:cmd+=["--notes",notes]
p=subprocess.run(cmd,cwd=ROOT)
if p.returncode==0:ACTIVE.unlink(missing_ok=True)
raise SystemExit(p.returncode)
