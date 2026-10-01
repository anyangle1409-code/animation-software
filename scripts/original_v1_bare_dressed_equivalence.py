#!/usr/bin/env python3
"""Verify exact Phase 7 bare-vs-dressed underlying-body equivalence evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT,CAND,digest,ensure_finite
from original_v1_dressed_evidence import POSES

CAPTURE="scripts/capture_original_v1_bare_dressed_equivalence_blender.py"
HELPER="scripts/original_v1_bare_dressed_equivalence.py"


def verify(report:dict,manifest:dict)->dict:
    if report.get("schema_version")!=1 or report.get("status")!="EVIDENCE_ONLY":
        raise ValueError("equivalence report identity/status differs")
    if report.get("phase_complete") is not False or report.get("production_approved") is not False:
        raise ValueError("equivalence report cannot claim phase/production completion")
    candidate=manifest.get("candidate_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}",str(candidate or "")):raise ValueError("candidate manifest SHA invalid")
    if report.get("candidate_sha256")!=candidate or report.get("candidate")!=manifest.get("candidate"):
        raise ValueError("equivalence candidate identity differs")
    if report.get("rig_id")!="hgpt_canonical_v4_original":raise ValueError("canonical v4 rig identity required")
    rows=report.get("poses")
    if not isinstance(rows,list):raise ValueError("equivalence pose rows required")
    by={}
    blockers=[]
    for row in rows:
        if not isinstance(row,dict) or row.get("pose") in by:raise ValueError("invalid/duplicate equivalence pose row")
        pose=row.get("pose");by[pose]=row
        if row.get("status")!="IDENTICAL":blockers.append(str(pose)+": underlying body differs")
        mask=row.get("body_mask")
        if not isinstance(mask,dict) or mask.get("active_in_either_state") is not False:
            blockers.append(str(pose)+": body hide-mask was active during comparison")
        bare=row.get("bare");dressed=row.get("dressed_presence")
        if not isinstance(bare,dict) or not isinstance(dressed,dict):raise ValueError("bare/dressed identity rows missing")
        if bare.get("vertex_count")!=dressed.get("vertex_count") or bare.get("face_count")!=dressed.get("face_count"):
            blockers.append(str(pose)+": evaluated body topology differs")
        for key in ("vertex_sha256_round9","pose_state_sha256","metrics_sha256"):
            if bare.get(key)!=dressed.get(key):
                blockers.append(str(pose)+": "+key+" differs")
        if row.get("max_vertex_delta_mm")!=0.0 or row.get("mean_vertex_delta_mm")!=0.0 or row.get("changed_vertex_count_exact_float")!=0:
            blockers.append(str(pose)+": nonzero underlying-body vertex delta")
    if set(by)!=set(POSES):raise ValueError("frozen stress-pose coverage incomplete")
    if report.get("pose_count")!=len(POSES):raise ValueError("pose count differs")
    ensure_finite(report)
    return {
        "schema_version":1,
        "status":"EVIDENCE_ONLY",
        "phase_complete":False,
        "production_approved":False,
        "candidate_revision":report.get("candidate_revision"),
        "candidate_sha256":candidate,
        "equivalence_status":"BLOCKED" if blockers else "IDENTICAL_UNDER_GARMENT_PRESENCE",
        "blockers":list(dict.fromkeys(blockers)),
        "pose_count":len(by),
        "limits":[
            "Exact underlying-body identity check only; garment clearance/contact/visual quality are separate.",
            "No deformation tolerance is invented: the same body under the same pose must remain identical when garment visibility changes.",
            "This result does not complete Phase 7."
        ]
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report",type=Path)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--json-out",type=Path,required=True)
    args=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+",args.revision):raise ValueError("numbered candidate revision required")
        report_path=args.report.resolve()
        if not report_path.is_relative_to(ROOT.resolve()) or not report_path.is_file():raise ValueError("report missing/outside repository")
        manifest_path=ROOT/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{args.revision}.json"
        report=json.loads(report_path.read_text(encoding="utf-8"));manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if report.get("candidate_revision")!=args.revision:raise ValueError("report revision differs")
        if report.get("candidate_manifest_sha256")!=digest(manifest_path):raise ValueError("candidate manifest bytes differ from capture")
        result=verify(report,manifest)
        result["source_evidence"]=[
            {"path":report_path.relative_to(ROOT).as_posix(),"sha256":digest(report_path)},
            {"path":manifest_path.relative_to(ROOT).as_posix(),"sha256":digest(manifest_path)},
            {"path":CAPTURE,"sha256":digest(ROOT/CAPTURE)},
            {"path":HELPER,"sha256":digest(ROOT/HELPER)},
        ]
        result["source_git_commit"]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        result["generated_utc"]=datetime.now(timezone.utc).isoformat()
        out=args.json_out.resolve()
        if not out.is_relative_to(ROOT.resolve()):raise ValueError("output must remain inside repository")
        if out.exists():raise ValueError("equivalence verification output collision")
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("BARE/DRESSED EQUIVALENCE",result["equivalence_status"],"— evidence only")
        return 0 if result["equivalence_status"]=="IDENTICAL_UNDER_GARMENT_PRESENCE" else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
