"""Read-only generic human movement sweep audit for ORIGINAL-v1.

This runner is deliberately separate from the frozen P3a stress-pose script.
It imports only the frozen pose-definition/helper section, constructs audit
motions from ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json, evaluates
weights-only and final-corrected surfaces, and NEVER saves the Blend.

Until Blender calibration is completed, this report is diagnostic evidence only
and may not set an anatomical PASS/CLEAR state.
"""
from __future__ import annotations
import hashlib,json,math,sys,tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix,Quaternion,Vector

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not ARGS:
    raise SystemExit("Usage: ... -- <out.json> [sweep,sweep,...] [evidence_root] [candidate_revision]")
OUT=Path(ARGS[0]).resolve()
ONLY=set(ARGS[1].split(",")) if len(ARGS)>1 and ARGS[1] else None
EVIDENCE_ROOT=Path(ARGS[2]).resolve() if len(ARGS)>2 and ARGS[2] else None
CANDIDATE_REVISION=ARGS[3] if len(ARGS)>3 and ARGS[3] else None
if EVIDENCE_ROOT is not None and not CANDIDATE_REVISION:
    raise SystemExit("candidate_revision required when evidence_root is supplied")
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")

RUNNER_PATH=Path(__file__).resolve()
ROOT=RUNNER_PATH.parents[1]
SPEC_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_EXECUTION_SPEC.json"
PLAN_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
CAMERA_PLAN_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CAMERA_PLAN.json"
CONTACT_REQ_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"
POSE_SCRIPT=Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
spec=json.loads(SPEC_PATH.read_text(encoding="utf-8"))
plan=json.loads(PLAN_PATH.read_text(encoding="utf-8"))
camera_plan=json.loads(CAMERA_PLAN_PATH.read_text(encoding="utf-8"))
contact_requirements=json.loads(CONTACT_REQ_PATH.read_text(encoding="utf-8"))

src=POSE_SCRIPT.read_text(encoding="utf-8")
marker="# ---------------------------------------------------------------- metrics"
if marker not in src:
    raise SystemExit("Frozen pose-definition marker missing")
_saved=sys.argv
sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"pose_defs","__file__":POSE_SCRIPT.name}
exec(compile(src[:src.index(marker)],"pose_test_defs","exec"),ns)
sys.argv=_saved

import importlib.util as _ilu
_driver_path=POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
_sp=_ilu.spec_from_file_location("original_v1_flexion_driver",str(_driver_path))
_fd=_ilu.module_from_spec(_sp); _sp.loader.exec_module(_fd); _fd.install(ns)

rig=ns["rig"]; body=ns["body"]; reset=ns["reset"]; upd=ns["upd"]
rot=ns["rot"]; aim=ns["aim"]; lat=ns["lat"]; bdir=ns["bdir"]
girdle_for_elevation=ns["girdle_for_elevation"]
external_rotation_for_elevation=ns["external_rotation_for_elevation"]
hinge_humerus=ns["hinge_humerus"]; grip=ns["grip"]
pb=ns["pb"]; place_handle=ns["place_handle"]; close_on_handle=ns["close_on_handle"]
handle_distance=ns["handle_distance"]; bone_vertex_sets=ns["bone_vertex_sets"]
HANDLE=ns["HANDLE"]; HANDLE_RADIUS=ns["HANDLE_RADIUS"]
F=ns["F"]; U=ns["U"]; D=ns["D"]; X=ns["X"]
if body.modifiers.get("HGPT_DRESSED_MASK") is not None:
    body.modifiers["HGPT_DRESSED_MASK"].show_viewport=False
    body.modifiers["HGPT_DRESSED_MASK"].show_render=False

candidate=Path(bpy.data.filepath).resolve()
if not candidate.is_file():
    raise SystemExit("Candidate Blend path unavailable")
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
runner_sha=hashlib.sha256(RUNNER_PATH.read_bytes()).hexdigest()

region_names=json.loads(bpy.context.scene["hgpt_region_names"])
vreg=np.array([d.value for d in body.data.attributes["hgpt_region"].data],dtype=np.int32)
OWNERS=bone_vertex_sets()

