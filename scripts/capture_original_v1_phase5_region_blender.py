"""Read-only real-render capture for one Phase 5 anatomy region."""
from __future__ import annotations
import hashlib, json, math, sys, tempfile
from pathlib import Path
import bpy
from mathutils import Vector

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=2: raise SystemExit("Usage: ... -- <5A-5G> <output_dir>")
REGION=argv[0]; OUT=Path(argv[1]).resolve()
if OUT.exists(): raise SystemExit("refusing to overwrite Phase 5 capture directory")
ROOT=Path(__file__).resolve().parents[1]
PLAN_PATH=ROOT/"ORIGINAL_V1_PHASE5_REGION_CAPTURE_PLAN.json"
P5_PATH=ROOT/"ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json"
plan=json.loads(PLAN_PATH.read_text(encoding="utf-8"));p5=json.loads(P5_PATH.read_text(encoding="utf-8"))
if REGION not in plan["regions"]: raise SystemExit("unsupported Phase 5 region")
caps=plan["regions"][REGION]["captures"]
if [x["id"] for x in caps]!=p5["regions"][REGION]["required_views"]: raise SystemExit("capture IDs disagree with anatomy plan")

pose_script=Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src=pose_script.read_text(encoding="utf-8")
saved_argv=sys.argv; sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"phase5_pose_defs","__file__":pose_script.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")],"phase5_pose_defs","exec"),ns)
sys.argv=saved_argv
rig,body,POSES=ns["rig"],ns["body"],ns["POSES"]
reset,upd,pb=ns["reset"],ns["upd"],ns["pb"]
palm_normal,bdir=ns["palm_normal"],ns["bdir"]
HANDLE=ns.get("HANDLE",{}); HANDLE_RADIUS=float(ns.get("HANDLE_RADIUS",0.018))
set_dressed=ns.get("set_dressed")
if set_dressed is not None: set_dressed(False)
mask=body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None: mask.show_viewport=False;mask.show_render=False

candidate_path=Path(bpy.data.filepath)
if not candidate_path.is_file(): raise SystemExit("candidate Blend has no saved source path")
candidate_sha=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
candidate_manifest=candidate_path.with_suffix(".json")
if not candidate_manifest.is_file(): raise SystemExit("candidate manifest missing")
man=json.loads(candidate_manifest.read_text(encoding="utf-8"))
if man.get("candidate_sha256")!=candidate_sha: raise SystemExit("candidate manifest SHA mismatch")

OUT.mkdir(parents=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH";scene.display.shading.light="STUDIO";scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type="WORLD";scene.display.shading.show_shadows=True
scene.display.shading.shadow_intensity=0.45;scene.display.light_direction=(-0.45,-0.35,0.82)
scene.render.resolution_x=plan["resolution"][0];scene.render.resolution_y=plan["resolution"][1];scene.render.resolution_percentage=plan["resolution"][2]
scene.render.image_settings.file_format="PNG"
if body.data.materials and body.data.materials[0] is not None: body.data.materials[0].diffuse_color=(0.78,0.66,0.58,1.0)

floor_mesh=bpy.data.meshes.new("PHASE5_REVIEW_FLOOR")
floor_mesh.from_pydata([(-0.9,-1.2,0),(0.9,-1.2,0),(0.9,0.9,0),(-0.9,0.9,0)],[],[(0,1,2,3)])
floor=bpy.data.objects.new("PHASE5_REVIEW_FLOOR",floor_mesh);scene.collection.objects.link(floor)
fm=bpy.data.materials.new("PHASE5_REVIEW_FLOOR_MAT");fm.diffuse_color=(0.30,0.31,0.33,1.0);floor_mesh.materials.append(fm)
cam_data=bpy.data.cameras.new("PHASE5_REVIEW_CAM");cam_data.type="ORTHO"
cam=bpy.data.objects.new("PHASE5_REVIEW_CAM",cam_data);scene.collection.objects.link(cam);scene.camera=cam

records=[]
def direction_for(row):
    c=row["camera"]
    if c["mode"]=="hand_surface":
        normal=palm_normal(c["side"])*(-1 if c["surface"]=="dorsal" else 1)
        if c.get("oblique"): normal+=bdir("hand_"+c["side"]).normalized()*0.35
        return (rig.matrix_world.to_3x3()@normal).normalized()
    az,el=c["angles"];a,e=math.radians(az),math.radians(el)
    return Vector((-math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
def target_for(row):
    c=row["camera"]
    if c["mode"]=="fixed": return Vector(c["centre"])
    points=[rig.matrix_world@(pb(b).head if end=="head" else pb(b).tail) for b,end in c["anchors"]]
    return sum(points,Vector((0,0,0)))/len(points)
def add_equipment():
    for side,(centre,axis) in HANDLE.items():
        bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=HANDLE_RADIUS,depth=0.13,location=Vector(centre.tolist()))
        h=bpy.context.active_object;h.name=f"PHASE5_HANDLE_{side}";h.rotation_mode="QUATERNION"
        h.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(axis.tolist()))
        hm=bpy.data.materials.new("PHASE5_HANDLE_MAT_"+side);hm.diffuse_color=(0.12,0.12,0.13,1.0);h.data.materials.append(hm)
def clear_equipment():
    for o in [o for o in bpy.data.objects if o.name.startswith("PHASE5_HANDLE_")]: bpy.data.objects.remove(o,do_unlink=True)
def crop_check():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());inv=cam.matrix_world.inverted()
    pts=[inv@(ev.matrix_world@v.co) for v in ev.data.vertices];half=cam_data.ortho_scale/2
    if any(abs(p.x)>half or abs(p.y)>half for p in pts): raise RuntimeError("fixed Phase 5 frame crops body")

for row in caps:
    pose=row["pose"]
    if pose not in POSES: raise SystemExit("capture pose missing: "+pose)
    reset();rig.location=(0,0,0);rig.rotation_euler=(0,0,0);upd();HANDLE.clear();clear_equipment()
    POSES[pose]();upd()
    if row.get("show_equipment"): add_equipment();upd()
    floor.hide_render=not bool(row.get("show_floor"));floor.hide_viewport=floor.hide_render
    target=target_for(row);direction=direction_for(row);cam_data.ortho_scale=float(row["camera"]["orthographic_scale"])
    cam.location=target+direction*8;cam.rotation_mode="QUATERNION";cam.rotation_quaternion=(-direction).to_track_quat("-Z","Y");upd()
    if row.get("whole_body"): crop_check()
    name=f"phase5_{REGION}_{row['id']}.png";scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
    p=OUT/name
    records.append({"capture_id":row["id"],"file":name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                    "capture":{"region":REGION,"capture_id":row["id"],"pose":pose,"camera":row["camera"],
                               "show_floor":bool(row.get("show_floor")),"show_equipment":bool(row.get("show_equipment")),
                               "renderer":scene.render.engine,"resolution":[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],
                               "dressed":False}})
clear_equipment();reset()
result={"schema_version":1,"status":"PHASE5_REGION_CAPTURE_COMPLETE","phase":5,"region":REGION,
        "candidate":candidate_path.name,"candidate_sha256":candidate_sha,"candidate_manifest_sha256":hashlib.sha256(candidate_manifest.read_bytes()).hexdigest(),
        "capture_plan_sha256":hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(),"pose_definition_sha256":hashlib.sha256(pose_script.read_bytes()).hexdigest(),
        "render_script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"blender_version":bpy.app.version_string,
        "images":records,"owner_review":"pending","blocking":False,"phase_complete":False,"production_approved":False}
(OUT/"render_source_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("PHASE5 REGION CAPTURE COMPLETE",REGION,len(records))
