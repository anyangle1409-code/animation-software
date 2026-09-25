"""Start one locally tracked Work-usage calibration sample."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"active_work_usage_sample.json"
TASKS=("local_script","status_or_file_check","visual_review","one_digit_topology",
       "one_file_code","multi_file_code","blender_debug","full_validation","open_ended")

ap=argparse.ArgumentParser()
ap.add_argument("task_class",choices=TASKS)
ap.add_argument("model",choices=("Astra","Sol","Terra","Luna"))
ap.add_argument("before",type=float)
ap.add_argument("--context",choices=("small","medium","large"),default="small")
ap.add_argument("--reasoning",choices=("low","medium","high"),default="medium")
ap.add_argument("--notes",default="")
args=ap.parse_args()
if not 0<=args.before<=100:raise SystemExit("before must be 0-100.")
payload={
    "started_utc":datetime.now(timezone.utc).isoformat(),
    "task_class":args.task_class,
    "model":args.model,
    "before_percent":args.before,
    "context":args.context,
    "reasoning":args.reasoning,
    "notes":args.notes,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
