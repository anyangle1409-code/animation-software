"""Female source baseline (read-only): renders and measurements of the received Meshy female against the owner's
Option 4 guide proportions, before any work. The source file is opened and never saved.

Renders: front, back, left, right, three-quarter front and back, orthographic, whole figure; (a) neutral clay, smooth,
three-point studio light (same set-up as the male review), (b) the model's own textures.
Measurements (tape-measure girths = convex hull perimeter of the trunk's horizontal section; the trunk loop crosses the
midline and is longer than 40 cm - the ponytail and small slivers near x = 0 are excluded):
  bust at the level of the most anterior chest point, arms excluded (in the A-pose they touch the side of the bra);
  waist = smallest trunk girth 0.95-1.15 m; hips = largest trunk girth 0.72-0.95 m; hip width and the trochanter level
  = widest trunk section there (leg length 'hip to floor' as the guide defines it); shoulder breadth across the deltoid
  caps 2-6 cm below the top of the shoulders (the A-pose arms make a wider band meaningless); shoulder:hip ratio =
  shoulder breadth / hip width; crotch height.

usage: python3.13 female_source_baseline_blender.py -- <female .blend> <out dir>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from scipy.spatial import ConvexHull

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
ob = [o for o in bpy.data.objects if o.type == "MESH"][0]; me = ob.data
V = np.array([ob.matrix_world @ v.co for v in me.vertices])


def section(z):
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
    segs = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    bm.free()
    key = lambda p: (round(p.x, 5), round(p.y, 5)); adj = {}; pos = {}
    for p, q in segs:
        a_, b_ = key(p), key(q); pos[a_] = p; pos[b_] = q; adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
    seen = set(); loops = []
    for s in adj:
        if s in seen:
            continue
        comp = []; st = [s]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(pos[x]); st += adj[x]
        loops.append(np.array([[p.x, p.y] for p in comp]))
    return loops


def girth(z):
    L = [l for l in section(z) if len(l) > 10]
    if not L:
        return None, None
    mid = min(L, key=lambda l: abs(l[:, 0].mean()) + (0 if (l[:, 0].min() < 0 < l[:, 0].max()) else 1))
    return float(ConvexHull(mid).area), float(np.ptp(mid[:, 0]))


def scan(lo, hi, n, pick):
    best = None
    for z in np.linspace(lo, hi, n):
        g, w = girth(z)
        if g is None:
            continue
        if best is None or pick(g, best[1]):
            best = (z, g, w)
    return best


H = float(np.ptp(V[:, 2])); m = {"height_m": round(H, 4), "vertices": len(V)}


def trunk_loop(z):
    """the trunk loop at height z: crosses the midline, perimeter > 40 cm (the ponytail and small internal slivers
    near x = 0 are excluded); where the arms touch the trunk (bust level) only |x| < xmax is kept"""
    L = [l for l in section(z) if len(l) > 10 and l[:, 0].min() < 0 < l[:, 0].max() and ConvexHull(l).area > 0.40]
    return max(L, key=lambda l: ConvexHull(l).area) if L else None


front = V[(np.abs(V[:, 0]) < 0.12) & (V[:, 2] > 1.10) & (V[:, 2] < 1.32)]
zb = float(front[np.argmin(front[:, 1]), 2]); lb = trunk_loop(zb)
arm_gap = []                                                      # the arm's inner edge just below the armpit
for z in np.linspace(zb - 0.08, zb, 9):
    L = [l for l in section(z) if len(l) > 10 and l[:, 0].min() > 0.05]
    if L:
        arm_gap.append(min(l[:, 0].min() for l in L))
xmax = (min(arm_gap) - 0.004) if arm_gap else 0.17
pb = lb[np.abs(lb[:, 0]) < xmax]
m["bust_girth_cm"] = round(float(ConvexHull(pb).area) * 100, 1); m["bust_level_m"] = round(zb, 3); m["bust_arm_exclusion_x_m"] = round(float(xmax), 3)
wz = [(z, ConvexHull(trunk_loop(z)).area) for z in np.linspace(0.95, 1.15, 41) if trunk_loop(z) is not None]
zw, gw = min(wz, key=lambda t: t[1]); m["waist_girth_cm"] = round(gw * 100, 1); m["waist_level_m"] = round(float(zw), 3)
hz = [(z, ConvexHull(trunk_loop(z)).area, float(np.ptp(trunk_loop(z)[:, 0]))) for z in np.linspace(0.72, 0.95, 47) if trunk_loop(z) is not None]
zh, gh_, _ = max(hz, key=lambda t: t[1]); m["hip_girth_cm"] = round(gh_ * 100, 1); m["hip_level_m"] = round(float(zh), 3)
zt, _, wt = max(hz, key=lambda t: t[2]); m["hip_width_cm"] = round(wt * 100, 1); m["trochanter_level_m"] = round(float(zt), 3)
m["leg_length_hip_to_floor_pct"] = round(100 * zt / H, 1)
cap = V[(np.abs(V[:, 0]) > 0.12) & (np.abs(V[:, 0]) < 0.20) & (V[:, 2] > 1.25)]; ztop = float(cap[:, 2].max())
band = V[(V[:, 2] > ztop - 0.06) & (V[:, 2] < ztop - 0.02)]
m["shoulder_breadth_deltoid_caps_cm"] = round(float(np.ptp(band[:, 0])) * 100, 1); m["shoulder_top_level_m"] = round(ztop, 3)
crotch = V[(np.abs(V[:, 0]) < 0.02) & (V[:, 2] < 1.0) & (V[:, 2] > 0.5)]; m["crotch_height_m"] = round(float(crotch[:, 2].min()), 3)
m["shoulder_to_hip_ratio"] = round(m["shoulder_breadth_deltoid_caps_cm"] / m["hip_width_cm"], 3)
m["guide"] = {"height_m": 1.68, "shoulder_width_cm": [37, 40], "bust_cm": [84, 92], "waist_cm": [64, 72], "hip_cm": [90, 98],
              "shoulder_hip_ratio": [0.95, 1.00], "leg_length_pct": [47, 50]}
(OUT / "female_source_measurements.json").write_text(json.dumps(m, indent=1)); print("MEAS", json.dumps(m))

sc = bpy.context.scene
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in eng else "BLENDER_EEVEE_NEXT"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.20, 0.21, 0.23, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
for nm, rot, en in (("key", (55, 0, 30), 3.2), ("fill", (70, 0, -55), 1.1), ("rim", (60, 0, 180), 1.8)):
    ld = bpy.data.lights.new(nm, "SUN"); ld.energy = en; ld.angle = math.radians(8)
    lo = bpy.data.objects.new(nm, ld); lo.rotation_euler = tuple(math.radians(x) for x in rot); sc.collection.objects.link(lo)
sc.view_settings.view_transform = "Standard"
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
VIEWS = {"front": (0, -1, 0), "back": (0, 1, 0), "left": (-1, 0, 0), "right": (1, 0, 0), "q34_fl": (-0.7, -0.7, 0.05), "q34_back": (0.7, 0.7, 0.05)}
tex_mats = list(me.materials)
clay = bpy.data.materials.new("clay"); clay.use_nodes = True; bs = clay.node_tree.nodes["Principled BSDF"]
bs.inputs["Base Color"].default_value = (0.66, 0.50, 0.41, 1); bs.inputs["Roughness"].default_value = 0.6
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.update()
for look in ("clay", "textured"):
    me.materials.clear()
    for mt in ([clay] if look == "clay" else tex_mats):
        me.materials.append(mt)
    for v, d in VIEWS.items():
        d = Vector(d).normalized(); cam.location = Vector((0, 0, 0.86)) + d * 6
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y"); cd.ortho_scale = 1.86
        sc.render.resolution_y = 1300; sc.render.resolution_x = 900 if v in ("front", "back", "q34_fl", "q34_back") else 560
        sc.render.filepath = str(OUT / f"F_{look}_{v}.png"); bpy.ops.render.render(write_still=True)
print("BASELINE done")
