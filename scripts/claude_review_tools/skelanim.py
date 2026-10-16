import sys, os, math, json
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
import original_v1_review_candidate_drives as drives
from mathutils import Vector, Matrix
blend, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=blend)
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
if os.environ.get("PRESS_PATH"): bpy.context.scene["hgpt_press_path"] = os.environ["PRESS_PATH"]
drives.setup(res); px.install(); bench._reset(rig)
if os.environ.get("CLAV2SCAP"):
    u0, u1, k = (float(x) for x in os.environ["CLAV2SCAP"].split(","))
    def _sm(x):
        x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
    n = 0
    for s in "rl":
        b = rig.data.bones["clavicle_" + s]; sc, ac = b.head_local, b.tail_local; L2 = (ac - sc).length_squared
        gc, gs = body.vertex_groups["clavicle_" + s], body.vertex_groups["scapula_" + s]
        for v in body.data.vertices:
            w = next((g.weight for g in v.groups if g.group == gc.index), 0.0)
            if w <= 0: continue
            u = (v.co - sc).dot(ac - sc) / L2
            m = w * k * _sm((u - u0) / (u1 - u0))
            if m <= 1e-5: continue
            ws = next((g.weight for g in v.groups if g.group == gs.index), 0.0)
            gc.add([v.index], w - m, "REPLACE"); gs.add([v.index], ws + m, "REPLACE"); n += 1
    print("CLAV2SCAP moved", n)
scene = bpy.context.scene
SKEL = [o for o in scene.objects if o.type == "MESH" and o.name.startswith(("HGPT_authored_", "HGPT_reference_"))]
for o in scene.objects:
    if o.type in ("MESH", "CURVE") and o is not body and o not in SKEL: o.hide_render = True
def mat(name, rgb):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); return m
SKIN = mat("skin", (0.72, 0.55, 0.45))
COL = {"clav": mat("clav", (1.0, 0.55, 0.05)), "scap": mat("scap", (0.9, 0.12, 0.1)), "hum": mat("hum", (0.15, 0.4, 1.0)),
       "arm": mat("arm", (0.2, 0.75, 0.95)), "spine": mat("spine", (0.95, 0.95, 0.9)), "rib": mat("rib", (0.62, 0.62, 0.6)),
       "lm": mat("lm", (1.0, 0.95, 0.1)), "helper": mat("helper", (0.2, 0.75, 0.35)), "leg": mat("leg", (0.8, 0.8, 0.75))}
body.data.materials.clear(); body.data.materials.append(SKIN)
for o in SKEL:
    o.data.materials.clear(); o.data.materials.append(COL["clav"] if "clavicle" in o.name else COL["scap"] if "scapula" in o.name else COL["rib"])
