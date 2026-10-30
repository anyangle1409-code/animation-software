"""EXPERIMENT (copy only): length response of the MG1 upper-arm envelopes through the curl, with Work's kernel.

For each elbow flexion angle the anatomical chain is posed natively (ulna and radius about the epicondyle axis, sign by
probe); each muscle's path is resolved from its PROPOSED anchors with kernel.resolve_path / kernel.path_length; the belly
length is the path less the MG1 tendon lengths (fixed); kernel.belly_axes (activation 0 - positioning only, no
activation display) gives the equal-volume radius.  (evaluate.evaluate is not used: it refuses unreviewed bindings by
design, and these anchors are unreviewed - nothing here is promoted.)

The response is stored per angle as a rest-space shape key on each belly, HGPT_LEN_ELBOW_<deg>, in the humeral axis's
cylindrical frame: the belly's stations move along the axis about its proximal end by k = L / L_rest, and each section
keeps its DEEP surface while the outer surface takes r_o'^2 = r_i^2 + (r_o^2 - r_i^2) / k - the section area scales by
1 / k, so the volume is kept (the kernel's equal-volume rule, belly_axes, applied to the section instead of a
cylinder) and the belly bulges towards the skin, not into the bone.  (Widening about each belly's own axis - the first
version - pushed bellies into the bone and their deep neighbours.)  The bellies ride the humerus; the armature binding
of the tendons does the rest.  MG_LAYERED=1 (default; MG3): superficial bellies (biceps over brachialis, triceps
lateral / long over triceps medial) keep their deep surface on the deep neighbour's NEW outer surface plus the gap, and
take their outer surface by the same area rule - layering instead of interpenetration; MG_LAYERED=0 reproduces MG2.  Measured per angle: belly volume against rest,
muscle-muscle triangle overlaps, and belly vertices outside the skin with the body posed by ITS OWN runtime rig to the
same elbow angle (the two skeletons are not linked - their elbow-centre distance is reported; skin crossings are a
diagnostic of where a skin response would be needed, not a failure of the proxy).  Saves a NEW blend; never the MG1 or
source blends.

usage: python3.13 arm_muscle_length_response_blender.py -- MG1.blend MG1_SHA256 anchors.json mg1_report.json OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.anatomical_muscles import kernel  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, mg1_p, outdir = Path(args[0]), args[1], Path(args[2]), Path(args[3]), Path(args[4])
SIDE = args[5] if len(args) > 5 else "left"
SUF = "L" if SIDE == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
import os
LAYERED = os.environ.get("MG_LAYERED", "1") == "1"         # MG3: superficial bellies pushed out by their deep neighbours
TAG = "MG3" if LAYERED else "MG2"
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_{TAG}_arm_{SIDE}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("MG1 blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; MW = anat.matrix_world.copy()
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
PROP = json.loads(anchors_p.read_text())["proposals"]
MG1 = json.loads(mg1_p.read_text())
ANGLES = [0, 45, 90, 120, 140]


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


GH, EJC = LM(f"scapula_{SIDE}__GH"), LM(f"humerus_{SIDE}__EJC")
AX = (EJC - GH).normalized(); LH_ = (EJC - GH).length
NPHI = int(json.loads(Path(args[3]).read_text())["rules"].get("nphi", 10))   # MG1 section samples per arc
GAP = 0.0012                                                # as MG1
F_ = Vector((0, -1, 0)); F_ = (F_ - AX * F_.dot(AX)).normalized()
L_ = Vector((1.0 if GH.x > 0 else -1.0, 0, 0)); L_ = (L_ - AX * L_.dot(AX) - F_ * L_.dot(F_)).normalized()
DEEP_OF = {"biceps_brachii_long": "brachialis", "biceps_brachii_short": "brachialis",
           "triceps_lateral": "triceps_medial", "triceps_long": "triceps_medial"}


def cyl(p):
    """(axial t from GH, phi deg (0 anterior, +90 lateral), radius) about the humeral axis"""
    t = (p - GH).dot(AX); q = p - (GH + AX * t)
    return t, math.degrees(math.atan2(q.dot(L_), q.dot(F_))), q.length


def outer_lookup(pos, nrings):
    """deep belly's outer radius as a function of (t, phi), from its (new) rings; None outside it"""
    rings = []
    for ring in range(nrings):
        pts = [cyl(pos[ring * 2 * NPHI + j]) for j in range(NPHI)]
        rings.append((pts[0][0], [(ph, r) for _t, ph, r in pts]))
    rings.sort(key=lambda x: x[0])

    def at_ring(rr, phi):
        mid = rr[len(rr) // 2][0]
        un = lambda a: mid + ((a - mid + 180.0) % 360.0 - 180.0)
        ph = [un(a) for a, _r in rr]; x = un(phi)
        lo, hi = min(ph), max(ph)
        if x < lo - 3.0 or x > hi + 3.0:                     # sector edges coincide (same inset): a superficial
            return None                                     # edge point at the deep edge's angle must still see it
        x = min(max(x, lo), hi)
        for (a0, r0), (a1, r1) in zip(zip(ph, [r for _a, r in rr]), zip(ph[1:], [r for _a, r in rr][1:])):
            if min(a0, a1) <= x <= max(a0, a1):
                return r0 if a1 == a0 else r0 + (r1 - r0) * (x - a0) / (a1 - a0)
        return None

    def f(t, phi):
        if t < rings[0][0] or t > rings[-1][0]:
            return None
        for (ta, ra), (tb, rb) in zip(rings, rings[1:]):
            if ta <= t <= tb:
                xa, xb = at_ring(ra, phi), at_ring(rb, phi)
                if xa is None or xb is None:
                    return xa if xb is None else xb
                return xa if tb == ta else xa + (xb - xa) * (t - ta) / (tb - ta)
        return None
    return f
EL, EM = LM(f"humerus_{SIDE}__epicondyle_lateral_skin"), LM(f"humerus_{SIDE}__epicondyle_medial_skin")
WJC = LM(f"radius_{SIDE}__WJC")
ELB = (EL - EM).normalized()
ULN, RAD = f"anat_ulna_{SIDE}", f"anat_radius_{SIDE}"
rot = lambda p, ax, deg: Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-p)
SG = 1.0 if ((rot(EJC, ELB, 5) @ WJC) - WJC).dot(Vector((0, -1, 0))) > 0 else -1.0
REST_ELB = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, (GH - EJC).normalized().dot((WJC - EJC).normalized())))))
RT = MG1["runtime_suffix_of_side"]


