"""Prepare the next Work task card and refuse wasteful configurations.

Runs one controller pass, reads its preflight, and writes/prints a simple task
card. It never starts GPT Work itself.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CTRL=ROOT/"scripts"/"project_controller.py"
STATE=ROOT/"reports"/"project_controller_state.json"
CARD=ROOT/"NEXT_WORK_TASK_CARD.md"

def main():
    p=subprocess.run([sys.executable,str(CTRL),"--once"],cwd=ROOT)
    if p.returncode!=0:
        raise SystemExit(p.returncode)
    if not STATE.is_file():
        raise SystemExit("Controller state missing.")
    data=json.loads(STATE.read_text(encoding="utf-8"))
    plan=data.get("work_plan") or {}
    route=data.get("route")
    v15=data.get("v15f") or {}
    estimate=plan.get("estimated_five_hour_drop_percent") or {}
    week_estimate=plan.get("estimated_weekly_drop_percent") or {}
    budget=data.get("budget") or {}

    ready=route=="GPT_WORK" and plan.get("decision")=="START"
    lines=[
        "# Next Work Task Card",
        "",
        f"- READY TO START: **{'YES' if ready else 'NO'}**",
        f"- route: **{route}**",
        f"- planner decision: **{plan.get('decision')}**",
        f"- task class: {data.get('task_class')}",
        f"- execution mode: **{plan.get('execution_mode')}**",
        f"- model: **{plan.get('recommended_model')}**",
        f"- reasoning: **{plan.get('reasoning')}**",
        f"- Fast mode: **{'ON' if plan.get('fast_mode') else 'OFF'}**",
        f"- estimated 5-hour use: **{estimate.get('low','?')}%-{estimate.get('high','?')}%**",
        f"- estimated weekly use: **{week_estimate.get('low','?')}%-{week_estimate.get('high','?')}%** "
        f"({plan.get('weekly_estimate_source','not calibrated')})",
        f"- current 5-hour remaining: {budget.get('work_window_percent')}",
        f"- current weekly remaining: {budget.get('work_week_percent')}",
        "",
        "## Amended scope",
        str(plan.get("scope") or v15.get("next_action") or ""),
        "",
        "## Exact project next action",
        str(v15.get("next_action") or ""),
        "",
        "## Why",
        str(plan.get("reason") or v15.get("reason") or ""),
        "",
    ]

    if ready:
        lines += [
            "## Before sending",
            "1. Set the Work model shown above.",
            "2. Set the reasoning level shown above.",
            "3. Ensure Fast mode matches the card (normally OFF).",
            "4. Paste/use PROJECT_CONTROLLER_WORK_PROMPT.txt.",
            "5. Do not broaden the task while it is running.",
        ]
    elif route=="WAIT_FOR_WORK_RESET":
        lines += [
            "## Action",
            "Do not start this Work task. Let local/normal-Chat work continue and rerun this card after the tighter reset.",
        ]
    elif route=="SPLIT_BEFORE_WORK":
        lines += [
            "## Action",
            "Do not start the original task. Use the amended scope above as the next smaller proof and run preflight again.",
        ]
    elif route=="LOCAL_SCRIPT":
        lines += [
            "## Action",
            "Do not spend Work usage. The task belongs to local deterministic tooling.",
        ]
    else:
        lines += [
            "## Action",
            "Do not start a broad Work task from this card. Follow the route above.",
        ]

    CARD.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
    if not ready:
        raise SystemExit(3)

if __name__=="__main__":
    main()
