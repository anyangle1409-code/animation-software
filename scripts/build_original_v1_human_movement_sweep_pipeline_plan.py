#!/usr/bin/env python3
"""Build a package-aware human-movement sweep pipeline plan."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SELECTOR=ROOT/"scripts/build_original_v1_package_validation_selection.py"
CONTACT_BEARING={"grip_release","loaded_hip_hinge","ankle_plantarflexion"}

def load_selector():
    sp=importlib.util.spec_from_file_location("package_validation_selector",SELECTOR)
    if sp is None or sp.loader is None: raise ValueError("unable to load package validation selector")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def build(package_ids):
    sel=load_selector().build(package_ids)
    if not sel.get("validation_definition_complete"):
        raise ValueError("package validation definition incomplete")
    if sel.get("sweep_only_movements_runner_unbound"):
        raise ValueError(f"required sweep runner unbound: {sel['sweep_only_movements_runner_unbound']}")
    sweeps=list(sel.get("sweep_only_movements_requiring_generic_runner") or [])
    contact=[x for x in sweeps if x in CONTACT_BEARING]
    return {
      "schema_version":1,
      "status":"HUMAN_MOVEMENT_SWEEP_PIPELINE_PLAN",
      "production_approved":False,
      "repair_package_ids":package_ids,
      "required_sweep_only_movements":sweeps,
      "contact_bearing_required_sweeps":contact,
      "runner_calibration_state":sel.get("generic_sweep_runner_calibration_state"),
      "all_11_raw_calibration_run_required":bool(sweeps),
      "visual_capture_required":bool(sweeps),
      "contact_raw_required":bool(contact),
      "review_workspace_required":bool(sweeps),
      "candidate_execution_complete_before_run":sel.get("candidate_sweep_execution_complete"),
      "rule":"If any sweep-only movement is required, calibration uses one all-11 raw report. Visual/contact/review work is then limited to the selected repair-package sweeps. Pipeline output never implies calibrated or accepted human motion."
    }

def write_text(path,text):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packages",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--sweeps-out")
    ap.add_argument("--contact-out")
    a=ap.parse_args()
    try:
        ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        if not ids: raise ValueError("repair packages required")
        d=build(ids); out=Path(a.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        if a.sweeps_out: write_text(a.sweeps_out,",".join(d["required_sweep_only_movements"])+"\n")
        if a.contact_out: write_text(a.contact_out,",".join(d["contact_bearing_required_sweeps"])+"\n")
        print("HUMAN MOVEMENT SWEEP PIPELINE PLAN: PASS")
        print(json.dumps({
          "packages":ids,
          "sweeps":d["required_sweep_only_movements"],
          "contact_sweeps":d["contact_bearing_required_sweeps"],
          "runner_calibration_state":d["runner_calibration_state"]
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