def pose_anat(deg):
    T = rot(EJC, ELB, SG * (deg - REST_ELB)) if deg > REST_ELB else Matrix()
    for bn in (ULN, RAD):
        anat.pose.bones[bn].matrix = MW.inverted() @ T @ MW @ anat.data.bones[bn].matrix_local
        bpy.context.view_layer.update()


def pose_runtime(deg):
    """the body's own rig: forearm flexion about its local X, sign chosen so the wrist moves anteriorly"""
    fb = rig.pose.bones[f"forearm_{RT}"]; fb.rotation_mode = "XYZ"
    best = None
    for sx in (1.0, -1.0):
        fb.rotation_euler = (math.radians(sx * deg), 0, 0); bpy.context.view_layer.update()
        y = (rig.matrix_world @ rig.pose.bones[f"hand_{RT}"].head).y
        if best is None or y < best[0]:
            best = (y, sx)
    fb.rotation_euler = (math.radians(best[1] * deg), 0, 0); bpy.context.view_layer.update()


def transforms():
    return {b.name: [list(r) for r in (MW @ b.matrix)] for b in anat.pose.bones}


MUS = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects if o.name.endswith(f".{SUF}")]
INFO = {}
for ob in MUS:
    mid = ob.name; rec = MG1["muscles"][mid]
    anchors = [{"bone": a["bone"], "local_m": a["local_m"]} for a in PROP[mid]["anchors"]]
    tend = rec["tendon_lengths_m"]; tsum = tend["origin"] + tend["insertion"]
    co = [v.co.copy() for v in ob.data.vertices]
    # rest belly axis: the two cap centres (the last two vertices built by MG1)
    c0, c1 = co[-2], co[-1]
    INFO[mid] = {"anchors": anchors, "tendon_sum": tsum, "c0": c0, "c1": c1, "co": co, "volume": rec["belly_volume_m3"]}
pose_anat(0.0)
T0 = transforms()
for mid, d in INFO.items():
    d["L_path_rest"] = kernel.path_length(kernel.resolve_path(d["anchors"], T0))
    d["L_belly_rest"] = d["L_path_rest"] - d["tendon_sum"]
    d["r_rest"] = kernel.belly_axes(d["volume"], d["L_belly_rest"], 0.0)[0]

# shape keys (rest space)
ob_by = {o.name: o for o in MUS}
for ob in MUS:
    if not ob.data.shape_keys:
        ob.shape_key_add(name="Basis", from_mix=False)
REP = {"status": "PROXY_LENGTH_RESPONSE_UNREVIEWED", "layered": LAYERED, "source": src.name, "source_sha256": expected, "side": SIDE,
       "kernel": "resolve_path / path_length / belly_axes (activation 0)", "evaluate_evaluate_not_used": "refuses unreviewed bindings by design",
       "rest_elbow_flexion_deg": round(REST_ELB, 1), "angles": {}}
