"""Read-only raw contact/load capture for contact-bearing human movement sweeps.

Usage:
  blender --background --factory-startup candidate.blend --python-exit-code 1 ^
    --python scripts/audit_original_v1_human_movement_sweep_contact_blender.py -- ^
    <out_dir> <candidate_revision> [sweep,sweep,...]

Produces immutable raw measurements only. It never assigns LEGITIMATE_CONTACT,
REQUIRED_CLEARANCE, PASS or FAIL classifications.
"""
from __future__ import annotations
import hashlib,json,sys,tempfile
from pathlib import Path

import bpy
import numpy as np

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(ARGS)<2:
    raise SystemExit("Usage: ... -- <out_dir> <candidate_revision> [sweep,...]")
OUT=Path(ARGS[0]).resolve(); REV=ARGS[1]
ONLY=set(ARGS[2].split(",")) if len(ARGS)>2 and ARGS[2] else None
if OUT.exists(): raise SystemExit(f"Refusing to overwrite contact output directory: {OUT}")

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
REQ_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"
requirements=json.loads(REQ_PATH.read_text(encoding="utf-8"))

runner_src=RUNNER.read_text(encoding="utf-8")
marker="result={"
if marker not in runner_src: raise SystemExit("Generic sweep runner report marker missing")
saved_argv=sys.argv
sys.argv=["blender","--",str(Path(tempfile.mkdtemp())/"unused_contact_sweep.json")]
env={"__name__":"human_sweep_contact_defs","__file__":str(RUNNER)}
exec(compile(runner_src[:runner_src.index(marker)],"human_sweep_contact_defs","exec"),env)
sys.argv=saved_argv

rig=env["rig"]; body=env["body"]; apply_sample=env["apply_sample"]
spec=env["spec"]; pose_ns=env["ns"]; candidate=env["candidate"]
candidate_sha=env["candidate_sha"]; runner_sha=env["runner_sha"]
upd=env["upd"]
contact_req_sha=hashlib.sha256(REQ_PATH.read_bytes()).hexdigest()
capture_script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

owners=pose_ns["bone_vertex_sets"]()
evaluated_positions=pose_ns["evaluated_positions"]
place_handle=pose_ns["place_handle"]
handle_distance=pose_ns["handle_distance"]
HANDLE=pose_ns["HANDLE"]
HANDLE_RADIUS=float(pose_ns["HANDLE_RADIUS"])

def ids_for(prefixes,side):
    ids=set()
    for bone,verts in owners.items():
        if not bone.endswith("_"+side): continue
        if any(bone.startswith(prefix) for prefix in prefixes):
            ids.update(int(x) for x in verts)
    return sorted(ids)

def stats(values):
    a=np.asarray(values,dtype=np.float64)
    if a.size==0: return {"count":0}
    return {
      "count":int(a.size),
      "min_m":round(float(a.min()),7),
      "p05_m":round(float(np.percentile(a,5)),7),
      "p50_m":round(float(np.percentile(a,50)),7),
      "p95_m":round(float(np.percentile(a,95)),7),
      "max_m":round(float(a.max()),7)
    }

def grip_measurement(side):
    place_handle(side); upd()
    ids=ids_for(("index_","middle_","ring_","pinky_","thumb_"),side)
    if not ids: raise RuntimeError(f"no finger/thumb vertices for side {side}")
    P=evaluated_positions(ids)
    d=handle_distance(P,side)
    centre,axis=HANDLE[side]
    return {
      "vertex_count":len(ids),
      "signed_distance_to_handle_surface_m":stats(d),
      "vertices_inside_handle":int((d<0).sum()),
      "vertices_within_3mm_of_surface":int((np.abs(d)<=0.003).sum()),
      "handle_radius_m":HANDLE_RADIUS,
      "handle_center_m":[round(float(x),7) for x in centre],
      "handle_axis":[round(float(x),7) for x in axis]
    }

