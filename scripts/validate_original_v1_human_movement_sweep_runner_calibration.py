#!/usr/bin/env python3
"""Validate generic human movement sweep runner calibration records."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
POSE=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,require_calibrated=False):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("calibration record may not claim production approval")
    if d.get("runner_id")!="generic_human_movement_sweep_v1": raise ValueError("runner_id differs")
    adapters=d.get("adapters") or []
    spec_ids=list((read(SPEC).get("sweeps") or {}).keys())
    if [x.get("id") for x in adapters]!=spec_ids: raise ValueError("adapter order/coverage differs from execution spec")
    allowed={"NOT_RUN","IN_REVIEW","CALIBRATED","REJECTED"}
    for row in adapters:
        state=row.get("state")
        if state not in allowed: raise ValueError(f"{row.get('id')}: invalid state")
        if state=="CALIBRATED":
            for key in ("skeleton_joint_state_manifest","outbound_return_evidence","sample_order_evidence","source_hash_evidence"):
                if not row.get(key): raise ValueError(f"{row['id']}: CALIBRATED without {key}")
            if not row.get("human_evidence_review_refs"): raise ValueError(f"{row['id']}: CALIBRATED without human evidence review")
            if row["id"]=="hip_abduction_adduction" and not row.get("mirrored_input_evidence"):
                raise ValueError("hip_abduction_adduction: CALIBRATED without mirrored input evidence")
    overall=d.get("overall_state")
    if overall not in {"NOT_RUN","IN_REVIEW","CALIBRATED","REJECTED"}: raise ValueError("overall_state invalid")
    calibrated=sum(1 for x in adapters if x.get("state")=="CALIBRATED")
    if overall=="CALIBRATED":
        if calibrated!=len(adapters): raise ValueError("overall CALIBRATED before all adapters calibrated")
        for key,path in (("runner_sha256",RUNNER),("execution_spec_sha256",SPEC),("frozen_pose_source_sha256",POSE)):
            got=d.get(key); want=hashlib.sha256(path.read_bytes()).hexdigest()
            if got!=want: raise ValueError(f"{key} differs from current authority")
        if not re.fullmatch(r"r\d+[a-z]?",str(d.get("calibration_candidate_revision","")),re.I):
            raise ValueError("calibration_candidate_revision invalid")
        if not SHA_RE.fullmatch(str(d.get("calibration_candidate_sha256",""))):
            raise ValueError("calibration_candidate_sha256 invalid")
        if d.get("engineering_review")!="PASS": raise ValueError("overall CALIBRATED requires engineering review PASS")
    if require_calibrated and overall!="CALIBRATED":
        raise ValueError("runner calibration incomplete")
    return {"adapters":len(adapters),"calibrated":calibrated,"overall_state":overall}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record",nargs="?",default=str(TEMPLATE)); ap.add_argument("--require-calibrated",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(read(a.record),a.require_calibrated)
        print("HUMAN SWEEP RUNNER CALIBRATION: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
