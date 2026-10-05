#!/usr/bin/env python3
"""Finalize a PRE-EDIT repair workspace against the saved POST-EDIT Blend SHA.

This creates new FINAL-SHA records and execution-record drafts. It never edits
the immutable pre-edit declarations or pre-edit workspace manifest.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXEC_TEMPLATE=ROOT/"ORIGINAL_V1_REPAIR_EXECUTION_RECORD_TEMPLATE.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_new(p,obj):
    if p.exists(): raise ValueError(f"refusing to overwrite {p}")
    p.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--final-candidate",required=True)
    a=ap.parse_args()
    try:
        ws=Path(a.workspace)
        wm=read(ws/"workspace_manifest.json")
        if wm.get("status")!="PRE_EDIT_REPAIR_WORKSPACE": raise ValueError("workspace is not a PRE_EDIT_REPAIR_WORKSPACE")
        pre=str(wm.get("pre_edit_candidate_sha256",""))
        if not SHA_RE.fullmatch(pre): raise ValueError("pre-edit SHA invalid")
        final_path=Path(a.final_candidate)
        if not final_path.exists(): raise ValueError("final candidate Blend missing")
        final=sha_file(final_path)
        if final==pre: raise ValueError("final candidate SHA equals pre-edit SHA; no executed repair is evidenced")
        rev=wm["candidate_revision"]; branch=wm["source_branch"]

        # Final candidate issue ledger starts blocked/open; closure happens only
        # after exact-final-candidate evidence is populated.
        pre_ledger=read(ws/wm["files"]["pre_edit_issue_ledger"])
        ledger=copy.deepcopy(pre_ledger)
        ledger["candidate_under_review"]={"revision":rev,"sha256":final}
        ledger["policy"]="FINAL candidate ledger. Critical/High issues remain Open until exact-final-SHA visual + weights-only + coupling + numerical/contact closure evidence is committed."
        for row in ledger.get("issues",[]):
            row["candidate"]={"revision":rev,"sha256":final}
            if row.get("severity") in {"Critical","High"}:
                row["state"]="Open"; row["closure_evidence"]=[]
        write_new(ws/"candidate_issue_ledger_final.json",ledger)

        # Bind previously unbound acceptance/coupling templates to FINAL SHA.
        wo=read(ws/wm["files"]["weights_only_final_template"])
        wo["status"]="WEIGHTS_ONLY_ACCEPTANCE_NOT_RUN"; wo["candidate_revision"]=rev; wo["candidate_sha256"]=final; wo["source_branch"]=branch
        write_new(ws/"weights_only_acceptance_final.json",wo)

        ce=read(ws/wm["files"]["coupling_final_template"])
        ce["status"]="COUPLING_EVIDENCE_NOT_RUN"; ce["candidate_revision"]=rev; ce["candidate_sha256"]=final; ce["source_branch"]=branch
        write_new(ws/"anatomical_coupling_evidence_final.json",ce)

        me=read(ws/wm["files"]["movement_coupling_final_template"])
        me["status"]="MOVEMENT_COUPLING_EVIDENCE_NOT_RUN"; me["candidate_revision"]=rev; me["candidate_sha256"]=final; me["source_branch"]=branch
        write_new(ws/"movement_coupling_evidence_final.json",me)

        vr=read(ws/wm["files"]["surface_visual_final_template"])
        vr["status"]="CANDIDATE_SURFACE_VISUAL_REVIEW"; vr["candidate_revision"]=rev; vr["candidate_sha256"]=final; vr["source_branch"]=branch
        write_new(ws/"surface_visual_review_final.json",vr)

        # Draft one post-edit provenance record for each immutable declaration.
        et=read(EXEC_TEMPLATE); execution_paths=[]
        declarations=wm["files"]["repair_declarations"]
        expected=wm["files"]["expected_repair_execution_records"]
        if len(declarations)!=len(expected): raise ValueError("declaration/execution record count differs")
        for dec_name,out_name in zip(declarations,expected):
            dp=ws/dec_name; raw=dp.read_bytes(); dec=json.loads(raw.decode("utf-8"))
            dpre=dec.get("pre_edit_candidate_sha256") or dec.get("candidate_sha256")
            if dpre!=pre: raise ValueError(f"{dec_name}: pre-edit SHA differs from workspace")
            rec=copy.deepcopy(et)
            rec["status"]="REPAIR_EXECUTION_RECORD_DRAFT"
            rec["candidate_revision"]=rev; rec["source_branch"]=branch
            rec["repair_package_id"]=dec.get("repair_package_id"); rec["coupling_system_id"]=dec.get("coupling_system_id"); rec["side"]=dec.get("side")
            rec["repair_declaration_path"]=dec_name
            rec["repair_declaration_sha256"]=hashlib.sha256(raw).hexdigest()
            rec["pre_edit_candidate_sha256"]=pre; rec["final_candidate_sha256"]=final
            write_new(ws/out_name,rec); execution_paths.append(out_name)

        cm=read(ws/wm["files"]["candidate_comparison_final_template"])
        cm["status"]="CANDIDATE_COMPARISON_MANIFEST_IN_PROGRESS"
        cm["candidate"]["revision"]=rev; cm["candidate"]["sha256"]=final; cm["candidate"]["source_branch"]=branch
        cm["candidate"]["issue_ledger_path"]="candidate_issue_ledger_final.json"
        cm["evidence"]["weights_only_acceptance_path"]="weights_only_acceptance_final.json"
        cm["evidence"]["anatomical_coupling_evidence_path"]="anatomical_coupling_evidence_final.json"
        cm["evidence"]["movement_coupling_evidence_path"]="movement_coupling_evidence_final.json"
        cm["evidence"]["surface_visual_review_path"]="surface_visual_review_final.json"
        cm["evidence"]["repair_execution_record_paths"]=execution_paths
        write_new(ws/"candidate_comparison_manifest_final.json",cm)

        finalization={
          "schema_version":1,"status":"POST_EDIT_WORKSPACE_FINALIZED","production_approved":False,
          "candidate_revision":rev,"pre_edit_candidate_sha256":pre,"final_candidate_sha256":final,
          "final_candidate_path":str(final_path),"source_branch":branch,
          "immutable_pre_edit_manifest":"workspace_manifest.json",
          "immutable_repair_declarations":declarations,
          "final_records":{
            "candidate_issue_ledger":"candidate_issue_ledger_final.json",
            "weights_only_acceptance":"weights_only_acceptance_final.json",
            "anatomical_coupling_evidence":"anatomical_coupling_evidence_final.json",
            "movement_coupling_evidence":"movement_coupling_evidence_final.json",
            "surface_visual_review":"surface_visual_review_final.json",
            "repair_execution_records":execution_paths,
            "candidate_comparison_manifest":"candidate_comparison_manifest_final.json"
          },
          "next_actions":[
            "fill and validate each repair execution record with actual operations/edited vertices/bones and evidence paths",
            "rerun final-candidate pose scope and automatic pose capture plan",
            "run final-candidate reversibility/continuity/full regression/contact/visual evidence",
            "populate weights-only and coupling evidence against the final SHA",
            "update final issue ledger only from committed closure evidence",
            "run unified candidate comparison; engineering eligibility must remain blocked until all scoped gates pass"
          ],
          "note":"Finalization binds records to the post-edit SHA but does not infer any anatomical pass, owner acceptance or production approval."
        }
        write_new(ws/"workspace_finalization_manifest.json",finalization)
        print("POST-EDIT REPAIR WORKSPACE: FINALIZED")
        print(json.dumps({"candidate_revision":rev,"pre_edit_sha256":pre,"final_candidate_sha256":final,"execution_records":execution_paths},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
