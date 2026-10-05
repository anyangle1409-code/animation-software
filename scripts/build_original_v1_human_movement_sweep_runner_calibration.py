#!/usr/bin/env python3
"""Build an IN_REVIEW calibration record from one validated all-sweep raw report."""
from __future__ import annotations
import argparse,copy,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION_TEMPLATE.json"
SPEC=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
RAW_VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_report.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def raw_validator():
    sp=importlib.util.spec_from_file_location("raw_sweep_validator",RAW_VALIDATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def build(raw_path,revision):
    raw_path=Path(raw_path); raw=read(raw_path)
    rv=raw_validator(); rv.validate(raw,rv.read(rv.SPEC))
    spec=read(SPEC); template=read(TEMPLATE)
    if set(raw.get("sweeps",{}))!=set(spec.get("sweeps",{})):
        raise ValueError("calibration requires one raw report containing all 11 sweep adapters")
    d=copy.deepcopy(template)
    d["status"]="HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION"
    d["calibration_candidate_revision"]=revision
    d["calibration_candidate_sha256"]=raw["candidate_sha256"]
    d["runner_sha256"]=raw["runner_script_sha256"]
    d["execution_spec_sha256"]=raw["sweep_execution_spec_sha256"]
    d["frozen_pose_source_sha256"]=raw["pose_definition_sha256"]
    for adapter in d["adapters"]:
        sid=adapter["id"]; samples=raw["sweeps"][sid]["samples"]
        ref=f"{raw_path}#sweeps/{sid}"
        adapter["state"]="IN_REVIEW"
        adapter["skeleton_joint_state_manifest"]=ref+"/samples"
        adapter["outbound_return_evidence"]=ref+"/samples"
        adapter["sample_order_evidence"]=ref+"/samples"
        adapter["source_hash_evidence"]=str(raw_path)
        adapter["human_evidence_review_refs"]=[]
        if sid=="hip_abduction_adduction":
            variants={x.get("variant") for x in samples}
            adapter["mirrored_input_evidence"]=ref+"/variants" if variants=={"l","r"} else None
        adapter["automatic_checks"]={
          "raw_report_contract_validated":True,
          "sample_order_validated":[x.get("label") for x in samples]==[
              sample["label"] for sample in spec["sweeps"][sid]["samples"]
          ]* (2 if sid=="hip_abduction_adduction" else 1),
          "return_samples_present":any(bool(x.get("return_leg")) for x in samples),
          "candidate_identity_bound":raw.get("candidate_sha256")==raw.get("candidate_sha256_before")==raw.get("candidate_sha256_after")
        }
        adapter["calibration_notes"]=[
          "Automatic source/sample/identity checks passed. Human evidence review and joint-construction engineering review remain required before CALIBRATED."
        ]
    d["overall_state"]="IN_REVIEW"
    d["engineering_review"]="PENDING"
    return d

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("raw_report"); ap.add_argument("candidate_revision"); ap.add_argument("out")
    a=ap.parse_args()
    try:
        out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        d=build(a.raw_report,a.candidate_revision)
        out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("HUMAN SWEEP RUNNER CALIBRATION: IN_REVIEW")
        print(json.dumps({"candidate_revision":d["calibration_candidate_revision"],"candidate_sha256":d["calibration_candidate_sha256"],"adapters":len(d["adapters"]),"overall_state":d["overall_state"]},indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
