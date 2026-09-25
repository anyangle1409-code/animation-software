"""Pre-flight planner for GPT Work tasks.

Chooses the cheapest capable model/reasoning configuration, keeps Fast mode off
for allowance efficiency, and splits/waits when the projected task is too large.

This is a scheduling recommendation, not a guarantee of usage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ESTIMATOR=ROOT/"scripts"/"estimate_work_usage.py"
BUDGET=ROOT/"reports"/"ai_budget_state.json"
CONFIG=ROOT/"PROJECT_CONTROLLER_CONFIG.json"

TASKS=(
    "local_script","status_or_file_check","visual_review","one_digit_topology",
    "one_file_code","multi_file_code","blender_debug","full_validation","open_ended"
)

# Cheapest capable first. The second entry is escalation, not default.
PROFILES={
    "local_script":[],
    "full_validation":[],
    "status_or_file_check":[("Luna","low"),("Terra","low")],
    "visual_review":[("Terra","low"),("Sol","low")],
    "one_file_code":[("Terra","low"),("Sol","low")],
    "multi_file_code":[("Sol","low"),("Astra","low")],
    "one_digit_topology":[("Sol","medium"),("Astra","low")],
    "blender_debug":[("Sol","medium"),("Astra","low")],
    "open_ended":[],
}

SCOPE_RULES={
    "status_or_file_check":"One status/file question only. No repository-wide review.",
    "visual_review":"Review one prepared comparison board only; do not start editing.",
    "one_file_code":"One issue, preferably one file, focused verification only.",
    "multi_file_code":"One coherent issue only; cap the first pass to the minimum implicated files and focused tests.",
    "one_digit_topology":"One finger, one topology strategy/attempt, save/checkpoint, run its local gate; do not propagate to another digit in the same task.",
    "blender_debug":"Diagnose the current failure first; make only the smallest owning fix before reevaluating.",
    "open_ended":"Do not launch open-ended. Split into one concrete deliverable first.",
}

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

def estimate(task,model,reasoning,context):
    p=subprocess.run(
        [sys.executable,str(ESTIMATOR),task,model,
         "--context",context,"--reasoning",reasoning],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,encoding="utf-8",errors="replace",
    )
    try:return json.loads(p.stdout)
    except Exception:return {"error":p.stdout,"model":model,"reasoning":reasoning}

def effective_budget():
    data=load(BUDGET,{})
    window=data.get("work_window_percent")
    if window is None:
        window=data.get("work_percent")  # legacy
    week=data.get("work_week_percent")
    return window,week,data

def safe_for_budget(high,weekly_high,window,week,cfg):
    # Keep explicit headroom in the five-hour window so a task can finish,
    # checkpoint and hand off. Weekly protection is policy-based until enough
    # weekly calibration samples exist.
    window_reserve=float(cfg.get("work_window_reserve_percent",8))
    week_reserve=float(cfg.get("work_week_reserve_percent",20))
    max_task_window=float(cfg.get("max_single_task_window_percent",30))

    if high > max_task_window:
        return False,"projected task is too large for one Work task"
    if isinstance(window,(int,float)) and high+window_reserve > window:
        return False,"insufficient five-hour headroom"
    if isinstance(week,(int,float)):
        if isinstance(weekly_high,(int,float)):
            if weekly_high + week_reserve > week:
                return False,"learned weekly task estimate would consume protected weekly reserve"
        else:
            if week <= week_reserve and high > 5:
                return False,"weekly allowance is in reserve territory"
            # Until weekly calibration exists, avoid a large five-hour task when
            # the weekly meter is already modest.
            if week <= 35 and high > 12:
                return False,"task is too large for remaining weekly allowance"
    return True,"within configured budget headroom"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("task_class",choices=TASKS)
    ap.add_argument("--context",choices=("small","medium","large"),default="small")
    ap.add_argument("--failed-attempts",type=int,default=0)
    ap.add_argument("--available-models",default="Luna,Terra,Sol,Astra")
    args=ap.parse_args()

    task=args.task_class
    available={x.strip() for x in args.available_models.split(",") if x.strip()}
    cfg=load(CONFIG,{})
    window,week,budget=effective_budget()

    if task in ("local_script","full_validation"):
        result={
            "decision":"LOCAL",
            "task_class":task,
            "reason":"This task should be run by local deterministic tooling, not GPT Work.",
            "recommended_model":None,
            "reasoning":None,
            "fast_mode":False,
            "scope":SCOPE_RULES.get(task,"Run local tooling only."),
            "work_window_remaining_percent":window,
            "work_week_remaining_percent":week,
        }
        print(json.dumps(result,indent=2));return

    if task=="open_ended":
        result={
            "decision":"SPLIT",
            "task_class":task,
            "reason":"Open-ended tasks are deliberately blocked because they are hard to cost and frequently waste allowance.",
            "scope":SCOPE_RULES[task],
            "recommended_model":None,
            "reasoning":None,
            "fast_mode":False,
            "work_window_remaining_percent":window,
            "work_week_remaining_percent":week,
        }
        print(json.dumps(result,indent=2));return

    profiles=[p for p in PROFILES[task] if p[0] in available]
    if not profiles:
        print(json.dumps({
            "decision":"BLOCKED",
            "task_class":task,
            "reason":"No configured capable model is marked available.",
            "available_models":sorted(available),
        },indent=2));return

    # Escalate one profile only after a failed genuine attempt. Do not jump to
    # high reasoning by default; OpenAI notes higher effort is not always better.
    index=min(max(args.failed_attempts,0),len(profiles)-1)
    ordered=profiles[index:]+profiles[:index]

    considered=[]
    selected=None
    selected_reason=None
    for model,reasoning in ordered:
        est=estimate(task,model,reasoning,args.context)
        rng=est.get("estimated_five_hour_drop_percent") or {}
        high=rng.get("high")
        weekly_rng=est.get("estimated_weekly_drop_percent") or {}
        weekly_high=weekly_rng.get("high")
        considered.append({
            "model":model,
            "reasoning":reasoning,
            "fast_mode":False,
            "estimate":est,
        })
        if isinstance(high,(int,float)):
            ok,why=safe_for_budget(
                float(high),
                float(weekly_high) if isinstance(weekly_high,(int,float)) else None,
                window,week,cfg
            )
            if ok:
                selected=(model,reasoning,est)
                selected_reason=why
                break

    if selected:
        model,reasoning,est=selected
        result={
            "decision":"START",
            "task_class":task,
            "recommended_model":model,
            "reasoning":reasoning,
            "fast_mode":False,
            "scope":SCOPE_RULES.get(task),
            "estimated_five_hour_drop_percent":est.get("estimated_five_hour_drop_percent"),
            "estimated_weekly_drop_percent":est.get("estimated_weekly_drop_percent"),
            "estimate_source":est.get("estimate_source"),
            "weekly_estimate_source":est.get("weekly_estimate_source"),
            "work_window_remaining_percent":window,
            "work_week_remaining_percent":week,
            "reason":selected_reason,
            "escalation_rule":(
                "If this scoped attempt fails because the model could not solve the problem "
                "despite having the needed files/access, preserve the evidence and rerun the "
                "preflight with --failed-attempts incremented by 1. Do not increase reasoning "
                "or switch to Astra mid-task without a new preflight."
            ),
            "context_rule":"Use small context: current handoff + exact files/report only.",
            "considered":considered,
        }
        print(json.dumps(result,indent=2));return

    # No safe profile fits. Distinguish a near-reset/window problem from a task
    # that is intrinsically too large.
    highs=[]
    for item in considered:
        rng=(item.get("estimate") or {}).get("estimated_five_hour_drop_percent") or {}
        if isinstance(rng.get("high"),(int,float)):highs.append(float(rng["high"]))
    min_high=min(highs) if highs else None

    if isinstance(window,(int,float)) and min_high is not None and window < min_high+float(cfg.get("work_window_reserve_percent",8)):
        decision="WAIT"
        reason="No capable configuration fits the current five-hour window with safe headroom."
    elif isinstance(week,(int,float)) and week <= float(cfg.get("work_week_reserve_percent",20)):
        decision="WAIT"
        reason="Weekly allowance is being protected; use local/normal Chat until reset."
    else:
        decision="SPLIT"
        reason="The task is too expensive as currently scoped; reduce it to a smaller proof/diagnosis."

    print(json.dumps({
        "decision":decision,
        "task_class":task,
        "reason":reason,
        "scope":SCOPE_RULES.get(task),
        "recommended_model":None,
        "reasoning":None,
        "fast_mode":False,
        "work_window_remaining_percent":window,
        "work_week_remaining_percent":week,
        "considered":considered,
    },indent=2))

if __name__=="__main__":
    main()
