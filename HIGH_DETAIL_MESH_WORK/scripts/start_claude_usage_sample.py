"""Start a tracked Claude usage sample from a preflight task class."""
from __future__ import annotations
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"scripts"/"plan_claude_task.py"
BUDGET=ROOT/"reports"/"ai_budget_state.json"
OUT=ROOT/"reports"/"active_claude_usage_sample.json"

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

ap=argparse.ArgumentParser()
ap.add_argument("task_class")
ap.add_argument("--notes",default="")
args=ap.parse_args()

p=subprocess.run(
    [sys.executable,str(PLAN),args.task_class],
    cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
    text=True,encoding="utf-8",errors="replace",
)
try:plan=json.loads(p.stdout)
except Exception:raise SystemExit(p.stdout)
if plan.get("decision")!="START":
    print(json.dumps(plan,indent=2))
    raise SystemExit(3)

budget=load(BUDGET,{})
before=budget.get("claude_percent")
if before is None:
    raise SystemExit("Set Claude remaining first: SET_AI_BUDGET.bat claude <percent>")

payload={
    "started_utc":datetime.now(timezone.utc).isoformat(),
    "task_class":args.task_class,
    "model_family":plan.get("model"),
    "effort":plan.get("effort"),
    "before_percent":float(before),
    "notes":args.notes,
    "plan":plan,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