scene=bpy.context.scene
cam=None
cam_data=None
floor=None
if EVIDENCE_ROOT is not None:
    if EVIDENCE_ROOT.exists():
        raise SystemExit(f"Refusing to reuse evidence_root {EVIDENCE_ROOT}")
    EVIDENCE_ROOT.mkdir(parents=True,exist_ok=False)
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type="WORLD"
    scene.display.shading.show_shadows=True
    scene.display.shading.shadow_intensity=0.45
    scene.display.light_direction=(-0.45,-0.35,0.82)
    if body.data.materials and body.data.materials[0] is not None:
        body.data.materials[0].diffuse_color=(0.78,0.66,0.58,1.0)
    floor_mesh=bpy.data.meshes.new("SWEEP_REVIEW_FLOOR")
    floor_mesh.from_pydata([(-1.2,-1.5,0),(1.2,-1.5,0),(1.2,1.1,0),(-1.2,1.1,0)],[],[(0,1,2,3)])
    floor=bpy.data.objects.new("SWEEP_REVIEW_FLOOR",floor_mesh)
    floor_mat=bpy.data.materials.new("SWEEP_REVIEW_FLOOR_MAT")
    floor_mat.diffuse_color=(0.30,0.31,0.33,1.0)
    floor_mesh.materials.append(floor_mat); scene.collection.objects.link(floor)
    cam_data=bpy.data.cameras.new("SWEEP_REVIEW_CAM"); cam_data.type="ORTHO"
    cam=bpy.data.objects.new("SWEEP_REVIEW_CAM",cam_data); scene.collection.objects.link(cam); scene.camera=cam
    res=camera_plan["renderer"]["resolution"]
    scene.render.resolution_x=int(res[0]); scene.render.resolution_y=int(res[1]); scene.render.resolution_percentage=int(res[2])
    scene.render.image_settings.file_format="PNG"

def _safe(s):
    return str(s).replace("%","pct").replace("/","_").replace("\\","_").replace(" ","_")

def _clear_review_handles():
    for o in [o for o in list(bpy.data.objects) if o.name.startswith("SWEEP_HANDLE_")]:
        bpy.data.objects.remove(o,do_unlink=True)

def _materialize_handles():
    _clear_review_handles()
    for s,(centre,axis) in HANDLE.items():
        bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=HANDLE_RADIUS,depth=0.13,location=Vector(centre.tolist()))
        h=bpy.context.active_object; h.name=f"SWEEP_HANDLE_{s}"
        h.rotation_mode="QUATERNION"; h.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis.tolist()))
        hm=bpy.data.materials.new(f"SWEEP_HANDLE_MAT_{s}"); hm.diffuse_color=(0.12,0.12,0.13,1.0); h.data.materials.append(hm)

def _camera_target(cfg):
    pts=[]
    for bone_name in cfg["focus_bones"]:
        p=pb(bone_name)
        local=p.head if cfg.get("anchor")=="head" else (p.head+p.tail)*0.5
        pts.append(rig.matrix_world @ local)
    return sum(pts,Vector((0,0,0)))/len(pts)

