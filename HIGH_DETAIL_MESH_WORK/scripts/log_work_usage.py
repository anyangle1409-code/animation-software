"""Record one observed Work percentage drop for estimator calibration."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"work_usage_samples.json"
TASKS=("local_script","status_or_file_check","visual_review","one_digit_topology",
       "one_file_code","multi_file_code","blender_debug","full_validation","open_ended")
MODELS=("astra","sol","terra","luna")

ap=argparse.ArgumentParser()
ap.add_argument("task_class",choices=TASKS)
ap.add_argument("model",choices=("Astra","Sol","Terra","Luna"))
ap.add_argument("before",type=float)
ap.add_argument("after",type=float)
ap.add_argument("minutes",type=float)
ap.add_argument("--context",choices=("small","medium","large"),default="small")
ap.add_argument("--reasoning",choices=("low","medium","high"),default="medium")
ap.add_argument("--notes",default="")
args=ap.parse_args()

if not (0<=args.before<=100 and 0<=args.after<=100):
    raise SystemExit("before/after must be percentages from 0 to 100.")
if args.after>args.before:
    raise SystemExit("After is greater than before. Do not log across a reset.")
drop=args.before-args.after

data={"samples":[]}
if OUT.is_file():
    try:data=json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:data={"samples":[]}

sample={
    "recorded_utc":datetime.now(timezone.utc).isoformat(),
    "task_class":args.task_class,
    "model":args.model.lower(),
    "before_percent":args.before,
    "after_percent":args.after,
    "drop_percent":round(drop,3),
    "minutes":args.minutes,
    "context":args.context,
    "reasoning":args.reasoning,
    "notes":args.notes,
    "valid":True,
}
data.setdefault("samples",[]).append(sample)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
print(json.dumps(sample,indent=2))
