"""Read-only outbound/return reversibility audit for ORIGINAL-v1 deformation.

Never saves the Blend.

Usage:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/audit_original_v1_motion_reversibility_blender.py -- ^
    <out.json> [pose,pose,...] [samples]

For each pose, samples rest->endpoint and then endpoint->rest. At every matched
joint-state fraction, compares the evaluated body surface and active shape-key
values. This detects stateful deformation, residual dents/twist, driver hysteresis,
or order-dependent evaluation. It does NOT prove anatomical realism by itself.
"""
from __future__ import annotations
import hashlib, json, math, sys, tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not ARGS:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...] [samples]")
OUT=Path(ARGS[0]).resolve()
POSE_LIST=ARGS[1].split(",") if len(ARGS)>1 and ARGS[1] else [
    "press_top","pullup_hang","row","curl_peak","pushup_bottom","squat_bottom","lunge"
]
NS=int(ARGS[2]) if len(ARGS)>2 else 21
if NS<3:
    raise SystemExit("samples must be >=3")
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")

POSE_SCRIPT=Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
SRC=POSE_SCRIPT.read_text(encoding="utf-8")
marker="# ---------------------------------------------------------------- metrics"
if marker not in SRC:
    raise SystemExit("pose script metrics marker missing")

_saved=sys.argv
sys.argv=["blender","--",tempfile.mkdtemp(),""]
ns={"__name__":"pose_defs","__file__":POSE_SCRIPT.name}
exec(compile(SRC[:SRC.index(marker)],"pose_test_defs","exec"),ns)
import importlib.util as _ilu
_driver_path=POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
_sp=_ilu.spec_from_file_location("original_v1_flexion_driver",str(_driver_path))
_fd=_ilu.module_from_spec(_sp); _sp.loader.exec_module(_fd); _fd.install(ns)
sys.argv=_saved

rig=ns["rig"]; body=ns["body"]; POSES=ns["POSES"]; reset=ns["reset"]; upd=ns["upd"]
if body.modifiers.get("HGPT_DRESSED_MASK") is not None:
    body.modifiers["HGPT_DRESSED_MASK"].show_viewport=False
    body.modifiers["HGPT_DRESSED_MASK"].show_render=False

candidate=Path(bpy.data.filepath)
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()

def swing_twist(q):
    v=Vector((q.x,q.y,q.z))
    proj=Vector((0,1,0))*v.dot(Vector((0,1,0)))
    tw=Quaternion((q.w,proj.x,proj.y,proj.z))
    if tw.magnitude<1e-12:
        tw=Quaternion((1,0,0,0))
    tw.normalize()
    return q@tw.inverted(),tw

def apply_fraction(final,f):
    for p in rig.pose.bones:
        q,t=final[p.name]
        sw,tw=swing_twist(q)
        ang=(2.0*math.atan2(tw.y,tw.w)+math.pi)%(2.0*math.pi)-math.pi
        qf=Quaternion((1,0,0,0)).slerp(sw,f) @ Quaternion((0.0,1.0,0.0),f*ang)
        p.matrix_basis=Matrix.Translation(t*f) @ qf.to_matrix().to_4x4()
    upd()

def evaluated_positions():
    dg=bpy.context.evaluated_depsgraph_get()
    ev=body.evaluated_get(dg)
    mesh=ev.to_mesh()
    try:
        return np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
    finally:
        ev.to_mesh_clear()

def key_values():
    keys=body.data.shape_keys
    if keys is None:
        return {}
    return {kb.name:float(kb.value) for kb in keys.key_blocks if kb.name!="Basis"}

def top_vertex_rows(diff,limit=20):
    ids=np.argsort(diff)[-limit:][::-1]
    return [{"vertex_id":int(i),"difference_m":round(float(diff[i]),9)} for i in ids if diff[i]>0]

result={
    "schema_version":1,
    "status":"READ_ONLY_MOTION_REVERSIBILITY_AUDIT",
    "candidate":candidate.name,
    "candidate_sha256":candidate_sha,
    "pose_definition_sha256":hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
    "driver_sha256":hashlib.sha256(_driver_path.read_bytes()).hexdigest(),
    "samples_per_direction":NS,
    "surface_tolerance_m":1e-6,
    "shape_key_tolerance":1e-7,
    "poses":{},
    "source_saved_or_modified":False,
}

overall_surface=0.0
overall_key=0.0
for pose_name in POSE_LIST:
    if pose_name not in POSES:
        raise SystemExit(f"unknown pose {pose_name}")
    reset(); rig.location=(0,0,0)
    if "HANDLE" in ns:
        ns["HANDLE"].clear()
    POSES[pose_name](); upd()
    final={p.name:(p.matrix_basis.to_quaternion(),p.matrix_basis.to_translation()) for p in rig.pose.bones}

    outbound={}
    for k in range(NS):
        f=k/(NS-1)
        apply_fraction(final,f)
        outbound[k]=(evaluated_positions(),key_values())

    rows=[]
    pose_surface=0.0
    pose_key=0.0
    for k in reversed(range(NS)):
        f=k/(NS-1)
        apply_fraction(final,f)
        P= evaluated_positions()
        kv= key_values()
        P0,kv0=outbound[k]
        if P.shape!=P0.shape:
            raise SystemExit(f"{pose_name}: evaluated vertex count changed across motion")
        diff=np.linalg.norm(P-P0,axis=1)
        max_surface=float(diff.max()) if len(diff) else 0.0
        names=set(kv)|set(kv0)
        key_diff=max([abs(kv.get(n,0.0)-kv0.get(n,0.0)) for n in names] or [0.0])
        pose_surface=max(pose_surface,max_surface)
        pose_key=max(pose_key,key_diff)
        rows.append({
            "fraction":round(float(f),6),
            "surface_max_difference_m":round(max_surface,10),
            "surface_p99_difference_m":round(float(np.percentile(diff,99)) if len(diff) else 0.0,10),
            "shape_key_max_difference":round(float(key_diff),10),
            "top_vertices":top_vertex_rows(diff),
        })
    rows.reverse()
    overall_surface=max(overall_surface,pose_surface)
    overall_key=max(overall_key,pose_key)
    result["poses"][pose_name]={
        "max_surface_difference_m":round(pose_surface,10),
        "max_shape_key_difference":round(pose_key,10),
        "status":"CLEAN" if pose_surface<=result["surface_tolerance_m"] and pose_key<=result["shape_key_tolerance"] else "REVERSIBILITY_FAILURE",
        "samples":rows,
    }
    print("REVERSIBILITY",pose_name,result["poses"][pose_name]["status"],pose_surface,pose_key)

reset()
result["overall_max_surface_difference_m"]=round(overall_surface,10)
result["overall_max_shape_key_difference"]=round(overall_key,10)
result["overall_status"]="CLEAN" if overall_surface<=result["surface_tolerance_m"] and overall_key<=result["shape_key_tolerance"] else "REVERSIBILITY_FAILURE"
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("MOTION REVERSIBILITY AUDIT",result["overall_status"],OUT)
