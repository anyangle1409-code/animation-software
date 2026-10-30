"""EXPERIMENT (copy only): upper-arm muscle belly / tendon ENVELOPE PROXIES inside the existing body, one anatomical side.

Work's handoff step 3 asks for tendon / belly geometry inside the existing body, in HGPT_EXPERIMENT_MUSCLES /
HGPT_EXPERIMENT_TENDONS collections of a copy, with reviewed volumes.  Reviewed volumes could not be obtained here
(the literature hosts are unreachable from this sandbox), so `tissue.rest_volume_m3` stays null and these meshes are
sized from THIS body instead: the space between the humeral shaft and the skin, less an authored subcutaneous layer,
split the way an upper-arm cross-section is -

  anterior compartment (phi -78..78 deg, 0 = anterior, +90 = lateral): biceps long head (lateral half) and short head
      (medial half) superficial, brachialis deep (distal half of the humerus);
  posterior compartment (98..262 deg): triceps lateral head (posterolateral) and long head (posteromedial)
      superficial, medial head deep (distal half);
  a superficial band is left for the deltoid on the lateral side of the proximal humerus (not built here).

Each belly is lofted between cross-section arcs along the humeral axis (GH -> EJC landmarks), tapers at both ends and
continues as a thin tendon to the PROPOSED (unreviewed) anchors of proposed_anchors_<side>.json.  All fractions,
sectors, ranges and thicknesses are authored rules recorded in the report - not anatomy, not fitted to data.  Every
object carries its permanent muscle ID; one neutral colour (no activation display).

Checks: every muscle vertex inside the skin and at least the subcutaneous layer below it; clear of the humeral shaft
radius; no muscle-muscle triangle overlaps; source hash unchanged.  Saves a NEW suffixed blend (never the source).
Renders: skin-only / muscle-only at rest (overlays composited outside Blender), and an elbow-flexion check (anatomical
chain posed natively; the probe records how far the distal biceps moved).

usage: python3.13 build_arm_muscle_envelopes_blender.py -- COPY.blend SHA256 anchors.json OUT_DIR [left|right]
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
src, expected, anchors_p, outdir = Path(args[0]), args[1], Path(args[2]), Path(args[3])
SIDE = args[4] if len(args) > 4 else "left"
SUF = "L" if SIDE == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
OUT_BLEND = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG1_arm_{SIDE}.blend"
if OUT_BLEND.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("copy hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
MW = anat.matrix_world.copy()
PROP = json.loads(anchors_p.read_text())["proposals"]

# ------------------------------------------------------------------ authored rules (recorded in the report)
FAT = 0.004            # skin + subcutaneous layer kept between muscle and skin (m); lean muscular adult, authored
GAP = 0.0012           # clearance between neighbouring envelopes (m)
SECTOR_INSET = 1.5     # deg trimmed from each sector edge
TENDON_R = 0.0035      # tendon proxy radius (m)
STEP = 0.02            # station spacing along the humerus (fraction of GH -> EJC)
NPHI = 10              # samples across a sector


def r_bone(s):
    """humeral radius proxy (m): 11 mm shaft, widening towards the head and the epicondyles (authored)"""
    sm = lambda x: 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)
    return 0.011 + 0.012 * sm((0.2 - s) / 0.2) + 0.010 * sm((s - 0.8) / 0.2)


def blend(s, a, b, s0, s1):
    t = min(1.0, max(0.0, (s - s0) / (s1 - s0))); t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def deltoid_reserve(s, phi):
    """fraction of the available thickness left for the deltoid (lateral, proximal; authored)"""
    if not (10 <= phi <= 170):
        return 0.0
    return blend(s, 0.45, 0.0, 0.10, 0.45)


MUS = {   # sector (deg, 0 anterior / +90 lateral, increasing), radial band (fraction of available), axial range (s)
    "biceps_brachii_long": {"sector": (2, 78), "band": (lambda s: blend(s, 0.12, 0.55, 0.40, 0.50), lambda s: 1.0),
                            "range": (0.22, 0.86), "distal": "radius"},
    "biceps_brachii_short": {"sector": (-78, -2), "band": (lambda s: blend(s, 0.12, 0.55, 0.40, 0.50), lambda s: 1.0),
                             "range": (0.24, 0.86), "distal": "radius"},
    "brachialis": {"sector": (-78, 78), "band": (lambda s: 0.0, lambda s: blend(s, 0.12, 0.55, 0.40, 0.50)),
                   "range": (0.45, 0.97), "distal": "ulna"},
    "triceps_lateral": {"sector": (98, 178), "band": (lambda s: blend(s, 0.05, 0.45, 0.33, 0.43), lambda s: 1.0),
                        "range": (0.18, 0.86), "distal": "ulna"},
    "triceps_long": {"sector": (182, 262), "band": (lambda s: blend(s, 0.05, 0.45, 0.33, 0.43), lambda s: 1.0),
                     "range": (0.14, 0.86), "distal": "ulna"},
    "triceps_medial": {"sector": (98, 262), "band": (lambda s: 0.0, lambda s: blend(s, 0.05, 0.45, 0.33, 0.43)),
                       "range": (0.38, 0.97), "distal": "ulna"},
}
TAPER = 0.07           # taper length at each belly end (fraction of the humerus)


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


GH, EJC = LM(f"scapula_{SIDE}__GH"), LM(f"humerus_{SIDE}__EJC")
EL, EM = LM(f"humerus_{SIDE}__epicondyle_lateral_skin"), LM(f"humerus_{SIDE}__epicondyle_medial_skin")
WJC = LM(f"radius_{SIDE}__WJC")
AX = (EJC - GH).normalized(); LH = (EJC - GH).length
lat_sign = 1.0 if GH.x > 0 else -1.0
F_ = Vector((0, -1, 0)); F_ = (F_ - AX * F_.dot(AX)).normalized()                       # anterior, in the section
L_ = Vector((lat_sign, 0, 0)); L_ = (L_ - AX * L_.dot(AX) - F_ * L_.dot(F_)).normalized()  # lateral, in the section


def dir_of(phi_deg):
    p = math.radians(phi_deg)
    return F_ * math.cos(p) + L_ * math.sin(p)


# ------------------------------------------------------------------ skin cross-sections of the arm
GN = [g.name for g in body.vertex_groups]
rt = None
for cand in ("r", "l"):          # runtime suffix of this anatomical side: the upperarm group on GH's side of x = 0
    gi = GN.index(f"upperarm_{cand}")
    xs = [body.matrix_world @ v.co for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    if xs and (sum(p.x for p in xs) / len(xs)) * lat_sign > 0:
        rt = cand
ARMG = {GN.index(n) for n in (f"upperarm_{rt}", f"forearm_{rt}", f"shoulder_cap_{rt}", f"forearm_tw0_{rt}")}
VW = [body.matrix_world @ v.co for v in body.data.vertices]
ARMV = [sum(g.weight for g in v.groups if g.group in ARMG) > 0.5 for v in body.data.vertices]
TRIS = []
for p in body.data.polygons:
    vs = p.vertices[:]
    for k in range(1, len(vs) - 1):
        TRIS.append((vs[0], vs[k], vs[k + 1]))
ARM_TRIS = [t for t in TRIS if all(ARMV[i] for i in t)]
NB = 72
R_CAP = 0.065          # section points farther than this from the humeral axis are shoulder / torso skin, not arm


def skin_profile(s):
    """outer skin radius (m) per 5 deg bin around the humeral axis at station s (plane cut through the arm skin)"""
    c = GH + AX * (s * LH)
    R = [0.0] * NB
    for t in ARM_TRIS:
        d = [(VW[i] - c).dot(AX) for i in t]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (d[a] > 0) != (d[b] > 0):
                q = VW[t[a]].lerp(VW[t[b]], d[a] / (d[a] - d[b])) - c
                r = q.length
                if r > R_CAP:
                    continue
                phi = math.degrees(math.atan2(q.dot(L_), q.dot(F_))) % 360.0
                k = int(phi / (360.0 / NB)) % NB
                R[k] = max(R[k], r)
    known = [k for k in range(NB) if R[k] > 0]
    if len(known) < NB // 3:
        raise RuntimeError(f"skin section too sparse at s={s:.2f}")
    out = []
    for k in range(NB):                                       # fill empty bins circularly
        if R[k] > 0:
            out.append(R[k]); continue
        lo = max((j for j in known if j < k), default=known[-1] - NB)
        hi = min((j for j in known if j > k), default=known[0] + NB)
        t = (k - lo) / (hi - lo)
        out.append(R[lo % NB] * (1 - t) + R[hi % NB] * t)
    return [(out[k - 1] + out[k] + out[(k + 1) % NB]) / 3.0 for k in range(NB)]   # light smoothing


PROFILES = {}


def skin_r(s, phi):
    key = round(s, 4)
    if key not in PROFILES:
        PROFILES[key] = skin_profile(s)
    P = PROFILES[key]
    x = (phi % 360.0) / (360.0 / NB) - 0.5
    k0 = math.floor(x); t = x - k0
    return P[k0 % NB] * (1 - t) + P[(k0 + 1) % NB] * t


# ------------------------------------------------------------------ envelopes
def section(spec, s, tau=1.0):
    """cross-section polygon (outer arc, then inner arc back) at station s; tau < 1 narrows it in POLAR terms - the
    angular span about the sector middle and the radial band about its middle radius - so a tapering end stays in its
    compartment (shrinking towards the Euclidean centroid put the wide deep bands' ends inside the bone)"""
    a0, a1 = spec["sector"][0] + SECTOR_INSET, spec["sector"][1] - SECTOR_INSET
    am, ah = (a0 + a1) / 2.0, (a1 - a0) / 2.0 * max(tau, 0.12)
    a0, a1 = am - ah, am + ah
    c = GH + AX * (s * LH)
    rb = r_bone(s)
    outer, inner = [], []
    for j in range(NPHI):
        phi = a0 + (a1 - a0) * j / (NPHI - 1)
        avail = skin_r(s, phi) - FAT - rb
        if avail <= 0.004:
            avail = 0.004
        fo = min(spec["band"][1](s), 1.0 - deltoid_reserve(s, phi))
        fi = spec["band"][0](s)
        ro = rb + fo * avail - (GAP if fo < 1.0 else 0.0)
        ri = rb + fi * avail + (GAP if fi > 0.0 else 0.0005)
        if ro - ri < 0.002:
            ro = ri + 0.002
        rm_, rh_ = (ro + ri) / 2.0, (ro - ri) / 2.0 * max(tau, 0.25)
        ro, ri = rm_ + rh_, rm_ - rh_
        d = dir_of(phi)
        outer.append(c + d * ro); inner.append(c + d * ri)
    return outer + inner[::-1]


BVH_BODY = BVHTree.FromPolygons(VW, TRIS, all_triangles=True)


def clamp_depth(ring):
    """keep every point at least the subcutaneous layer below the skin (whole body surface, so the axilla counts):
    shallower or outside points move radially towards the humeral axis"""
    out = []
    for p in ring:
        for _ in range(3):
            loc, nrm, _i, dist = BVH_BODY.find_nearest(p)
            depth = -dist if (p - loc).dot(nrm) > 0 else dist
            if depth >= FAT - 1e-4:
                break
            c = GH + AX * ((p - GH).dot(AX))
            r = p - c
            if r.length < 1e-6:
                break
            sb = (p - GH).dot(AX) / LH                      # never inside the humeral radius (the skin wins
            floor = r_bone(sb) + 0.0015 if 0.0 < sb < 1.0 else 0.002   # only down to the bone: reported, not hidden)
            if r.length <= floor + 1e-6:
                break
            p = c + r.normalized() * max(r.length - (FAT - depth), floor)
        out.append(p)
    return out


def build(mid, spec):
    s0, s1 = spec["range"]
    n = max(4, int(round((s1 - s0) / STEP)))
    rings = []
    for k in range(n + 1):
        s = s0 + (s1 - s0) * k / n
        tau = min(1.0, (s - s0) / TAPER, (s1 - s) / TAPER)
        tau = tau * tau * (3 - 2 * tau)
        rings.append(clamp_depth(section(spec, s, tau)))
    verts, faces = [], []
    m = len(rings[0])
    for ring in rings:
        verts.extend(ring)
    for k in range(len(rings) - 1):
        for j in range(m):
            a, b = k * m + j, k * m + (j + 1) % m
            faces.append((a, b, b + m, a + m))
    c0 = sum(rings[0], Vector()) / m; c1 = sum(rings[-1], Vector()) / m
    i0 = len(verts); verts.append(c0); i1 = len(verts); verts.append(c1)
    for j in range(m):
        faces.append((i0, (j + 1) % m, j))
        faces.append((i1, (len(rings) - 1) * m + j, (len(rings) - 1) * m + (j + 1) % m))
    me = bpy.data.meshes.new(mid)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate(); me.update()
    return me, c0, c1


def tube(name, a, b, r=TENDON_R, n=8):
    d = (b - a); L = d.length; z = d.normalized()
    x = z.orthogonal().normalized(); y = z.cross(x)
    verts = [a + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    verts += [b + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    faces += [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, L


def mesh_volume(me):
    v = 0.0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            v += vs[0].dot(vs[k].cross(vs[k + 1])) / 6.0
    return abs(v)


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


C_MUS, C_TEN, C_WRAP = coll("HGPT_EXPERIMENT_MUSCLES"), coll("HGPT_EXPERIMENT_TENDONS"), coll("HGPT_EXPERIMENT_WRAP_GUIDES")
mat_m = bpy.data.materials.new("HGPT_EXPERIMENT_MUSCLE_NEUTRAL"); mat_m.diffuse_color = (0.62, 0.22, 0.20, 1)
mat_t = bpy.data.materials.new("HGPT_EXPERIMENT_TENDON_NEUTRAL"); mat_t.diffuse_color = (0.86, 0.84, 0.76, 1)
HUM, RAD, ULN, SCA = (f"anat_humerus_{SIDE}", f"anat_radius_{SIDE}", f"anat_ulna_{SIDE}", f"anat_scapula_{SIDE}")
# R41's anatomical master is a guide skeleton: its bones do not deform (use_deform False), so an armature modifier would
# ignore them.  In this COPY only, the four bones the proxies are weighted to are switched to deform; no rest data
# changes, and the body is driven by the runtime rig (its armature modifier), not by this skeleton.
DEFORM_ON = []
for bn in (SCA, HUM, RAD, ULN):
    if not anat.data.bones[bn].use_deform:
        anat.data.bones[bn].use_deform = True; DEFORM_ON.append(bn)
BODY_ARM_OBJ = [m.object.name for m in body.modifiers if m.type == "ARMATURE" and m.object]


def bind(ob, weights):
    """armature binding to the anatomical chain: weights = function(world point) -> {bone: w}"""
    for v in ob.data.vertices:
        for bn, w in weights(ob.matrix_world @ v.co).items():
            g = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
            g.add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("HGPT_ANATOMICAL_CHAIN", "ARMATURE"); mod.object = anat


def s_of(p):
    return (p - GH).dot(AX) / LH


def arm_weights(distal_bone, prox_bone=HUM, prox_until=None):
    def w(p):
        s = s_of(p)
        t = min(1.0, max(0.0, (s - 0.86) / 0.14))
        out = {HUM: 1.0 - t, distal_bone: t}
        if prox_until is not None and s < prox_until:
            u = min(1.0, max(0.0, (prox_until - s) / prox_until))
            out = {prox_bone: u, HUM: (1.0 - u) * (1.0 - t), distal_bone: t * (1.0 - u)}
        return {k: v for k, v in out.items() if v > 1e-4}
    return w


REP = {"status": "ENVELOPE_PROXY_UNREVIEWED", "source_sha256": expected, "side": SIDE, "runtime_suffix_of_side": rt,
       "copy_only_changes": {"anatomical_master_use_deform_enabled": DEFORM_ON, "body_armature_modifier_objects": BODY_ARM_OBJ},
       "rules": {"subcutaneous_layer_m": FAT, "gap_m": GAP, "sector_inset_deg": SECTOR_INSET, "tendon_radius_m": TENDON_R,
                 "humeral_radius_m": "11 mm shaft, +12 mm towards the head (s<0.2), +10 mm towards the epicondyles (s>0.8)",
                 "deltoid_reserve": "lateral 10-170 deg: 45 % of the available thickness at s=0.10 fading to 0 at s=0.45",
                 "taper": TAPER, "sections": {m: {"sector_deg": v["sector"], "range_s": v["range"], "distal_bone": v["distal"]} for m, v in MUS.items()},
                 "axis": "GH -> EJC landmarks", "s": "fraction of GH -> EJC"},
       "volume_source": "geometry-derived from this body (NOT reviewed literature volumes: hosts unreachable from the sandbox)",
       "muscles": {}}
OBJS = []
for m, spec in MUS.items():
    mid = f"hgpt.muscle.{m}.{SUF}"
    anchors = {a["role"]: Vector(a["world_rest_m"]) for a in PROP[mid]["anchors"]}
    me, c0, c1 = build(mid, spec)
    me.materials.append(mat_m)
    ob = bpy.data.objects.new(mid, me); C_MUS.objects.link(ob); OBJS.append(ob)
    ob["hgpt_muscle_id"] = mid; ob["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"; ob["hgpt_activation_display"] = False
    distal = RAD if spec["distal"] == "radius" else ULN
    prox_bone = SCA if PROP[mid]["anchors"][0]["bone"] == SCA else HUM
    bind(ob, arm_weights(distal))
    tendons = {}
    for role, c in (("origin", c0), ("insertion", c1)):
        tm, tl = tube(f"{mid}.tendon_{role}", c, anchors[role]); tm.materials.append(mat_t)
        to = bpy.data.objects.new(tm.name, tm); C_TEN.objects.link(to)
        to["hgpt_muscle_id"] = mid; to["hgpt_tendon_role"] = role; to["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"
        if role == "origin":
            bind(to, lambda p, pb=prox_bone: ({pb: 1.0} if pb == SCA and (p - anchors["origin"]).length < 0.03 else {HUM: 1.0}))
        else:
            bind(to, lambda p, d=distal: ({d: 1.0} if (p - anchors["insertion"]).length < 0.03 else arm_weights(d)(p)))
        tendons[role] = round(tl, 4)
    vol = mesh_volume(me)
    belly_len = (c1 - c0).length
    REP["muscles"][mid] = {"belly_volume_m3": round(vol, 7), "belly_volume_cm3": round(vol * 1e6, 1),
                           "belly_length_m": round(belly_len, 4), "tendon_lengths_m": tendons,
                           "kernel_equivalent_radius_m": round(math.sqrt(vol / (math.pi * belly_len)), 4)}
    print("MUSCLE", mid, json.dumps(REP["muscles"][mid]), flush=True)

# ------------------------------------------------------------------ checks
bpy.context.view_layer.update()
bvh_body = BVH_BODY
chk = {}
for ob in OBJS:
    P = [ob.matrix_world @ v.co for v in ob.data.vertices]
    outside, shallow, bone = 0, 0, 0
    min_depth = 1.0
    for p in P:
        loc, nrm, _, dist = bvh_body.find_nearest(p)
        if (p - loc).dot(nrm) > 0:
            outside += 1
        else:
            min_depth = min(min_depth, dist)
            if dist < FAT - 0.0015:
                shallow += 1
        s = s_of(p); radial = ((p - GH) - AX * ((p - GH).dot(AX))).length
        if 0.0 < s < 1.0 and radial < r_bone(s) - 1e-4:
            bone += 1
    chk[ob.name] = {"vertices": len(P), "outside_skin": outside, "shallower_than_layer": shallow,
                    "min_depth_below_skin_mm": round(min_depth * 1000, 2), "inside_humeral_radius": bone}
pairs = {}
trees = {ob.name: BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get()) for ob in OBJS}
names = list(trees)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        ov = trees[names[i]].overlap(trees[names[j]])
        if ov:
            pairs[f"{names[i]} | {names[j]}"] = len(ov)
REP["checks"] = {"per_muscle": chk, "muscle_muscle_overlap_pairs": pairs}
print("CHECKS", json.dumps(REP["checks"]), flush=True)

# ------------------------------------------------------------------ save the NEW experiment and confirm the source
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND), copy=True)
REP["output_blend"] = OUT_BLEND.name
REP["output_sha256"] = hashlib.sha256(OUT_BLEND.read_bytes()).hexdigest()
REP["source_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

# ------------------------------------------------------------------ renders: rest (skin / muscle / both) and elbow flexion
sc = bpy.context.scene
cam_d = bpy.data.cameras.new("C"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 0.46
cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 700
skin_mat = bpy.data.materials.new("REVIEW_SKIN"); skin_mat.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin_mat)
for ob in sc.objects:
    if ob.type == "MESH" and ob is not body and ob.name not in [o.name for o in OBJS] and not ob.name.startswith("hgpt.muscle."):
        ob.hide_render = True
TEN = [o for o in C_TEN.objects]


def shoot(tag, show_skin, show_mus, centre):
    body.hide_render = not show_skin
    for o in OBJS + TEN:
        o.hide_render = not show_mus
    out = []
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat_sign, 0, 0), "posterior": (0, 1, 0)}.items():
        d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        f = outdir / f"mg1_{SIDE}_{tag}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        out.append(f.name)
    return out


mid_c = (GH + EJC) / 2 + AX * 0.02
REP["renders"] = {"rest_skin": shoot("rest_skin", True, False, mid_c), "rest_muscle": shoot("rest_muscle", False, True, mid_c)}
anat.data.pose_position = "POSE"                              # (renders only - the blend was saved above)
probe_ob = bpy.data.objects[f"{OBJS[0].name}.tendon_insertion"]   # the biceps belly rides the humerus; its tendon the radius
probe_v = max(range(len(probe_ob.data.vertices)), key=lambda i: (probe_ob.data.vertices[i].co - GH).dot(AX))
# elbow flexion on the anatomical chain (rigid, about the epicondyle axis; sign by probe: the wrist moves anteriorly)
ELB = (EL - EM).normalized()
rot = lambda p, ax, deg: Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-p)
sg = 1.0 if ((rot(EJC, ELB, 5) @ WJC) - WJC).dot(Vector((0, -1, 0))) > 0 else -1.0
for deg in (90, 120):
    T = rot(EJC, ELB, sg * deg)
    for bn in (ULN, RAD):
        anat.pose.bones[bn].matrix = MW.inverted() @ T @ MW @ anat.data.bones[bn].matrix_local
        bpy.context.view_layer.update()
    dg_ = bpy.context.evaluated_depsgraph_get(); ev = probe_ob.evaluated_get(dg_); em = ev.to_mesh()
    REP.setdefault("flex_probe_moved_mm", {})[str(deg)] = round((em.vertices[probe_v].co - probe_ob.data.vertices[probe_v].co).length * 1000, 1)
    ev.to_mesh_clear()
    REP["renders"][f"flex{deg}_muscle"] = shoot(f"flex{deg}_muscle", False, True, mid_c)
for bn in (ULN, RAD):
    anat.pose.bones[bn].matrix_basis = Matrix()
(outdir / f"mg1_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT_BLEND.name, "source_unchanged": REP["source_unchanged"]}), flush=True)
