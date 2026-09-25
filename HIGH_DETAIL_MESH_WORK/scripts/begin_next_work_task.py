"""Guard, prepare and begin usage tracking for the next planned Work task.

Does not launch ChatGPT Work or change its model picker. It creates the task
card/prompt and starts the calibration timer only when the preflight says START.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/"scripts"/"prepare_next_work_task.py"
STATE=ROOT/"reports"/"project_controller_state.json"
START_SAMPLE=ROOT/"scripts"/"start_work_usage_sample.py"

p=subprocess.run([sys.executable,str(PREP)],cwd=ROOT)
if p.returncode!=0:
    raise SystemExit(p.returncode)

data=json.loads(STATE.read_text(encoding="utf-8"))
plan=data.get("work_plan") or {}
if data.get("route")!="GPT_WORK" or plan.get("decision")!="START":
    raise SystemExit("Preflight is not START/GPT_WORK.")

task=data.get("task_class")
model=plan.get("recommended_model")
reasoning=plan.get("reasoning") or "medium"
if not task or not model:
    raise SystemExit("Missing task/model from preflight.")

cmd=[
    sys.executable,str(START_SAMPLE),task,model,
    "--context","small",
    "--reasoning",reasoning,
    "--notes","controller-planned task",
]
p=subprocess.run(cmd,cwd=ROOT)
if p.returncode!=0:
    raise SystemExit(p.returncode)

print("")
print("WORK_TASK_TRACKING_STARTED")
print("Set the Work picker exactly as shown in NEXT_WORK_TASK_CARD.md, then use PROJECT_CONTROLLER_WORK_PROMPT.txt.")
