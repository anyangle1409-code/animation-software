#!/usr/bin/env python3
"""Validate and summarize fail-closed ORIGINAL-v1 Stage 1 progress."""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROGRESS=ROOT/"ORIGINAL_V1_STAGE1_PROGRESS.json"
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")
WAVE_STATES={"BLOCKED","ACTIVE","EVIDENCE_PARTIAL","CLEAR","REJECTED"}
PKG_STATES={"NOT_RUN","IN_PROGRESS","BLOCKED","CLEAR","REJECTED"}

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,g,p):
    if d.get("schema_version")!=1 or d.get("status")!="STAGE1_HUMAN_FOUNDATION_PROGRESS":
        raise ValueError("invalid Stage 1 progress identity")
    if d.get("production_approved") is not False:
        raise ValueError("progress ledger may not claim production approval")
    if d.get("master_stage")!=1:
        raise ValueError("progress ledger must remain master stage 1")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I):
        raise ValueError("candidate_revision invalid")
    if not SHA_RE.fullmatch(str(d.get("candidate_sha256",""))):
        raise ValueError("candidate_sha256 invalid")

    expected=[x["id"] for x in g.get("waves",[])]
    rows=d.get("waves") or []
    if [x.get("id") for x in rows]!=expected:
        raise ValueError("wave order/coverage differs from execution graph")
    if d.get("active_wave_id") not in expected:
        raise ValueError("active_wave_id unknown")
    pids={x["id"] for x in p.get("packages",[])}

    clear_waves=set()
    clear_packages=set()
    active_count=0
    for row,authority in zip(rows,g["waves"]):
        wid=row["id"]
        state=row.get("state")
        if state not in WAVE_STATES:
            raise ValueError(f"{wid}: invalid wave state")
        if state=="ACTIVE":
            active_count+=1
        if row.get("depends_on",[])!=(authority.get("depends_on",[]) or []):
            raise ValueError(f"{wid}: dependencies differ from authority")
        if row.get("package_ids",[])!=(authority.get("package_ids",[]) or []):
            raise ValueError(f"{wid}: package ids differ from authority")
        ps=row.get("package_statuses") or []
        if [x.get("repair_package_id") for x in ps]!=(authority.get("package_ids",[]) or []):
            raise ValueError(f"{wid}: package-status coverage differs")
        for pr in ps:
            pid=pr["repair_package_id"]
            if pid not in pids: raise ValueError(f"{wid}: unknown package {pid}")
            if pr.get("state") not in PKG_STATES: raise ValueError(f"{pid}: invalid package state")
            if pr.get("state")=="CLEAR":
                mandatory=(
                    "repair_declaration_refs","repair_execution_record_refs","weights_only_evidence_refs",
                    "coupling_evidence_refs","surface_visual_review_refs","regression_refs","comparison_report_refs"
                )
                for key in mandatory:
                    if not pr.get(key):
                        raise ValueError(f"{pid}: CLEAR without {key}")
                clear_packages.add(pid)
        if state=="CLEAR":
            if any(pr.get("state")!="CLEAR" for pr in ps):
                raise ValueError(f"{wid}: CLEAR while package not CLEAR")
            if not row.get("exit_evidence_refs"):
                raise ValueError(f"{wid}: CLEAR without exit evidence")
            deps=set(row.get("depends_on") or [])
            if not deps.issubset(clear_waves):
                raise ValueError(f"{wid}: CLEAR before dependency waves {sorted(deps-clear_waves)}")
            clear_waves.add(wid)

    if active_count>1:
        raise ValueError("more than one ACTIVE wave")
    active=d.get("active_wave_id")
    active_row=next(x for x in rows if x["id"]==active)
    if active_row.get("state")!="ACTIVE":
        raise ValueError("active_wave_id does not point to ACTIVE wave")

    # Wave 1 may be current repair focus before global preconditions have fully
    # cleared, but no Wave 1 package is allowed to CLEAR in that state.
    if active=="shoulder_yoke_foundation" and "global_foundation" not in clear_waves:
        for pr in active_row.get("package_statuses",[]):
            if pr.get("state")=="CLEAR":
                raise ValueError("shoulder package CLEAR before global foundation CLEAR")

    overall=d.get("overall") or {}
    if overall.get("waves_total")!=len(rows): raise ValueError("overall waves_total differs")
    if overall.get("packages_total")!=len(pids): raise ValueError("overall packages_total differs")
    if overall.get("waves_clear")!=len(clear_waves): raise ValueError("overall waves_clear differs")
    if overall.get("packages_clear")!=len(clear_packages): raise ValueError("overall packages_clear differs")
    if overall.get("high_detail_anatomy_allowed") is not False:
        raise ValueError("high-detail anatomy must remain false during Stage 1")
    return {
      "active_wave_id":active,
      "waves_clear":len(clear_waves),
      "packages_clear":len(clear_packages),
      "global_foundation_clear":"global_foundation" in clear_waves,
      "status":"PASS"
    }

def next_action(d,g):
    by={x["id"]:x for x in d["waves"]}
    global_row=by["global_foundation"]
    if global_row["state"]!="CLEAR":
        return {
          "action":"complete_global_pre_repair_diagnostics",
          "wave":"global_foundation",
          "reason":"Exact-candidate skinning mode, pose/tissue scope and diagnostic bundle must clear before any repair package can clear."
        }
    active=by[d["active_wave_id"]]
    pending=[x["repair_package_id"] for x in active.get("package_statuses",[]) if x.get("state")!="CLEAR"]
    if pending:
        return {"action":"execute_active_wave_packages","wave":active["id"],"pending_packages":pending}
    return {"action":"evaluate_wave_exit","wave":active["id"]}

def main():
    try:
        d=read(PROGRESS); g=read(GRAPH); p=read(PACKAGES)
        out=validate(d,g,p); out["next_action"]=next_action(d,g)
        print("STAGE1 PROGRESS: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
