#!/usr/bin/env python3
"""Create a complete PRE-EDIT repair workspace for a fresh ORIGINAL-v1 candidate.

The immutable declaration layer is bound to the PRE-EDIT candidate SHA.
All acceptance/coupling/comparison records remain FINAL-SHA templates until the
repaired Blend is saved and finalized. This prevents accidental mixing of
before-edit and after-edit evidence identities.
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
 "visual_template":ROOT/"ORIGINAL_V1_CANDIDATE_SURFACE_VISUAL_REVIEW_TEMPLATE.json",
 "visual_requirements":ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json",
 "sweep_acceptance_template":ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_ACCEPTANCE_TEMPLATE.json",
 "sweep_visual_template":ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE_TEMPLATE.json",
 "sweep_contact_template":ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REPORT_TEMPLATE.json",
 "sweep_contact_requirements":ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json",
 "sweep_plan":ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json",
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

def declaration_for(pkg,cp,linked,template,rev,pre_sha,side,branch):
    t=copy.deepcopy(template)
    t["status"]="COUPLING_ZONE_DECLARATION_DRAFT"
    t["candidate_revision"]=rev
    t["candidate_sha256"]=pre_sha
    t["pre_edit_candidate_sha256"]=pre_sha
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
    ap.add_argument("--sha256",required=True,help="PRE-EDIT candidate Blend SHA-256")
    ap.add_argument("--side",required=True,choices=["l","r","bilateral","midline"])
    ap.add_argument("--source-branch",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        if not re.fullmatch(r"r\d+[a-z]?",a.candidate,re.I): raise ValueError("candidate revision invalid")
        if not SHA_RE.fullmatch(a.sha256): raise ValueError("pre-edit candidate sha256 invalid")
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
        selected_regions=list(dict.fromkeys(r for cid in selected_cids for r in cby[cid]["body_regions"]))
        selected_set=set(selected_cids)
        linked_defects=list(dict.fromkeys(
            x["issue_id"] for x in defects["mappings"]
            if set(x["required_coupling_system_ids"]) and set(x["required_coupling_system_ids"]).issubset(selected_set)
        ))

        evidence_builder=load_builder("build_original_v1_repair_evidence_brief.py")
        regression_builder=load_builder("build_original_v1_repair_regression_plan.py")
        validation_builder=load_builder("build_original_v1_package_validation_selection.py")
        validation_selection=validation_builder.build(ids)
        if not validation_selection.get("validation_definition_complete") or validation_selection.get("uncovered_proof_movements"):
            raise ValueError("repair-package validation definition is incomplete")
        write_new(out/"repair_evidence_brief.json",evidence_builder.build(ids))
        write_new(out/"repair_regression_plan.json",regression_builder.build(ids))
        write_new(out/"package_validation_selection.json",validation_selection)
        write_new(out/"parent_issue_ledger_r95.json",issue_parent)

        # PRE-EDIT issue snapshot: blockers remain open and identity is immutable.
        pre_ledger=copy.deepcopy(issue_parent)
        pre_ledger["candidate_under_review"]={"revision":a.candidate,"sha256":a.sha256}
        for row in pre_ledger.get("issues",[]):
            row["candidate"]={"revision":a.candidate,"sha256":a.sha256}
            if row.get("severity") in {"Critical","High"}:
                row["state"]="Open"; row["closure_evidence"]=[]
        pre_ledger["policy"]="Immutable pre-edit issue snapshot. Critical/High issues remain Open; this file is never used as final closure evidence."
        write_new(out/"candidate_issue_ledger_pre_edit.json",pre_ledger)

        # FINAL-SHA templates: intentionally unbound until repaired Blend exists.
        wo=read(FILES["weights_template"])
        wo["status"]="WEIGHTS_ONLY_ACCEPTANCE_FINAL_SHA_NOT_BOUND"
        wo["candidate_revision"]=a.candidate; wo["candidate_sha256"]=None; wo["source_branch"]=a.source_branch
        wby={x["id"]:x for x in wc["regions"]}
        defect_map={x["issue_id"]:set(x["required_coupling_system_ids"]) for x in defects["mappings"]}
        for row in wo["regions"]:
            region_cids=set(wby[row["id"]]["coupling_ids"])
            row["linked_defect_ids"]=[iid for iid,cids in defect_map.items() if cids & region_cids]
        write_new(out/"weights_only_acceptance_FINAL_TEMPLATE.json",wo)

        ce=read(FILES["coupling_template"])
        ce["status"]="COUPLING_EVIDENCE_FINAL_SHA_NOT_BOUND"; ce["candidate_revision"]=a.candidate; ce["candidate_sha256"]=None; ce["source_branch"]=a.source_branch
        for row in ce["systems"]:
            row["linked_defect_ids"]=[x["issue_id"] for x in defects["mappings"] if row["coupling_system_id"] in x["required_coupling_system_ids"]]
        write_new(out/"anatomical_coupling_evidence_FINAL_TEMPLATE.json",ce)

        me=read(FILES["movement_template"])
        me["status"]="MOVEMENT_COUPLING_EVIDENCE_FINAL_SHA_NOT_BOUND"; me["candidate_revision"]=a.candidate; me["candidate_sha256"]=None; me["source_branch"]=a.source_branch
        write_new(out/"movement_coupling_evidence_FINAL_TEMPLATE.json",me)

        vr=read(FILES["visual_template"]); visual_req=read(FILES["visual_requirements"])
        vr["status"]="CANDIDATE_SURFACE_VISUAL_REVIEW_FINAL_SHA_NOT_BOUND"
        vr["candidate_revision"]=a.candidate; vr["candidate_sha256"]=None; vr["source_branch"]=a.source_branch
        vr["scope_region_ids"]=selected_regions
        visual_by={x["id"]:x for x in visual_req["regions"]}
        for row in vr["regions"]:
            if row["id"] in selected_regions:
                row["human_evidence_ids"]=list(visual_by[row["id"]].get("current_visual_evidence_ids",[]))
        write_new(out/"surface_visual_review_FINAL_TEMPLATE.json",vr)

        sweep_accept_template=read(FILES["sweep_acceptance_template"])
        sweep_visual_template=read(FILES["sweep_visual_template"])
        sweep_contact_template=read(FILES["sweep_contact_template"])
        sweep_contact_req=read(FILES["sweep_contact_requirements"])
        sweep_plan=read(FILES["sweep_plan"])
        sweep_acceptance_templates=[]
        expected_sweep_acceptance_records=[]
        sweep_visual_templates=[]
        expected_sweep_visual_records=[]
        sweep_contact_templates=[]
        expected_sweep_contact_records=[]
        for sid in validation_selection.get("sweep_only_movements_requiring_generic_runner",[]):
            stem=sid.lower().replace("-","_")
            visual_template_name=f"human_movement_sweep_visual_{stem}_FINAL_TEMPLATE.json"
            visual_final_name=f"human_movement_sweep_visual_{stem}_final.json"
            sv=copy.deepcopy(sweep_visual_template)
            sv["status"]="HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE_FINAL_SHA_NOT_BOUND"
            sv["candidate_revision"]=a.candidate
            sv["candidate_sha256"]=None
            sv["sweep_id"]=sid
            sv["samples"]=[{"label":label,"views":[]} for label in sweep_plan["sweeps"][sid].get("samples",[])]
            write_new(out/visual_template_name,sv)
            sweep_visual_templates.append(visual_template_name)
            expected_sweep_visual_records.append(visual_final_name)

            contact_final_name=None
            if sid in sweep_contact_req.get("sweeps",{}):
                contact_template_name=f"human_movement_sweep_contact_{stem}_FINAL_TEMPLATE.json"
                contact_final_name=f"human_movement_sweep_contact_{stem}_final.json"
                cr=copy.deepcopy(sweep_contact_template)
                cr["status"]="HUMAN_MOVEMENT_SWEEP_CONTACT_REPORT_FINAL_SHA_NOT_BOUND"
                cr["candidate_revision"]=a.candidate
                cr["candidate_sha256"]=None
                cr["sweep_id"]=sid
                cr["samples"]=[]
                for label,ar in sweep_contact_req["sweeps"][sid]["samples"].items():
                    row={"label":label,"domains":{}}
                    for domain in ar.get("required_domains",[]):
                        row["domains"][domain]={
                          "classification":"UNCLASSIFIED",
                          "raw_measurement_ref":None,
                          "evidence_note":None
                        }
                    if "heel_state" in ar:
                        row["heel_state_observed"]=None
                    cr["samples"].append(row)
                write_new(out/contact_template_name,cr)
                sweep_contact_templates.append(contact_template_name)
                expected_sweep_contact_records.append(contact_final_name)

            sat=copy.deepcopy(sweep_accept_template)
            sat["status"]="HUMAN_MOVEMENT_SWEEP_ACCEPTANCE_FINAL_SHA_NOT_BOUND"
            sat["candidate_revision"]=a.candidate
            sat["candidate_sha256"]=None
            sat["sweep_id"]=sid
            sat["required_human_evidence_ids"]=list(sweep_plan["sweeps"][sid].get("evidence_ids",[]))
            sat["human_evidence_review_refs"]=[]
            sat["visual_capture_manifest_path"]=visual_final_name
            sat["contact_report_path"]=contact_final_name
            sat["contact_review_status"]="PENDING" if contact_final_name else "NOT_APPLICABLE"
            template_name=f"human_movement_sweep_acceptance_{stem}_FINAL_TEMPLATE.json"
            final_name=f"human_movement_sweep_acceptance_{stem}_final.json"
            write_new(out/template_name,sat)
            sweep_acceptance_templates.append(template_name)
            expected_sweep_acceptance_records.append(final_name)

        dt=read(FILES["declaration_template"]); declarations=[]; expected_exec=[]
        for pid in ids:
            pkg=pby[pid]; cp=cby[pkg["coupling_system_id"]]
            linked=[x["issue_id"] for x in defects["mappings"] if cp["id"] in x["required_coupling_system_ids"]]
            stem=pid.lower().replace("-","_")
            name="repair_declaration_"+stem+".json"
            write_new(out/name,declaration_for(pkg,cp,linked,dt,a.candidate,a.sha256,a.side,a.source_branch))
            declarations.append(name)
            expected_exec.append("repair_execution_"+stem+".json")

        # Comparison template is scope-filled but FINAL SHA remains intentionally null.
        cm=read(FILES["comparison_template"])
        cm["status"]="CANDIDATE_COMPARISON_FINAL_SHA_NOT_BOUND"
        cm["parent"]["issue_ledger_path"]="parent_issue_ledger_r95.json"
        cm["candidate"]={"revision":a.candidate,"sha256":None,"source_branch":a.source_branch,"issue_ledger_path":"candidate_issue_ledger_final.json"}
        cm["scope"]={"repair_package_ids":ids,"coupling_system_ids":selected_cids,"region_ids":selected_regions,"defect_ids":linked_defects}
        cm["evidence"]["weights_only_acceptance_path"]="weights_only_acceptance_final.json"
        cm["evidence"]["anatomical_coupling_evidence_path"]="anatomical_coupling_evidence_final.json"
        cm["evidence"]["movement_coupling_evidence_path"]="movement_coupling_evidence_final.json"
        cm["evidence"]["repair_declaration_paths"]=declarations
        cm["evidence"]["repair_execution_record_paths"]=expected_exec
        cm["evidence"]["regression_report_path"]="repair_regression_result.json"
        cm["evidence"]["pose_capture_plan_path"]="pose_capture_evidence_plan_final.json"
        cm["evidence"]["surface_visual_review_path"]="surface_visual_review_final.json"
        cm["evidence"]["human_movement_sweep_acceptance_paths"]=expected_sweep_acceptance_records
        write_new(out/"candidate_comparison_FINAL_TEMPLATE.json",cm)

        workspace={
          "schema_version":1,"status":"PRE_EDIT_REPAIR_WORKSPACE","production_approved":False,
          "candidate_revision":a.candidate,"pre_edit_candidate_sha256":a.sha256,"final_candidate_sha256":None,
          "source_branch":a.source_branch,"repair_package_ids":ids,"coupling_system_ids":selected_cids,
          "body_regions":selected_regions,"defect_ids":linked_defects,
          "identity_rule":"Declarations/pre-edit snapshot bind pre-edit SHA. Acceptance/coupling/comparison evidence MUST bind final post-edit SHA after the repaired Blend is saved.",
          "files":{
            "evidence_brief":"repair_evidence_brief.json","regression_plan":"repair_regression_plan.json",
            "package_validation_selection":"package_validation_selection.json",
            "parent_issue_ledger":"parent_issue_ledger_r95.json","pre_edit_issue_ledger":"candidate_issue_ledger_pre_edit.json",
            "weights_only_final_template":"weights_only_acceptance_FINAL_TEMPLATE.json",
            "coupling_final_template":"anatomical_coupling_evidence_FINAL_TEMPLATE.json",
            "movement_coupling_final_template":"movement_coupling_evidence_FINAL_TEMPLATE.json",
            "surface_visual_final_template":"surface_visual_review_FINAL_TEMPLATE.json",
            "sweep_acceptance_final_templates":sweep_acceptance_templates,
            "expected_sweep_acceptance_records":expected_sweep_acceptance_records,
            "sweep_visual_final_templates":sweep_visual_templates,
            "expected_sweep_visual_records":expected_sweep_visual_records,
            "sweep_contact_final_templates":sweep_contact_templates,
            "expected_sweep_contact_records":expected_sweep_contact_records,
            "repair_declarations":declarations,"expected_repair_execution_records":expected_exec,
            "candidate_comparison_final_template":"candidate_comparison_FINAL_TEMPLATE.json"
          },
          "validation_selection":{
            "pose_names":validation_selection.get("pose_names",[]),
            "deterministic_sweep_names":validation_selection.get("deterministic_sweep_names",[]),
            "sweep_only_movements_requiring_generic_runner":validation_selection.get("sweep_only_movements_requiring_generic_runner",[]),
            "validation_definition_complete":validation_selection.get("validation_definition_complete",False),
            "sweep_acceptance_records_required":expected_sweep_acceptance_records
          },
          "next_actions":[
            "complete each pre-edit repair declaration with exact candidate-specific zones/bones/hashes and validate it",
            "run coupling-weight audit before editing",
            "capture before evidence",
            "repair earliest failing layer only",
            "save repaired Blend and calculate FINAL SHA",
            "finalize workspace to bind final evidence templates/issue ledger/comparison manifest to FINAL SHA",
            "prove weights-only acceptance before corrective refinement",
            "populate coupling/movement/visual/regression evidence, sweep acceptance records and execution records",
            "run unified candidate comparison before any issue closure or progression"
          ],
          "note":"Workspace creation is administrative PRE-EDIT preparation only. Nothing is anatomically clear, owner-accepted or production-approved."
        }
        write_new(out/"workspace_manifest.json",workspace)
        print("PRE-EDIT REPAIR WORKSPACE: CREATED")
        print(json.dumps({"out_dir":str(out),"candidate_revision":a.candidate,"pre_edit_sha256":a.sha256,"packages":ids,"coupling_systems":selected_cids,"defects":linked_defects},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
