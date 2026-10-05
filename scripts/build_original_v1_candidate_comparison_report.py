#!/usr/bin/env python3
"""Build one fail-closed parent->candidate whole-body comparison report."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
BLOCKING_STATES={"open","in progress","pending review","not_run","fail","blocked"}
PASS={"PASS","NOT_APPLICABLE"}

def load(base,p):
    if p is None: return None
    q=Path(p); q=q if q.is_absolute() else base/q
    return json.loads(q.read_text(encoding="utf-8"))

def blockers(ledger):
    out={}
    for x in (ledger or {}).get("issues",[]):
        if str(x.get("severity","")).lower() in {"critical","high"} and str(x.get("state","")).lower() in BLOCKING_STATES:
            out[x["id"]]=x
    return out

def build(manifest,base):
    cand=manifest["candidate"]; parent=manifest["parent"]; scope=manifest["scope"]; ev=manifest["evidence"]
    csha=str(cand.get("sha256","")); psha=str(parent.get("sha256",""))
    if not SHA_RE.fullmatch(csha): raise ValueError("candidate sha256 invalid")
    if not SHA_RE.fullmatch(psha): raise ValueError("parent sha256 invalid")
    parent_ledger=load(base,parent.get("issue_ledger_path"))
    cand_ledger=load(base,cand.get("issue_ledger_path"))
    wo=load(base,ev.get("weights_only_acceptance_path"))
    ce=load(base,ev.get("anatomical_coupling_evidence_path"))
    me=load(base,ev.get("movement_coupling_evidence_path"))
    rev=load(base,ev.get("motion_reversibility_path"))
    cont=load(base,ev.get("motion_continuity_path"))

    checks=[]; failures=[]; warnings=[]
    def check(name,ok,detail):
        checks.append({"name":name,"pass":bool(ok),"detail":detail})
        if not ok: failures.append(name)

    for name,obj in [("weights_only",wo),("coupling",ce),("movement_coupling",me),("reversibility",rev),("continuity",cont)]:
        if obj is None:
            check(f"{name}_present",False,"required evidence path missing")
        else:
            got=obj.get("candidate_sha256")
            check(f"{name}_candidate_sha",got==csha,f"expected {csha}; got {got}")

    if wo is not None:
        by={x["id"]:x for x in wo.get("regions",[])}
        for rid in scope.get("region_ids",[]):
            ok=rid in by and by[rid].get("state")=="CLEAR"
            check(f"weights_only:{rid}",ok,by.get(rid,{}).get("state","missing"))

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
        check("motion_continuity_engineering_review",ev.get("continuity_engineering_review_status")=="PASS",
              ev.get("continuity_engineering_review_status"))

    for key in ("regression_status","contact_status","visual_engineering_review_status","change_audit_status"):
        check(key,ev.get(key) in PASS,ev.get(key))

    if cand_ledger is None:
        check("candidate_issue_ledger_present",False,"missing")
        cand_block={}
    else:
        under=cand_ledger.get("candidate_under_review") or {}
        check("candidate_issue_ledger_sha",under.get("sha256")==csha,under.get("sha256"))
        cand_block=blockers(cand_ledger)
        issues={x["id"]:x for x in cand_ledger.get("issues",[])}
        for iid in scope.get("defect_ids",[]):
            row=issues.get(iid)
            ok=bool(row) and str(row.get("state","")).lower() not in BLOCKING_STATES and bool(row.get("closure_evidence"))
            check(f"defect_closed:{iid}",ok,{"state":None if row is None else row.get("state"),
                                              "closure_evidence_count":0 if row is None else len(row.get("closure_evidence") or [])})

    parent_block=blockers(parent_ledger) if parent_ledger else {}
    new_blockers=sorted(set(cand_block)-set(parent_block))
    check("no_new_critical_high_blockers",not new_blockers,{"new_blockers":new_blockers})
    unresolved_scope=sorted(set(scope.get("defect_ids",[])) & set(cand_block))
    if unresolved_scope: warnings.append({"unresolved_scope_blockers":unresolved_scope})

    eligible=not failures
    return {
      "schema_version":1,"status":"CANDIDATE_COMPARISON_REPORT","production_approved":False,
      "parent":parent,"candidate":cand,"scope":scope,
      "checks":checks,"failed_checks":failures,"warnings":warnings,
      "parent_open_critical_high":sorted(parent_block),
      "candidate_open_critical_high":sorted(cand_block),
      "new_open_critical_high":new_blockers,
      "engineering_clear_eligible":eligible,
      "owner_review":"PENDING",
      "production_promotion_allowed":False,
      "interpretation":"Engineering clearance eligibility only. Owner acceptance and production promotion are separate controlled gates."
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("out")
    a=ap.parse_args(); mp=Path(a.manifest)
    try:
        man=json.loads(mp.read_text(encoding="utf-8")); outp=Path(a.out)
        if outp.exists(): raise ValueError(f"refusing to overwrite {outp}")
        report=build(man,mp.parent); outp.parent.mkdir(parents=True,exist_ok=True)
        outp.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print("CANDIDATE COMPARISON", "ELIGIBLE" if report["engineering_clear_eligible"] else "BLOCKED")
        print(json.dumps({"failed_checks":report["failed_checks"],"new_blockers":report["new_open_critical_high"]},indent=2))
        return 0 if report["engineering_clear_eligible"] else 3
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
