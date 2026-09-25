"""Plan a low-usage Claude Code task.

Uses qualitative Anthropic model guidance plus observed project samples. It does
not invent an exact percentage before calibration exists.
"""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUDGET=ROOT/"reports"/"ai_budget_state.json"
SAMPLES=ROOT/"reports"/"claude_usage_samples.json"

TASKS=("mechanical_edit","report_analysis","one_file_code","multi_file_code",
       "hard_debug","architecture","open_ended")

PROFILES={
    "mechanical_edit":("Haiku","low","/clear"),
    "report_analysis":("Sonnet","low","/clear"),
    "one_file_code":("Sonnet","low","/clear"),
    "multi_file_code":("Sonnet","medium","/clear"),
    "hard_debug":("opusplan","low","/clear"),
    "architecture":("opusplan","medium","/clear"),
}

RISK={
    "mechanical_edit":"VERY LOW",
    "report_analysis":"LOW",
    "one_file_code":"LOW",
    "multi_file_code":"MEDIUM",
    "hard_debug":"HIGH",
    "architecture":"HIGH",
    "open_ended":"VERY HIGH",
}

SCOPE={
    "mechanical_edit":"One mechanical change only; no repo scan.",
    "report_analysis":"One report and only directly implicated files.",
    "one_file_code":"One issue/one file where possible; focused test only.",
    "multi_file_code":"One coherent change; plan touched files first; focused tests.",
    "hard_debug":"Diagnosis/plan first. Use Opus only for the hard reasoning, then Sonnet for execution.",
    "architecture":"Produce a bounded plan/decision first; execute separately with Sonnet.",
    "open_ended":"Do not start. Split into one concrete deliverable.",
}

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

def history(task,model):
    rows=[
        float(x["drop_percent"]) for x in load(SAMPLES,{"samples":[]}).get("samples",[])
        if x.get("task_class")==task and x.get("model_family")==model
        and x.get("valid",True) and x.get("drop_percent") is not None
    ]
    if not rows:return None
    med=statistics.median(rows)
    pad=max(1.0,med*.25)
    return {
        "low":round(max(0,min(rows)-pad),1),
        "high":round(min(100,max(rows)+pad),1),
        "median":round(med,1),
        "samples":len(rows),
    }

ap=argparse.ArgumentParser()
ap.add_argument("task_class",choices=TASKS)
args=ap.parse_args()

budget=load(BUDGET,{})
remaining=budget.get("claude_percent")
task=args.task_class

if task=="open_ended":
    print(json.dumps({
        "decision":"SPLIT","task_class":task,"risk":RISK[task],
        "scope":SCOPE[task],"reason":"Open-ended Claude sessions grow context and waste quota.",
        "context_action":"/clear","model":None,"effort":None,
        "remaining_percent":remaining,
    },indent=2));raise SystemExit(0)

model,effort,context_action=PROFILES[task]
hist=history(task,model)

decision="START"
reason="Cheapest capable Claude profile for this task."
if isinstance(remaining,(int,float)):
    if remaining<=10 and RISK[task] not in ("VERY LOW",):
        decision="WAIT"
        reason="Claude allowance is in critical reserve."
    elif remaining<=20 and RISK[task] in ("MEDIUM","HIGH","VERY HIGH"):
        decision="WAIT"
        reason="Preserve remaining Claude allowance for smaller tasks/reset."
    elif hist and hist["high"]+5>remaining:
        decision="WAIT"
        reason="Observed project usage range does not fit remaining Claude allowance with headroom."

print(json.dumps({
    "decision":decision,
    "task_class":task,
    "model":model,
    "effort":effort,
    "context_action":context_action,
    "web_search":"OFF unless task explicitly requires current public information",
    "tools":"only directly required tools",
    "scope":SCOPE[task],
    "qualitative_risk":RISK[task],
    "observed_drop_percent":hist,
    "remaining_percent":remaining,
    "reason":reason,
    "note":"Use /model to confirm actual available Claude model/version. For opusplan, plan with Opus and execute with Sonnet.",
},indent=2))
