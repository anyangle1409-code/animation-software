"""Compare estimated Work consumption across available model classes."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"estimate_work_usage.py"
TASKS=("local_script","status_or_file_check","visual_review","one_digit_topology",
       "one_file_code","multi_file_code","blender_debug","full_validation","open_ended")

ap=argparse.ArgumentParser()
ap.add_argument("task_class",choices=TASKS)
ap.add_argument("--context",choices=("small","medium","large"),default="small")
ap.add_argument("--reasoning",choices=("low","medium","high"),default="medium")
args=ap.parse_args()

rows=[]
for model in ("Astra","Sol","Terra","Luna"):
    p=subprocess.run(
        [sys.executable,str(SCRIPT),args.task_class,model,
         "--context",args.context,"--reasoning",args.reasoning],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,encoding="utf-8",errors="replace",
    )
    try:data=json.loads(p.stdout)
    except Exception:
        data={"model":model,"error":p.stdout}
    rows.append(data)

print(json.dumps({
    "task_class":args.task_class,
    "context":args.context,
    "reasoning":args.reasoning,
    "models":rows,
    "note":"Choose the cheapest capable model; these are ranges, not guaranteed costs."
},indent=2))
