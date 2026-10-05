"""Read-only LBS vs Preserve Volume/DQ weights-only A/B audit for ORIGINAL-v1.

Never saves the Blend and restores the original Armature modifier setting.
Corrective shape keys are disabled for both modes so the comparison isolates
base-skinning formulation while keeping rig, weights, pose and topology identical.

Usage:
  blender --background --factory-startup candidate.blend --python-exit-code 1 ^
    --python scripts/audit_original_v1_skinning_ab_blender.py -- ^
    out.json [pose,pose,...] [samples]
"""
from __future__ import annotations
import hashlib,json,math,sys,tempfile
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Quaternion,Vector

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not ARGS: raise SystemExit("Usage: ... -- out.json [pose,pose,...] [samples]")
OUT=Path(ARGS[0]).resolve()
POSE_LIST=ARGS[1].split(",") if len(ARGS)>1 and ARGS[1] else ["press_top","pullup_hang","row","curl_peak","pushup_bottom","squat_bottom","lunge"]
NS=int(ARGS[2]) if len(ARGS)>2 else 13
if NS<3: raise SystemExit("samples must be >=3")
if OUT.exists(): raise SystemExit(f"Refusing to overwrite {OUT}")

ROOT=Path(__file__).resolve().parents[1]
POSE_SCRIPT=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"
SRC=POSE_SCRIPT.read_text(encoding="utf-8")
MARK="# ---------------------------------------------------------------- metrics"
if MARK not in SRC: raise SystemExit("pose script metrics marker missing")

_saved=sys.argv
sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"pose_defs","__file__":POSE_SCRIPT.name}
exec(compile(SRC[:SRC.index(MARK)],"pose_defs","exec"),ns)
import importlib.util as _ilu
DP=POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
sp=_ilu.spec_from_file_location("original_v1_flexion_driver",str(DP))
fd=_ilu.module_from_spec(sp); sp.loader.exec_module(fd); fd.install(ns)
sys.argv=_saved

rig=ns["rig"]; body=ns["body"]; POSES=ns["POSES"]; reset=ns["reset"]; upd=ns["upd"]
mods=[m for m in body.modifiers if m.type=="ARMATURE" and m.object==rig]
if len(mods)!=1: raise SystemExit(f"expected exactly one canonical body Armature modifier, found {len(mods)}")
arm=mods[0]
original_mode=bool(arm.use_deform_preserve_volume)

if body.modifiers.get("HGPT_DRESSED_MASK") is not None:
    body.modifiers["HGPT_DRESSED_MASK"].show_viewport=False
    body.modifiers["HGPT_DRESSED_MASK"].show_render=False

candidate=Path(bpy.data.filepath)
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()

def swing_twist(q):
    v=Vector((q.x,q.y,q.z)); proj=Vector((0,1,0))*v.dot(Vector((0,1,0)))
    tw=Quaternion((q.w,proj.x,proj.y,proj.z))
    if tw.magnitude<1e-12: tw=Quaternion((1,0,0,0))
    tw.normalize(); return q@tw.inverted(),tw

def apply_fraction(final,f):
    for p in rig.pose.bones:
        q,t=final[p.name]; sw,tw=swing_twist(q)
        a=(2*math.atan2(tw.y,tw.w)+math.pi)%(2*math.pi)-math.pi
        qf=Quaternion((1,0,0,0)).slerp(sw,f) @ Quaternion((0,1,0),f*a)
        p.matrix_basis=Matrix.Translation(t*f) @ qf.to_matrix().to_4x4()
    upd()

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
        for n,v in saved.items():
            kb=sk.key_blocks.get(n)
            if kb is not None: kb.value=v
        bpy.context.view_layer.update()

