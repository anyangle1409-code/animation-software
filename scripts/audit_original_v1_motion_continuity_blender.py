"""Read-only dense motion-continuity audit for ORIGINAL-v1.

Never saves the Blend. Samples each pose densely and reports where evaluated
surface motion or corrective contribution changes most sharply. This is a
diagnostic report, not an anatomical pass/fail threshold.
"""
from __future__ import annotations
import hashlib,json,math,sys,tempfile
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Quaternion,Vector

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not ARGS: raise SystemExit("Usage: ... -- <out.json> [pose,pose,...] [samples]")
OUT=Path(ARGS[0]).resolve()
POSE_LIST=ARGS[1].split(",") if len(ARGS)>1 and ARGS[1] else ["press_top","pullup_hang","row","curl_peak","pushup_bottom","squat_bottom","lunge"]
NS=int(ARGS[2]) if len(ARGS)>2 else 61
if NS<5: raise SystemExit("samples must be >=5")
if OUT.exists(): raise SystemExit(f"Refusing to overwrite {OUT}")

POSE_SCRIPT=Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
SRC=POSE_SCRIPT.read_text(encoding="utf-8"); MARK="# ---------------------------------------------------------------- metrics"
_saved=sys.argv; sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"pose_defs","__file__":POSE_SCRIPT.name}
exec(compile(SRC[:SRC.index(MARK)],"pose_test_defs","exec"),ns)
import importlib.util as _ilu
DP=POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
sp=_ilu.spec_from_file_location("original_v1_flexion_driver",str(DP)); mod=_ilu.module_from_spec(sp); sp.loader.exec_module(mod); mod.install(ns)
sys.argv=_saved
rig=ns["rig"]; body=ns["body"]; POSES=ns["POSES"]; reset=ns["reset"]; upd=ns["upd"]
if body.modifiers.get("HGPT_DRESSED_MASK") is not None:
    body.modifiers["HGPT_DRESSED_MASK"].show_viewport=False
    body.modifiers["HGPT_DRESSED_MASK"].show_render=False

candidate=Path(bpy.data.filepath)
sha=hashlib.sha256(candidate.read_bytes()).hexdigest()

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

def eval_pos():
    dg=bpy.context.evaluated_depsgraph_get(); ev=body.evaluated_get(dg); me=ev.to_mesh()
    try: return np.array([v.co[:] for v in me.vertices],dtype=np.float64)
    finally: ev.to_mesh_clear()

def key_vals():
    sk=body.data.shape_keys
    return {} if sk is None else {k.name:float(k.value) for k in sk.key_blocks if k.name!="Basis"}

def zero_keys():
    sk=body.data.shape_keys
    saved={}
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

def top_rows(values,limit=20):
    ids=np.argsort(values)[-limit:][::-1]
    return [{"vertex_id":int(i),"value_m":round(float(values[i]),7)} for i in ids]

result={
 "schema_version":1,"status":"READ_ONLY_MOTION_CONTINUITY_REPORT",
 "candidate":candidate.name,"candidate_sha256":sha,
 "pose_definition_sha256":hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
 "driver_sha256":hashlib.sha256(DP.read_bytes()).hexdigest(),
 "samples":NS,"poses":{},"source_saved_or_modified":False,
 "interpretation":"Report-only. Large local first/second differences identify candidate popping or abrupt deformation zones for visual review; no anatomical pass is inferred."
}

for pose in POSE_LIST:
    if pose not in POSES: raise SystemExit(f"unknown pose {pose}")
    reset(); rig.location=(0,0,0)
    if "HANDLE" in ns: ns["HANDLE"].clear()
    POSES[pose](); upd()
    final={p.name:(p.matrix_basis.to_quaternion(),p.matrix_basis.to_translation()) for p in rig.pose.bones}
    Pf=[]; Pw=[]; K=[]
    for k in range(NS):
        f=k/(NS-1); apply_fraction(final,f)
        K.append(key_vals()); Pf.append(eval_pos())
        saved=zero_keys(); Pw.append(eval_pos()); restore_keys(saved)
    Pf=np.stack(Pf); Pw=np.stack(Pw)
    step_final=np.linalg.norm(np.diff(Pf,axis=0),axis=2)
    step_weights=np.linalg.norm(np.diff(Pw,axis=0),axis=2)
    corr=Pf-Pw
    step_corr=np.linalg.norm(np.diff(corr,axis=0),axis=2)
    accel_final=np.linalg.norm(Pf[2:]-2*Pf[1:-1]+Pf[:-2],axis=2)
    accel_corr=np.linalg.norm(corr[2:]-2*corr[1:-1]+corr[:-2],axis=2)
    max_step_by_v=step_final.max(axis=0); max_accel_by_v=accel_final.max(axis=0)
    max_corr_step_by_v=step_corr.max(axis=0); max_corr_accel_by_v=accel_corr.max(axis=0)
    rows=[]
    for i in range(NS):
        rows.append({"fraction":round(i/(NS-1),6),"shape_key_values":{n:round(v,8) for n,v in sorted(K[i].items())}})
    result["poses"][pose]={
      "final_surface_max_step_m":round(float(step_final.max()),7),
      "weights_only_max_step_m":round(float(step_weights.max()),7),
      "corrective_contribution_max_step_m":round(float(step_corr.max()),7),
      "final_surface_max_second_difference_m":round(float(accel_final.max()),7),
      "corrective_contribution_max_second_difference_m":round(float(accel_corr.max()),7),
      "top_vertices_final_step":top_rows(max_step_by_v),
      "top_vertices_final_second_difference":top_rows(max_accel_by_v),
      "top_vertices_corrective_step":top_rows(max_corr_step_by_v),
      "top_vertices_corrective_second_difference":top_rows(max_corr_accel_by_v),
      "samples":rows
    }
    print("MOTION CONTINUITY",pose,result["poses"][pose]["final_surface_max_second_difference_m"])

reset()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("MOTION CONTINUITY REPORT",OUT)
