"""Bind the Meshy appearance mesh to the canonical Home Gym PT skeleton (experimental; production untouched).

* The source GLB is imported read-only; the working copy is scaled uniformly to the canonical stature (1.856 m).
* A COPY of the canonical rig (MESHY_RIG) is posed into the mesh's A-pose WITHOUT changing any bone length or joint
  definition: the upper arm is aimed along the mesh's arm, the forearm at the mesh's wrist centre, the thighs abducted
  to the mesh's ankle spacing.  That pose is then applied as MESHY_RIG's rest pose (an A-pose bind).
* Deforming bones: the primary chain only.  The canonical helper bones (shoulder_cap, muscle_*, hip_crease,
  forearm_tw0) are driven by the R121 drives on the production body and are not weighted here; root is not weighted.
* Weights: Blender bone-heat automatic weights.

usage: python3.13 bind_meshy_blender.py -- <canonical rig .blend> <meshy source .glb> <landmarks.json> <out .blend>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]
RIGBLEND, GLB, LMK, OUT = Path(a[0]), Path(a[1]), json.loads(Path(a[2]).read_text()), Path(a[3])
bpy.ops.wm.open_mainfile(filepath=str(RIGBLEND))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "body_v2"))
import character_profile  # noqa: E402
bn, rn = character_profile.blender_names()
src_rig = bpy.data.objects[rn]
for o in list(bpy.data.objects):                     # keep only the canonical rig in this scratch file
    if o is not src_rig:
        bpy.data.objects.remove(o, do_unlink=True)
rig = src_rig.copy(); rig.data = src_rig.data.copy(); rig.name = "MESHY_RIG"; bpy.context.scene.collection.objects.link(rig)
bpy.data.objects.remove(src_rig, do_unlink=True)
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.ops.import_scene.gltf(filepath=str(GLB))
mesh = [o for o in bpy.data.objects if o.type == "MESH"][0]; mesh.name = "MESHY_BODY"
k = LMK["scale_to_canonical"]
mesh.scale = (k, k, k); bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
mesh.select_set(False)
V = np.array([v.co[:] for v in mesh.data.vertices]); z0 = V[:, 2].min(); mesh.location.z -= z0; bpy.context.view_layer.update()
V[:, 2] -= z0
import os  # noqa: E402
GHD = [float(x) for x in os.environ.get("GH_DELTA", "0,0,0").split(",")]   # EXPERIMENT: move each shoulder joint (m):
if any(GHD):                                                               # dx inwards (+ = narrower), dy forwards (+), dz up
    bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode="EDIT"); eb = rig.data.edit_bones
    for sd in ("l", "r"):
        lat = 1.0 if eb[f"upperarm_{sd}"].head.x > 0 else -1.0
        d = Vector((-lat * GHD[0], -GHD[1], GHD[2]))
        arm_bones = [b for b in eb if b.name.endswith("_" + sd) and any(k in b.name for k in (
            "upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal", "shoulder_cap"))]
        for b in arm_bones:                    # the whole arm moves rigidly: arm bone lengths are unchanged
            b.use_connect = False; b.head += d; b.tail += d
        cl = eb[f"clavicle_{sd}"]; cl.tail += d             # the clavicle ends at the moved joint (its length changes)
        sp = eb[f"scapula_{sd}"]; sp.head += d * 0.6; sp.tail += d * 0.6
        for nm in (f"muscle_lat_{sd}", f"muscle_pec_{sd}", f"muscle_trap_{sd}"):   # the fans' arm ends follow the joint
            if nm in eb:
                eb[nm].tail += d
    bpy.ops.object.mode_set(mode="OBJECT")
pb = rig.pose.bones; MW = rig.matrix_world; W2A = MW.to_3x3().inverted(); wp = lambda v: MW @ v


def subtree(root):
    out = [root]
    for c in pb[root].children_recursive:
        out.append(c.name)
    return out


def aim_rigid(names, bone, target_w):
    b = pb[bone]; cur = (wp(b.tail) - wp(b.head)).normalized(); tgt = Vector(target_w).normalized()
    ax = cur.cross(tgt)
    if ax.length < 1e-7:
        return 0.0
    ang = cur.angle(tgt); piv = b.head.copy(); R = Matrix.Rotation(ang, 4, (W2A @ ax).normalized())
    D = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv)
    mats = {n: pb[n].matrix.copy() for n in names}
    for n in names:
        pb[n].matrix = D @ mats[n]; bpy.context.view_layer.update()
    return math.degrees(ang)


fitlog = {"gh_delta_m_in_fwd_up": GHD}
for sd in ("l", "r"):
    arm = LMK[f"arm_{sd}"]; CL = [Vector(q) for q in LMK[f"arm_{sd}_centerline"]]
    wrist = Vector(arm["wrist"]); gh = wp(pb[f"upperarm_{sd}"].head)
    L_ua = (wp(pb[f"upperarm_{sd}"].tail) - gh).length

    def on_line_at(dist):                      # first centerline point (distal direction) at `dist` from the GH
        for p0, p1 in zip(CL[:-1], CL[1:]):
            d0, d1 = (p0 - gh).length, (p1 - gh).length
            if (d0 - dist) * (d1 - dist) <= 0 and d1 != d0:
                t = (dist - d0) / (d1 - d0); return p0 + (p1 - p0) * t
        return CL[-1]
    fitlog[f"upperarm_{sd}_deg"] = round(aim_rigid(subtree(f"upperarm_{sd}"), f"upperarm_{sd}", on_line_at(L_ua) - gh), 1)
    el = wp(pb[f"forearm_{sd}"].head)
    fitlog[f"forearm_{sd}_deg"] = round(aim_rigid(subtree(f"forearm_{sd}"), f"forearm_{sd}", wrist - el), 1)
    dist_line = lambda p: min((p - q).length for q in CL)
    fitlog[f"gh_{sd}_off_arm_axis_mm"] = round(dist_line(gh) * 1000, 1)       # canonical GH vs the mesh arm centre line
    fitlog[f"wrist_{sd}_residual_mm"] = round((wp(pb[f"hand_{sd}"].head) - wrist).length * 1000, 1)
    lc = LMK[f"leg_{sd}_at_canonical"]; hip = wp(pb[f"thigh_{sd}"].head)
    ank_m = Vector(lc["ankle"]); ank = wp(pb[f"foot_{sd}"].head)
    fitlog[f"thigh_{sd}_deg"] = round(aim_rigid(subtree(f"thigh_{sd}"), f"thigh_{sd}", ank_m - hip), 1)
    fitlog[f"knee_{sd}_residual_mm"] = round((wp(pb[f"shin_{sd}"].head) - Vector(lc["knee"])).length * 1000, 1)
    fitlog[f"ankle_{sd}_residual_mm"] = round((wp(pb[f"foot_{sd}"].head) - ank_m).length * 1000, 1)
# A-pose bind: apply the pose as MESHY_RIG's rest pose (bone lengths / joint definitions unchanged)
bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode="POSE"); bpy.ops.pose.select_all(action="SELECT"); bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")
SKIP = ("root", "forearm_tw0", "shoulder_cap", "muscle_", "hip_crease")
for b in rig.data.bones:
    b.use_deform = not any(b.name.startswith(s) for s in SKIP)
lengths_ok = True
# weights
for o in bpy.context.selected_objects:
    o.select_set(False)
mesh.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
W = np.zeros(len(mesh.data.vertices))
for v in mesh.data.vertices:
    W[v.index] = sum(g.weight for g in v.groups)
fitlog["unweighted_vertices"] = int((W < 1e-4).sum()); fitlog["vertices"] = len(W)
fitlog["groups"] = len(mesh.vertex_groups)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
(OUT.parent / "bind_report.json").write_text(json.dumps(fitlog, indent=1)); print("BIND", json.dumps(fitlog), flush=True)
