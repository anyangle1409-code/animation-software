#!/usr/bin/env python3
"""Create a complete pre-edit repair workspace for a fresh ORIGINAL-v1 candidate.

Creates data/control files only. It never edits a Blend and never marks anatomy
clear. All current Critical/High issues remain open until candidate-bound closure
evidence is added after repair and validation.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
FILES={
 "packages":ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json",
 "coupling":ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json",
 "defects":ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json",
 "issues":ROOT/"ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json",
 "weights_contract":ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json",
 "weights_template":ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_TEMPLATE.json",
 "coupling_template":ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json",
 "movement_template":ROOT/"ORIGINAL_V1_MOVEMENT_COUPLING_EVIDENCE_TEMPLATE.json",
 "comparison_template":ROOT/"ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json",
 "declaration_template":ROOT/"ORIGINAL_V1_COUPLING_ZONE_DECLARATION_TEMPLATE.json",
}
def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_new(p,obj):
    if p.exists(): raise ValueError(f"refusing to overwrite {p}")
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
def file_sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_builder(name):
    p=ROOT/"scripts"/name
    sp=importlib.util.spec_from_file_location(name.replace(".py",""),p)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def declaration_for(pkg,cp,linked,template,rev,sha,side,branch):
    t=copy.deepcopy(template)
    t["status"]="COUPLING_ZONE_DECLARATION_DRAFT"; t["candidate_revision"]=rev; t["candidate_sha256"]=sha
    t["coupling_system_id"]=cp["id"]; t["side"]=side; t["source_branch"]=branch
    t["intent"]=f"Execute {pkg['id']} {pkg['name']} at the earliest failing diagnosis layer; no downstream masking."
    t["diagnosis"]={"observed_defect_ids":linked,"suspected_layer":None,"human_evidence_ids":cp["evidence_ids"],"before_evidence":[]}
    t["proximal_anchor_groups"]=[{"name":x,"bones":[],"expected_behavior":"remain anatomically rooted while sharing deformation with bridge tissue"} for x in cp["proximal_anchors"]]
    t["distal_anchor_groups"]=[{"name":x,"bones":[],"expected_behavior":"follow the anatomically connected distal segment without dragging the whole chain"} for x in cp["distal_anchors"]]
    t["expected_human_behavior"]=cp["must_move"]+["ROOTED: "+x for x in cp["must_remain_rooted"]]
    t["forbidden_visual_failures"]=cp["forbidden_failures"]
    t["repair_package_id"]=pkg["id"]; t["proof_movements"]=pkg["proof_movements"]
    t["weights_only_acceptance"]=pkg["weights_only_acceptance"]; t["residual_corrective_role"]=pkg["residual_corrective_role"]
    t["allowed_operations"]=["diagnostic_capture","local_weight_redistribution_after_diagnosis"]
    t["declaration_sources_sha256"]={k:file_sha(FILES[k]) for k in ("packages","coupling","defects")}
    return t

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packages",required=True)
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--sha256",required=True)
    ap.add_argument("--side",required=True,choices=["l","r","bilateral","midline"])
    ap.add_argument("--source-branch",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+[a-z]?",a.candidate,re.I): raise ValueError("candidate revision invalid")
        if not SHA_RE.fullmatch(a.sha256): raise ValueError("candidate sha256 invalid")
        ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        if not ids: raise ValueError("repair packages required")
        out=Path(a.out_dir)
        if out.exists() and any(out.iterdir()): raise ValueError(f"workspace directory not empty: {out}")
        out.mkdir(parents=True,exist_ok=True)

        packages=read(FILES["packages"]); coupling=read(FILES["coupling"]); defects=read(FILES["defects"])
        issue_parent=read(FILES["issues"]); wc=read(FILES["weights_contract"])
        pby={x["id"]:x for x in packages["packages"]}; cby={x["id"]:x for x in coupling["coupling_systems"]}
        unknown=[x for x in ids if x not in pby]
        if unknown: raise ValueError(f"unknown repair packages {unknown}")
        selected_cids=[pby[x]["coupling_system_id"] for x in ids]
        selected_regions=[]
        for cid in selected_cids:
            selected_regions.extend(cby[cid]["body_regions"])
        selected_regions=list(dict.fromkeys(selected_regions))
        linked_defects=list(dict.fromkeys([x["issue_id"] for x in defects["mappings"] if set(x["required_coupling_system_ids"]) & set(selected_cids)]))

        # Human-evidence brief + focused regression plan.
        evidence_builder=load_builder("build_original_v1_repair_evidence_brief.py")
        regression_builder=load_builder("build_original_v1_repair_regression_plan.py")
        evidence_brief=evidence_builder.build(ids)
        regression=regression_builder.build(ids)
        write_new(out/"repair_evidence_brief.json",evidence_brief)
        write_new(out/"repair_regression_plan.json",regression)

        # Immutable comparator ledger copy.
        write_new(out/"parent_issue_ledger_r95.json",issue_parent)

        # Candidate issue ledger starts conservatively with blockers open.
        issue_candidate=copy.deepcopy(issue_parent)
        issue_candidate["candidate_under_review"]={"revision":a.candidate,"sha256":a.sha256}
        for row in issue_candidate.get("issues",[]):
            row["candidate"]={"revision":a.candidate,"sha256":a.sha256}
            if row.get("severity") in {"Critical","High"}:
                row["state"]="Open"
                row["closure_evidence"]=[]
        issue_candidate["policy"]="Candidate-specific ledger. Critical/High issues remain Open until exact-candidate visual + numerical/contact/coupling closure evidence is committed."
        write_new(out/"candidate_issue_ledger.json",issue_candidate)

        # Candidate weights-only acceptance record.
        wo=read(FILES["weights_template"]); wo["status"]="WEIGHTS_ONLY_ACCEPTANCE_NOT_RUN"
        wo["candidate_revision"]=a.candidate; wo["candidate_sha256"]=a.sha256; wo["source_branch"]=a.source_branch
        wby={x["id"]:x for x in wc["regions"]}
        defect_map={x["issue_id"]:set(x["required_coupling_system_ids"]) for x in defects["mappings"]}
        for row in wo["regions"]:
            region_cids=set(wby[row["id"]]["coupling_ids"])
            row["linked_defect_ids"]=[iid for iid,cids in defect_map.items() if cids & region_cids]
        write_new(out/"weights_only_acceptance.json",wo)

        # Candidate coupling evidence record.
        ce=read(FILES["coupling_template"]); ce["status"]="COUPLING_EVIDENCE_NOT_RUN"
        ce["candidate_revision"]=a.candidate; ce["candidate_sha256"]=a.sha256; ce["source_branch"]=a.source_branch
        for row in ce["systems"]:
            row["linked_defect_ids"]=[x["issue_id"] for x in defects["mappings"] if row["coupling_system_id"] in x["required_coupling_system_ids"]]
        write_new(out/"anatomical_coupling_evidence.json",ce)

        # Candidate movement coupling record.
        me=read(FILES["movement_template"]); me["status"]="MOVEMENT_COUPLING_EVIDENCE_NOT_RUN"
        me["candidate_revision"]=a.candidate; me["candidate_sha256"]=a.sha256; me["source_branch"]=a.source_branch
        write_new(out/"movement_coupling_evidence.json",me)

        # One pre-edit declaration draft per package.
        dt=read(FILES["declaration_template"]); declarations=[]
        for pid in ids:
            pkg=pby[pid]; cp=cby[pkg["coupling_system_id"]]
            linked=[x["issue_id"] for x in defects["mappings"] if cp["id"] in x["required_coupling_system_ids"]]
            name="repair_declaration_"+pid.lower().replace("-","_")+".json"
            write_new(out/name,declaration_for(pkg,cp,linked,dt,a.candidate,a.sha256,a.side,a.source_branch))
            declarations.append(name)

        # Candidate comparison manifest prefilled but still blocked/PENDING.
        cm=read(FILES["comparison_template"])
        cm["status"]="CANDIDATE_COMPARISON_MANIFEST_IN_PROGRESS"
        cm["parent"]["issue_ledger_path"]="parent_issue_ledger_r95.json"
        cm["candidate"]={"revision":a.candidate,"sha256":a.sha256,"source_branch":a.source_branch,"issue_ledger_path":"candidate_issue_ledger.json"}
        cm["scope"]={"repair_package_ids":ids,"coupling_system_ids":selected_cids,"region_ids":selected_regions,"defect_ids":linked_defects}
        cm["evidence"]["weights_only_acceptance_path"]="weights_only_acceptance.json"
        cm["evidence"]["anatomical_coupling_evidence_path"]="anatomical_coupling_evidence.json"
        cm["evidence"]["movement_coupling_evidence_path"]="movement_coupling_evidence.json"
        cm["evidence"]["repair_declaration_paths"]=declarations
        cm["evidence"]["regression_report_path"]="repair_regression_result.json"
        cm["evidence"]["pose_capture_plan_path"]="pose_capture_evidence_plan.json"
        cm["evidence"]["surface_visual_review_path"]="surface_visual_review.json"
        write_new(out/"candidate_comparison_manifest.json",cm)

        workspace={
          "schema_version":1,"status":"PRE_EDIT_REPAIR_WORKSPACE","production_approved":False,
          "candidate_revision":a.candidate,"candidate_sha256":a.sha256,"source_branch":a.source_branch,
          "repair_package_ids":ids,"coupling_system_ids":selected_cids,"body_regions":selected_regions,"defect_ids":linked_defects,
          "files":{
            "evidence_brief":"repair_evidence_brief.json","regression_plan":"repair_regression_plan.json",
            "parent_issue_ledger":"parent_issue_ledger_r95.json","candidate_issue_ledger":"candidate_issue_ledger.json",
            "weights_only_acceptance":"weights_only_acceptance.json","anatomical_coupling_evidence":"anatomical_coupling_evidence.json",
            "movement_coupling_evidence":"movement_coupling_evidence.json","repair_declarations":declarations,
            "candidate_comparison_manifest":"candidate_comparison_manifest.json"
          },
          "next_actions":[
            "complete each repair declaration with exact candidate-specific zones/bones/hashes and validate it",
            "run coupling-weight audit before editing",
            "capture before evidence",
            "repair earliest failing layer only",
            "prove weights-only acceptance before corrective refinement",
            "populate coupling/movement/visual/regression evidence",
            "run unified candidate comparison before any issue closure or progression"
          ],
          "note":"Workspace creation is administrative preparation only. Nothing is anatomically clear, owner-accepted or production-approved."
        }
        write_new(out/"workspace_manifest.json",workspace)
        print("PRE-EDIT REPAIR WORKSPACE: CREATED")
        print(json.dumps({"out_dir":str(out),"packages":ids,"coupling_systems":selected_cids,"defects":linked_defects,"declarations":declarations},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
