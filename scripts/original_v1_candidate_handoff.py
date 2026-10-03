#!/usr/bin/env python3
"""Build one read-only candidate handoff summary from existing ORIGINAL-v1 evidence.

Combines candidate evidence closure, real review-package state, local Blend identity
and current generated next action. It does not render, save Blender, edit handoffs,
commit, push or promote a candidate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from original_v1_production_control import ROOT,build
from original_v1_candidate_closure import verify_candidate
from original_v1_review_package import build_package
from original_v1_blend_inventory import inventory as blend_inventory


def summarise(revision:str,closure:dict,review:dict,blend:dict,status:dict)->dict:
    rows=[row for row in blend.get("rows",[]) if row.get("revision")==revision]
    blend_row=rows[0] if len(rows)==1 else None
    issues=[]
    if closure.get("evidence_closure_status")!="EVIDENCE_CLOSED":
        issues.append("candidate evidence is not closed")
    if status.get("current_candidate")!=revision:
        issues.append("candidate is not the current generated candidate")
    if blend_row is None:
        issues.append("local candidate Blend is not inventoried")
    elif blend_row.get("status")!="IDENTITY_VERIFIED":
        issues.append("local candidate Blend identity is not verified")
    result={
        "schema_version":1,
        "status":"HANDOFF_READY" if not issues else "HANDOFF_NEEDS_ATTENTION",
        "production_approved":False,
        "revision":revision,
        "candidate_sha256":closure.get("candidate_sha256"),
        "candidate_state":closure.get("candidate_state"),
        "candidate_classification":closure.get("classification"),
        "evidence_closure":closure,
        "review_package":review,
        "local_blend":blend_row,
        "current_generated_state":{
            "candidate":status.get("current_candidate"),
            "phase":status.get("current_phase"),
            "subphase":status.get("current_subphase"),
            "next_action":status.get("next_action"),
            "development_failure_count":status.get("development_failure_count"),
            "active_epoch_baseline":status.get("pinned_baseline"),
            "strict_active_epoch_regression_count":len(status.get("unresolved_regressions",[])),
        },
        "issues":issues,
        "review_blocking":False,
        "next_steps":[
            "If HANDOFF_READY, update O4 handoff/status truthfully and commit evidence.",
            "Re-read remote HEAD before push and preserve newer work.",
            "Run RUN_ORIGINAL_V1_PROGRESS.bat.",
            "Run RUN_ORIGINAL_V1_SESSION_CLOSE.bat before ending the laptop session."
        ],
        "note":"Handoff readiness means evidence/local identity are coherent. It does not mean the candidate passes gates, is owner-accepted or production-approved."
    }
    return result


def markdown(data:dict)->str:
    cur=data["current_generated_state"]
    lines=[
        f"# {data['revision']} candidate handoff","",
        f"Status: **{data['status']}**",
        f"Candidate SHA: {data.get('candidate_sha256')}",
        f"Classification/state: {data.get('candidate_classification')} / {data.get('candidate_state')}",
        f"Evidence closure: {data['evidence_closure'].get('evidence_closure_status')}",
        f"Review package: {data['review_package'].get('status')} (routine review non-blocking)",
        f"Local Blend: {data['local_blend'].get('status') if data.get('local_blend') else 'NOT INVENTORIED'}","",
        f"Current generated node: Phase {cur.get('phase')} / {cur.get('subphase')}",
        f"Next action: {cur.get('next_action',{}).get('action')} - {cur.get('next_action',{}).get('command') or cur.get('next_action',{}).get('work_package') or cur.get('next_action',{}).get('reason')}","",
    ]
    if data["issues"]:
        lines+=["## Needs attention",""]+[f"- {x}" for x in data["issues"]]+[""]
    lines+=["## Close-out sequence",""]+[f"- {x}" for x in data["next_steps"]]+["",
             "This summary is non-mutating and is not candidate acceptance.",""]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--out-dir",type=Path)
    args=ap.parse_args()
    try:
        closure=verify_candidate(ROOT,args.revision)
        review=build_package(ROOT,args.revision)
        blend=blend_inventory(ROOT)
        status,_=build(ROOT)
        data=summarise(args.revision,closure,review,blend,status)
        if args.out_dir:
            out=args.out_dir.resolve()
            if not out.is_relative_to(ROOT.resolve()):raise ValueError("output folder must remain inside repository")
            if out.exists():raise ValueError("candidate handoff output collision")
            out.mkdir(parents=True)
            (out/"candidate_handoff.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
            (out/"README.md").write_text(markdown(data),encoding="utf-8")
        print(markdown(data))
        return 0 if data["status"]=="HANDOFF_READY" else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
