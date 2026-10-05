"""Read-only visual capture for ORIGINAL-v1 generic human movement sweeps.

Usage:
  blender --background --factory-startup candidate.blend --python-exit-code 1 ^
    --python scripts/capture_original_v1_human_movement_sweep_visual_blender.py -- ^
    <out_dir> <candidate_revision> [sweep,sweep,...]

Reuses the exact generic sweep adapter source up to (but not including) report
execution, then renders every authoritative sample/camera. Never saves the Blend.
"""
from __future__ import annotations
import hashlib,json,math,sys,tempfile
from pathlib import Path

import bpy
from mathutils import Vector

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(ARGS)<2:
    raise SystemExit("Usage: ... -- <out_dir> <candidate_revision> [sweep,...]")
OUT=Path(ARGS[0]).resolve()
REV=ARGS[1]
ONLY=set(ARGS[2].split(",")) if len(ARGS)>2 and ARGS[2] else None
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite visual sweep directory: {OUT}")

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/"scripts/audit_original_v1_human_movement_sweeps_blender.py"
CAM_PLAN_PATH=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CAMERA_PLAN.json"
camera_plan=json.loads(CAM_PLAN_PATH.read_text(encoding="utf-8"))

# Load exactly the runner setup/motion functions, but do not execute its report loop.
runner_src=RUNNER.read_text(encoding="utf-8")
marker="result={"
if marker not in runner_src:
    raise SystemExit("Generic sweep runner report marker missing")
saved_argv=sys.argv
sys.argv=["blender","--",str(Path(tempfile.mkdtemp())/"unused_sweep_report.json")]
env={"__name__":"human_sweep_defs","__file__":str(RUNNER)}
exec(compile(runner_src[:runner_src.index(marker)],"human_sweep_defs","exec"),env)
sys.argv=saved_argv

rig=env["rig"]; body=env["body"]; apply_sample=env["apply_sample"]
spec=env["spec"]; plan=env["plan"]; pose_ns=env["ns"]
candidate=env["candidate"]; candidate_sha=env["candidate_sha"]; runner_sha=env["runner_sha"]
upd=env["upd"]
camera_plan_sha=hashlib.sha256(CAM_PLAN_PATH.read_bytes()).hexdigest()
render_script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

mask=body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport=False; mask.show_render=False
for obj in list(bpy.context.scene.objects):
    if obj.type=="MESH" and obj is not body:
        obj.hide_viewport=True; obj.hide_render=True

OUT.mkdir(parents=True)
scene=bpy.context.scene
render_cfg=camera_plan["renderer"]
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(0.78,0.66,0.58)
scene.display.shading.show_cavity=bool(render_cfg.get("show_cavity",True))
scene.display.shading.show_shadows=bool(render_cfg.get("show_shadows",True))
scene.render.resolution_x=int(render_cfg["resolution"][0])
scene.render.resolution_y=int(render_cfg["resolution"][1])
scene.render.resolution_percentage=int(render_cfg["resolution"][2])
scene.render.image_settings.file_format="PNG"

stage=bpy.data.collections.new("HGPT_SWEEP_VISUAL_STAGE_TMP")
scene.collection.children.link(stage)

# Neutral floor context for load-bearing sweeps.
floor_mat=bpy.data.materials.new("HGPT_SWEEP_VISUAL_FLOOR_MAT")
floor_mat.diffuse_color=(0.28,0.29,0.31,1.0)
bpy.ops.mesh.primitive_plane_add(size=5.0,location=(0,0,0))
floor=bpy.context.object
for col in list(floor.users_collection): col.objects.unlink(floor)
stage.objects.link(floor); floor.data.materials.append(floor_mat)

handle_mat=bpy.data.materials.new("HGPT_SWEEP_VISUAL_HANDLE_MAT")
handle_mat.diffuse_color=(0.12,0.12,0.13,1.0)

cam_data=bpy.data.cameras.new("HGPT_SWEEP_VISUAL_CAM")
cam_data.type="ORTHO"
cam=bpy.data.objects.new("HGPT_SWEEP_VISUAL_CAM",cam_data)
stage.objects.link(cam); scene.camera=cam

def clear_handles():
    for obj in [o for o in stage.objects if o.name.startswith("HGPT_SWEEP_HANDLE_")]:
        bpy.data.objects.remove(obj,do_unlink=True)

def add_handles():
    place=pose_ns.get("place_handle")
    handles=pose_ns.get("HANDLE",{})
    radius=float(pose_ns.get("HANDLE_RADIUS",0.017))
    if place is None: raise RuntimeError("frozen handle placement helper missing")
    for side in "lr":
        place(side)
    upd()
    for side,(centre,axis) in handles.items():
        c=Vector(tuple(float(x) for x in centre))
        a=Vector(tuple(float(x) for x in axis)).normalized()
        bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=0.15,location=c)
        obj=bpy.context.object; obj.name="HGPT_SWEEP_HANDLE_"+side
        for col in list(obj.users_collection): col.objects.unlink(obj)
        stage.objects.link(obj)
        obj.rotation_mode="QUATERNION"
        obj.rotation_quaternion=Vector((0,0,1)).rotation_difference(a)
        obj.data.materials.append(handle_mat)

