"""Diagnostic (read-only): leg / hip skin roughness of a body_v2 blend in the squat and deadlift, with key families
switched on / off.

Poses the benchmark squat (depth 1.0) and deadlift (t 0.75, hip flexion ~114 deg) and measures the high-frequency
roughness of the legs and hips (0.30 < z < 1.15 m): per vertex |normal component of the umbrella Laplacian minus its
neighbourhood mean| (mm, p50 / p95 / p99), for: all keys, without the legacy HGPT_H1_* / HGPT_K1_KNEE* families,
without the R121 keys, and plain skinning.  Renders side / back / front-three-quarter close-ups.  Nothing is saved.

usage: python3.13 leg_roughness_diag_blender.py -- <body.blend> <r57src> <out_dir>
"""
import sys, math, json, os
import bpy, numpy as np
from mathutils import Vector
from scipy.sparse import csr_matrix
a = sys.argv[sys.argv.index("--")+1:]; SRC, ROOT, OUT = a[0], a[1], a[2]; os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT+"/scripts", ROOT+"/scripts/anatomy_fit", "/home/user/animation-software/scripts/body_v2"]
bpy.ops.wm.open_mainfile(filepath=SRC)
import build_original_movement_benchmarks_blender as bench, original_v1_review_candidate_drives as drives, r121_drives
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
E = np.empty(len(me.edges)*2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2*len(E)), (np.r_[E[:,0],E[:,1]], np.r_[E[:,1],E[:,0]])), shape=(n,n))
Dinv = 1.0/np.maximum(np.asarray(A.sum(1)).ravel(), 1)
R = np.empty(n*3); me.vertices.foreach_get("co", R); R = R.reshape(-1,3)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k+1]) for p in me.polygons for k in range(1, len(p.vertices)-1)])
REG = (R[:,2] > 0.30) & (R[:,2] < 1.15) & (np.abs(R[:,0]) < 0.25)
def normals(P):
    fn = np.cross(P[TRI[:,1]]-P[TRI[:,0]], P[TRI[:,2]]-P[TRI[:,0]]); vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, TRI[:,k], fn)
    return vn/np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-15)
def rough(P):
    L = (A@P)*Dinv[:,None] - P; v = np.abs(np.einsum("ij,ij->i", L, normals(P))); hf = np.abs(v - (A@v)*Dinv)
    return {q: round(float(np.percentile(hf[REG], int(q[1:])))*1000,3) for q in ("p50","p95","p99")}
def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    P = np.empty(n*3); m.vertices.foreach_get("co", P); e.to_mesh_clear(); return P.reshape(-1,3)
bench._reset(rig); bpy.context.view_layer.update()
HEADS = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l","r")}
LEG = ("HGPT_H1_", "HGPT_K1_KNEE")
def pose(kind, mode):
    bench._reset(rig)
    if kind == "squat": bench.pose_squat(rig, 1.0, HEADS)
    elif kind == "deadlift": bench.pose_deadlift(rig, 0.75, HEADS)
    bpy.context.view_layer.update(); drives.drive(rig, body); r121_drives.drive(rig, body)
    for kb in me.shape_keys.key_blocks[1:]:
        if mode == "no_legacy_leg" and kb.name.startswith(LEG): kb.value = 0.0
        if mode == "no_r121" and kb.name.startswith("R121_"): kb.value = 0.0
        if mode == "lbs": kb.value = 0.0
    bpy.context.view_layer.update()
    return {kb.name: round(kb.value,2) for kb in me.shape_keys.key_blocks[1:] if kb.value > 0.01 and kb.name.startswith(LEG + ("R121_HIP","R121_KNEE"))}
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH","CURVE") and ob is not body: ob.hide_render = True
cd = bpy.data.cameras.new("C"); cd.type="ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera=cam; cd.ortho_scale=0.9
mat = bpy.data.materials.new("M"); mat.diffuse_color=(.72,.55,.45,1); body.data.materials.clear(); body.data.materials.append(mat)
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="MATERIAL"; sc.display.shading.show_cavity=True
sc.render.resolution_x=500; sc.render.resolution_y=500
rep = {}
for kind in ("rest", "squat", "deadlift"):
    for mode in (("all",) if kind == "rest" else ("all", "no_legacy_leg", "no_r121", "lbs")):
        act = pose(kind, mode); P = ev()
        rep[f"{kind}_{mode}"] = {"roughness_legs_mm": rough(P), "active_leg_keys": act}
        if kind != "rest" and mode in ("all", "no_legacy_leg", "lbs"):
            c = Vector(tuple(P[REG].mean(0)))
            for view, dv in {"side": (1,0,0), "back": (0.3,1,0), "front34": (0.6,-0.8,0)}.items():
                d = Vector(dv).normalized(); cam.location = c + d*3; cam.rotation_mode="QUATERNION"; cam.rotation_quaternion=(-d).to_track_quat("-Z","Y")
                sc.render.filepath = f"{OUT}/{kind}_{mode}_{view}.png"; bpy.ops.render.render(write_still=True)
json.dump(rep, open(f"{OUT}/legdiag.json","w"), indent=1)
for k, v in rep.items(): print("LEGDIAG", k, v["roughness_legs_mm"], len(v["active_leg_keys"]), list(v["active_leg_keys"].items())[:8])
