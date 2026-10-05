#!/usr/bin/env python3
"""Build one fail-closed parent->candidate whole-body comparison report.

A PASS label never stands alone: when a status is PASS, its evidence path must
exist, parse as JSON where required, and bind to the exact candidate SHA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPAIR_PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING_MAP=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
WEIGHTS_CONTRACT=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_CONTRACT.json"

SHA_RE=re.compile(r"^[0-9a-f]{64}$")
BLOCKING_STATES={"open","in progress","pending review","not_run","fail","blocked"}
PASS={"PASS","NOT_APPLICABLE"}


def load(base,p):
    if p is None:
        return None
    q=Path(p)
    q=q if q.is_absolute() else base/q
    return json.loads(q.read_text(encoding="utf-8"))


def resolve(base,p):
    if p is None:
        return None
    q=Path(p)
    return q if q.is_absolute() else base/q


def candidate_sha(obj):
    if not isinstance(obj,dict):
        return None
    direct=obj.get("candidate_sha256")
    if isinstance(direct,str):
        return direct
    cand=obj.get("candidate")
    if isinstance(cand,dict) and isinstance(cand.get("sha256"),str):
        return cand["sha256"]
    under=obj.get("candidate_under_review")
    if isinstance(under,dict) and isinstance(under.get("sha256"),str):
        return under["sha256"]
    return None


def blockers(ledger):
    out={}
    for x in (ledger or {}).get("issues",[]):
        if str(x.get("severity","")).lower() in {"critical","high"} and str(x.get("state","")).lower() in BLOCKING_STATES:
            out[x["id"]]=x
    return out


def build(manifest,base):
    cand=manifest["candidate"]
    parent=manifest["parent"]
    scope=manifest["scope"]
    ev=manifest["evidence"]
    csha=str(cand.get("sha256",""))
    psha=str(parent.get("sha256",""))
    if not SHA_RE.fullmatch(csha):
        raise ValueError("candidate sha256 invalid")
    if not SHA_RE.fullmatch(psha):
        raise ValueError("parent sha256 invalid")

    repairs=json.loads(REPAIR_PACKAGES.read_text(encoding="utf-8"))
    coupling=json.loads(COUPLING_MAP.read_text(encoding="utf-8"))
    weights_contract=json.loads(WEIGHTS_CONTRACT.read_text(encoding="utf-8"))
    repair_by={x["id"]:x for x in repairs.get("packages",[])}
    coupling_ids={x["id"] for x in coupling.get("coupling_systems",[])}
    region_ids={x["id"] for x in weights_contract.get("regions",[])}

    checks=[]
    failures=[]
    warnings=[]

    def check(name,ok,detail):
        checks.append({"name":name,"pass":bool(ok),"detail":detail})
        if not ok:
            failures.append(name)

    # Scope itself must be authoritative.
    bad_repairs=sorted(set(scope.get("repair_package_ids",[]))-set(repair_by))
    bad_coupling=sorted(set(scope.get("coupling_system_ids",[]))-coupling_ids)
    bad_regions=sorted(set(scope.get("region_ids",[]))-region_ids)
    check("scope_repair_packages_known",not bad_repairs,{"unknown":bad_repairs})
    check("scope_coupling_systems_known",not bad_coupling,{"unknown":bad_coupling})
    check("scope_regions_known",not bad_regions,{"unknown":bad_regions})
    for pid in scope.get("repair_package_ids",[]):
        if pid in repair_by:
            cid=repair_by[pid]["coupling_system_id"]
            check(f"scope_repair_maps_to_coupling:{pid}",cid in scope.get("coupling_system_ids",[]),
                  {"required_coupling_system_id":cid})

    # Ledgers are mandatory because no-new-blocker and scoped-defect closure are
    # core comparison rules.
    parent_ledger=load(base,parent.get("issue_ledger_path"))
    cand_ledger=load(base,cand.get("issue_ledger_path"))
    check("parent_issue_ledger_present",parent_ledger is not None,parent.get("issue_ledger_path"))
    check("candidate_issue_ledger_present",cand_ledger is not None,cand.get("issue_ledger_path"))
    if cand_ledger is not None:
        check("candidate_issue_ledger_sha",candidate_sha(cand_ledger)==csha,candidate_sha(cand_ledger))

    # Core candidate-bound evidence.
    core={
      "weights_only":ev.get("weights_only_acceptance_path"),
      "coupling":ev.get("anatomical_coupling_evidence_path"),
      "movement_coupling":ev.get("movement_coupling_evidence_path"),
      "reversibility":ev.get("motion_reversibility_path"),
      "continuity":ev.get("motion_continuity_path"),
      "pose_capture_plan":ev.get("pose_capture_plan_path"),
    }
    loaded={}
    for name,path in core.items():
        try:
            obj=load(base,path)
        except (OSError,json.JSONDecodeError) as exc:
            obj=None
            check(f"{name}_present",False,f"{path}: {exc}")
        else:
            check(f"{name}_present",obj is not None,path)
        loaded[name]=obj
        if obj is not None:
            got=candidate_sha(obj)
            check(f"{name}_candidate_sha",got==csha,f"expected {csha}; got {got}")

    wo=loaded["weights_only"]
    ce=loaded["coupling"]
    me=loaded["movement_coupling"]
    rev=loaded["reversibility"]
    cont=loaded["continuity"]

    if wo is not None:
        by={x["id"]:x for x in wo.get("regions",[])}
        for rid in scope.get("region_ids",[]):
            state=by.get(rid,{}).get("state")
            check(f"weights_only:{rid}",state=="CLEAR",state or "missing")

    if ce is not None:
        by={x["coupling_system_id"]:x for x in ce.get("systems",[])}
        for cid in scope.get("coupling_system_ids",[]):
            state=by.get(cid,{}).get("engineering_disposition")
            check(f"coupling:{cid}",state=="CLEAR",state or "missing")

    if me is not None:
        incomplete=[x.get("sample_id") for x in me.get("samples",[]) if x.get("state")!="COMPLETE"]
        check("movement_coupling_samples_complete",not incomplete,{"incomplete":incomplete})

    if rev is not None:
        check("motion_reversibility_clean",rev.get("overall_status")=="CLEAN",rev.get("overall_status"))

    if cont is not None:
        check("motion_continuity_engineering_review",
              ev.get("continuity_engineering_review_status")=="PASS",
              ev.get("continuity_engineering_review_status"))

    # Repair provenance has two immutable layers:
    #   pre-edit declaration -> post-edit execution record -> final candidate SHA.
    declarations=[]
    declaration_hashes=set()
    for path in ev.get("repair_declaration_paths",[]) or []:
        try:
            q=resolve(base,path)
            raw=q.read_bytes()
            obj=json.loads(raw.decode("utf-8"))
        except (OSError,json.JSONDecodeError,AttributeError) as exc:
            check(f"repair_declaration_present:{path}",False,str(exc))
            continue
        declarations.append(obj)
        digest=hashlib.sha256(raw).hexdigest()
        declaration_hashes.add(digest)
        check(f"repair_declaration_revision:{path}",obj.get("candidate_revision")==cand.get("revision"),
              obj.get("candidate_revision"))
        pre=obj.get("pre_edit_candidate_sha256") or obj.get("candidate_sha256")
        check(f"repair_declaration_pre_edit_sha:{path}",bool(SHA_RE.fullmatch(str(pre))),pre)
    declared_packages={x.get("repair_package_id") for x in declarations}
    declared_coupling={x.get("coupling_system_id") for x in declarations}
    for pid in scope.get("repair_package_ids",[]):
        check(f"repair_declaration_package:{pid}",pid in declared_packages,sorted(x for x in declared_packages if x))
        if pid in repair_by:
            cid=repair_by[pid]["coupling_system_id"]
            check(f"repair_declaration_coupling:{cid}",cid in declared_coupling,sorted(x for x in declared_coupling if x))

    executions=[]
    for path in ev.get("repair_execution_record_paths",[]) or []:
        try:
            obj=load(base,path)
        except (OSError,json.JSONDecodeError,TypeError) as exc:
            check(f"repair_execution_record_present:{path}",False,str(exc))
            continue
        executions.append(obj)
        check(f"repair_execution_final_sha:{path}",obj.get("final_candidate_sha256")==csha,
              obj.get("final_candidate_sha256"))
        check(f"repair_execution_revision:{path}",obj.get("candidate_revision")==cand.get("revision"),
              obj.get("candidate_revision"))
        check(f"repair_execution_declaration_hash:{path}",
              obj.get("repair_declaration_sha256") in declaration_hashes,
              obj.get("repair_declaration_sha256"))
    executed_packages={x.get("repair_package_id") for x in executions}
    executed_coupling={x.get("coupling_system_id") for x in executions}
    for pid in scope.get("repair_package_ids",[]):
        check(f"repair_execution_package:{pid}",pid in executed_packages,sorted(x for x in executed_packages if x))
        if pid in repair_by:
            cid=repair_by[pid]["coupling_system_id"]
            check(f"repair_execution_coupling:{cid}",cid in executed_coupling,sorted(x for x in executed_coupling if x))

    # PASS statuses for external reports are invalid without an actual,
    # candidate-bound JSON evidence file.
    for status_key,path_key in (
        ("regression_status","regression_report_path"),
        ("contact_status","contact_report_path"),
        ("change_audit_status","change_audit_path"),
    ):
        status=ev.get(status_key)
        path=ev.get(path_key)
        check(status_key,status in PASS,status)
        if status=="PASS":
            try:
                obj=load(base,path)
            except (OSError,json.JSONDecodeError,TypeError) as exc:
                check(f"{path_key}_present",False,f"{path}: {exc}")
            else:
                check(f"{path_key}_present",obj is not None,path)
                if obj is not None:
                    check(f"{path_key}_candidate_sha",candidate_sha(obj)==csha,candidate_sha(obj))

    # Visual PASS requires a candidate-bound visual review and all declared
    # capture manifests to bind to the exact candidate.
    vis_status=ev.get("visual_engineering_review_status")
    check("visual_engineering_review_status",vis_status in PASS,vis_status)
    if vis_status=="PASS":
        try:
            vis_review=load(base,ev.get("surface_visual_review_path"))
        except (OSError,json.JSONDecodeError,TypeError) as exc:
            vis_review=None
            check("surface_visual_review_present",False,str(exc))
        else:
            check("surface_visual_review_present",vis_review is not None,ev.get("surface_visual_review_path"))
        if vis_review is not None:
            check("surface_visual_review_candidate_sha",candidate_sha(vis_review)==csha,candidate_sha(vis_review))
            check("surface_visual_review_engineering_pass",vis_review.get("engineering_review")=="PASS",
                  vis_review.get("engineering_review"))
            vis_by={x.get("id"):x for x in vis_review.get("regions",[])}
            for rid in scope.get("region_ids",[]):
                state=vis_by.get(rid,{}).get("state")
                check(f"surface_visual_region:{rid}",state=="PASS",state or "missing")
        manifests=ev.get("visual_capture_manifest_paths",[]) or []
        check("visual_capture_manifests_present",bool(manifests),{"count":len(manifests)})
        for path in manifests:
            try:
                obj=load(base,path)
            except (OSError,json.JSONDecodeError) as exc:
                check(f"visual_capture_manifest:{path}",False,str(exc))
            else:
                check(f"visual_capture_manifest:{path}",candidate_sha(obj)==csha,candidate_sha(obj))

    # Scoped defect closure and no-new-blocker comparison.
    if cand_ledger is None:
        cand_block={}
    else:
        cand_block=blockers(cand_ledger)
        issues={x["id"]:x for x in cand_ledger.get("issues",[])}
        for iid in scope.get("defect_ids",[]):
            row=issues.get(iid)
            ok=bool(row) and str(row.get("state","")).lower() not in BLOCKING_STATES and bool(row.get("closure_evidence"))
            check(f"defect_closed:{iid}",ok,{
                "state":None if row is None else row.get("state"),
                "closure_evidence_count":0 if row is None else len(row.get("closure_evidence") or [])
            })

    parent_block=blockers(parent_ledger) if parent_ledger else {}
    new_blockers=sorted(set(cand_block)-set(parent_block))
    check("no_new_critical_high_blockers",not new_blockers,{"new_blockers":new_blockers})
    unresolved_scope=sorted(set(scope.get("defect_ids",[])) & set(cand_block))
    if unresolved_scope:
        warnings.append({"unresolved_scope_blockers":unresolved_scope})

    eligible=not failures
    return {
      "schema_version":1,
      "status":"CANDIDATE_COMPARISON_REPORT",
      "production_approved":False,
      "parent":parent,
      "candidate":cand,
      "scope":scope,
      "checks":checks,
      "failed_checks":failures,
      "warnings":warnings,
      "parent_open_critical_high":sorted(parent_block),
      "candidate_open_critical_high":sorted(cand_block),
      "new_open_critical_high":new_blockers,
      "engineering_clear_eligible":eligible,
      "owner_review":"PENDING",
      "production_promotion_allowed":False,
      "interpretation":"Engineering clearance eligibility only. Every PASS is evidence-bound; owner acceptance and production promotion are separate controlled gates."
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("out")
    a=ap.parse_args()
    mp=Path(a.manifest)
    try:
        man=json.loads(mp.read_text(encoding="utf-8"))
        outp=Path(a.out)
        if outp.exists():
            raise ValueError(f"refusing to overwrite {outp}")
        report=build(man,mp.parent)
        outp.parent.mkdir(parents=True,exist_ok=True)
        outp.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("CANDIDATE COMPARISON","ELIGIBLE" if report["engineering_clear_eligible"] else "BLOCKED")
        print(json.dumps({"failed_checks":report["failed_checks"],"new_blockers":report["new_open_critical_high"]},indent=2))
        return 0 if report["engineering_clear_eligible"] else 3
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
