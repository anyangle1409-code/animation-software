"""Estimate Work five-hour-window consumption for a project task.

Uses:
1) broad OpenAI Plus model priors;
2) project-specific task-class multipliers;
3) median historical percentage drops from locally logged samples.

This is deliberately conservative and reports a range, never an exact cost.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SAMPLES=ROOT/"reports"/"work_usage_samples.json"
BUDGET=ROOT/"reports"/"ai_budget_state.json"

# OpenAI-published estimated local messages per Plus five-hour window.
MODEL_MESSAGE_RANGES={
    "astra":(5,45),
    "sol":(10,100),
    "terra":(25,200),
    "luna":(250,2000),
}

# Equivalent local-message work units for this project's common tasks.
# These are starting priors only and are superseded increasingly by personal
# observed samples.
TASK_UNITS={
    "local_script":(0.0,0.0),
    "status_or_file_check":(0.5,1.5),
    "visual_review":(0.5,2.0),
    "one_digit_topology":(2.0,7.0),
    "one_file_code":(1.0,4.0),
    "multi_file_code":(2.0,8.0),
    "blender_debug":(2.0,10.0),
    "full_validation":(1.0,4.0),
    "open_ended":(5.0,25.0),
}

def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default
    except Exception:return default

def generic_range(task,model):
    lo_msgs,hi_msgs=MODEL_MESSAGE_RANGES[model]
    lo_units,hi_units=TASK_UNITS[task]
    # Least consumption: low task units spread across generous message count.
    low=100.0*lo_units/hi_msgs if hi_msgs else 0.0
    # Conservative upper prior: high units against low end of message count.
    high=100.0*hi_units/lo_msgs if lo_msgs else 100.0
    return max(0.0,low),min(100.0,high)

def historical(task,model):
    data=load(SAMPLES,{"samples":[]}).get("samples",[])
    exact=[
        float(x["drop_percent"])
        for x in data
        if x.get("task_class")==task and x.get("model")==model
        and x.get("valid",True) and float(x.get("drop_percent",0))>=0
    ]
    same_task=[
        float(x["drop_percent"])
        for x in data
        if x.get("task_class")==task
        and x.get("valid",True) and float(x.get("drop_percent",0))>=0
    ]
    chosen=exact if exact else same_task
    if not chosen:return None
    med=statistics.median(chosen)
    if len(chosen)>=4:
        ordered=sorted(chosen)
        lo=ordered[max(0,math.floor((len(ordered)-1)*0.15))]
        hi=ordered[min(len(ordered)-1,math.ceil((len(ordered)-1)*0.85))]
    else:
        lo=min(chosen);hi=max(chosen)
    # Give sparse history breathing room.
    pad=max(1.5,med*0.25) if len(chosen)<6 else max(1.0,med*0.15)
    return max(0.0,lo-pad),min(100.0,hi+pad),len(chosen),med,bool(exact)

def blend_prior(generic,hist):
    if hist is None:return generic,"generic prior"
    hlo,hhi,n,med,exact=hist
    # Increasingly trust project observations.
    weight=min(0.85,0.30+0.10*n)
    if not exact:weight*=0.65
    lo=(1-weight)*generic[0]+weight*hlo
    hi=(1-weight)*generic[1]+weight*hhi
    return (max(0.0,lo),min(100.0,max(lo,hi))),f"calibrated from {n} sample(s)"

def band(high):
    if high<=2:return "VERY LOW"
    if high<=6:return "LOW"
    if high<=15:return "MEDIUM"
    if high<=30:return "HIGH"
    return "VERY HIGH"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("task_class",choices=sorted(TASK_UNITS))
    ap.add_argument("model",choices=("Astra","Sol","Terra","Luna"))
    ap.add_argument("--context",choices=("small","medium","large"),default="small")
    ap.add_argument("--reasoning",choices=("low","medium","high"),default="medium")
    args=ap.parse_args()

    task=args.task_class
    model=args.model.lower()
    generic=generic_range(task,model)
    hist=historical(task,model)
    estimate,source=blend_prior(generic,hist)

    factor=1.0
    if args.context=="medium":factor*=1.15
    elif args.context=="large":factor*=1.40
    if args.reasoning=="low":factor*=0.85
    elif args.reasoning=="high":factor*=1.30

    low=max(0.0,min(100.0,estimate[0]*factor))
    high=max(low,min(100.0,estimate[1]*factor))

    budget=load(BUDGET,{})
    remaining=budget.get("work_window_percent")
    if remaining is None:
        remaining=budget.get("work_percent")
    recommendation="UNKNOWN_BUDGET"
    if isinstance(remaining,(int,float)):
        if task=="local_script":
            recommendation="USE_LOCAL_SCRIPT"
        elif high+5 <= remaining:
            recommendation="SAFE_TO_START"
        elif low < remaining and high+2 > remaining:
            recommendation="RISKY_NEAR_LIMIT"
        else:
            recommendation="WAIT_FOR_RESET"

    result={
        "task_class":task,
        "model":args.model,
        "context":args.context,
        "reasoning":args.reasoning,
        "estimated_five_hour_drop_percent":{
            "low":round(low,1),
            "high":round(high,1),
        },
        "risk_band":band(high),
        "estimate_source":source,
        "generic_plus_prior_percent":{
            "low":round(generic[0],1),
            "high":round(generic[1],1),
        },
        "manual_work_remaining_percent":remaining,
        "recommendation":recommendation,
        "caveat":"Approximation only. OpenAI does not expose exact future task cost; actual usage varies by task/model/context/reasoning/tools.",
    }
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
