import sys, os
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy, numpy as np
import original_v1_review_candidate_drives as drives
bpy.ops.wm.open_mainfile(filepath=sys.argv[-2])
import os
if os.environ.get("LOCK_HT"): bpy.context.scene["hgpt_press_lockout_ht"] = float(os.environ["LOCK_HT"])
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
V0, F = bench._evaluated(body); R = np.array([tuple(v) for v in V0]); Fa = np.array(F)
s4.press_pose(res, float(os.environ.get("KEY","172.0"))); drives.drive(rig, body)
gh = np.array(tuple(rig.matrix_world @ rig.pose.bones["upperarm_r"].head))
for path in sys.argv[-1].split(","):
    X = np.load(path)[os.environ.get("KEY","172.0")] if path.endswith("npz") else np.load(path)
    def fn(Y):
        n = np.cross(Y[Fa[:,1]]-Y[Fa[:,0]], Y[Fa[:,2]]-Y[Fa[:,0]]); return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
    from collections import defaultdict
    ef = defaultdict(list)
    for k,f in enumerate(F):
        for i in range(3): ef[tuple(sorted((f[i],f[(i+1)%3])))].append(k)
    E = np.array([k for k,v in ef.items() if len(v)==2]); FF = np.array([ef[tuple(e)] for e in E])
    nX, nR = fn(X), fn(R)
    dX = np.degrees(np.arccos(np.clip((nX[FF[:,0]]*nX[FF[:,1]]).sum(1),-1,1)))
    dR = np.degrees(np.arccos(np.clip((nR[FF[:,0]]*nR[FF[:,1]]).sum(1),-1,1)))
    mid = (X[E[:,0]]+X[E[:,1]])/2; rel = mid-gh
    sel = (np.linalg.norm(rel,axis=1)<0.16)&(dX>45)&(dX-dR>20)
    print(path.split('/')[-2], "sharp edges inboard of joint:", sel.sum())
    for i in np.argsort(-dX*sel)[:15]:
        if sel[i]: print("   %.1f %.1f %.1f  dihedral %.0f" % (*(rel[i]*100), dX[i]))
