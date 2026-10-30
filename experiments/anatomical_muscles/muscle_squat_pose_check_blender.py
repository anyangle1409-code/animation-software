"""Read-only check: how the bound leg muscle ENVELOPE PROXIES (MG7) follow the squat when R41's anatomical leg is posed
natively - hip flexion about HJC, knee flexion about KJC on the epicondyle axis, ankle dorsiflexion about AJC on the
malleolar axis, signs fixed by landmark probes (as squat_path_length_check_blender.py; re-implemented, as that script
runs on import).  Descent (hip, knee, ankle) 5 / 5 / 2 -> 100 / 102 / 17 deg in quarters.

Per pose: face overlaps between the muscles (the thigh bellies ride the femur and the calf bellies the tibia, so they
meet behind the knee as it flexes); renders (lateral / posterior / medial).  The skin is not posed.  Nothing is saved.

usage: python3.13 muscle_squat_pose_check_blender.py -- MG7.blend MG7_SHA256 OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, outdir = Path(args[0]), args[1], Path(args[2])
S = args[3] if len(args) > 3 else "left"
SUF = "L" if S == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; MW = anat.matrix_world.copy()


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


HJC, KJC, AJC = LM(f"hip_bone_{S}__HJC"), LM(f"femur_{S}__KJC"), LM(f"tibia_{S}__AJC")
EL, EM = LM(f"femur_{S}__epicondyle_lateral_skin"), LM(f"femur_{S}__epicondyle_medial_skin")
ML, MM = LM(f"tibia_{S}__malleolus_lateral_skin"), LM(f"tibia_{S}__malleolus_medial_skin")
TOE = MW @ anat.data.bones[f"anat_metatarsal_2_{S}"].tail_local
lat = 1.0 if HJC.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
KNEE_AX, ANK_AX = (EL - EM).normalized(), (ML - MM).normalized()


def rot_about(p, axis, deg):
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p)


def signed(axis, probe, want, pivot):
    return 1.0 if ((rot_about(pivot, axis, 5.0) @ probe) - probe).dot(want) > 0 else -1.0


SIGN = {"hip_flexion": signed(LAT, KJC, ANT, HJC), "knee_flexion": signed(KNEE_AX, AJC, -ANT, KJC),
        "ankle_dorsiflexion": signed(ANK_AX, TOE, UP, AJC)}
CHAIN = [f"anat_femur_{S}", f"anat_tibia_{S}", f"anat_talus_{S}"]


def pose(hip, knee, ankle):
    Tf = rot_about(HJC, LAT, SIGN["hip_flexion"] * hip)
    Tt = Tf @ rot_about(KJC, KNEE_AX, SIGN["knee_flexion"] * knee)
    Ta = Tt @ rot_about(AJC, ANK_AX, SIGN["ankle_dorsiflexion"] * ankle)
    return {CHAIN[0]: Tf, CHAIN[1]: Tt, CHAIN[2]: Ta}


def apply(T):
    for b in CHAIN:
        anat.pose.bones[b].matrix = MW.inverted() @ T[b] @ MW @ anat.data.bones[b].matrix_local
        bpy.context.view_layer.update()


LEG = ("rectus_femoris", "vastus_", "biceps_femoris", "semitendinosus", "semimembranosus", "adductor_magnus",
       "gastrocnemius", "soleus")
MUS = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects
       if o.name.endswith(f".{SUF}") and o.name.split(".")[2].startswith(LEG)]
TEN = [o for o in bpy.data.collections["HGPT_EXPERIMENT_TENDONS"].objects
       if o.name.split(".")[3] == SUF and o.name.split(".")[2].startswith(LEG)]
followers = {b: [c.name for c in anat.data.bones[b].children_recursive][:6] for b in CHAIN}
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 1.1
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 640
for ob in sc.objects:
    if ob.type == "MESH" and ob not in MUS and ob not in TEN:
        ob.hide_render = True
rep = {"status": "READ_ONLY_CHECK", "input": src.name, "input_sha256": expected, "side": S, "probe_signs": SIGN,
       "chain_children_follow": followers, "poses": {}}
for q in (0.0, 0.25, 0.5, 0.75, 1.0):
    h, k, a = (5 + 95 * q, 5 + 97 * q, 2 + 15 * q)
    apply(pose(h, k, a))
    dg = bpy.context.evaluated_depsgraph_get()
    trees = {o.name: BVHTree.FromObject(o, dg) for o in MUS}
    pairs, names = {}, list(trees)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            ov = trees[x].overlap(trees[y])
            if ov:
                pairs[f"{x.split('.')[2]} | {y.split('.')[2]}"] = len(ov)
    tag = f"q{int(q * 100):03d}"
    rep["poses"][tag] = {"hip_deg": round(h, 1), "knee_deg": round(k, 1), "ankle_deg": round(a, 1),
                         "overlap_pairs": pairs, "overlap_total": sum(pairs.values())}
    print("POSE", tag, json.dumps(rep["poses"][tag]), flush=True)
    if q in (0.0, 0.5, 1.0):
        centre = Vector((KJC.x, KJC.y + 0.05, KJC.z + 0.05))
        for view, dv in {"lateral": (lat, 0, 0), "posterior": (0, 1, 0), "medial": (-lat, 0, 0)}.items():
            d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = str(outdir / f"mg7sq_{S}_{tag}_{view}.png"); bpy.ops.render.render(write_still=True)
apply(pose(0, 0, 0))
rep["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected
(outdir / f"mg7_{S}_squat_pose_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", flush=True)
