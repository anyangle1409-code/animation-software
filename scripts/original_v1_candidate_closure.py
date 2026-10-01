#!/usr/bin/env python3
"""Verify that one ORIGINAL-v1 candidate is evidence-closed.

Evidence closure means the candidate's committed identity, full pose report,
declared baseline comparisons and ledger disposition are all present and hash-bound.
It does not mean the candidate passed its gates, was visually accepted, or is production-ready.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from original_v1_production_control import ROOT, CAND, digest, ensure_finite

LEDGER="ORIGINAL_V1_CANDIDATE_LEDGER.json"
HELPER="scripts/original_v1_candidate_closure.py"


def path_ref(root:Path,ref:dict,label:str)->Path:
    if not isinstance(ref,dict) or not ref.get("path") or not re.fullmatch(r"[0-9a-f]{64}",str(ref.get("sha256",""))):
        raise ValueError(label+" path/SHA-256 required")
    p=(root/ref["path"]).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError(label+" file missing/outside repository")
    if digest(p)!=ref["sha256"]:
        raise ValueError(label+" hash differs")
    return p


def candidate_entry(root:Path,revision:str):
    ledger=json.loads((root/LEDGER).read_text(encoding="utf-8"))
    ensure_finite(ledger)
    rows=[row for row in ledger.get("candidates",[]) if row.get("revision")==revision]
    if len(rows)!=1:raise ValueError("candidate ledger must contain revision exactly once")
    return rows[0],ledger


def verify_candidate(root:Path,revision:str)->dict:
    if not re.fullmatch(r"r\d+",revision):
        raise ValueError("numbered candidate revision required")
    row,ledger=candidate_entry(root,revision)
    issues=[]
    sha=row.get("sha256")
    if not re.fullmatch(r"[0-9a-f]{64}",str(sha or "")):
        issues.append("candidate SHA-256 invalid")
    try:
        manifest_path=path_ref(root,row.get("manifest"),"candidate manifest")
        manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        ensure_finite(manifest)
        if manifest.get("candidate_sha256")!=sha:issues.append("candidate manifest SHA identity differs")
        if manifest.get("candidate")!=f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend":
            issues.append("candidate manifest Blend name differs")
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        manifest_path=None;issues.append(str(exc))

    evidence=row.get("evidence_location")
    pose_path=None
    if not isinstance(evidence,str) or not evidence:
        issues.append("full merged pose evidence location missing")
    else:
        pose_path=(root/evidence).resolve()
        if not pose_path.is_relative_to(root.resolve()) or not pose_path.is_file():
            issues.append("full merged pose report missing")
        else:
            try:
                pose=json.loads(pose_path.read_text(encoding="utf-8-sig"));ensure_finite(pose)
                # Candidate identity may live in one of several existing receipt shapes.
                values={
                    pose.get("candidate_sha256"),
                    pose.get("source_candidate_sha256"),
                    pose.get("manifest_candidate_sha256"),
                }-{None}
                if values and sha not in values:
                    issues.append("merged pose report candidate identity differs")
            except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
                issues.append("merged pose report invalid: "+str(exc))

    baselines=row.get("comparison_baselines")
    comparisons=row.get("comparisons")
    if not isinstance(baselines,list) or not baselines:
        issues.append("comparison baseline list missing")
    if not isinstance(comparisons,dict):
        issues.append("comparison map missing")
        comparisons={}
    if isinstance(baselines,list):
        if set(comparisons)!=set(baselines):
            issues.append("comparison map does not exactly match declared baselines")
        for baseline in baselines:
            comp=comparisons.get(baseline)
            try:
                p=path_ref(root,comp.get("evidence") if isinstance(comp,dict) else None,f"comparison {baseline}")
                data=json.loads(p.read_text(encoding="utf-8-sig"));ensure_finite(data)
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
                issues.append(str(exc))

    if row.get("classification") not in ("EXPERIMENTAL","STRICT IMPROVEMENT","TRADE-OFF","NO MATERIAL CHANGE","REGRESSION"):
        issues.append("candidate classification missing/unsupported")
    if row.get("state") not in ("experimental","rejected","accepted"):
        issues.append("candidate state missing/unsupported")
    if not isinstance(row.get("reason"),str) or not row["reason"].strip():
        issues.append("candidate disposition reason missing")
    if row.get("owner_review") not in ("pending","accepted","rejected"):
        issues.append("owner review state missing")

    local_blend=root/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.blend"
    local_blend_state={"path":local_blend.relative_to(root).as_posix(),"exists":local_blend.is_file(),
                       "sha256":None,"matches_manifest":None}
    if local_blend.is_file():
        actual=digest(local_blend);local_blend_state["sha256"]=actual
        local_blend_state["matches_manifest"]=actual==sha
        if actual!=sha:issues.append("local candidate Blend hash differs from ledger/manifest")

    review=[]
    for kind in ("visual","milestone"):
        folder=root/CAND/f"review/{kind}_{revision}"
        manifest=folder/"visual_review_manifest.json"
        if manifest.is_file():
            try:
                data=json.loads(manifest.read_text(encoding="utf-8"));ensure_finite(data)
                if data.get("candidate_sha256")!=sha:raise ValueError("review candidate identity differs")
                if data.get("candidate_revision")!=revision:raise ValueError("review revision differs")
                for file_row in data.get("files",[]):
                    p=(root/file_row["output"]).resolve()
                    if not p.is_file() or digest(p)!=file_row["sha256"]:
                        raise ValueError("review image hash differs")
                review.append({"kind":kind,"status":"AVAILABLE","owner_review":data.get("owner_review"),
                               "manifest":{"path":manifest.relative_to(root).as_posix(),"sha256":digest(manifest)}})
            except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
                issues.append(kind+" review invalid: "+str(exc))
        else:
            review.append({"kind":kind,"status":"NOT_CAPTURED","owner_review":"pending"})

    return {
        "schema_version":1,
        "revision":revision,
        "candidate_sha256":sha,
        "evidence_closure_status":"REFUSED" if issues else "EVIDENCE_CLOSED",
        "production_approved":False,
        "issues":list(dict.fromkeys(issues)),
        "classification":row.get("classification"),
        "candidate_state":row.get("state"),
        "owner_review":row.get("owner_review"),
        "manifest":row.get("manifest"),
        "merged_pose_report":{"path":evidence,"sha256":digest(pose_path)} if pose_path and pose_path.is_file() else None,
        "comparison_baselines":baselines,
        "comparisons":comparisons,
        "local_blend":local_blend_state,
        "review_packages":review,
        "note":"EVIDENCE_CLOSED means candidate identity/evidence/disposition is complete. It does not mean gates pass or owner/production approval."
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision")
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    try:
        result=verify_candidate(ROOT,args.revision)
        if args.json_out:
            out=args.json_out.resolve()
            if not out.is_relative_to(ROOT.resolve()):raise ValueError("output must remain inside repository")
            if out.exists():raise ValueError("candidate closure output collision")
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))
        return 0 if result["evidence_closure_status"]=="EVIDENCE_CLOSED" else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