def eval_surface():
    dg=bpy.context.evaluated_depsgraph_get(); ev=body.evaluated_get(dg); me=ev.to_mesh()
    try:
        P=np.array([v.co[:] for v in me.vertices],dtype=np.float64)
        me.calc_loop_triangles()
        area=float(sum(t.area for t in me.loop_triangles))
        if len(P):
            lo=P.min(axis=0); hi=P.max(axis=0); ext=hi-lo
        else:
            ext=np.zeros(3)
        return P,area,ext
    finally:
        ev.to_mesh_clear()

def top_rows(vals,limit=20):
    ids=np.argsort(vals)[-limit:][::-1]
    return [{"vertex_id":int(i),"difference_m":round(float(vals[i]),8)} for i in ids if vals[i]>0]

result={
 "schema_version":1,"status":"READ_ONLY_BASE_SKINNING_AB_AUDIT","production_approved":False,
 "candidate":candidate.name,"candidate_sha256":candidate_sha,
 "pose_definition_sha256":hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
 "driver_sha256":hashlib.sha256(DP.read_bytes()).hexdigest(),
 "original_use_deform_preserve_volume":original_mode,
 "corrective_layer":"DISABLED_FOR_BOTH_MODES",
 "samples_per_pose":NS,"poses":{},"source_saved_or_modified":False,
 "decision_rule":"Diagnostic only. Do not select LBS or Preserve Volume/DQ from numeric difference magnitude alone; inspect whole-body/regional human-reference renders and regression evidence under controlled conditions."
}

try:
    for pose_name in POSE_LIST:
        if pose_name not in POSES: raise SystemExit(f"unknown pose {pose_name}")
        reset(); rig.location=(0,0,0)
        if "HANDLE" in ns: ns["HANDLE"].clear()
        POSES[pose_name](); upd()
        final={p.name:(p.matrix_basis.to_quaternion(),p.matrix_basis.to_translation()) for p in rig.pose.bones}
        rows=[]; pose_max=0.0
        for k in range(NS):
            frac=k/(NS-1); apply_fraction(final,frac)
            saved=zero_keys()
            mode_data={}
            for pv in (False,True):
                arm.use_deform_preserve_volume=pv; bpy.context.view_layer.update()
                P,area,ext=eval_surface()
                mode_data[pv]=(P,area,ext)
            P0,a0,e0=mode_data[False]; P1,a1,e1=mode_data[True]
            if P0.shape!=P1.shape: raise SystemExit(f"{pose_name}: vertex count differs between modes")
            diff=np.linalg.norm(P1-P0,axis=1)
            mx=float(diff.max()) if len(diff) else 0.0; pose_max=max(pose_max,mx)
            rows.append({
              "fraction":round(frac,6),
              "lbs":{"surface_area_m2":round(a0,8),"bbox_extent_m":[round(float(x),8) for x in e0]},
              "preserve_volume":{"surface_area_m2":round(a1,8),"bbox_extent_m":[round(float(x),8) for x in e1]},
              "mode_surface_difference":{"max_m":round(mx,8),"p95_m":round(float(np.percentile(diff,95)) if len(diff) else 0.0,8),"p99_m":round(float(np.percentile(diff,99)) if len(diff) else 0.0,8),"mean_m":round(float(diff.mean()) if len(diff) else 0.0,8),"top_vertices":top_rows(diff)}
            })
            restore_keys(saved)
        ranked=sorted(rows,key=lambda x:x["mode_surface_difference"]["max_m"],reverse=True)
        result["poses"][pose_name]={
          "max_mode_surface_difference_m":round(pose_max,8),
          "highest_difference_fractions":[{"fraction":x["fraction"],"max_m":x["mode_surface_difference"]["max_m"]} for x in ranked[:5]],
          "samples":rows
        }
        print("SKINNING A/B",pose_name,"max difference",pose_max)
finally:
    arm.use_deform_preserve_volume=original_mode
    reset(); bpy.context.view_layer.update()

result["original_mode_restored"]=bool(arm.use_deform_preserve_volume)==original_mode
if not result["original_mode_restored"]: raise SystemExit("failed to restore original preserve-volume setting")
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("SKINNING A/B AUDIT WRITTEN",OUT)
