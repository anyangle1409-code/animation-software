"""Diagnostic (read-only): press-lockout skin roughness of a body_v2 blend, with key families switched on / off.

Poses the press lockout (shoulder_girdle_candidate.apply_press_pose at 160 deg, elbows straight) and measures the
high-frequency roughness of the upper body (z > 1.25 m): per vertex |normal component of the umbrella Laplacian minus
its neighbourhood mean| (mm, p50 / p95 / p99), for: rest, lockout without R121 keys, lockout with all keys, lockout
without the legacy HGPT_S* keys, and plain skinning (no corrective keys).  Renders front / back / side close-ups of
each and lists the rest-space roughness of every key's own offset field.  Nothing is saved.

usage: python3.13 lockout_roughness_diag_blender.py -- <body.blend> <r57src> <out_dir>
"""
import sys, math, json, os
import bpy
import numpy as np
from mathutils import Vector
from scipy.sparse import csr_matrix
a = sys.argv[sys.argv.index("--")+1:]; SRC, ROOT, OUT = a[0], a[1], a[2]
os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT+"/scripts", ROOT+"/scripts/anatomy_fit", "/home/user/animation-software/scripts/body_v2"]
bpy.ops.wm.open_mainfile(filepath=SRC)
import build_original_movement_benchmarks_blender as bench, original_v1_review_candidate_drives as drives, r121_drives
import build_functional_shoulder_correction_blender as correction, functional_shoulder_correction as corr
import shoulder_girdle_candidate as girdle
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
AX = {}
for side, name in correction.HUMERI:
    b = rig.data.bones[name]
    AX[name] = corr.humeral_axial_angle_deg(tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
E = np.empty(len(me.edges)*2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2*len(E)), (np.r_[E[:,0],E[:,1]], np.r_[E[:,1],E[:,0]])), shape=(n,n))
Dinv = 1.0/np.maximum(np.asarray(A.sum(1)).ravel(), 1)
R = np.empty(n*3); me.vertices.foreach_get("co", R); R = R.reshape(-1,3)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k+1]) for p in me.polygons for k in range(1, len(p.vertices)-1)])
REG = (R[:,2] > 1.25) & (np.abs(R[:,0]) < 0.33)
def normals(P):
    fn = np.cross(P[TRI[:,1]]-P[TRI[:,0]], P[TRI[:,2]]-P[TRI[:,0]]); vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, TRI[:,k], fn)
    return vn/np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-15)
def rough(P, m=REG):
    L = (A@P)*Dinv[:,None] - P; nn = normals(P)
    v = np.abs(np.einsum("ij,ij->i", L, nn))
    # second-order: deviation of the normal Laplacian from its neighbourhood mean = high-frequency bumps
    hf = np.abs(v - (A@v)*Dinv)
    return {"p50_mm": round(float(np.percentile(hf[m],50))*1000,3), "p95_mm": round(float(np.percentile(hf[m],95))*1000,3),
            "p99_mm": round(float(np.percentile(hf[m],99))*1000,3)}, hf
def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    P = np.empty(n*3); m.vertices.foreach_get("co", P); e.to_mesh_clear(); return P.reshape(-1,3)
def pose(lock, r121=True, legacy=True):
    bench._reset(rig)
    for kb in me.shape_keys.key_blocks[1:]: kb.value = 0.0
    if lock:
        girdle.apply_press_pose(rig, 160.0, AX)
        for s in ("l","r"):
            pb = rig.pose.bones[f"forearm_{s}"]; pb.rotation_mode="XYZ"; pb.rotation_euler=(0,0,0)
    bpy.context.view_layer.update(); drives.drive(rig, body)
    if r121: r121_drives.drive(rig, body)
    else:
        for kb in me.shape_keys.key_blocks:
            if kb.name.startswith("R121_"): kb.value = 0.0
    if not legacy:
        for kb in me.shape_keys.key_blocks:
            if kb.name.startswith("HGPT_S"): kb.value = 0.0
    bpy.context.view_layer.update()
    return {kb.name: round(kb.value,3) for kb in me.shape_keys.key_blocks[1:] if kb.value > 1e-3}
rep = {}
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH","CURVE") and ob is not body: ob.hide_render = True
cd = bpy.data.cameras.new("C"); cd.type="ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera=cam; cd.ortho_scale=0.75
mat = bpy.data.materials.new("M"); mat.diffuse_color=(.72,.55,.45,1); body.data.materials.clear(); body.data.materials.append(mat)
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="MATERIAL"; sc.display.shading.show_cavity=True
sc.render.resolution_x=600; sc.render.resolution_y=600
VAR = [("rest", False, True, True), ("lock_no_r121", True, False, True), ("lock_all", True, True, True),
       ("lock_no_legacy", True, True, False), ("lock_lbs_only", True, False, False)]
for tag, lock, r121, leg in VAR:
    active = pose(lock, r121, leg); P = ev(); st, hf = rough(P)
    rep[tag] = {"roughness_upper_body": st, "active_keys": active}
    c = Vector((0, 0, 1.45))
    for view, dv in {"front": (0,-1,0), "back": (0,1,0), "side": (1,0,0)}.items():
        d = Vector(dv); cam.location = c + d*3; cam.rotation_mode="QUATERNION"; cam.rotation_quaternion=(-d).to_track_quat("-Z","Y")
        sc.render.filepath = f"{OUT}/{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
# roughness of each key's rest-space offset field (high-frequency content added by the key itself)
keys = {}
basis = R
for kb in me.shape_keys.key_blocks[1:]:
    c = np.empty(n*3); kb.data.foreach_get("co", c); D = c.reshape(-1,3) - basis
    if np.abs(D).max() < 1e-5: continue
    L = (A@D)*Dinv[:,None] - D; lm = np.linalg.norm(L, axis=1); hf = np.abs(lm - (A@lm)*Dinv)
    act = np.linalg.norm(D,axis=1) > 1e-4
    keys[kb.name] = {"moved": int(act.sum()), "max_mm": round(float(np.linalg.norm(D,axis=1).max())*1000,2),
                     "hf_p99_mm": round(float(np.percentile(hf[act],99))*1000,3) if act.any() else 0}
rep["key_offset_roughness"] = dict(sorted(keys.items(), key=lambda kv: -kv[1]["hf_p99_mm"]))
json.dump(rep, open(f"{OUT}/diag.json","w"), indent=1)
print("DIAG", json.dumps({k: v["roughness_upper_body"] for k, v in rep.items() if k != "key_offset_roughness"}))
for k, v in list(rep["key_offset_roughness"].items())[:15]: print(k, v)
print("active lock_all", rep["lock_all"]["active_keys"])
