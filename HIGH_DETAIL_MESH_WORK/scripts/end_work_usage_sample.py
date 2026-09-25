"""Finish the active Work-usage sample and append it to calibration history."""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/"reports"/"active_work_usage_sample.json"
LOGGER=ROOT/"scripts"/"log_work_usage.py"
BUDGET=ROOT/"reports"/"ai_budget_state.json"

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

ap=argparse.ArgumentParser()
ap.add_argument("after",type=float,nargs="?",default=None)
ap.add_argument("--week-after",type=float,default=None)
ap.add_argument("--credits-used",type=float,default=None)
ap.add_argument("--notes",default="")
args=ap.parse_args()

if not ACTIVE.is_file():raise SystemExit("No active Work usage sample. Run START_WORK_TASK.bat first.")
data=json.loads(ACTIVE.read_text(encoding="utf-8"))
budget=load(BUDGET,{})

after=args.after
if after is None:
    after=budget.get("work_window_percent",budget.get("work_percent"))
week_after=args.week_after

if after is None:
    raise SystemExit("No ending five-hour percentage supplied or stored.")
if not 0<=float(after)<=100:raise SystemExit("after must be 0-100.")

started=datetime.fromisoformat(data["started_utc"])
minutes=max(0.1,(datetime.now(timezone.utc)-started).total_seconds()/60.0)
notes="; ".join(x for x in (data.get("notes",""),args.notes) if x)

cmd=[
    sys.executable,str(LOGGER),data["task_class"],data["model"],
    str(data["before_percent"]),str(float(after)),f"{minutes:.2f}",
    "--context",data.get("context","small"),
    "--reasoning",data.get("reasoning","medium"),
]
week_before=data.get("week_before_percent")
if week_before is not None and week_after is not None:
    cmd += ["--before-week",str(week_before),"--after-week",str(float(week_after))]
if args.credits_used is not None:
    cmd += ["--credits-used",str(args.credits_used)]
if notes:
    cmd += ["--notes",notes]

p=subprocess.run(cmd,cwd=ROOT)
if p.returncode==0:
    ACTIVE.unlink(missing_ok=True)
raise SystemExit(p.returncode)
