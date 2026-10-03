#!/usr/bin/env python3
"""Build a read-only post-validation disposition summary for an axilla repair candidate.

This tool combines committed candidate comparisons, evidence closure, the declared-face
post-edit audit and real-review availability. It never accepts anatomy, writes production
control, changes candidate lineage, enters Phase 4 or infers owner approval.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, CAND, RC, build, digest, ensure_finite
from original_v1_candidate_closure import candidate_entry, verify_candidate
from original_v1_review_package import build_package

HELPER="scripts/original_v1_axilla_disposition.py"


def assess(row:dict, active_baseline:str, parent_revision:str, face_summary:dict,
           closure_status:str, review_status:str)->dict:
    comparisons=row.get("comparisons") if isinstance(row,dict) else None
    if not isinstance(comparisons,dict):
        raise ValueError("candidate comparison map missing")
    if active_baseline not in comparisons:
        raise ValueError("active epoch baseline comparison missing")
    if parent_revision not in comparisons:
        raise ValueError("direct-parent comparison missing")
    active=comparisons[active_baseline]
    parent=comparisons[parent_revision]
    for name,comp in ((active_baseline,active),(parent_revision,parent)):
        if not isinstance(comp,dict) or type(comp.get("regression_count")) is not int:
            raise ValueError("comparison evidence incomplete: "+name)
    local_clear=face_summary.get("status")=="LOCAL_FACE_NUMERIC_CLEAR"
    dev=row.get("development_failure_count")
    if type(dev) is not int:
        raise ValueError("candidate development failure count missing")
    numeric_blockers=[]
    if closure_status!="EVIDENCE_CLOSED":
        numeric_blockers.append("candidate evidence closure is incomplete")
    if dev:
        numeric_blockers.append(f"{dev} development failure(s) remain")
    if parent["regression_count"]:
        numeric_blockers.append(f"{parent['regression_count']} strict regression(s) versus direct parent {parent_revision}")
    if not local_clear:
        numeric_blockers.append("declared axilla-face audit is not LOCAL_FACE_NUMERIC_CLEAR")

    review_ready=review_status=="REVIEW_PACKAGE_READY"
    active_regs=active["regression_count"]
    freeze_numeric_ready=not numeric_blockers and active_regs==0

    if numeric_blockers:
        status="NUMERIC_REPAIR_BLOCKED"
    elif not review_ready:
        status="READY_FOR_REVIEW_CAPTURE"
    elif freeze_numeric_ready:
        status="READY_FOR_VISUAL_DISPOSITION_AND_PHASE4_AFTER_LINEAGE"
    else:
        status="READY_FOR_VISUAL_DISPOSITION_PHASE4_STILL_BLOCKED"

    return {
        "status":status,
        "development_failure_count":dev,
        "direct_parent":parent_revision,
        "direct_parent_regression_count":parent["regression_count"],
        "direct_parent_improvement_count":parent.get("improvement_count"),
        "active_epoch_baseline":active_baseline,
        "active_epoch_regression_count":active_regs,
        "active_epoch_improvement_count":active.get("improvement_count"),
        "local_face_status":face_summary.get("status"),
        "local_face_min_signed_projected_area_ratio":face_summary.get("min_signed_projected_area_ratio"),
        "local_face_max_flipped_faces_per_sample":face_summary.get("max_flipped_faces_per_sample"),
        "evidence_closure_status":closure_status,
        "review_package_status":review_status,
        "numeric_blockers":numeric_blockers,
        "phase4_numeric_ready_after_lineage":freeze_numeric_ready,
        "visual_acceptance_inferred":False,
        "production_approved":False,
    }


def build_disposition(root:Path,revision:str,parent_revision:str)->dict:
    if not re.fullmatch(r"r\d+",revision) or not re.fullmatch(r"r\d+",parent_revision):
        raise ValueError("numbered candidate/parent revisions required")
    if revision==parent_revision:
        raise ValueError("candidate and parent must differ")
    status,_=build(root)
    if status.get("current_candidate")!=revision:
        raise ValueError("disposition candidate is not the generated current candidate")
    row,ledger=candidate_entry(root,revision)
    parent_row,_=candidate_entry(root,parent_revision)
    if row.get("parent_sha256")!=parent_row.get("sha256"):
        raise ValueError("candidate direct-parent SHA does not match requested parent")
    active=ledger.get("pinned_baseline")
    if active!=(status.get("pinned_baseline") or {}).get("revision"):
        raise ValueError("ledger/generated active epoch baseline differs")

    face_path=root/RC/f"axilla_{revision}/post_edit_face_audit.json"
    if not face_path.is_file():
        raise ValueError("post-edit axilla face audit missing")
    face=json.loads(face_path.read_text(encoding="utf-8"))
    ensure_finite(face)
    if face.get("candidate_sha256")!=row.get("sha256"):
        raise ValueError("post-edit face audit candidate identity differs")
    if face.get("parent_candidate_sha256")!=parent_row.get("sha256"):
        raise ValueError("post-edit face audit parent identity differs")
    summary=face.get("summary")
    if not isinstance(summary,dict):
        raise ValueError("post-edit face audit summary missing")

    closure=verify_candidate(root,revision)
    review=build_package(root,revision)
    measured=assess(
        row,active,parent_revision,summary,
        closure.get("evidence_closure_status"),review.get("status"),
    )
    comparison_refs={}
    for name in (active,parent_revision):
        comp=row["comparisons"][name]
        ev=comp.get("evidence")
        if not isinstance(ev,dict) or not ev.get("path") or digest(root/ev["path"])!=ev.get("sha256"):
            raise ValueError("comparison evidence hash/path differs: "+name)
        comparison_refs[name]=ev

    if measured["status"]=="NUMERIC_REPAIR_BLOCKED":
        next_action="Preserve this candidate/evidence and diagnose the listed numeric blockers before another local experiment."
    elif measured["status"]=="READY_FOR_REVIEW_CAPTURE":
        next_action="Capture/index the real milestone review before any lineage or freeze decision."
    elif measured["status"]=="READY_FOR_VISUAL_DISPOSITION_PHASE4_STILL_BLOCKED":
        next_action="Inspect real axilla/overhead renders. If visually retained as the experimental continuation, record lineage explicitly, rebuild status, then reconcile remaining active-epoch regressions before Phase 4."
    else:
        next_action="Inspect real axilla/overhead renders. If visually retained as the experimental continuation, record lineage explicitly, rebuild status, then run the Phase 4 preflight."

    return {
        "schema_version":1,
        "kind":"AXILLA_POST_VALIDATION_DISPOSITION",
        "candidate_revision":revision,
        "candidate_sha256":row.get("sha256"),
        "candidate_classification":row.get("classification"),
        "candidate_state":row.get("state"),
        **measured,
        "face_audit":{"path":face_path.relative_to(root).as_posix(),"sha256":digest(face_path)},
        "comparisons":comparison_refs,
        "review_package":review,
        "next_action_guidance":next_action,
        "lineage_decision_recorded":False,
        "owner_review":row.get("owner_review"),
        "owner_acceptance_inferred":False,
        "production_approved":False,
        "note":"Evidence triage only. Real-render visual disposition and explicit continuation lineage remain separate decisions.",
    }


def markdown(data:dict)->str:
    lines=[
        f"# {data['candidate_revision']} axilla disposition","",
        f"Status: **{data['status']}**",
        f"Candidate SHA: `{data['candidate_sha256']}`",
        f"Development failures: {data['development_failure_count']}",
        f"Direct-parent regressions vs {data['direct_parent']}: {data['direct_parent_regression_count']}",
        f"Active-epoch regressions vs {data['active_epoch_baseline']}: {data['active_epoch_regression_count']}",
        f"Local face audit: **{data['local_face_status']}**",
        f"Review package: **{data['review_package_status']}**",
        f"Phase 4 numerically ready after lineage: **{data['phase4_numeric_ready_after_lineage']}**","",
    ]
    if data["numeric_blockers"]:
        lines+=["## Numeric blockers",""]+[f"- {x}" for x in data["numeric_blockers"]]+[""]
    lines+=["## Next evidence action","",data["next_action_guidance"],"",
            "Visual acceptance is **not inferred**. Production approved: **NO**.",""]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("parent_revision")
    ap.add_argument("--json-out",type=Path,required=True)
    ap.add_argument("--markdown-out",type=Path)
    args=ap.parse_args()
    try:
        result=build_disposition(ROOT,args.revision,args.parent_revision)
        result["source_git_commit"]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        result["generated_utc"]=datetime.now(timezone.utc).isoformat()
        for out in [args.json_out,args.markdown_out]:
            if out is None:continue
            target=out.resolve()
            if not target.is_relative_to(ROOT.resolve()):raise ValueError("output must remain inside repository")
            if target.exists():raise ValueError("disposition output collision")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps(result,indent=2)+"\n" if out==args.json_out else markdown(result),encoding="utf-8")
        print(markdown(result))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
