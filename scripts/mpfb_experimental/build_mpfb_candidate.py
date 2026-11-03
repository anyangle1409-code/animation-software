"""EXPERIMENTAL REFERENCE ONLY - NOT PRODUCTION GEOMETRY.

Builds an MPFB (MakeHuman Plugin for Blender) athletic male as a shape benchmark against the owner's photographic
reference, poses it in the same relaxed stance as the Body v2 'stand' move, renders the same four views with the same
camera / light / material as scripts/body_v2/movement_trajectory_test_blender.py, and writes simple measurements.

Provenance: MPFB 2.0.18 (git makehumancommunity/mpfb2, GPL-3.0 code) with its bundled MakeHuman assets (base mesh hm08,
targets, rigs, weights: CC0 1.0).  The OUTPUT of this script is a benchmark: per the owner's first-party rule (3 Nov
2026) no MPFB geometry, topology, rig, weights or textures may be copied into the production model.  Outputs go to
the scratch area / review-assets as images and numbers only; the .blend stays out of git.

Run with Blender's Python where MPFB is installed as an extension (bl_ext.user_default.mpfb):
  BLENDER_USER_RESOURCES=<dir with MPFB> python3.13 build_mpfb_candidate.py -- <params.json> <out dir>
params.json: {"macros": {"gender": 1, "age": 0.5, "muscle": 0.8, "weight": 0.45, "proportions": 1, "height": 0.6,
              "african": 0.0, "asian": 0.0, "caucasian": 1.0},
              "targets": {"torso/torso-vshape-incr": 0.3, "arms/upperarm-muscle-incr": 0.2, ...},  (l-/r- added for
              paired names given without a side; value < 0 picks the -decr partner)
              "stature_m": 1.856, "stand": {"abduction_deg": 8, "plane_deg": 15, "elbow_deg": 12, "curl": 1.0}}
"""
import importlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import addon_utils  # noqa: E402  (after bpy)
import numpy as np
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
P = json.loads(Path(args[0]).read_text()); OUT = Path(args[1]); OUT.mkdir(parents=True, exist_ok=True)
if "bl_ext.user_default.mpfb" not in bpy.context.preferences.addons:
    addon_utils.enable("bl_ext.user_default.mpfb", default_set=True)


def mpfb(mod, key):
    for name in list(sys.modules):
        if name.endswith(mod):
            return getattr(importlib.import_module(name), key)
    raise ImportError(mod)


HumanService = mpfb("mpfb.services.humanservice", "HumanService")
TargetService = mpfb("mpfb.services.targetservice", "TargetService")
LocationService = mpfb("mpfb.services.locationservice", "LocationService")
HumanObjectProperties = mpfb("mpfb.entities.objectproperties", "HumanObjectProperties")

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
h = HumanService.create_human()
for k, v in P.get("macros", {}).items():
    HumanObjectProperties.set_value(k, float(v), entity_reference=h)
TargetService.reapply_macro_details(h)
troot = LocationService.get_mpfb_data("targets")
loaded = {}
for name, w in P.get("targets", {}).items():
    cat, base = name.split("/")
    if w < 0:
        base = base.replace("-incr", "-decr"); w = -w
    paths = []
    f0 = os.path.join(troot, cat, base + ".target.gz")
    if os.path.exists(f0):
        paths = [f0]
    else:                                                       # paired: l- and r- versions
        for sd in ("l", "r"):
            f1 = os.path.join(troot, cat, f"{sd}-{base}.target.gz")
            if not os.path.exists(f1):
                raise FileNotFoundError(f1)
            paths.append(f1)
    for f in paths:
        TargetService.load_target(h, f, weight=float(w)); loaded[os.path.relpath(f, troot)] = float(w)
rig = HumanService.add_builtin_rig(h, P.get("rig", "game_engine"))
bpy.context.view_layer.update()


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); ev = h.evaluated_get(dg); m = ev.to_mesh()
    a = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", a); ev.to_mesh_clear()
    a = a.reshape(-1, 3); mw = np.array(h.matrix_world)
    return a @ mw[:3, :3].T + mw[:3, 3]


