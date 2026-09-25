"""Start one locally tracked Work-usage calibration sample."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"active_work_usage_sample.json"
BUDGET=ROOT/"reports"/"ai_budget_state.json"
TASKS=("local_script","status_or_file_check","visual_review","one_digit_topology",
       "one_file_code","multi_file_code","blender_debug","full_validation","open_ended")

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

ap=argparse.ArgumentParser()
ap.add_argument("task_class",choices=TASKS)
ap.add_argument("model",choices=("Astra","Sol","Terra","Luna"))
ap.add_argument("before",type=float,nargs="?",default=None)
ap.add_argument("--week-before",type=float,default=None)
ap.add_argument("--context",choices=("small","medium","large"),default="small")
ap.add_argument("--reasoning",choices=("low","medium","high"),default="medium")
ap.add_argument("--fast",action="store_true")
ap.add_argument("--notes",default="")
args=ap.parse_args()

budget=load(BUDGET,{})
before=args.before
if before is None:
    before=budget.get("work_window_percent",budget.get("work_percent"))
week=args.week_before
if week is None:
    week=budget.get("work_week_percent")

if before is None:
    raise SystemExit("No five-hour percentage supplied or stored. Run SET_AI_BUDGET.bat work_window <percent>.")
if not 0<=float(before)<=100:raise SystemExit("before must be 0-100.")
if week is not None and not 0<=float(week)<=100:raise SystemExit("week-before must be 0-100.")

payload={
    "started_utc":datetime.now(timezone.utc).isoformat(),
    "task_class":args.task_class,
    "model":args.model,
    "before_percent":float(before),
    "week_before_percent":float(week) if week is not None else None,
    "context":args.context,
    "reasoning":args.reasoning,
    "fast_mode":bool(args.fast),
    "notes":args.notes,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