def target_for(camera_id):
    row=camera_plan["cameras"][camera_id]
    pts=[]
    for name in row["focus_bones"]:
        pb=rig.pose.bones.get(name)
        if pb is None: raise RuntimeError(f"{camera_id}: focus bone missing {name}")
        anchor=row["anchor"]
        local=pb.head if anchor=="head" else pb.tail if anchor=="tail" else (pb.head+pb.tail)*0.5
        pts.append(rig.matrix_world@local)
    return sum(pts,Vector((0,0,0)))/len(pts)

def camera_direction(camera_id):
    row=camera_plan["cameras"][camera_id]
    a=math.radians(float(row["azimuth_deg"])); e=math.radians(float(row["elevation_deg"]))
    return Vector((-math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e))).normalized()

def matrix_rows(m):
    return [[round(float(m[r][c]),8) for c in range(4)] for r in range(4)]

selected=[x for x in spec["sweeps"] if ONLY is None or x in ONLY]
unknown=[] if ONLY is None else sorted(ONLY-set(spec["sweeps"]))
if unknown: raise SystemExit(f"Unknown sweeps requested: {unknown}")

for sweep in selected:
    authority=plan["sweeps"][sweep]
    variants=["l","r"] if sweep=="hip_abduction_adduction" else [None]
    manifest={
      "schema_version":1,
      "status":"HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE",
      "production_approved":False,
      "candidate_revision":REV,
      "candidate_sha256":candidate_sha,
      "sweep_id":sweep,
      "raw_sweep_report_path":None,
      "camera_plan_sha256":camera_plan_sha,
      "render_script_sha256":render_script_sha,
      "runner_script_sha256":runner_sha,
      "blender_version":bpy.app.version_string,
      "samples":[],
      "engineering_review":"PENDING",
      "owner_review":"PENDING"
    }
    for variant in variants:
        for sample in spec["sweeps"][sweep]["samples"]:
            apply_sample(sweep,sample,variant)
            clear_handles()
            if sweep=="grip_release":
                add_handles()
            floor_visible=sweep in {"loaded_hip_hinge","ankle_plantarflexion"}
            floor.hide_render=not floor_visible; floor.hide_viewport=not floor_visible
            views=[]
            for camera_id in authority["cameras"]:
                crow=camera_plan["cameras"][camera_id]
                target=target_for(camera_id); direction=camera_direction(camera_id)
                cam_data.ortho_scale=float(crow["ortho_scale"])
                cam.location=target+direction*8.0
                cam.rotation_mode="QUATERNION"
                cam.rotation_quaternion=(-direction).to_track_quat("-Z","Y")
                upd()
                variant_tag=(variant+"__") if variant is not None else ""
                filename=f"{sweep}__{variant_tag}{sample['label']}__{camera_id}.png"
                scene.render.filepath=str(OUT/filename)
                bpy.ops.render.render(write_still=True)
                img=OUT/filename
                views.append({
                  "camera_id":camera_id,
                  "path":filename,
                  "sha256":hashlib.sha256(img.read_bytes()).hexdigest(),
                  "capture":{
                    "candidate_sha256":candidate_sha,
                    "sweep_id":sweep,
                    "sample_label":sample["label"],
                    "variant":variant,
                    "camera_id":camera_id,
                    "runner_script_sha256":runner_sha,
                    "camera_plan_sha256":camera_plan_sha,
                    "render_script_sha256":render_script_sha,
                    "camera_matrix_world":matrix_rows(cam.matrix_world),
                    "resolution":[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],
                    "renderer":scene.render.engine,
                    "bare_body":True,
                    "floor_visible":floor_visible,
                    "generic_handle_visible":sweep=="grip_release"
                  }
                })
            manifest["samples"].append({"label":sample["label"],"variant":variant,"views":views})
    mp=OUT/f"human_movement_sweep_visual_{sweep}.json"
    mp.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("SWEEP VISUAL",sweep,"samples",len(manifest["samples"]),"views",sum(len(x["views"]) for x in manifest["samples"]))

clear_handles()
env["reset"]()
candidate_after=hashlib.sha256(candidate.read_bytes()).hexdigest()
if candidate_after!=candidate_sha:
    raise RuntimeError(f"Source Blend changed during read-only visual capture: before={candidate_sha} after={candidate_after}")
print("HUMAN MOVEMENT SWEEP VISUAL CAPTURE COMPLETE",OUT)