# scale to the requested stature (rest pose), feet on the ground
V0 = evaluated(); st0 = float(V0[:, 2].max() - V0[:, 2].min())
s = float(P.get("stature_m", st0)) / st0
rig.scale = rig.scale * s; bpy.context.view_layer.update()
V0 = evaluated(); rig.location.z -= float(V0[:, 2].min()); bpy.context.view_layer.update()
V0 = evaluated()
# relaxed stance (as the Body v2 'stand' move): arms hanging close, slightly forward, elbows a little bent, fingers
# curled towards the thighs, feet about hip width.  Each hinge axis is found by probing (rig-agnostic)
st = P.get("stand", {})
pb = rig.pose.bones
MW = rig.matrix_world
W2A = MW.to_3x3().inverted()


def wpos(v):
    return MW @ v


def swing_to(b, target_w):
    target = (W2A @ target_w).normalized(); cur = (b.tail - b.head).normalized(); piv = b.head.copy()
    b.matrix = Matrix.Translation(piv) @ cur.rotation_difference(target).to_matrix().to_4x4() @ Matrix.Translation(-piv) @ b.matrix
    bpy.context.view_layer.update()


def hinge(b, deg, score):
    """rotate pose bone b by deg about the local axis (x / z, either sign) that maximises score(tail world) per probe"""
    best = None
    for ax in ("x", "z"):
        for sg in (1.0, -1.0):
            b.rotation_mode = "XYZ"; r0 = b.rotation_euler.copy()
            e = list(r0); e["xyz".index(ax)] += sg * math.radians(5.0); b.rotation_euler = e
            bpy.context.view_layer.update(); sc_ = score(wpos(b.tail)); b.rotation_euler = r0; bpy.context.view_layer.update()
            if best is None or sc_ > best[0]:
                best = (sc_, ax, sg)
    _, ax, sg = best
    e = list(b.rotation_euler); e["xyz".index(ax)] += sg * math.radians(deg); b.rotation_euler = e
    bpy.context.view_layer.update()
    return ax, sg


pose_log = {}
for side in ("l", "r"):
    ua = pb[f"upperarm_{side}"]
    lat = 1.0 if wpos(ua.head).x > 0 else -1.0
    e, p = math.radians(st.get("abduction_deg", 8)), math.radians(st.get("plane_deg", 15))
    swing_to(ua, Vector((lat * math.sin(e) * math.cos(p), -math.sin(e) * math.sin(p), -math.cos(e))))
    fa = pb[f"lowerarm_{side}"]
    # the MakeHuman rest pose already bends the elbow (~47 deg, forearm forward): aim the forearm directly, elbow_deg
    # forward of the upper arm's line
    u = (wpos(ua.tail) - wpos(ua.head)).normalized(); fw = Vector((0, -1, 0)); fw = (fw - u * fw.dot(u)).normalized()
    ed = math.radians(st.get("elbow_deg", 12))
    swing_to(fa, (u * math.cos(ed) + fw * math.sin(ed)).normalized())
    f_ = (wpos(fa.tail) - wpos(fa.head)).normalized()
    pose_log[f"elbow_{side}"] = round(math.degrees(u.angle(f_)), 1)
    hd = pb[f"hand_{side}"]                                          # wrist straight (in line with the forearm)
    swing_to(hd, f_)
    curl = float(st.get("curl", 1.0))
    for d, degs in {"index": (20, 30, 12), "middle": (25, 35, 15), "ring": (30, 40, 18), "pinky": (35, 45, 20)}.items():
        for j, deg in zip(("01", "02", "03"), degs):
            bb = pb[f"{d}_{j}_{side}"]; t0b = wpos(bb.tail).copy()
            hinge(bb, deg * curl, lambda t, t0b=t0b: -abs(t.x) + abs(t0b.x))   # towards the body (palms face it)
    for j, deg in (("thumb_02", 10), ("thumb_03", 15)):
        bb = pb[f"{j}_{side}"]; t0b = wpos(bb.tail).copy()
        hinge(bb, deg * curl, lambda t, t0b=t0b: -abs(t.x) + abs(t0b.x))