def floor_measurement(side,prefixes):
    ids=ids_for(prefixes,side)
    if not ids: raise RuntimeError(f"no floor-contact vertices for {prefixes}/{side}")
    P=evaluated_positions(ids); z=P[:,2]
    return {
      "vertex_count":len(ids),
      "z_to_floor_m":stats(z),
      "vertices_below_floor":int((z<0).sum()),
      "vertices_within_3mm_of_floor":int((np.abs(z)<=0.003).sum()),
      "vertices_within_6mm_of_floor":int((np.abs(z)<=0.006).sum())
    }

selected=set(requirements["sweeps"]) if ONLY is None else ONLY
unknown=sorted(selected-set(requirements["sweeps"]))
if unknown: raise SystemExit(f"Requested sweeps are not contact-bearing: {unknown}")
OUT.mkdir(parents=True)

for sweep in requirements["sweeps"]:
    if sweep not in selected: continue
    authority=requirements["sweeps"][sweep]
    report={
      "schema_version":1,
      "status":"READ_ONLY_HUMAN_MOVEMENT_SWEEP_CONTACT_RAW",
      "production_approved":False,
      "candidate_revision":REV,
      "candidate_sha256":candidate_sha,
      "candidate_sha256_before":candidate_sha,
      "candidate_sha256_after":None,
      "sweep_id":sweep,
      "runner_script_sha256":runner_sha,
      "capture_script_sha256":capture_script_sha,
      "contact_requirements_sha256":contact_req_sha,
      "blender_version":bpy.app.version_string,
      "source_saved_or_modified":None,
      "samples":[],
      "classification_state":"RAW_MEASUREMENTS_ONLY",
      "engineering_review":"PENDING",
      "owner_review":"PENDING"
    }
    for sample in spec["sweeps"][sweep]["samples"]:
        apply_sample(sweep,sample,None)
        domains={}
        if sweep=="grip_release":
            domains["finger_thumb_to_equipment"]={
              "left":grip_measurement("l"),
              "right":grip_measurement("r")
            }
            domains["wrist_forearm_load_path"]={
              "left_forearm":floor_measurement("l",("forearm_","hand_")),
              "right_forearm":floor_measurement("r",("forearm_","hand_")),
              "note":"z values are geometry reference only; this domain is not a floor-contact classification."
            }
        elif sweep=="loaded_hip_hinge":
            domains["left_foot_to_floor"]=floor_measurement("l",("foot_","toe_"))
            domains["right_foot_to_floor"]=floor_measurement("r",("foot_","toe_"))
        elif sweep=="ankle_plantarflexion":
            domains["left_forefoot_to_floor"]=floor_measurement("l",("toe_",))
            domains["right_forefoot_to_floor"]=floor_measurement("r",("toe_",))
            domains["left_heel_to_floor"]=floor_measurement("l",("foot_",))
            domains["right_heel_to_floor"]=floor_measurement("r",("foot_",))
        joint_state=env["active_joint_state"]()
        report["samples"].append({
          "label":sample["label"],
          "input":{k:v for k,v in sample.items() if k!="label"},
          "return_leg":bool(sample.get("return_leg",False)),
          "joint_state_sha256":hashlib.sha256(json.dumps(joint_state,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest(),
          "domains":domains
        })
    path=OUT/f"human_movement_sweep_contact_raw_{sweep}.json"
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("SWEEP RAW CONTACT",sweep,"samples",len(report["samples"]))

env["reset"]()
candidate_after=hashlib.sha256(candidate.read_bytes()).hexdigest()
for path in OUT.glob("human_movement_sweep_contact_raw_*.json"):
    d=json.loads(path.read_text(encoding="utf-8"))
    d["candidate_sha256_after"]=candidate_after
    d["source_saved_or_modified"]=candidate_after!=candidate_sha
    path.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
if candidate_after!=candidate_sha:
    raise RuntimeError(f"Source Blend changed during read-only contact audit: before={candidate_sha} after={candidate_after}")
print("HUMAN MOVEMENT SWEEP RAW CONTACT COMPLETE",OUT)
