#!/usr/bin/env python3
"""Finalize a reviewed generic human-movement sweep runner calibration.

The input record must already contain per-adapter engineering/human review PASS
and the required human-evidence refs. This script only performs the controlled
state transition from IN_REVIEW -> CALIBRATED and re-validates the result.
"""
from __future__ import annotations
import argparse,copy,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VALIDATOR=ROOT/"scripts/validate_original_v1_human_movement_sweep_runner_calibration.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def load_validator():
    sp=importlib.util.spec_from_file_location("sweep_calibration_validator",VALIDATOR)
    if sp is None or sp.loader is None:
        raise ValueError("unable to load sweep calibration validator")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def finalize(record):
    if record.get("status")!="HUMAN_MOVEMENT_SWEEP_RUNNER_CALIBRATION":
        raise ValueError("input must be an IN_REVIEW calibration record, not the template")
    if record.get("overall_state")!="IN_REVIEW":
        raise ValueError("input calibration overall_state must be IN_REVIEW")
    if record.get("engineering_review") not in {"PENDING","PASS"}:
        raise ValueError("input overall engineering_review is not promotable")
    out=copy.deepcopy(record)
    for row in out.get("adapters") or []:
        sid=row.get("id")
        if row.get("state")!="IN_REVIEW":
            raise ValueError(f"{sid}: adapter state must be IN_REVIEW before finalization")
        if row.get("engineering_review_status")!="PASS":
            raise ValueError(f"{sid}: per-adapter engineering review PASS required")
        if row.get("human_evidence_review_status")!="PASS":
            raise ValueError(f"{sid}: per-adapter human-evidence review PASS required")
        required=set(row.get("required_human_evidence_ids") or [])
        refs=set(row.get("human_evidence_review_refs") or [])
        missing=sorted(required-refs)
        if missing:
            raise ValueError(f"{sid}: missing required human-evidence review refs {missing}")
        checks=row.get("automatic_checks") or {}
        if not checks or not all(v is True for v in checks.values()):
            raise ValueError(f"{sid}: automatic checks are not all true")
        if not row.get("calibration_notes"):
            raise ValueError(f"{sid}: calibration_notes required")
        row["state"]="CALIBRATED"
    out["overall_state"]="CALIBRATED"
    out["engineering_review"]="PASS"
    out["owner_review"]="PENDING"
    v=load_validator()
    v.validate(out,True)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("reviewed_record")
    ap.add_argument("out")
    a=ap.parse_args()
    try:
        src=Path(a.reviewed_record); dst=Path(a.out)
        if not src.is_file(): raise ValueError("reviewed calibration record not found")
        if dst.exists(): raise ValueError(f"refusing to overwrite {dst}")
        d=finalize(read(src))
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        print("HUMAN SWEEP RUNNER CALIBRATION: CALIBRATED")
        print(json.dumps({
          "candidate_revision":d["calibration_candidate_revision"],
          "candidate_sha256":d["calibration_candidate_sha256"],
          "adapters":len(d["adapters"]),
          "overall_state":d["overall_state"],
          "owner_review":d["owner_review"]
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