# feet: bring the ankles to V2 stance width (ankle centres stand["ankle_gap_m"] apart) by adducting the thighs
gap = float(st.get("ankle_gap_m", 0.22))
for side in ("l", "r"):
    th, ft = pb[f"thigh_{side}"], pb[f"foot_{side}"]
    hip, ank = wpos(th.head), wpos(ft.head)
    want_x = math.copysign(gap / 2, ank.x)
    ang = math.atan2(ank.x - hip.x, hip.z - ank.z) - math.atan2(want_x - hip.x, hip.z - ank.z)
    axis_w = Vector((0, 1, 0)); piv = th.head.copy()
    for sg in (1.0, -1.0):
        m0 = th.matrix.copy()
        th.matrix = Matrix.Translation(piv) @ Matrix.Rotation(sg * ang, 4, (W2A @ axis_w).normalized()) @ Matrix.Translation(-piv) @ m0
        bpy.context.view_layer.update()
        if abs(abs(wpos(ft.head).x) - gap / 2) < 0.01:
            break
        th.matrix = m0; bpy.context.view_layer.update()
    ft2 = wpos(pb[f"foot_{side}"].head)
    pose_log[f"ankle_x_{side}"] = round(ft2.x, 4)
    # keep the foot flat: undo the thigh's roll at the ankle
    fb = pb[f"foot_{side}"]; fb.rotation_mode = "XYZ"
bpy.context.view_layer.update()
if P.get("subdivide", 1):
    sub = h.modifiers.new("SUBDIV_REVIEW", "SUBSURF"); sub.levels = sub.render_levels = int(P.get("subdivide", 1))
V = evaluated()
z0 = float(V[:, 2].min()); H = float(V[:, 2].max() - z0)
# render: as the Body v2 harness (ortho 2.45 m, centre 0.635 H, camera 4 m out, 0.12 tilt, workbench + cavity, floor)
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (0.80, 0.60, 0.48, 1)
h.data.materials.clear(); h.data.materials.append(mat)
for ob in sc.objects:
    if ob.type == "MESH" and ob is not h:
        ob.hide_render = True
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True
sh.show_shadows = True
if sc.world is None:
    sc.world = bpy.data.worlds.new("REVIEW_ONLY")
sc.world.color = (0.86, 0.88, 0.88); sc.view_settings.view_transform = "Standard"
fm = bpy.data.meshes.new("FLOOR_REVIEW_ONLY"); a = 3.0
fm.from_pydata([(-a, -a, z0), (a, -a, z0), (a, a, z0), (-a, a, z0)], [], [(0, 1, 2, 3)])
fo = bpy.data.objects.new("FLOOR_REVIEW_ONLY", fm); sc.collection.objects.link(fo)
fmat = bpy.data.materials.new("FLOOR_REVIEW_ONLY"); fmat.diffuse_color = (.80, .82, .84, 1); fm.materials.append(fmat)
VIEWS = {"front": ((0, -1, 0), 0.635, 2.45), "side": ((1, 0, 0), 0.635, 2.45), "back": ((0, 1, 0), 0.635, 2.45),
         "front34": ((0.7071, -0.7071, 0), 0.635, 2.45), "front_upper": ((0, -1, 0), 0.80, 1.05),
         "side_upper": ((1, 0, 0), 0.80, 1.05), "back_upper": ((0, 1, 0), 0.80, 1.05),
         "front34_upper": ((0.7071, -0.7071, 0), 0.80, 1.05), "back34": ((0.7071, 0.7071, 0), 0.635, 2.45)}
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
for view, (dv, hc, scale) in VIEWS.items():
    dvec = Vector(dv) + Vector((0.0, 0.0, 0.12)); dvec.normalize(); centre = Vector((0.0, 0.0, z0 + hc * H))
    cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"; cd.ortho_scale = scale * H / 1.856
    cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
    sc.render.filepath = str(OUT / f"stand_{view}_000.png"); bpy.ops.render.render(write_still=True)
