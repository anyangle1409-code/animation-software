#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROGRESS=ROOT/"ORIGINAL_V1_STAGE1_PROGRESS.json"
GRAPH=ROOT/"ORIGINAL_V1_STAGE1_REPAIR_EXECUTION_GRAPH.json"
SWEEP_STATUS=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_STATUS.json"
PACKAGE_VALIDATION=ROOT/"scripts/build_original_v1_package_validation_selection.py"
WAVE_BUILDER=ROOT/"scripts/build_original_v1_stage1_wave_work_package.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""): h.update(chunk)
    return h.hexdigest()
def load_module(path,name):
    sp=importlib.util.spec_from_file_location(name,path)
    if sp is None or sp.loader is None: raise ValueError("unable to load "+name)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def dq(x): return '"' + str(x).replace('"','""') + '"'

def build(a):
    progress=read(PROGRESS); graph=read(GRAPH); sweep_status=read(SWEEP_STATUS)
    wave_id=progress["active_wave_id"] if a.wave=="current" else a.wave
    graph_by={x["id"]:x for x in graph["waves"]}
    if wave_id not in graph_by: raise ValueError("unknown wave "+wave_id)
    candidate=Path(a.candidate)
    if not candidate.is_file(): raise ValueError("candidate Blend not found")
    pre_sha=sha_file(candidate)
    if a.expected_sha and pre_sha!=a.expected_sha: raise ValueError("candidate SHA differs")
    if not re.fullmatch(r"r\d+[a-z]?",a.current_revision,re.I): raise ValueError("current revision invalid")
    if not re.fullmatch(r"r\d+[a-z]?",a.new_revision,re.I): raise ValueError("new revision invalid")
    if a.current_revision==a.new_revision: raise ValueError("new revision must differ")

    wp=load_module(WAVE_BUILDER,"wave_builder").build(wave_id)
    packages=wp["repair_package_ids"]
    if packages:
        validation=load_module(PACKAGE_VALIDATION,"package_validation").build(packages)
    else:
        validation={"pose_names":["neutral"],"sweep_only_movements_requiring_generic_runner":[],"sweep_only_movements_runner_unbound":[],"validation_definition_complete":True}
    if not validation.get("validation_definition_complete"): raise ValueError("validation definition incomplete")
    if validation.get("sweep_only_movements_runner_unbound"): raise ValueError("required sweep adapter unbound")

    package_csv=",".join(packages)
    sweep_csv=",".join(validation.get("sweep_only_movements_requiring_generic_runner",[]))
    commands=[]
    commands.append({"phase":"contract","command":"RUN_ORIGINAL_V1_HUMAN_BODY_GATES.bat","blocking":True})
    commands.append({"phase":"wave_packet","command":"RUN_ORIGINAL_V1_STAGE1_WAVE_WORK_PACKAGE.bat "+dq(wave_id)+" "+dq(Path(a.out_dir)/"wave"),"blocking":True})
    diag="RUN_ORIGINAL_V1_PRE_REPAIR_DIAGNOSTIC_BUNDLE.bat "+dq(candidate)+" "+dq(a.label)
    if package_csv: diag+=" "+dq(package_csv)
    commands.append({"phase":"pre_repair_diagnostics","command":diag,"blocking":True})

    calibration_required=sweep_status.get("runner_calibration_state")!="CALIBRATED"
    sweep_pipeline_label=a.label+"_sweep_pipeline"
    sweep_pipeline_dir=Path("ORIGINAL_V1_WORK/candidates/repair_checks/human_movement_sweep_pipeline")/sweep_pipeline_label
    cal_in_review=sweep_pipeline_dir/"runner_calibration_IN_REVIEW.json"
    cal_final=sweep_pipeline_dir/"runner_calibration_CALIBRATED.json"
    if sweep_csv:
        commands.append({
          "phase":"sweep_pipeline_prepare",
          "command":"RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PIPELINE.bat "+dq(candidate)+" "+dq(a.current_revision)+" "+dq(package_csv)+" "+dq(sweep_pipeline_label),
          "blocking":True
        })
        if calibration_required:
            commands.append({
              "phase":"sweep_calibration_review_and_finalize",
              "command":"Review every adapter in "+str(cal_in_review)+"; set per-adapter engineering/human review PASS with required refs, then run RUN_ORIGINAL_V1_FINALIZE_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat "+dq(cal_in_review)+" "+dq(cal_final),
              "blocking":True,
              "review_gate":True
            })
    if package_csv:
        commands.append({"phase":"repair_workspace","command":"RUN_ORIGINAL_V1_CREATE_REPAIR_WORKSPACE.bat "+dq(package_csv)+" "+dq(a.new_revision)+" "+dq(pre_sha)+" "+dq(a.side)+" "+dq(a.source_branch)+" "+dq(a.workspace),"blocking":True})
        commands.append({"phase":"declaration_review","command":"Complete/validate repair_declaration files and run coupling-weight audit before any edit.","blocking":True,"review_gate":True})
        commands.append({"phase":"model_edit_boundary","command":"Begin the smallest declared Blender repair only after all previous gates are satisfied.","blocking":False})

    return {
      "schema_version":1,
      "status":"STAGE1_LAPTOP_PICKUP_PLAN",
      "production_approved":False,
      "generated_without_blender":True,
      "wave_id":wave_id,
      "wave_name":graph_by[wave_id]["name"],
      "current_candidate":{"path":str(candidate),"revision":a.current_revision,"sha256":pre_sha},
      "new_candidate_revision":a.new_revision,
      "source_branch":a.source_branch,
      "side":a.side,
      "repair_package_ids":packages,
      "selected_pose_names":validation.get("pose_names",[]),
      "required_sweep_only_movements":validation.get("sweep_only_movements_requiring_generic_runner",[]),
      "sweep_runner_calibration_state":sweep_status.get("runner_calibration_state"),
      "sweep_runner_calibration_required":calibration_required,
      "sweep_pipeline_label":sweep_pipeline_label,
      "sweep_pipeline_dir":str(sweep_pipeline_dir),
      "calibrated_sweep_runner_record":str(cal_final) if sweep_csv and calibration_required else None,
      "workspace":a.workspace,
      "post_edit_continuation_command_template":"RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat "+dq(a.workspace)+" <final-candidate.blend> "+dq(a.new_revision)+" "+dq(a.current_revision)+" <fresh-post-label> <calibration-record-or-empty> <fresh-post-plan-dir>",
      "commands":commands,
      "stop_conditions":[
        "human-body gate failure",
        "candidate SHA mismatch",
        "required sweep adapter unbound",
        "required sweep calibration still in review",
        "required sweep pipeline preparation failure",
        "incomplete repair declaration",
        "edit exceeds declared scope",
        "newer local Work candidate/evidence not preserved"
      ],
      "note":"Non-Blender orchestration only. The first model edit is deliberately the final command boundary. Immediately after saving the new candidate, generate the post-edit continuation packet using post_edit_continuation_command_template."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--current-revision",required=True)
    ap.add_argument("--new-revision",required=True)
    ap.add_argument("--source-branch",required=True)
    ap.add_argument("--side",required=True,choices=["l","r","bilateral","midline"])
    ap.add_argument("--label",required=True)
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--wave",default="current")
    ap.add_argument("--expected-sha")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        d=build(a)
        out=Path(a.out_dir)
        if out.exists() and any(out.iterdir()): raise ValueError("output directory is not empty")
        out.mkdir(parents=True,exist_ok=True)
        (out/"laptop_pickup_plan.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        lines=["# ORIGINAL v1 Stage 1 laptop pickup","", "Wave: "+d["wave_id"]+" - "+d["wave_name"], "Current SHA: "+d["current_candidate"]["sha256"], "Packages: "+(", ".join(d["repair_package_ids"]) or "none"), "", "## Run order",""]
        for i,row in enumerate(d["commands"],1):
            lines.append(str(i)+". "+row["phase"])
            lines.append("   "+row["command"])
            if row.get("review_gate"): lines.append("   REVIEW GATE - do not skip")
        (out/"laptop_pickup_plan.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        print("STAGE1 LAPTOP PICKUP PLAN: READY")
        print(json.dumps({"wave":d["wave_id"],"candidate_sha256":d["current_candidate"]["sha256"],"packages":d["repair_package_ids"],"commands":len(d["commands"])},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
