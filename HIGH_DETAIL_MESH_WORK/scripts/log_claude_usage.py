"""Record one observed Claude allowance drop for local calibration."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"claude_usage_samples.json"

ap=argparse.ArgumentParser()
ap.add_argument("task_class")
ap.add_argument("model_family",choices=("Haiku","Sonnet","opusplan","Opus"))
ap.add_argument("before",type=float)
ap.add_argument("after",type=float)
ap.add_argument("minutes",type=float)
ap.add_argument("--effort",default="low")
ap.add_argument("--notes",default="")
args=ap.parse_args()
if not (0<=args.before<=100 and 0<=args.after<=100):
    raise SystemExit("before/after must be 0-100.")
if args.after>args.before:
    raise SystemExit("After is greater than before; do not log across a reset.")

data={"samples":[]}
if OUT.is_file():
    try:data=json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:data={"samples":[]}
sample={
    "recorded_utc":datetime.now(timezone.utc).isoformat(),
    "task_class":args.task_class,
    "model_family":args.model_family,
    "before_percent":args.before,
    "after_percent":args.after,
    "drop_percent":round(args.before-args.after,3),
    "minutes":args.minutes,
    "effort":args.effort,
    "notes":args.notes,
    "valid":True,
}
data.setdefault("samples",[]).append(sample)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
print(json.dumps(sample,indent=2))