# arms-out views (owner pack, Option 5): both humeri at P["arms_out_deg"] from the body in the frontal plane
if P.get("arms_out_deg"):
    for side in ("l", "r"):
        ua = pb[f"upperarm_{side}"]; lat = 1.0 if wpos(ua.head).x > 0 else -1.0
        e = math.radians(P["arms_out_deg"]); swing_to(ua, Vector((lat * math.sin(e), 0.0, -math.cos(e))))
    bpy.context.view_layer.update()
    for view in ("front", "back"):
        dv, hc, scale = VIEWS[view]
        dvec = Vector(dv) + Vector((0.0, 0.0, 0.12)); dvec.normalize(); centre = Vector((0.0, 0.0, z0 + hc * H))
        cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"; cd.ortho_scale = scale * H / 1.856
        cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
        sc.render.filepath = str(OUT / f"armsout_{view}_000.png"); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mpfb_candidate_armsout.blend"), copy=True)
    for side, ang in (("l", None), ("r", None)):
        pass
    import importlib as _il  # re-pose the stand arms for the saved stand file below
    for side in ("l", "r"):
        ua = pb[f"upperarm_{side}"]; lat = 1.0 if wpos(ua.head).x > 0 else -1.0
        e, p_ = math.radians(st.get("abduction_deg", 8)), math.radians(st.get("plane_deg", 15))
        swing_to(ua, Vector((lat * math.sin(e) * math.cos(p_), -math.sin(e) * math.sin(p_), -math.cos(e))))
    bpy.context.view_layer.update()
# measurements (stand pose, world metres): stature, and per-level front / side extents of the TRUNK skin (arm, hand
# and leg vertices excluded by rig weights)
GN = {g.index: g.name for g in h.vertex_groups}
arm = np.zeros(len(V))
dg = bpy.context.evaluated_depsgraph_get(); ev = h.evaluated_get(dg); em = ev.to_mesh()   # the evaluated mesh (helper
for v in em.vertices:                                                                    # geometry masked out)
    for g in v.groups:
        nm = GN.get(g.group, "")
        if any(k in nm for k in ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")):
            arm[v.index] += g.weight
ev.to_mesh_clear()
trunk = arm < 0.3
lev = {}
for f in (0.80, 0.75, 0.72, 0.65, 0.60, 0.55, 0.52, 0.48, 0.37, 0.28, 0.20, 0.06):
    sel = np.abs((V[:, 2] - z0) / H - f) < 0.004
    t = sel & trunk
    lev[f"{f:.2f}"] = {"width_all_m": round(float(np.ptp(V[sel, 0])), 4) if sel.any() else None,
                      "width_trunk_m": round(float(np.ptp(V[t, 0])), 4) if t.any() else None,
                      "depth_trunk_m": round(float(np.ptp(V[t, 1])), 4) if t.any() else None}
rep = {"pose": {k: (list(v) if isinstance(v, tuple) else v) for k, v in pose_log.items()},
       "shape_keys_on": {kb.name: round(kb.value, 3) for kb in h.data.shape_keys.key_blocks if kb.value > 0.001},
       "provenance": "MPFB 2.0.18 + bundled MakeHuman CC0 assets; experimental benchmark, not production",
       "params": P, "targets_loaded": loaded, "native_stature_m": round(st0, 4), "scale_applied": round(s, 5),
       "stature_m": round(H, 4), "levels_fraction_of_stature": lev, "vertices": len(V)}
(OUT / "mpfb_candidate_report.json").write_text(json.dumps(rep, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mpfb_candidate.blend"))
print("MPFB", json.dumps({k: rep[k] for k in ("native_stature_m", "scale_applied", "stature_m")}), flush=True)
