#!/usr/bin/env python3
"""Build an exact Stage-1 wave work package from the authoritative graph/progress."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
PROGRESS=ROOT/"ORIGINAL_V1_STAGE1_PROGRESS.json"
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
DEFECTS=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def load_module(filename):
    p=ROOT/"scripts"/filename
    s=importlib.util.spec_from_file_location(filename.replace(".py",""),p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def build(wave_id):
    graph=read(GRAPH); progress=read(PROGRESS); packages=read(PACKAGES); defects=read(DEFECTS)
    gby={x["id"]:x for x in graph["waves"]}; pby={x["id"]:x for x in progress["waves"]}
    if wave_id=="current": wave_id=progress["active_wave_id"]
    if wave_id not in gby: raise ValueError(f"unknown Stage 1 wave {wave_id}")
    wave=gby[wave_id]; prow=pby[wave_id]
    deps=wave.get("depends_on",[]) or []
    dep_states={x:pby[x]["state"] for x in deps}
    deps_clear=all(state=="CLEAR" for state in dep_states.values())
    package_ids=wave.get("package_ids",[]) or []

    out={
      "schema_version":1,"status":"STAGE1_WAVE_WORK_PACKAGE","production_approved":False,
      "wave":{"index":wave["wave"],"id":wave_id,"name":wave["name"],"state":prow["state"]},
      "dependencies":dep_states,"dependencies_clear":deps_clear,
      "repair_package_ids":package_ids,
      "required_integrated_movements":wave.get("required_integrated_movements",[]) or [],
      "exit_requirements":wave.get("exit",[]) or [],
      "editing_allowed":bool(package_ids) and deps_clear and wave_id!="whole_body_integration",
      "diagnostic_capture_allowed":True,
      "owner_review":"PENDING"
    }

    if not package_ids:
        out["scope"]={"coupling_system_ids":[],"body_regions":[],"defect_ids":[]}
        out["validation"]={
          "pose_names":["neutral"],
          "deterministic_sweeps":[],
          "sweep_only_movements_requiring_generic_runner":[],
          "validation_definition_complete":True
        }
        out["commands"]=[
          "RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat",
          "RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat <candidate.blend> <fresh-label> <next-wave-package-ids>",
          "Do not mark global_foundation CLEAR until exact-candidate skinning mode, pose/tissue scope, reversibility, continuity and diagnostic identity are committed."
        ]
        return out

    validation_mod=load_module("build_original_v1_package_validation_selection.py")
    evidence_mod=load_module("build_original_v1_repair_evidence_brief.py")
    regression_mod=load_module("build_original_v1_repair_regression_plan.py")
    validation=validation_mod.build(package_ids)
    evidence=evidence_mod.build(package_ids)
    regression=regression_mod.build(package_ids)

    package_by={x["id"]:x for x in packages["packages"]}
    selected_coupling=[package_by[x]["coupling_system_id"] for x in package_ids]
    selected_set=set(selected_coupling)
    closure_defects=[
      row["issue_id"] for row in defects.get("mappings",[])
      if set(row.get("required_coupling_system_ids",[]))
      and set(row.get("required_coupling_system_ids",[])).issubset(selected_set)
    ]
    out["scope"]={
      "coupling_system_ids":selected_coupling,
      "body_regions":regression["body_regions"],
      "closure_eligible_defect_ids":closure_defects,
      "regression_linked_defect_ids":regression["linked_defect_ids"],
      "focused_neighbor_coupling_system_ids":regression["focused_neighbor_coupling_system_ids"]
    }
    out["validation"]={
      "pose_names":validation["pose_names"],
      "pose_csv":validation["pose_csv"],
      "proof_movement_families":validation["proof_movement_families"],
      "deterministic_sweeps":validation["deterministic_sweep_names"],
      "sweep_only_movements_requiring_generic_runner":validation["sweep_only_movements_requiring_generic_runner"],
      "sweep_only_movements_runner_bound":validation["sweep_only_movements_runner_bound"],
      "sweep_only_movements_runner_unbound":validation["sweep_only_movements_runner_unbound"],
      "sweep_movements_requiring_candidate_execution":validation["sweep_movements_requiring_candidate_execution"],
      "generic_sweep_runner_calibration_state":validation["generic_sweep_runner_calibration_state"],
      "validation_definition_complete":validation["validation_definition_complete"],
      "validation_execution_path_complete":validation["validation_execution_path_complete"],
      "candidate_sweep_execution_complete":validation["candidate_sweep_execution_complete"],
      "fully_runnable_via_frozen_pose_harness":validation["fully_runnable_via_frozen_pose_harness"]
    }
    out["human_evidence_brief"]=evidence
    out["regression_plan"]=regression
    out["commands"]=[
      f"RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat <candidate.blend> <fresh-label> {','.join(package_ids)}",
      (f"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat <candidate.blend> <fresh-pre-repair-sweep-label> \"{','.join(validation['sweep_only_movements_requiring_generic_runner'])}\"" if validation["sweep_only_movements_requiring_generic_runner"] else "No separate sweep-only movements required for this package set."),
      f"RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat {','.join(package_ids)} <new-revision> <pre-edit-sha256> <side> <source-branch> <fresh-workspace-dir>",
      "Complete and validate every generated repair_declaration_*.json before any edit.",
      "Run RUN_ORIGINAL_V1_COUPLING_WEIGHT_AUDIT.bat for every generated declaration.",
      "Make only the smallest declared earliest-layer repair and save a NEW candidate.",
      "RUN_ORIGINAL_V1_FINALIZE_REPAIR_WORKSPACE.bat <workspace-dir> <final-candidate.blend>",
      "RUN_ORIGINAL_V1_POST_REPAIR_VALIDATION_BUNDLE.bat <revision> <prior-revision-or-dash> <workspace-dir> <fresh-label>",
      (f"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEPS.bat <final-candidate.blend> <fresh-post-repair-sweep-label> \"{','.join(validation['sweep_only_movements_requiring_generic_runner'])}\"" if validation["sweep_only_movements_requiring_generic_runner"] else "No separate sweep-only movements required for this package set."),
      "Complete weights-only/coupling/movement/surface/execution/regression/contact/change evidence against the exact final SHA.",
      "RUN_ORIGINAL_V1_CANDIDATE_COMPARISON.bat <workspace-dir>\\candidate_comparison_manifest_post_repair.json <fresh-comparison-report.json>",
      "Do not advance the wave until every exit requirement has committed candidate-bound evidence."
    ]
    out["blocking_preconditions"]=[]
    if not deps_clear:
        out["blocking_preconditions"].append({
          "type":"DEPENDENCY_WAVES_NOT_CLEAR",
          "waves":[k for k,v in dep_states.items() if v!="CLEAR"]
        })
    if validation["sweep_only_movements_runner_unbound"]:
        out["blocking_preconditions"].append({
          "type":"GENERIC_SWEEP_RUNNER_UNBOUND",
          "movements":validation["sweep_only_movements_runner_unbound"],
          "note":"A deterministic sweep definition exists but no bound Blender adapter exists. Package clearance is impossible until the adapter is bound."
        })
    if validation["sweep_only_movements_requiring_generic_runner"] and validation["generic_sweep_runner_calibration_state"]!="CALIBRATED":
        out["blocking_preconditions"].append({
          "type":"GENERIC_SWEEP_RUNNER_CALIBRATION_REQUIRED",
          "movements":validation["sweep_only_movements_requiring_generic_runner"],
          "note":"The generic runner is bound, but remains PREPARED_UNCALIBRATED. Blender calibration/review is required before sweep evidence can support package clearance."
        })
    if validation["sweep_movements_requiring_candidate_execution"]:
        out["blocking_preconditions"].append({
          "type":"GENERIC_SWEEP_CANDIDATE_EXECUTION_REQUIRED",
          "movements":validation["sweep_movements_requiring_candidate_execution"],
          "note":"Runner binding does not count as evidence. These sweeps must run against the exact candidate and produce reviewed candidate-bound evidence."
        })
    out["interpretation"]="This package is execution planning only. It never marks a repair package, wave, owner review or production state clear."
    return out

def markdown(d):
    lines=[
      f"# Stage 1 wave {d['wave']['index']} — {d['wave']['name']}",
      "",
      f"Wave ID: {d['wave']['id']}",
      f"Progress state: {d['wave']['state']}",
      f"Dependencies clear: {'YES' if d['dependencies_clear'] else 'NO'}",
      f"Editing allowed by dependency graph: {'YES' if d['editing_allowed'] else 'NO'}",
      "",
      "## Scope",""
    ]
    lines.append("- Repair packages: "+(", ".join(d["repair_package_ids"]) if d["repair_package_ids"] else "none — global diagnostics"))
    for key,label in (("coupling_system_ids","Coupling systems"),("body_regions","Body regions"),("closure_eligible_defect_ids","Closure-eligible defects"),("regression_linked_defect_ids","Regression-linked defects")):
        vals=d.get("scope",{}).get(key,[])
        lines.append(f"- {label}: "+(", ".join(vals) if vals else "none"))
    lines += ["","## Validation",""]
    v=d["validation"]
    lines.append("- Frozen poses: "+", ".join(v.get("pose_names",[])))
    lines.append("- Deterministic sweeps: "+(", ".join(v.get("deterministic_sweeps",[])) or "none"))
    gap=v.get("sweep_only_movements_requiring_generic_runner",[])
    lines.append("- Sweep-only movements using the separate Blender sweep runner: "+(", ".join(gap) or "none"))
    lines.append("- Generic sweep runner calibration state: "+str(v.get("generic_sweep_runner_calibration_state","n/a")))
    lines.append("- Sweep movements still needing candidate execution: "+(", ".join(v.get("sweep_movements_requiring_candidate_execution",[])) or "none"))
    if d.get("blocking_preconditions"):
        lines += ["","## Blocking preconditions",""]
        for row in d["blocking_preconditions"]:
            lines.append(f"- {row['type']}: "+", ".join(row.get("waves") or row.get("movements") or []))
    lines += ["","## Exact operator sequence",""]
    for i,x in enumerate(d["commands"],1): lines.append(f"{i}. {x}")
    lines += ["","## Wave exit",""]
    for x in d["exit_requirements"]: lines.append(f"- {x}")
    lines += ["","> This work package is planning authority only. Engineering clearance, owner review and production approval remain separate.",""]
    return "\n".join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--wave",default="current")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    a=ap.parse_args()
    try:
        d=build(a.wave)
        if a.out_json:
            p=Path(a.out_json)
            if p.exists(): raise ValueError(f"refusing to overwrite {p}")
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        if a.out_md:
            p=Path(a.out_md)
            if p.exists(): raise ValueError(f"refusing to overwrite {p}")
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(markdown(d),encoding="utf-8")
        print("STAGE1 WAVE WORK PACKAGE: PASS")
        print(json.dumps({"wave":d["wave"],"packages":d["repair_package_ids"],"blocking_preconditions":d.get("blocking_preconditions",[])},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
