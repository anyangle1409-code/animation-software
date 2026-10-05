#!/usr/bin/env python3
"""Collect post-repair evidence into a finalized candidate workspace.

Copies only existing evidence. Every candidate-bound JSON must match the workspace
FINAL SHA. Engineering statuses remain PENDING; this collector never infers PASS.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RC=ROOT/"ORIGINAL_V1_WORK/candidates/repair_checks"
REVIEW=ROOT/"ORIGINAL_V1_WORK/candidates/review"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def candidate_sha(obj):
    if isinstance(obj,dict):
        if isinstance(obj.get("candidate_sha256"),str): return obj["candidate_sha256"]
        c=obj.get("candidate")
        if isinstance(c,dict) and isinstance(c.get("sha256"),str): return c["sha256"]
        u=obj.get("candidate_under_review")
        if isinstance(u,dict) and isinstance(u.get("sha256"),str): return u["sha256"]
    return None

def copy_json(src,dst,expected_sha,require_candidate=True):
    if not src.is_file(): raise ValueError(f"missing evidence: {src}")
    obj=read(src)
    if require_candidate:
        got=candidate_sha(obj)
        if got!=expected_sha: raise ValueError(f"{src}: candidate SHA mismatch; expected {expected_sha}, got {got}")
    shutil.copy2(src,dst)
    return obj

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--revision",required=True)
    ap.add_argument("--label",required=True)
    ap.add_argument("--prior")
    a=ap.parse_args()
    try:
        ws=Path(a.workspace)
        fm=read(ws/"workspace_finalization_manifest.json")
        final=fm["final_candidate_sha256"]
        if fm.get("candidate_revision")!=a.revision: raise ValueError("revision differs from finalized workspace")
        out=ws/"evidence_post_repair"
        if out.exists(): raise ValueError("evidence_post_repair already exists")
        out.mkdir(parents=True)

        sources={
          "skinning_mode":RC/"skinning_mode"/a.label/"skinning_mode.json",
          "pose_coupling_scope":RC/"pose_coupling_scope"/a.label/"pose_coupling_scope.json",
          "pose_capture_evidence_plan":RC/"pose_evidence_plans"/a.label/"pose_capture_evidence_plan.json",
          "shoulder_layer_diagnostic":RC/"shoulder_layer_diagnostics"/a.label/"shoulder_layer_diagnostic.json",
          "motion_reversibility":RC/"motion_reversibility"/a.label/"motion_reversibility.json",
          "motion_continuity":RC/"motion_continuity"/a.label/"motion_continuity.json",
          "full_evidence_manifest":RC/f"full_{a.revision}_evidence_manifest.json",
        }
        copied={}
        for name,src in sources.items():
            dst=out/(name+".json")
            copy_json(src,dst,final,True)
            copied[name]=dst

        # Additional regression comparisons may not expose a standard candidate
        # identity field, so they are copied only as supporting evidence and are
        # never sufficient to set regression PASS.
        support={}
        for src in sorted(RC.glob(f"full_{a.revision}_comparison_vs_*.json")):
            dst=out/src.name; shutil.copy2(src,dst); support[src.stem]=dst
        merged=RC/f"full_{a.revision}_merged_pose_report.json"
        if merged.is_file():
            dst=out/merged.name; shutil.copy2(merged,dst); support["merged_pose_report"]=dst

        milestone=REVIEW/f"milestone_{a.revision}"/"visual_review_manifest.json"
        visual_manifests=[]
        if milestone.is_file():
            dst=out/"milestone_visual_review_manifest.json"
            copy_json(milestone,dst,final,True)
            visual_manifests.append(dst)

        review_package=REVIEW/f"package_{a.revision}_{a.label}"/"review_package.json"
        if review_package.is_file():
            dst=out/"review_package.json"
            copy_json(review_package,dst,final,True)
            copied["review_package"]=dst

        # Link copied evidence into a new comparison manifest; never overwrite the
        # final template and never manufacture PASS statuses.
        cm=read(ws/"candidate_comparison_manifest_final.json")
        cm["status"]="CANDIDATE_COMPARISON_POST_REPAIR_EVIDENCE_LINKED"
        cm["evidence"]["motion_reversibility_path"]="evidence_post_repair/motion_reversibility.json"
        cm["evidence"]["motion_continuity_path"]="evidence_post_repair/motion_continuity.json"
        cm["evidence"]["pose_capture_plan_path"]="evidence_post_repair/pose_capture_evidence_plan.json"
        cm["evidence"]["regression_report_path"]="evidence_post_repair/full_evidence_manifest.json"
        cm["evidence"]["regression_status"]="PENDING"
        cm["evidence"]["continuity_engineering_review_status"]="PENDING"
        cm["evidence"]["visual_capture_manifest_paths"]=["evidence_post_repair/"+p.name for p in visual_manifests]
        cm["evidence"]["visual_engineering_review_status"]="PENDING"
        cm["evidence"]["contact_status"]="PENDING"
        cm["evidence"]["change_audit_status"]="PENDING"
        linked=ws/"candidate_comparison_manifest_post_repair.json"
        if linked.exists(): raise ValueError("post-repair comparison manifest already exists")
        linked.write_text(json.dumps(cm,indent=2)+"\n",encoding="utf-8")

        all_files={**copied,**support}
        index={
          "schema_version":1,"status":"POST_REPAIR_EVIDENCE_COLLECTED","production_approved":False,
          "candidate_revision":a.revision,"candidate_sha256":final,"label":a.label,
          "files":{k:{"path":str(v.relative_to(ws)).replace("\\","/"),"sha256":digest(v)} for k,v in all_files.items()},
          "visual_capture_manifest_paths":[str(p.relative_to(ws)).replace("\\","/") for p in visual_manifests],
          "comparison_manifest":"candidate_comparison_manifest_post_repair.json",
          "engineering_statuses":"PENDING",
          "next_actions":[
            "review dense motion continuity and set explicit engineering disposition",
            "review full regression comparisons/acceptance output and produce candidate-bound regression review",
            "complete contact and change-audit evidence",
            "perform region-by-region human visual review from real candidate renders",
            "populate final weights-only/coupling/movement evidence and repair execution records",
            "only then run unified candidate comparison"
          ],
          "note":"Collection/indexing is not acceptance. No PASS status is inferred."
        }
        (ws/"post_repair_evidence_index.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
        print("POST-REPAIR EVIDENCE COLLECTION: PASS")
        print(json.dumps({"candidate_revision":a.revision,"candidate_sha256":final,"copied":sorted(all_files),"visual_manifests":len(visual_manifests)},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,shutil.Error) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