for deg in ANGLES:
    pose_anat(max(deg, REST_ELB))
    T = transforms()
    rows = {}; NEW = {}
    for mid, d in INFO.items():
        L_path = kernel.path_length(kernel.resolve_path(d["anchors"], T))
        L_b = L_path - d["tendon_sum"]
        r = kernel.belly_axes(d["volume"], L_b, 0.0)[0]
        k = L_b / d["L_belly_rest"]; g = r / d["r_rest"]
        co = d["co"]; nv = len(co) - 2; N2 = 2 * NPHI
        if nv % N2:
            raise RuntimeError("unexpected MG1 vertex layout")
        t0 = (d["c0"] - GH).dot(AX)                         # proximal end of the belly, along the humeral axis
        shift = lambda p: AX * ((t0 + ((p - GH).dot(AX) - t0) * k) - (p - GH).dot(AX))
        new = [None] * len(co)
        for ring in range(nv // N2):
            base = ring * N2
            for j in range(NPHI):
                io, ii = base + j, base + N2 - 1 - j        # outer arc point j and its inner partner
                po, pi = co[io], co[ii]
                fo = GH + AX * ((po - GH).dot(AX)); fi = GH + AX * ((pi - GH).dot(AX))
                ro, ri = (po - fo).length, (pi - fi).length
                ro2 = math.sqrt(max(ri * ri + (ro * ro - ri * ri) / k, (ri + 1e-4) ** 2))
                new[io] = fo + (po - fo).normalized() * ro2 + shift(po)
                new[ii] = pi + shift(pi)
        for ci in (nv, nv + 1):                             # cap centres: mid-section, moved along the axis
            new[ci] = co[ci] + shift(co[ci])
        NEW[mid] = {"pos": new, "k": k, "nrings": nv // N2}
        rows[mid] = {"path_m": round(L_path, 4), "belly_length_m": round(L_b, 4), "k": round(k, 4), "radius_scale": round(g, 4)}
    if LAYERED:                                             # superficial bellies sit on their deep neighbours' new
        for mid, d in INFO.items():                         # outer surface (+ gap); outer surface by the area rule
            short = mid.split(".")[2]
            if short not in DEEP_OF:
                continue
            deep = f"hgpt.muscle.{DEEP_OF[short]}.{SUF}"
            look = outer_lookup(NEW[deep]["pos"], NEW[deep]["nrings"])
            co, new, k = d["co"], NEW[mid]["pos"], NEW[mid]["k"]
            nv = len(co) - 2; N2 = 2 * NPHI; pushed = 0; push_max = 0.0; RING_PUSH = {}
            for ring in range(nv // N2):
                base = ring * N2; dr_ring = []
                for j in range(NPHI):
                    io, ii = base + j, base + N2 - 1 - j
                    t, ph, ri_new = cyl(new[ii])
                    win = [look(t + dt * LH_, ph) for dt in (-0.012, -0.006, 0.0, 0.006, 0.012)]   # the deep surface can
                    win = [w for w in win if w is not None]                                       # peak between stations
                    rd = max(win) if win else None
                    if rd is None or rd + GAP <= ri_new:
                        continue
                    ri_rest, ro_rest = cyl(co[ii])[2], cyl(co[io])[2]
                    ri2 = rd + GAP
                    ro2 = math.sqrt(ri2 * ri2 + (ro_rest * ro_rest - ri_rest * ri_rest) / k)
                    fi = GH + AX * t; fo = GH + AX * cyl(new[io])[0]
                    new[ii] = fi + (new[ii] - fi).normalized() * ri2
                    new[io] = fo + (new[io] - fo).normalized() * ro2
                    pushed += 1; push_max = max(push_max, ri2 - ri_new); dr_ring.append(ri2 - ri_new)
                RING_PUSH[ring] = max(dr_ring) if dr_ring else 0.0
            for ci, ring in ((nv, 0), (nv + 1, nv // N2 - 1)):  # end-cap centres follow their ring's largest push
                if RING_PUSH.get(ring, 0.0) > 0:
                    t, _ph, r = cyl(new[ci]); fc = GH + AX * t
                    if r > 1e-6:
                        new[ci] = fc + (new[ci] - fc).normalized() * (r + RING_PUSH[ring])
            rows[mid].update({"layer_pushed_sections_points": pushed, "layer_push_max_mm": round(push_max * 1000, 1)})
    for mid, d in INFO.items():
        kb = ob_by[mid].shape_key_add(name=f"HGPT_LEN_ELBOW_{deg}", from_mix=False); kb.value = 0.0
        for i, p in enumerate(NEW[mid]["pos"]):
            kb.data[i].co = p
    REP["angles"][str(deg)] = {"muscles": rows}

# ------------------------------------------------------------------ evaluate each angle with its key on
VW_rest = None


def evaluated(ob):
    dg = bpy.context.evaluated_depsgraph_get(); e = ob.evaluated_get(dg); m = e.to_mesh()
    P = [e.matrix_world @ v.co for v in m.vertices]
    F = [p.vertices[:] for p in m.polygons]
    e.to_mesh_clear()
    return P, F


def volume(P, F):
    v = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            v += P[f[0]].dot(P[f[k]].cross(P[f[k + 1]])) / 6.0
    return abs(v)


for deg in ANGLES:
    pose_anat(max(deg, REST_ELB)); pose_runtime(deg)
    for ob in MUS:
        for kb in ob.data.shape_keys.key_blocks[1:]:
            kb.value = 1.0 if kb.name == f"HGPT_LEN_ELBOW_{deg}" else 0.0
    bpy.context.view_layer.update()
    BP, BF = evaluated(body)
    tris = [(f[0], f[k], f[k + 1]) for f in BF for k in range(1, len(f) - 1)]
    bvh_b = BVHTree.FromPolygons(BP, tris, all_triangles=True)
    trees, out = {}, {}
    for ob in MUS:
        P, F = evaluated(ob)
        vol = volume(P, F)
        outside = 0
        for p in P:
            loc, nrm, _i, _d = bvh_b.find_nearest(p)
            if loc is not None and (p - loc).dot(nrm) > 0:
                outside += 1
        tris_m = [(f[0], f[k], f[k + 1]) for f in F for k in range(1, len(f) - 1)]
        trees[ob.name] = BVHTree.FromPolygons(P, tris_m, all_triangles=True)
        REP["angles"][str(deg)]["muscles"][ob.name].update({"volume_vs_rest": round(vol / INFO[ob.name]["volume"], 4),
                                                             "vertices_outside_posed_skin": outside, "vertices": len(P)})
    names = list(trees); pairs = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            ov = trees[names[i]].overlap(trees[names[j]])
            if ov:
                pairs[f"{names[i].split('.')[2]} | {names[j].split('.')[2]}"] = len(ov)
    ejc_anat = MW @ anat.pose.bones[ULN].head
    ejc_rt = rig.matrix_world @ rig.pose.bones[f"forearm_{RT}"].head
    REP["angles"][str(deg)].update({"muscle_muscle_overlaps": pairs,
                                     "elbow_centre_anat_vs_runtime_mm": round((ejc_anat - ejc_rt).length * 1000, 1)})
    print("ANGLE", deg, json.dumps({m.split('.')[2]: (r["k"], r["radius_scale"], r["volume_vs_rest"], r["vertices_outside_posed_skin"])
                                    for m, r in REP["angles"][str(deg)]["muscles"].items()}), json.dumps(pairs), flush=True)

for ob in MUS:
    for kb in ob.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
pose_anat(REST_ELB); rig.pose.bones[f"forearm_{RT}"].rotation_euler = (0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
REP["output_blend"] = OUT.name; REP["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
REP["mg1_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

# ------------------------------------------------------------------ renders (lateral view): muscle-only and skin, per angle
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 620
skin_mat = bpy.data.materials.new("REVIEW_SKIN"); skin_mat.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin_mat)
TEN = list(bpy.data.collections["HGPT_EXPERIMENT_TENDONS"].objects)
lat = 1.0 if GH.x > 0 else -1.0
for ob in sc.objects:
    if ob.type == "MESH" and ob is not body and ob not in MUS and ob not in TEN:
        ob.hide_render = True
centre = EJC + (GH - EJC) * 0.35
files = {}
for deg in ANGLES:
    pose_anat(max(deg, REST_ELB)); pose_runtime(deg)
    for ob in MUS:
        for kb in ob.data.shape_keys.key_blocks[1:]:
            kb.value = 1.0 if kb.name == f"HGPT_LEN_ELBOW_{deg}" else 0.0
    bpy.context.view_layer.update()
    d = Vector((lat, 0, 0)); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    for tag, skin, mus in (("muscle", False, True), ("skin", True, False)):
        body.hide_render = not skin
        for o in MUS + TEN:
            o.hide_render = not mus
        f = outdir / f"{TAG.lower()}_{SIDE}_{deg:03d}_{tag}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files.setdefault(str(deg), []).append(f.name)
REP["renders"] = files
(outdir / f"{TAG.lower()}_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT.name, "mg1_unchanged": REP["mg1_unchanged"]}), flush=True)
