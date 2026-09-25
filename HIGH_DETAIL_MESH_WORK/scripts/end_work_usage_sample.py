"""Finish the active Work-usage sample and append it to calibration history."""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/"reports"/"active_work_usage_sample.json"
LOGGER=ROOT/"scripts"/"log_work_usage.py"

ap=argparse.ArgumentParser()
ap.add_argument("after",type=float)
ap.add_argument("--notes",default="")
args=ap.parse_args()
if not ACTIVE.is_file():raise SystemExit("No active Work usage sample. Run START_WORK_TASK.bat first.")
data=json.loads(ACTIVE.read_text(encoding="utf-8"))
if not 0<=args.after<=100:raise SystemExit("after must be 0-100.")
started=datetime.fromisoformat(data["started_utc"])
minutes=max(0.1,(datetime.now(timezone.utc)-started).total_seconds()/60.0)
notes="; ".join(x for x in (data.get("notes",""),args.notes) if x)
cmd=[
    sys.executable,str(LOGGER),data["task_class"],data["model"],
    str(data["before_percent"]),str(args.after),f"{minutes:.2f}",
    "--context",data.get("context","small"),
    "--reasoning",data.get("reasoning","medium"),
    "--notes",notes,
]
p=subprocess.run(cmd,cwd=ROOT)
if p.returncode==0:
    ACTIVE.unlink(missing_ok=True)
raise SystemExit(p.returncode)
