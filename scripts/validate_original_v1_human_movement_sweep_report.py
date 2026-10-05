#!/usr/bin/env python3
"""Validate candidate-bound generic human movement sweep report.

The validator intentionally does not convert an uncalibrated sweep report into
an anatomical PASS/CLEAR state.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
POSE=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"
FLEXION=ROOT/"scripts/original_v1_flexion_driver.py"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,s):
    if d.get("schema_version")!=1 or d.get("status")!="READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT":
        raise ValueError("invalid sweep report identity")
    if d.get("production_approved") is not False: raise ValueError("sweep report may not claim production approval")
    if d.get("source_saved_or_modified") is not False: raise ValueError("sweep audit must remain read-only")
    if d.get("calibration_state")!="EXPERIMENTAL_UNCALIBRATED": raise ValueError("unexpected calibration state")
    if d.get("evidence_readiness")!="DIAGNOSTIC_ONLY_INCOMPLETE": raise ValueError("uncalibrated runner may not claim evidence readiness")
    for key in ("candidate_sha256","candidate_sha256_before","candidate_sha256_after","runner_script_sha256","pose_definition_sha256","flexion_driver_sha256","movement_plan_sha256","sweep_execution_spec_sha256"):
        if not SHA_RE.fullmatch(str(d.get(key,""))): raise ValueError(f"{key} invalid")
    if not (d["candidate_sha256"]==d["candidate_sha256_before"]==d["candidate_sha256_after"]):
        raise ValueError("candidate before/after identity differs")
    if not d.get("blender_version"): raise ValueError("blender_version missing")
    expected_hashes={
      "movement_plan_sha256":hashlib.sha256(PLAN.read_bytes()).hexdigest(),
      "sweep_execution_spec_sha256":hashlib.sha256(SPEC.read_bytes()).hexdigest(),
      "runner_script_sha256":hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
      "pose_definition_sha256":hashlib.sha256(POSE.read_bytes()).hexdigest(),
      "flexion_driver_sha256":hashlib.sha256(FLEXION.read_bytes()).hexdigest(),
    }
    for key,want in expected_hashes.items():
        if d.get(key)!=want: raise ValueError(f"{key} differs from current reviewed authority")
    caps=d.get("runner_capabilities") or {}
    for key in ("deterministic_joint_state_sampling","per_sample_joint_state_hash","weights_only_surface_summary","corrective_contribution_summary","runner_script_hash","end_of_run_source_rehash"):
        if caps.get(key)!="IMPLEMENTED": raise ValueError(f"runner capability missing {key}")
    for key in ("visual_capture_manifest","required_regional_renders","contact_load_state"):
        if caps.get(key)!="NOT_IMPLEMENTED": raise ValueError(f"diagnostic-only runner capability state unexpected for {key}")
    if not d.get("diagnostic_limitations"): raise ValueError("diagnostic limitations missing")
    rows=d.get("sweeps") or {}
    unknown=set(rows)-set(s.get("sweeps",{}))
    if unknown: raise ValueError(f"unknown sweeps in report {sorted(unknown)}")
    if not rows: raise ValueError("no sweeps reported")
    for name,row in rows.items():
        if row.get("engineering_review")!="PENDING" or row.get("owner_review")!="PENDING":
            raise ValueError(f"{name}: uncalibrated report may not infer review PASS")
        expected=[x["label"] for x in s["sweeps"][name]["samples"]]
        samples=row.get("samples") or []
        variants=["l","r"] if name=="hip_abduction_adduction" else [None]
        for variant in variants:
            got=[x.get("label") for x in samples if x.get("variant")==variant]
            if got!=expected: raise ValueError(f"{name}/{variant}: sample labels differ")
        for sample in samples:
            snap=sample.get("snapshot") or {}
            for layer in ("final_surface","weights_only_surface","corrective_contribution","shape_key_values","joint_state"):
                if layer not in snap: raise ValueError(f"{name}/{sample.get('label')}: snapshot missing {layer}")
            if not isinstance(snap["joint_state"],dict): raise ValueError(f"{name}: joint_state invalid")
            for key in ("joint_state_sha256","snapshot_sha256"):
                if not SHA_RE.fullmatch(str(sample.get(key,""))): raise ValueError(f"{name}/{sample.get('label')}: {key} invalid")
            spec_sample=next((x for x in s["sweeps"][name]["samples"] if x["label"]==sample.get("label")),None)
            if spec_sample is None: raise ValueError(f"{name}/{sample.get('label')}: sample absent from execution spec")
            expected_input={k:v for k,v in spec_sample.items() if k!="label"}
            if sample.get("input")!=expected_input:
                raise ValueError(f"{name}/{sample.get('label')}: input differs from execution spec")
            if bool(sample.get("return_leg"))!=bool(spec_sample.get("return_leg",False)):
                raise ValueError(f"{name}/{sample.get('label')}: return-leg flag differs from execution spec")
        if row.get("implementation_status")!=s["sweeps"][name].get("implementation_status"):
            raise ValueError(f"{name}: implementation status differs from execution spec")
        for key,report_key in (("evidence_ids","plan_evidence_ids"),("regions","plan_regions"),("cameras","plan_cameras")):
            if row.get(report_key)!=s["sweeps"][name].get(key):
                raise ValueError(f"{name}: {report_key} differs from execution spec")
        if row.get("visual_capture_status")!="NOT_IMPLEMENTED":
            raise ValueError(f"{name}: uncalibrated diagnostic runner may not claim visual capture")
        contact_required=bool(s["sweeps"][name].get("contact_load_required"))
        if bool(row.get("contact_load_required"))!=contact_required:
            raise ValueError(f"{name}: contact requirement differs from execution spec")
        expected_contact="NOT_IMPLEMENTED" if contact_required else "NOT_APPLICABLE"
        if row.get("contact_load_status")!=expected_contact:
            raise ValueError(f"{name}: contact-load status differs from diagnostic capability")
    return {"sweeps":len(rows),"candidate_sha256":d["candidate_sha256"],"calibration_state":d["calibration_state"],"evidence_readiness":d["evidence_readiness"],"visual_capture_ready":False,"contact_capture_ready":False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report"); a=ap.parse_args()
    try:
        out=validate(read(a.report),read(SPEC)); print("HUMAN MOVEMENT SWEEP REPORT: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