scene.render.engine = "BLENDER_WORKBENCH"; sh = scene.display.shading
sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 700, 700
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 1.15
cam = bpy.data.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
# ---- skeleton sticks, rebuilt per pose
SKCOL = bpy.data.collections.new("sk"); scene.collection.children.link(SKCOL)
def kind(n):
    if n.startswith(("muscle_", "shoulder_cap", "deltoid", "axilla", "hip_crease")): return "helper"
    if n.startswith("clavicle"): return "clav"
    if n.startswith("scapula"): return "scap"
    if n.startswith("upperarm"): return "hum"
    if n.startswith(("forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "lowerarm")): return "arm"
    if n.startswith(("spine", "neck", "head", "pelvis", "root")): return "spine"
    return "leg"
def stick(a, b, r, m):
    d = b - a; L = d.length
    if L < 1e-5: return
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=L, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    SKCOL.objects.link(o)
def ball(p, r, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=p, segments=16, ring_count=8)
    o = bpy.context.active_object; o.data.materials.append(m)
    for c in o.users_collection: c.objects.unlink(o)
    SKCOL.objects.link(o)
ANAT = {"r": "left", "l": "right"}
def lm_rest(name):
    o = bpy.data.objects.get(name); return o.matrix_world.translation.copy() if o else None
REST_LM = {}
for s, a in ANAT.items():
    for n in ("AA", "TS", "AI"):
        REST_LM[(s, n)] = ("scapula_" + s, lm_rest(f"LM_scapula_{a}__{n}"))
def posed(bone, p):
    pb, b = rig.pose.bones[bone], rig.data.bones[bone]
    return (rig.matrix_world @ pb.matrix @ b.matrix_local.inverted() @ rig.matrix_world.inverted()) @ p
def build_skel():
    for o in list(SKCOL.objects): bpy.data.objects.remove(o, do_unlink=True)
    W = rig.matrix_world
    for b in rig.data.bones:
        if not b.use_deform: continue
        k = kind(b.name); pb = rig.pose.bones[b.name]
        r = {"helper": 0.005, "clav": 0.010, "scap": 0.008, "hum": 0.013, "arm": 0.009, "spine": 0.012}.get(k, 0.009)
        stick(W @ pb.head, W @ pb.tail, r, COL[k])
        ball(W @ pb.head, r * 1.5, COL[k])
    for s in "rl":
        P = {n: posed(*REST_LM[(s, n)]) for n in ("AA", "TS", "AI")}
        for a, b in (("TS", "AA"), ("TS", "AI"), ("AI", "AA")):
            stick(P[a], P[b], 0.006, COL["scap"])
        for n in P: ball(P[n], 0.014, COL["lm"])
        ball(W @ rig.pose.bones["upperarm_" + s].head, 0.024, COL["hum"])      # humeral head
    bpy.context.view_layer.update()
VIEWS = {"back": (0, 1, 0.02), "front": (0, -1, 0.02), "side": (1, 0, 0.02)}
def shoot(tag, view, skin, skel):
    body.hide_render = not skin
    for o in SKEL: o.hide_render = not skel
    for o in SKCOL.objects: o.hide_render = not skel
    d = Vector(VIEWS[view]).normalized(); tgt = Vector((0, 0, 1.45))
    cam.location = tgt + d * 4.0; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    scene.render.filepath = f"{out}/{tag}_{view}_{'skin' if skin and not skel else 'skel'}.png"
    bpy.ops.render.render(write_still=True)
def angles():
    W = rig.matrix_world; pb = rig.pose.bones; o = {}
    for s in "rl":
        cl = pb["clavicle_" + s]; v = (W @ cl.tail) - (W @ cl.head)
        P = {n: posed(*REST_LM[(s, n)]) for n in ("AA", "TS", "AI")}
        med = P["AI"] - P["TS"]                                       # medial border direction
        sign = 1 if s == "r" else -1
        upward = math.degrees(math.atan2(sign * med.x, -med.z))       # 0 = vertical border; + = AI swung laterally
        hum = (W @ pb["upperarm_" + s].tail - W @ pb["upperarm_" + s].head).normalized()
        ht = math.degrees(hum.angle(Vector((0, 0, -1))))
        # GH elevation: humerus relative to the scapula blade (angle between humerus and the medial-border line TS->AI, minus rest)
        gh = math.degrees(hum.angle(med.normalized()))
        o[s] = {"clavicle_elevation_deg": round(math.degrees(math.atan2(v.z, math.hypot(v.x, v.y))), 1),
                "clavicle_retraction_deg": round(math.degrees(math.atan2(v.y, sign * v.x)), 1),
                "scapula_upward_rot_deg": round(upward, 1), "humerothoracic_deg": round(ht, 1), "humerus_vs_medial_border_deg": round(gh, 1),
                "AC": [round(x, 3) for x in W @ cl.tail], "GH": [round(x, 3) for x in W @ pb["upperarm_" + s].head],
                "AA": [round(x, 3) for x in P["AA"]], "AI": [round(x, 3) for x in P["AI"]], "TS": [round(x, 3) for x in P["TS"]]}
    return o
VIEWS["three_quarter"] = (0.7, 0.7, 0.05)
import original_v1_shoulder_r4 as r4
STEPS = int(os.environ.get("STEPS", 20))
rows = []
MUTE = tuple(x for x in os.environ.get("MUTE", "").split(",") if x)
if MUTE:
    for kb in body.data.shape_keys.key_blocks:
        if kb.name.startswith(MUTE): kb.mute = True
ONLY = [int(x) for x in os.environ.get("ONLY", "").split(",") if x]
for n in range(STEPS + 1):
    if ONLY and n not in ONLY: continue
    t = n / STEPS
    bench._reset(rig)
    st = px.pose_press_full(res, t)
    drives.drive(rig, body)
    for kb in body.data.shape_keys.key_blocks:
        if not os.environ.get("KEEP_S5") and kb.name.startswith(("HGPT_S5_BAKE_", "HGPT_S4_SCULPT_")): kb.value = 0.0
    bpy.context.view_layer.update()
    a = angles()["r"]
    P = {k: posed(*REST_LM[("r", k)]) for k in ("AA", "TS", "AI")}
    hum = (W2 := rig.matrix_world) @ rig.pose.bones["upperarm_r"].tail - W2 @ rig.pose.bones["upperarm_r"].head
    a["arm_vs_scapular_spine_deg"] = round(math.degrees(hum.angle(P["AA"] - P["TS"])), 1)
    a["scapula_isb_deg"] = (r4._S.get("last", {}).get("r") or {}).get("scapula_isb_deg")
    a["t"] = t; a["state"] = st; rows.append(a)
    build_skel()
    for v in ("back", "side", "three_quarter"):
        if os.environ.get("SKINONLY") and v == "side": continue
        shoot(f"f{n:03d}", v, True, False)
        if not os.environ.get("SKINONLY"): shoot(f"f{n:03d}", v, False, True)
json.dump(rows, open(f"{out}/frames.json", "w"), indent=1)
print("ANIMDONE")