def _render_view(sweep,label,variant,camera_id):
    cfg=camera_plan["cameras"][camera_id]
    target=_camera_target(cfg)
    a=math.radians(float(cfg["azimuth_deg"])); e=math.radians(float(cfg["elevation_deg"]))
    direction=Vector((-math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
    cam_data.ortho_scale=float(cfg["ortho_scale"])
    cam.location=target+direction*8
    cam.rotation_mode="QUATERNION"; cam.rotation_quaternion=(-direction).to_track_quat("-Z","Y")
    upd()
    variant_dir=_safe(variant if variant is not None else "default")
    out_dir=EVIDENCE_ROOT/"visual"/sweep/variant_dir/_safe(label)
    out_dir.mkdir(parents=True,exist_ok=True)
    path=out_dir/f"{_safe(camera_id)}.png"
    if path.exists(): raise RuntimeError(f"Refusing to overwrite visual evidence {path}")
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {
      "camera_id":camera_id,
      "path":str(path.relative_to(EVIDENCE_ROOT/"visual"/sweep)),
      "sha256":digest,
      "capture":{
        "candidate_sha256":candidate_sha,
        "sweep_id":sweep,
        "sample_label":label,
        "camera_id":camera_id,
        "variant":variant,
        "runner_script_sha256":runner_sha,
        "camera_plan_sha256":hashlib.sha256(CAMERA_PLAN_PATH.read_bytes()).hexdigest(),
        "camera_matrix_world":[[round(float(v),8) for v in row] for row in cam.matrix_world],
        "orthographic_scale":float(cam_data.ortho_scale),
        "resolution":[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],
        "engine":scene.render.engine,
        "bare_body":True
      }
    }

def _owned_positions(names):
    ids=sorted({i for name in names for i in OWNERS.get(name,[])})
    if not ids: return ids,np.empty((0,3),dtype=np.float64)
    return ids,ns["evaluated_positions"](ids)

def _z_stats(names):
    ids,P=_owned_positions(names)
    if not len(ids): return {"vertex_count":0}
    z=P[:,2]
    return {
      "vertex_count":len(ids),
      "min_z_m":round(float(z.min()),7),
      "p05_z_m":round(float(np.percentile(z,5)),7),
      "vertices_below_floor":int((z<0).sum()),
      "vertices_within_2mm_floor":int((np.abs(z)<=0.002).sum())
    }

def _contact_measurements(sweep,label,variant):
    rec={"label":label,"variant":variant,"domains":{}}
    if sweep=="grip_release":
        ns["OWNERS"]=OWNERS
        per_side={}
        wrist_state={}
        for s,long_side in (("l","left"),("r","right")):
            if s in HANDLE:
                metrics=ns["grip_metrics"](s)
                per_side[long_side]={
                  "max_penetration_mm":metrics["max_penetration_mm"],
                  "contact_vertices_within_2mm":metrics["contact_vertices_within_2mm"],
                  "finger_vertices":metrics["finger_vertices"]
                }
            wrist_state[long_side]={
              "forearm_direction":[round(float(x),7) for x in bdir(f"forearm_{s}")],
              "hand_direction":[round(float(x),7) for x in bdir(f"hand_{s}")]
            }
        rec["domains"]["finger_thumb_to_equipment"]={"per_side":per_side}
        rec["domains"]["wrist_forearm_load_path"]={"per_side":wrist_state}
    elif sweep=="loaded_hip_hinge":
        for s,long_side in (("l","left"),("r","right")):
            rec["domains"][f"{long_side}_foot_to_floor"]=_z_stats([f"foot_{s}",f"toe_{s}"])
    elif sweep=="ankle_plantarflexion":
        for s,long_side in (("l","left"),("r","right")):
            rec["domains"][f"{long_side}_forefoot_to_floor"]=_z_stats([f"toe_{s}"])
            rec["domains"][f"{long_side}_heel_to_floor"]=_z_stats([f"foot_{s}"])
            foot=pb(f"foot_{s}")
            rec["domains"][f"{long_side}_heel_to_floor"]["foot_bone_head_z_m"]=round(float((rig.matrix_world@foot.head).z),7)
            rec["domains"][f"{long_side}_heel_to_floor"]["foot_bone_tail_z_m"]=round(float((rig.matrix_world@foot.tail).z),7)
    return rec

def eval_positions():
    dg=bpy.context.evaluated_depsgraph_get()
    ev=body.evaluated_get(dg); mesh=ev.to_mesh()
    try:
        mw=ev.matrix_world
        return np.array([(mw @ v.co)[:] for v in mesh.vertices],dtype=np.float64)
    finally:
        ev.to_mesh_clear()

def key_values():
    sk=body.data.shape_keys
    if sk is None: return {}
    return {k.name:float(k.value) for k in sk.key_blocks if k.name!="Basis"}

def zero_keys():
    sk=body.data.shape_keys; saved={}
    if sk is not None:
        for k in sk.key_blocks:
            if k.name!="Basis":
                saved[k.name]=float(k.value); k.value=0.0
        bpy.context.view_layer.update()
    return saved

def restore_keys(saved):
    sk=body.data.shape_keys
    if sk is not None:
        for name,val in saved.items():
            kb=sk.key_blocks.get(name)
            if kb is not None: kb.value=val
        bpy.context.view_layer.update()

reset(); rig.location=(0,0,0); upd()
REST=eval_positions()

def region_summary(P):
    rows={}
    for rid,name in enumerate(region_names):
        mask=vreg==rid
        if not np.any(mask): continue
        Q=P[mask]
        rows[name]={
          "vertex_count":int(mask.sum()),
          "centroid":[round(float(x),6) for x in Q.mean(axis=0)],
          "aabb_min":[round(float(x),6) for x in Q.min(axis=0)],
          "aabb_max":[round(float(x),6) for x in Q.max(axis=0)],
          "max_displacement_from_neutral_m":round(float(np.linalg.norm(Q-REST[mask],axis=1).max()),7),
        }
    return rows

def active_joint_state():
    rows={}
    for p in rig.pose.bones:
        q=p.matrix_basis.to_quaternion()
        t=p.matrix_basis.to_translation()
        if p.name=="root" or q.rotation_difference(Quaternion((1,0,0,0))).angle>1e-7 or t.length>1e-9:
            rows[p.name]={
              "quat_wxyz":[round(float(q.w),8),round(float(q.x),8),round(float(q.y),8),round(float(q.z),8)],
              "translation":[round(float(x),8) for x in t],
            }
    return rows

def surface_snapshot():
    final=eval_positions(); keys=key_values()
    saved=zero_keys(); weights=eval_positions(); restore_keys(saved)
    corr=final-weights
    return {
      "final_surface":{"min_z":round(float(final[:,2].min()),7),"max_displacement_from_neutral_m":round(float(np.linalg.norm(final-REST,axis=1).max()),7),"regions":region_summary(final)},
      "weights_only_surface":{"min_z":round(float(weights[:,2].min()),7),"max_displacement_from_neutral_m":round(float(np.linalg.norm(weights-REST,axis=1).max()),7),"regions":region_summary(weights)},
      "corrective_contribution":{"max_m":round(float(np.linalg.norm(corr,axis=1).max()),7),"p99_m":round(float(np.percentile(np.linalg.norm(corr,axis=1),99)),7)},
      "shape_key_values":{k:round(v,8) for k,v in sorted(keys.items())},
      "joint_state":active_joint_state(),
    }

def distributed_trunk(axis,amount,shares=(0.12,0.28,0.30,0.30)):
    for name,share in zip(("pelvis","spine_01","spine_02","spine_03"),shares):
        rot(name,axis,amount*share)

def shoulder_abduction(deg):
    th=math.radians(deg)
    for s in "lr":
        target=(D*math.cos(th)+lat(s)*math.sin(th)).normalized()
        girdle_for_elevation(s,target)
        aim(f"upperarm_{s}",target)
        external_rotation_for_elevation(s)

def humeral_rotation(deg):
    shoulder_abduction(45.0)
    for s in "lr":
        sign=1.0 if s=="r" else -1.0
        rot(f"upperarm_{s}",bdir(f"upperarm_{s}"),deg*sign)

def forearm_rotation(deg):
    for s in "lr":
        aim(f"upperarm_{s}",D)
        hinge_humerus(s,F)
        aim(f"forearm_{s}",F)
        sign=1.0 if s=="r" else -1.0
        rot(f"forearm_{s}",bdir(f"forearm_{s}"),deg*sign)

def trunk_flex(frac):
    # Conservative audit target: 42 degrees distributed, not a production ROM limit.
    distributed_trunk(X,42.0*frac)
    rot("neck",X,-10.0*frac)

def trunk_extend(frac):
    distributed_trunk(X,-24.0*frac)
    rot("neck",X,6.0*frac)

def trunk_lateral(frac):
    distributed_trunk(F,28.0*frac,(0.08,0.27,0.31,0.34))

def trunk_rotate(deg):
    distributed_trunk(U,deg,(0.10,0.25,0.30,0.35))

def hip_hinge(frac):
    # Scaled version of the already-used bent-over validation construction.
    rot("pelvis",X,34.0*frac)
    rot("spine_01",X,4.0*frac); rot("spine_02",X,3.0*frac); rot("spine_03",X,3.0*frac)
    rot("neck",X,-24.0*frac)
    for s in "lr":
        aim(f"thigh_{s}",(D+F*(0.28*frac)).normalized())
        aim(f"shin_{s}",(D+F*(0.12*frac)).normalized())
        aim(f"foot_{s}",(F+D*(0.18*frac)).normalized())

def hip_ab_ad(frac,side):
    s=side
    # Single-side frontal-plane audit; positive = abduction, negative = adduction.
    max_deg=35.0 if frac>=0 else 20.0
    deg=max_deg*abs(frac)
    axis=F
    sign=(-1.0 if s=="l" else 1.0) * (1.0 if frac>=0 else -1.0)
    rot(f"thigh_{s}",axis,deg*sign)

def ankle_plantar(frac):
    for s in "lr":
        target=(F+D*(0.65*frac)).normalized()
        aim(f"foot_{s}",target)
        aim(f"toe_{s}",F)

def grip_release(frac):
    for s in "lr":
        aim(f"forearm_{s}",F+D*0.2)
        place_handle(s)
        if frac>=0.999:
            close_on_handle(s)
        else:
            grip(s,max(0.0,min(1.0,frac)))

def apply_sample(name,row,variant=None):
    reset(); rig.location=(0,0,0); rig.rotation_euler=(0,0,0); upd()
    HANDLE.clear(); _clear_review_handles()
    if name=="shoulder_abduction_elevation": shoulder_abduction(float(row["elevation_deg"]))
    elif name=="humeral_internal_external_rotation": humeral_rotation(float(row["rotation_deg"]))
    elif name=="forearm_pronation_supination": forearm_rotation(float(row["rotation_deg"]))
    elif name=="trunk_flexion": trunk_flex(float(row["fraction"]))
    elif name=="trunk_extension": trunk_extend(float(row["fraction"]))
    elif name=="trunk_lateral_bend": trunk_lateral(float(row["fraction"]))
    elif name=="trunk_axial_rotation": trunk_rotate(float(row["rotation_deg"]))
    elif name=="loaded_hip_hinge": hip_hinge(float(row["fraction"]))
    elif name=="hip_abduction_adduction": hip_ab_ad(float(row["fraction"]),variant)
    elif name=="ankle_plantarflexion": ankle_plantar(float(row["fraction"]))
    elif name=="grip_release": grip_release(float(row["fraction"]))
    else: raise RuntimeError(f"unsupported sweep {name}")
    upd()

result={
 "schema_version":1,
 "status":"READ_ONLY_GENERIC_HUMAN_MOVEMENT_SWEEP_AUDIT",
 "production_approved":False,
 "candidate":candidate.name,
 "candidate_sha256":candidate_sha,
 "candidate_sha256_before":candidate_sha,
 "candidate_sha256_after":None,
 "runner_script_sha256":runner_sha,
 "blender_version":bpy.app.version_string,
 "pose_definition_sha256":hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
 "flexion_driver_sha256":hashlib.sha256(_driver_path.read_bytes()).hexdigest(),
 "movement_plan_sha256":hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(),
 "sweep_execution_spec_sha256":hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
 "source_saved_or_modified":None,
 "calibration_state":"EXPERIMENTAL_UNCALIBRATED",
 "evidence_readiness":"DIAGNOSTIC_ONLY_INCOMPLETE",
 "runner_capabilities":{
   "deterministic_joint_state_sampling":"IMPLEMENTED",
   "per_sample_joint_state_hash":"IMPLEMENTED",
   "weights_only_surface_summary":"IMPLEMENTED",
   "corrective_contribution_summary":"IMPLEMENTED",
   "runner_script_hash":"IMPLEMENTED",
   "end_of_run_source_rehash":"IMPLEMENTED",
   "visual_capture_manifest":"NOT_IMPLEMENTED",
   "required_regional_renders":"NOT_IMPLEMENTED",
   "contact_load_state":"NOT_IMPLEMENTED"
 },
 "diagnostic_limitations":[
   "The raw sweep report is diagnostic motion/surface evidence only; visual capture is produced by the separate dedicated visual runner.",
   "Contact/load evidence is produced by the separate dedicated raw-contact runner and never auto-classifies LEGITIMATE_CONTACT or REQUIRED_CLEARANCE.",
   "Audit joint ranges remain provisional until Blender calibration/review.",
   "This output cannot close a human visual, contact, coupling or Stage-1 acceptance gate by itself."
 ],
 "interpretation":"Diagnostic sampling only. Binding/execution proves that a deterministic audit motion ran; it does not by itself prove anatomical realism or authorize PASS/CLEAR.",
 "sweeps":{}
}

visual_manifests={}
raw_contact_reports={}

for name,cfg in spec["sweeps"].items():
    if ONLY and name not in ONLY: continue
    if name not in plan["sweeps"]:
        raise SystemExit(f"{name}: execution spec has no movement-plan authority")
    samples=[]
    variants=["l","r"] if name=="hip_abduction_adduction" else [None]
    for variant in variants:
        for row in cfg["samples"]:
            apply_sample(name,row,variant)
            if name=="grip_release" and EVIDENCE_ROOT is not None:
                _materialize_handles()
            snap=surface_snapshot()
            views=[]
            if EVIDENCE_ROOT is not None:
                for camera_id in plan["sweeps"][name]["cameras"]:
                    views.append(_render_view(name,row["label"],variant,camera_id))
                visual_manifests.setdefault(name,[]).append({
                  "label":row["label"],"variant":variant,"views":views
                })
                if name in contact_requirements.get("sweeps",{}):
                    raw_contact_reports.setdefault(name,[]).append(_contact_measurements(name,row["label"],variant))
            joint_state_bytes=json.dumps(snap["joint_state"],sort_keys=True,separators=(",",":")).encode("utf-8")
            snapshot_bytes=json.dumps(snap,sort_keys=True,separators=(",",":")).encode("utf-8")
            rec={
              "label":row["label"],
              "return_leg":bool(row.get("return_leg",False)),
              "input":{k:v for k,v in row.items() if k!="label"},
              "variant":variant,
              "joint_state_sha256":hashlib.sha256(joint_state_bytes).hexdigest(),
              "snapshot_sha256":hashlib.sha256(snapshot_bytes).hexdigest(),
              "snapshot":snap,
            }
            samples.append(rec)
    contact_bearing=name in {"grip_release","loaded_hip_hinge","ankle_plantarflexion"}
    result["sweeps"][name]={
      "implementation_status":cfg["implementation_status"],
      "plan_evidence_ids":plan["sweeps"][name]["evidence_ids"],
      "plan_regions":plan["sweeps"][name]["regions"],
      "plan_cameras":plan["sweeps"][name]["cameras"],
      "samples":samples,
      "visual_capture_status":"NOT_IMPLEMENTED",
      "contact_load_required":contact_bearing,
      "contact_load_status":"NOT_IMPLEMENTED" if contact_bearing else "NOT_APPLICABLE",
      "engineering_review":"PENDING",
      "owner_review":"PENDING",
    }
    print("HUMAN SWEEP",name,"samples",len(samples))

if EVIDENCE_ROOT is not None:
    for sweep,rows in visual_manifests.items():
        out_dir=EVIDENCE_ROOT/"visual"/sweep
        manifest={
          "schema_version":1,
          "status":"HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE",
          "production_approved":False,
          "candidate_revision":CANDIDATE_REVISION,
          "candidate_sha256":candidate_sha,
          "sweep_id":sweep,
          "raw_sweep_report_path":str(OUT),
          "samples":rows,
          "engineering_review":"PENDING",
          "owner_review":"PENDING",
          "rules":[
            "Captured images are raw visual evidence and do not grant anatomical PASS.",
            "Engineering review must compare all required samples/cameras against the declared human evidence before setting PASS."
          ]
        }
        (out_dir/"visual_capture_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    for sweep,rows in raw_contact_reports.items():
        out_dir=EVIDENCE_ROOT/"contact"/sweep
        out_dir.mkdir(parents=True,exist_ok=True)
        raw={
          "schema_version":1,
          "status":"RAW_HUMAN_MOVEMENT_SWEEP_CONTACT_MEASUREMENTS",
          "production_approved":False,
          "candidate_revision":CANDIDATE_REVISION,
          "candidate_sha256":candidate_sha,
          "sweep_id":sweep,
          "contact_requirements_sha256":hashlib.sha256(CONTACT_REQ_PATH.read_bytes()).hexdigest(),
          "runner_script_sha256":runner_sha,
          "samples":rows,
          "interpretation":"Raw geometry measurements only. No contact/clearance classification is inferred."
        }
        (out_dir/"raw_contact_measurements.json").write_text(json.dumps(raw,indent=2)+"\n",encoding="utf-8")

reset(); _clear_review_handles()
candidate_sha_after=hashlib.sha256(candidate.read_bytes()).hexdigest()
result["candidate_sha256_after"]=candidate_sha_after
result["source_saved_or_modified"]=candidate_sha_after!=candidate_sha
if result["source_saved_or_modified"]:
    raise RuntimeError(f"Source Blend changed during read-only sweep audit: before={candidate_sha} after={candidate_sha_after}")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("GENERIC HUMAN MOVEMENT SWEEP AUDIT",OUT,"sweeps",len(result["sweeps"]))
