#!/usr/bin/env python3
"""Fail-closed validator/evaluator for ORIGINAL-v1 shoulder anatomical acceptance."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json"
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")

def validate_contract(c:dict[str,Any])->list[str]:
    e=[]
    if c.get("schema_version")!=1:e.append("schema_version must be 1")
    if c.get("status")!="blocking":e.append("contract must be blocking")
    if c.get("applies_to",{}).get("model")!="HomeGymPT_Male_ORIGINAL_v1":e.append("model identity mismatch")
    matrix=c.get("movement_matrix",{})
    if matrix.get("shoulder_elevation_degrees")!=[0,30,60,90,120,150,"maximum_valid"]:e.append("required elevation matrix changed")
    for key in ("planes","axial_rotation","views","temporal_samples"):
        if not isinstance(matrix.get(key),list) or not matrix[key]:e.append("movement_matrix."+key+" missing")
    mg=c.get("machine_reject_gates",[]); vg=c.get("mandatory_visual_reject_gates",[])
    mids=[x.get("id") for x in mg if isinstance(x,dict)]; vids=[x.get("id") for x in vg if isinstance(x,dict)]
    if len(mids)!=len(set(mids)) or not mids:e.append("machine gate ids invalid/duplicate")
    if len(vids)!=len(set(vids)) or not vids:e.append("visual gate ids invalid/duplicate")
    if any(not re.fullmatch(r"SH-M\d{2}",str(x)) for x in mids):e.append("machine gate id format invalid")
    if any(not re.fullmatch(r"SH-V\d{2}",str(x)) for x in vids):e.append("visual gate id format invalid")
    p=c.get("promotion_rule",{})
    if p.get("fail_closed") is not True:e.append("promotion must fail closed")
    req=set(p.get("requirements",[]))
    for x in ("all_machine_reject_gates_pass","all_mandatory_visual_reject_gates_pass","weights_only_foundation_passes_before_correctives","human_anatomical_review_recorded"):
        if x not in req:e.append("missing promotion requirement "+x)
    return e

def evaluate(c:dict[str,Any],r:dict[str,Any])->dict[str,Any]:
    errors=validate_contract(c)
    if r.get("schema_version")!=1:errors.append("review schema_version must be 1")
    if r.get("candidate_revision") is None:errors.append("candidate_revision missing")
    if not SHA256_RE.fullmatch(str(r.get("candidate_sha256",""))):errors.append("candidate_sha256 invalid")
    if not SHA256_RE.fullmatch(str(r.get("parent_sha256",""))):errors.append("parent_sha256 invalid")
    machine={x.get("id"):x for x in r.get("machine_gates",[]) if isinstance(x,dict)}
    visual={x.get("id"):x for x in r.get("visual_gates",[]) if isinstance(x,dict)}
    missing_machine=[];failed_machine=[]
    for gate in c.get("machine_reject_gates",[]):
        row=machine.get(gate["id"])
        if row is None:missing_machine.append(gate["id"])
        elif row.get("pass") is not True:failed_machine.append(gate["id"])
    missing_visual=[];failed_visual=[]
    for gate in c.get("mandatory_visual_reject_gates",[]):
        row=visual.get(gate["id"])
        if row is None:missing_visual.append(gate["id"])
        elif row.get("pass") is not True:failed_visual.append(gate["id"])
        elif not isinstance(row.get("evidence_paths"),list) or not row["evidence_paths"]:failed_visual.append(gate["id"])
        elif not isinstance(row.get("review_note"),str) or not row["review_note"].strip():failed_visual.append(gate["id"])
    weights_first=r.get("weights_only_foundation_pass") is True
    human_review=r.get("human_anatomical_review_recorded") is True
    blockers=r.get("open_critical_high_linked_issues")
    blockers_ok=isinstance(blockers,list) and len(blockers)==0
    samples=r.get("movement_matrix_complete") is True
    corrective_started=r.get("residual_corrective_fitted") is True
    causal_violation=corrective_started and not weights_first
    passed=not(errors or missing_machine or failed_machine or missing_visual or failed_visual or causal_violation) and weights_first and human_review and blockers_ok and samples
    return {
      "schema_version":1,"contract_id":c.get("id"),"candidate_revision":r.get("candidate_revision"),
      "pass":passed,"production_approved":False,
      "errors":errors,"missing_machine_gates":missing_machine,"failed_machine_gates":failed_machine,
      "missing_visual_gates":missing_visual,"failed_visual_gates":failed_visual,
      "weights_only_foundation_pass":weights_first,"movement_matrix_complete":samples,
      "human_anatomical_review_recorded":human_review,"no_open_linked_blockers":blockers_ok,
      "causal_order_violation":causal_violation,
      "disposition":"ELIGIBLE_FOR_NEXT_RECOVERY_STAGE" if passed else "BLOCKED"
    }

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("review",type=Path);ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--out",type=Path);a=ap.parse_args()
    try:c=json.loads(a.contract.read_text(encoding="utf-8-sig"));r=json.loads(a.review.read_text(encoding="utf-8-sig"));out=evaluate(c,r)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print("SHOULDER ACCEPTANCE INVALID: "+str(exc));return 2
    text=json.dumps(out,indent=2)+"\n"
    if a.out:a.out.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0 if out["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
