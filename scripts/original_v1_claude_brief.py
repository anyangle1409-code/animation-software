#!/usr/bin/env python3
"""Generate a compact live ORIGINAL-v1 Claude laptop brief from authoritative state.

Derivative/read-only. The master plan, O4 handoff and generated status remain the
authorities. This script simply compresses them into a start-of-session brief.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from original_v1_production_control import ROOT,build,digest
from original_v1_execution_orchestration import validate_plan,select_node

PLAN="ORIGINAL_V1_EXECUTION_ORCHESTRATION.json"
MASTER="docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md"
HANDOFF="docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md"
QUICKSTART="docs/ORIGINAL_V1_PRODUCTION_CONTROL_QUICKSTART.md"


def build_brief(root:Path)->dict:
    status,_=build(root)
    plan=json.loads((root/PLAN).read_text(encoding="utf-8"))
    info=validate_plan(root,plan)
    node=select_node(plan,status)
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    branch=subprocess.check_output(["git","branch","--show-current"],cwd=root,text=True).strip()
    support_map={row["stage"]:row for row in plan["prepared_support_stages"]}
    support=[support_map[n] for n in node.get("support_stages",[])]
    return {
        "schema_version":1,
        "status":"READ_ONLY_CLAUDE_SESSION_BRIEF",
        "production_approved":False,
        "branch":branch,
        "source_git_commit":head,
        "current_candidate":status["current_candidate"],
        "candidate_sha256":status["last_known_candidate_sha256"],
        "candidate_state":status["candidate_state"],
        "candidate_classification":status["candidate_classification"],
        "current_phase":status["current_phase"],
        "current_subphase":status["current_subphase"],
        "development_failure_count":status["development_failure_count"],
        "active_epoch_baseline":status.get("pinned_baseline"),
        "strict_active_epoch_regression_count":len(status["unresolved_regressions"]),
        "next_action":status["next_action"],
        "selected_execution_node":node,
        "prepared_support":[
            {"stage":row["stage"],"name":row["name"],"artifacts":row["artifacts"],"boundary":row["boundary"]}
            for row in support
        ],
        "start_commands":[
            "RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat",
            "RUN_ORIGINAL_V1_NEXT.bat",
            "RUN_ORIGINAL_V1_EXECUTION_PLAN.bat",
        ],
        "actual_work_command":status["next_action"].get("command"),
        "end_commands":[
            "RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat <new-complete-rN>",
            "RUN_ORIGINAL_V1_PROGRESS.bat",
            "RUN_ORIGINAL_V1_SESSION_CLOSE.bat",
        ],
        "non_negotiables":[
            "Re-read live remote HEAD before every write/push; preserve newer work.",
            "Do not work from main.",
            "Never merge/modify V15f or copy V-series/third-party geometry, topology, weights, bind matrices, materials or textures.",
            "Keep immutable historical/active epoch baselines, the locked rev2c rig, frozen stress poses and thresholds unchanged unless direct evidence plus explicit authority changes them.",
            "Use fresh numbered candidate/output paths; never overwrite evidence.",
            "Routine owner review is non-blocking; never infer OWNER ACCEPTED or production approval.",
            "Do not wholesale merge this model branch into the standalone runtime branch.",
        ],
        "authorities":[
            {"path":MASTER,"sha256":digest(root/MASTER)},
            {"path":HANDOFF,"sha256":digest(root/HANDOFF)},
            {"path":"ORIGINAL_V1_HIGH_DETAIL_STATUS.json","sha256":digest(root/"ORIGINAL_V1_HIGH_DETAIL_STATUS.json")},
            {"path":PLAN,"sha256":digest(root/PLAN)},
            {"path":QUICKSTART,"sha256":digest(root/QUICKSTART)},
        ],
        "prepared_artifact_count":info["artifact_count"],
        "note":"Compressed derivative brief only. If this disagrees with live generated state or authority documents, stop and use the authorities."
    }


def markdown(data:dict)->str:
    n=data["next_action"];node=data["selected_execution_node"]
    lines=[
        "# ORIGINAL v1 - Claude session brief","",
        f"Branch: {data['branch']}",
        f"HEAD: {data['source_git_commit']}",
        f"Current: Phase {data['current_phase']} / {data['current_subphase']} - {data['current_candidate']} ({data['candidate_classification']}, {data['candidate_state']})",
        f"Blockers: {data['development_failure_count']} development failures; {data['strict_active_epoch_regression_count']} strict active-epoch regressions (baseline {(data.get('active_epoch_baseline') or {}).get('revision')}).",
        f"Execution node: {node['id']} - {node['roadmap']}",
        f"Next actual action: {n.get('action')} - {n.get('command') or n.get('work_package') or n.get('reason')}","",
        "## Start","",
    ]
    lines += [f"{i}. {cmd}" for i,cmd in enumerate(data["start_commands"],1)]
    if data.get("actual_work_command"):
        lines += ["",f"Then execute only after those checks agree: {data['actual_work_command']}"]
    lines += ["","## Non-negotiables",""]+[f"- {x}" for x in data["non_negotiables"]]
    if data["prepared_support"]:
        lines += ["","## Prepared support for this node",""]
        for row in data["prepared_support"]:
            lines += [f"- Stage {row['stage']} - {row['name']}: {', '.join(row['artifacts'])}"]
    lines += ["","## Before ending","",
              "- Save/preserve the newest numbered candidate and all available evidence.",
              "- Update the O4 handoff/status truthfully for complete or partial work.",
              "- Commit/push only after re-reading remote HEAD.",
              "- Run RUN_ORIGINAL_V1_SESSION_CLOSE.bat.","",
              "This brief is derivative; authority documents and live generated state win on any disagreement.",""]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    try:
        data=build_brief(ROOT)
        text=json.dumps(data,indent=2)+"\n" if args.json else markdown(data)
        if args.out:
            out=args.out.resolve()
            if not out.is_relative_to(ROOT.resolve()):raise ValueError("brief output must remain inside repository")
            if out.exists():raise ValueError("brief output collision")
            out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding="utf-8")
        print(text,end="" if text.endswith("\n") else "\n")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP - "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
