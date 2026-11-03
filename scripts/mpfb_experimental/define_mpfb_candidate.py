"""EXPERIMENTAL REFERENCE ONLY - NOT PRODUCTION GEOMETRY.

Muscle-definition relief for an MPFB benchmark body (build_mpfb_candidate.py output).  MakeHuman targets shape volumes
only; the owner's photographs show lean definition (abdominal segments, pectoral borders, deltoid / arm / thigh / calf
separations, spinal groove).  This pass applies the posed pose and subdivision to a static copy, then displaces the
skin along its normals with smooth Gaussian grooves and bulges placed from the rig's bone positions (no hand-painted
data), smooths the field and renders the same eight views as the builder.  Depths in mm scale with V2_DEF (default 1).

usage: BLENDER_USER_RESOURCES=<dir> python3.13 define_mpfb_candidate.py -- <mpfb_candidate.blend> <out dir>
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
K = float(os.environ.get("V2_DEF", "1.0")) / 1000.0
bpy.ops.wm.open_mainfile(filepath=str(SRC))
rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
body = max((o for o in bpy.data.objects if o.type == "MESH" and "FLOOR" not in o.name), key=lambda o: len(o.data.vertices))
for o in bpy.data.objects:
    o.hide_render = o.type == "MESH" and o is not body and "FLOOR" not in o.name
sub = body.modifiers.get("SUBDIV_REVIEW")
if sub:
    sub.levels = sub.render_levels = 2
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
new = bpy.data.objects.new("MPFB_DEFINED_REVIEW", me); bpy.context.scene.collection.objects.link(new)
new.matrix_world = body.matrix_world.copy(); body.hide_render = True
n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
mw = np.array(new.matrix_world); W = V @ mw[:3, :3].T + mw[:3, 3]
me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
N = np.empty(n * 3); me.vertices.foreach_get("normal", N); N = N.reshape(-1, 3) @ mw[:3, :3].T
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
GN = {g.index: g.name for g in body.vertex_groups}
G = {}
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(n))[v.index] = g.weight
gw = lambda *ks: sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n))
B = {b.name: (np.array(rig.matrix_world @ b.head), np.array(rig.matrix_world @ b.tail)) for b in rig.pose.bones}
armw, legw = gw("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky"), gw("thigh", "calf", "foot", "ball")
trunk = (armw < 0.3) & (legw < 0.5)
x, y, z = W[:, 0], W[:, 1], W[:, 2]; ax = np.abs(x)
front, back = trunk & (N[:, 1] < -0.3), trunk & (N[:, 1] > 0.3)
D = np.zeros(n)


def gauss(d, s):
    return np.exp(-0.5 * (d / s) ** 2)


def ramp(v, lo, hi):
    t = np.clip((v - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)


def band(v, lo, hi, f=0.01):
    return ramp(v, lo - f, lo + f) * (1 - ramp(v, hi - f, hi + f))


def seg_dist(P2, a2, b2):
    ab = b2 - a2; t = np.clip(((P2 - a2) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(P2 - (a2 + t[:, None] * ab), axis=1), t


def line_xz(mask, p0, p1, depth, s):
    """groove (depth < 0) or ridge along the segment p0 -> p1 in the |x|-z plane, on the masked skin"""
    d, t = seg_dist(np.c_[ax, z], np.array(p0), np.array(p1))
    D[:] += mask * depth * gauss(d, s) * ramp(t, 0.0, 0.08) * (1 - ramp(t, 0.92, 1.0))


pel, sp3, clav = B["pelvis"][0], B["spine_03"][0], B["clavicle_l"][0]
zn = pel[2] + 0.095                                          # navel
zx = sp3[2] + 0.03                                           # xiphoid region
znip = zx + 0.085                                            # nipple line
# --- abdomen: linea alba, three tendinous intersections, linea semilunaris, inguinal lines
line_xz(front, (0, zn - 0.03), (0, zx), -2.6 * K, 0.0055)
for zi, w in ((zn + 0.045, 0.060), (zn + 0.095, 0.064), (zn + 0.145, 0.066)):
    d = np.abs(z - (zi + 0.010 * (ax / w) ** 2))
    D[:] += front * -2.2 * K * gauss(d, 0.0045) * (1 - ramp(ax, w - 0.012, w + 0.004))
for s_ in (1,):
    line_xz(front, (0.072, zx), (0.060, zn - 0.04), -2.6 * K, 0.0065)
    line_xz(front, (0.060, zn - 0.04), (0.035, pel[2] - 0.05), -2.0 * K, 0.006)
line_xz(front, (0.125, pel[2] + 0.04), (0.035, pel[2] - 0.07), -2.2 * K, 0.007)   # inguinal ("Adonis") line
# --- chest: sternal groove, lower pectoral border with the pectoral mass above it, deltopectoral groove
line_xz(front, (0, znip - 0.04), (0, clav[2] - 0.05), -2.2 * K, 0.007)
xb = np.clip(ax, 0.015, 0.17); zb = znip - 0.050 + float(os.environ.get('V2_PEC_RISE', '0.075')) * ((xb - 0.015) / 0.155) ** 1.6
pm = front & (ax < 0.17)
D[:] += pm * -3.0 * K * gauss(z - zb, 0.0075)
D[:] += pm * float(os.environ.get('V2_PEC_MASS', '2.0')) * K * gauss(z - (zb + 0.04), 0.022) * (1 - ramp(ax, 0.13, 0.17))
gh = B["upperarm_l"][0]
line_xz(trunk | (armw > 0), (abs(clav[0]) + 0.10, clav[2] - 0.035), (abs(gh[0]) - 0.025, gh[2] - 0.10), -2.6 * K, 0.007)


def limb(bone, w_mask, feats):
    """cylindrical features around a bone: (t0, t1, angle centre deg (0 = lateral, 90 = front), angle width deg, depth)"""
    for sd in ("l", "r"):
        h, t = B[bone.format(sd)]; L = np.linalg.norm(t - h); a_ = (t - h) / L
        sel = w_mask(sd)
        rel = W - h; tt = rel @ a_ / L; rad = rel - np.outer(rel @ a_, a_)
        lat = np.array([np.sign(h[0]) or 1.0, 0, 0]); lat = lat - a_ * (lat @ a_); lat /= np.linalg.norm(lat)
        fr = np.cross(a_, lat) if np.cross(a_, lat)[1] < 0 else -np.cross(a_, lat)
        ang = np.degrees(np.arctan2(rad @ fr, rad @ lat))
        for t0, t1, ac, aw, dep in feats:
            da = (ang - ac + 180) % 360 - 180
            D[:] += sel * dep * K * band(tt, t0, t1, 0.05) * gauss(da, aw)


limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.45,
     [(0.38, 0.52, 0, 35, -2.0), (0.45, 0.92, 15, 9, -2.0), (0.45, 0.92, 180, 10, -1.6), (0.15, 0.40, 0, 60, 1.2)])
limb("lowerarm_{}", lambda s: G.get(f"lowerarm_{s}", np.zeros(n)) > 0.5, [(0.10, 0.55, 60, 12, -1.4)])
limb("thigh_{}", lambda s: G.get(f"thigh_{s}", np.zeros(n)) > 0.5,
     [(0.30, 0.85, 35, 9, -2.4), (0.15, 0.75, 125, 9, -1.8), (0.30, 0.90, -5, 10, -1.4),
      (0.74, 0.92, 135, 22, 3.2), (0.55, 0.85, 70, 25, 1.4)])
limb("calf_{}", lambda s: G.get(f"calf_{s}", np.zeros(n)) > 0.5,
     [(0.10, 0.42, -125, 25, 2.6), (0.10, 0.38, -60, 22, 1.8), (0.12, 0.40, -92, 8, -1.4), (0.42, 0.52, -90, 70, -1.6)])
# --- back: spinal groove between the erector columns, lower latissimus border, lower trapezius, scapular border
line_xz(back, (0, pel[2] - 0.02), (0, clav[2] - 0.08), -3.2 * K, 0.008)
line_xz(back, (0.020, pel[2] + 0.02), (0.020, sp3[2] + 0.08), 1.6 * K, 0.012)
line_xz(back, (abs(gh[0]) - 0.06, gh[2] - 0.15), (0.075, pel[2] + 0.07), -2.0 * K, 0.008)
line_xz(back, (0.02, sp3[2]), (0.11, gh[2] - 0.05), -1.5 * K, 0.008)
line_xz(back, (0.075, gh[2] - 0.02), (0.095, gh[2] - 0.16), -1.4 * K, 0.007)
# --- added 3 Nov (owner: "better definition"): serratus digitations, external oblique border, deltoid head separations,
# infraspinatus / teres border
sideF = trunk & (np.abs(N[:, 0]) > 0.35) & (N[:, 1] < 0.35)
for k_ in range(3):
    zc = znip - 0.035 - 0.028 * k_
    line_xz(sideF, (abs(gh[0]) - 0.075, zc + 0.012), (abs(gh[0]) - 0.105, zc - 0.012), -1.8 * K, 0.005)
line_xz(trunk & (N[:, 1] < 0.2), (0.115, zx - 0.01), (0.120, pel[2] + 0.06), -1.8 * K, 0.008)
line_xz(back, (abs(gh[0]) - 0.075, gh[2] - 0.05), (abs(gh[0]) - 0.02, gh[2] - 0.11), -1.6 * K, 0.007)
limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.3, [(0.02, 0.36, 50, 8, -1.6), (0.02, 0.36, -45, 8, -1.6)])
# --- added (owner: biceps-to-forearm transition, legs): brachioradialis / extensor mass on the upper forearm, the
# biceps' lower end tapering into the elbow crease, quadriceps (vastus lateralis) mass, patella outline
limb("lowerarm_{}", lambda s: G.get(f"lowerarm_{s}", np.zeros(n)) > 0.3, [(0.0, 0.45, 40, 30, 2.2), (0.0, 0.45, 120, 28, 1.4), (0.05, 0.6, 90, 9, -1.2)])
limb("upperarm_{}", lambda s: G.get(f"upperarm_{s}", np.zeros(n)) > 0.3, [(0.55, 0.85, 95, 30, 1.6), (0.88, 1.0, 95, 40, -1.6)])
limb("thigh_{}", lambda s: G.get(f"thigh_{s}", np.zeros(n)) > 0.4, [(0.25, 0.80, 15, 25, 2.2), (0.10, 0.60, 95, 30, 1.6), (0.92, 1.02, 90, 50, -1.5)])
# smooth the field a little (no faceting on the subdivided mesh), then displace along the normals
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
for _ in range(3):
    D = 0.5 * D + 0.5 * (A @ D) * Dinv
Nl = np.empty(n * 3); me.vertices.foreach_get("normal", Nl); Nl = Nl.reshape(-1, 3)
me.vertices.foreach_set("co", (V + D[:, None] * Nl).ravel()); me.update()
# render (same cameras / light / material as build_mpfb_candidate.py)
sc = bpy.context.scene; cam = sc.camera; cd = cam.data
me.materials.clear(); me.materials.append(body.data.materials[0])
from mathutils import Vector as Vec  # noqa: E402
z0 = float(W[:, 2].min()); H = float(W[:, 2].max() - z0)
VIEWS = {"front": ((0, -1, 0), 0.635, 2.45), "side": ((1, 0, 0), 0.635, 2.45), "back": ((0, 1, 0), 0.635, 2.45),
         "front34": ((0.7071, -0.7071, 0), 0.635, 2.45), "front_upper": ((0, -1, 0), 0.80, 1.05),
         "side_upper": ((1, 0, 0), 0.80, 1.05), "back_upper": ((0, 1, 0), 0.80, 1.05),
         "front34_upper": ((0.7071, -0.7071, 0), 0.80, 1.05)}
sc.render.resolution_x, sc.render.resolution_y = int(os.environ.get("V2_RES_X", "720")), int(os.environ.get("V2_RES_Y", "1280"))
for view, (dv, hc, scale) in VIEWS.items():
    dvec = Vec(dv) + Vec((0.0, 0.0, 0.12)); dvec.normalize(); centre = Vec((0.0, 0.0, z0 + hc * H))
    cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"; cd.ortho_scale = scale * H / 1.856
    cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
    sc.render.filepath = str(OUT / f"stand_{view}_000.png"); bpy.ops.render.render(write_still=True)
rep = {"source": SRC.name, "def_scale": K * 1000, "vertices": n, "max_in_mm": round(float(D.min()) * 1000, 2),
       "max_out_mm": round(float(D.max()) * 1000, 2), "moved_over_0.5mm": int((np.abs(D) > 5e-4).sum())}
(OUT / "define_report.json").write_text(json.dumps(rep, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mpfb_candidate_defined.blend"))
print("DEFINE", json.dumps(rep), flush=True)
