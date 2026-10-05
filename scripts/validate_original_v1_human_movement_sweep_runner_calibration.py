#!/usr/bin/env python3
"""Validate generic human movement sweep runner calibration records."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
POSE=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_report.py"
HUMAN=ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(p):
    q=Path(p)
    return q if q.is_absolute() else ROOT/q
def load_module(path,name):
    sp=importlib.util.spec_from_file_location(name,path)
    if sp is None or sp.loader is None: raise ValueError(f"unable to load {name}")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def expected_auto_checks(raw,sid,spec_data):
    samples=raw["sweeps"][sid]["samples"]
    labels=[x.get("label") for x in samples]
    expected=[x["label"] for x in spec_data["sweeps"][sid]["samples"]]
    if sid=="hip_abduction_adduction":
        expected=expected*2
    return {
      "raw_report_contract_validated":True,
      "sample_order_validated":labels==expected,
      "return_samples_present":any(bool(x.get("return_leg")) for x in samples),
      "candidate_identity_bound":raw.get("candidate_sha256")==raw.get("candidate_sha256_before")==raw.get("candidate_sha256_after"),
    }

def validate(d,require_calibrated=False):
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("calibration record may not claim production approval")
    if d.get("runner_id")!="generic_human_movement_sweep_v1": raise ValueError("runner_id differs")
    adapters=d.get("adapters") or []
    spec_data=read(SPEC)
    spec_ids=list((spec_data.get("sweeps") or {}).keys())
    if [x.get("id") for x in adapters]!=spec_ids: raise ValueError("adapter order/coverage differs from execution spec")
    allowed={"NOT_RUN","IN_REVIEW","CALIBRATED","REJECTED"}
    overall=d.get("overall_state")
    if overall not in allowed: raise ValueError("overall_state invalid")

    raw=None; raw_path=None
    if overall in {"IN_REVIEW","CALIBRATED"} or any(x.get("state") in {"IN_REVIEW","CALIBRATED"} for x in adapters):
        rp=d.get("raw_sweep_report_path")
        if not rp: raise ValueError("calibration record missing raw_sweep_report_path")
        raw_path=resolve(rp)
        if not raw_path.is_file(): raise ValueError("calibration raw sweep report missing")
        raw_bytes=raw_path.read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest()!=d.get("raw_sweep_report_sha256"):
            raise ValueError("calibration raw sweep report SHA mismatch")
        raw=json.loads(raw_bytes.decode("utf-8"))
        rv=load_module(RAW_VALIDATOR,"original_v1_raw_sweep_validator")
        rv.validate(raw,rv.read(rv.SPEC))
        if set(raw.get("sweeps",{}))!=set(spec_ids):
            raise ValueError("calibration raw report must contain all 11 sweep adapters")
        if raw.get("candidate_sha256")!=d.get("calibration_candidate_sha256"):
            raise ValueError("calibration candidate differs from raw sweep report")
        for key,path in (("runner_sha256",RUNNER),("execution_spec_sha256",SPEC),("frozen_pose_source_sha256",POSE)):
            want=hashlib.sha256(path.read_bytes()).hexdigest()
            if d.get(key)!=want: raise ValueError(f"{key} differs from current authority")
        if d.get("runner_sha256")!=raw.get("runner_script_sha256"):
            raise ValueError("runner_sha256 differs from raw sweep report")
        if d.get("execution_spec_sha256")!=raw.get("sweep_execution_spec_sha256"):
            raise ValueError("execution_spec_sha256 differs from raw sweep report")
        if d.get("frozen_pose_source_sha256")!=raw.get("pose_definition_sha256"):
            raise ValueError("frozen_pose_source_sha256 differs from raw sweep report")
        if not re.fullmatch(r"r\d+[a-z]?",str(d.get("calibration_candidate_revision","")),re.I):
            raise ValueError("calibration_candidate_revision invalid")
        if not SHA_RE.fullmatch(str(d.get("calibration_candidate_sha256",""))):
            raise ValueError("calibration_candidate_sha256 invalid")

    known_human={x["id"] for x in read(HUMAN).get("entries",[])}
    calibrated=0
    for row in adapters:
        sid=row["id"]; state=row.get("state")
        if state not in allowed: raise ValueError(f"{sid}: invalid state")
        required=list(spec_data["sweeps"][sid].get("evidence_ids") or [])
        if row.get("required_human_evidence_ids")!=required:
            raise ValueError(f"{sid}: required human evidence differs from execution spec")
        unknown_refs=sorted(set(row.get("human_evidence_review_refs") or [])-known_human)
        if unknown_refs: raise ValueError(f"{sid}: unknown human evidence review refs {unknown_refs}")
        if row.get("engineering_review_status") not in {"PENDING","PASS","FAIL"}:
            raise ValueError(f"{sid}: engineering_review_status invalid")
        if row.get("human_evidence_review_status") not in {"PENDING","PASS","FAIL"}:
            raise ValueError(f"{sid}: human_evidence_review_status invalid")
        checks=row.get("automatic_checks") or {}
        for key in ("raw_report_contract_validated","sample_order_validated","return_samples_present","candidate_identity_bound"):
            if key not in checks: raise ValueError(f"{sid}: automatic check missing {key}")
        if state in {"IN_REVIEW","CALIBRATED"}:
            if raw is None: raise ValueError(f"{sid}: {state} without raw calibration report")
            expected_checks=expected_auto_checks(raw,sid,spec_data)
            if checks!=expected_checks:
                raise ValueError(f"{sid}: automatic checks differ from raw report")
            ref_prefix=f"{d.get('raw_sweep_report_path')}#sweeps/{sid}"
            for key in ("skeleton_joint_state_manifest","outbound_return_evidence","sample_order_evidence"):
                ref=row.get(key)
                if not isinstance(ref,str) or not ref.startswith(ref_prefix):
                    raise ValueError(f"{sid}: {state} {key} is not bound to raw report sweep")
            if row.get("source_hash_evidence")!=d.get("raw_sweep_report_path"):
                raise ValueError(f"{sid}: source_hash_evidence differs from raw report path")
            if sid=="hip_abduction_adduction":
                ref=row.get("mirrored_input_evidence")
                if not isinstance(ref,str) or not ref.startswith(ref_prefix):
                    raise ValueError("hip_abduction_adduction: mirrored input evidence not bound to raw report")
        if state=="CALIBRATED":
            calibrated+=1
            if row.get("engineering_review_status")!="PASS":
                raise ValueError(f"{sid}: CALIBRATED without per-adapter engineering review PASS")
            if row.get("human_evidence_review_status")!="PASS":
                raise ValueError(f"{sid}: CALIBRATED without per-adapter human-evidence review PASS")
            if not all(checks.get(k) is True for k in checks):
                raise ValueError(f"{sid}: CALIBRATED with incomplete automatic checks")
            refs=set(row.get("human_evidence_review_refs") or [])
            missing=set(required)-refs
            if missing: raise ValueError(f"{sid}: CALIBRATED without human evidence review {sorted(missing)}")
    if overall=="CALIBRATED":
        if calibrated!=len(adapters): raise ValueError("overall CALIBRATED before all adapters calibrated")
        if d.get("engineering_review")!="PASS": raise ValueError("overall CALIBRATED requires engineering review PASS")
    elif calibrated==len(adapters):
        raise ValueError("all adapters calibrated but overall_state is not CALIBRATED")
    if require_calibrated and overall!="CALIBRATED":
        raise ValueError("runner calibration incomplete")
    return {
      "adapters":len(adapters),
      "calibrated":calibrated,
      "overall_state":overall,
      "raw_report_bound":raw is not None,
      "calibration_candidate_sha256":d.get("calibration_candidate_sha256")
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("record",nargs="?",default=str(TEMPLATE)); ap.add_argument("--require-calibrated",action="store_true")
    a=ap.parse_args()
    try:
        out=validate(read(a.record),a.require_calibrated)
        print("HUMAN SWEEP RUNNER CALIBRATION: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
