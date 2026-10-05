#!/usr/bin/env python3
"""Validate candidate-bound generic human movement sweep report.

The validator intentionally does not convert an uncalibrated sweep report into
an anatomical PASS/CLEAR state.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def validate(d,s):
    if d.get("schema_version")!=1 or d.get("status")!="READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT":
        raise ValueError("invalid sweep report identity")
    if d.get("production_approved") is not False: raise ValueError("sweep report may not claim production approval")
    if d.get("source_saved_or_modified") is not False: raise ValueError("sweep audit must remain read-only")
    if d.get("calibration_state")!="EXPERIMENTAL_UNCALIBRATED": raise ValueError("unexpected calibration state")
    for key in ("candidate_sha256","pose_definition_sha256","flexion_driver_sha256","movement_plan_sha256","sweep_execution_spec_sha256"):
        if not SHA_RE.fullmatch(str(d.get(key,""))): raise ValueError(f"{key} invalid")
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
    return {"sweeps":len(rows),"candidate_sha256":d["candidate_sha256"],"calibration_state":d["calibration_state"]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("report"); a=ap.parse_args()
    try:
        out=validate(read(a.report),read(SPEC)); print("HUMAN MOVEMENT SWEEP REPORT: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
