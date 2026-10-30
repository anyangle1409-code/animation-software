"""EXPERIMENT (copy only): deltoid ENVELOPE PROXIES (anterior / middle / posterior heads) over the MG1 arm envelopes.

The deltoid runs along the shaft and caps the humeral head, so each head is built in two parts: along the shaft
(s 0.40 -> 0.12 of GH -> EJC) as cylindrical sections filling exactly the reserve band MG1 left for it (inner surface =
where MG1's envelopes stop + the gap: no overlap by construction), and over the head in a GH-centred spherical frame
(from a 58 deg cone, whose ring lies wholly above the last shaft ring, to the origin): theta from the humeral axis (0 = down the arm, 180 = straight up),
phi about it (0 anterior, +90 lateral, 180 posterior, -90 medial).  For each direction a ray from the GH centre finds
the skin (first hit on the body); the head occupies

  directions: from its insertion end (theta_lo, narrow phi share of the deltoid tuberosity) to its origin direction
      (theta / phi of its PROPOSED origin anchor less an aponeurotic margin), its phi span widening from insertion to
      origin; anterior head spans phi -45..55 at the top (lateral third of the clavicle, up to the AC joint at about 72 deg),
      middle 58..139 (acromion), posterior 141..210 (spine of the scapula);
  radius: outer = skin - subcutaneous layer; inner = the deepest of (a) the humeral head + a rotator-cuff reserve,
      (b) the humeral shaft radius proxy, (c) the MG1 arm envelopes (ray marched; the deltoid lies over them), and
      (d) outer - an authored thickness profile (tapering to tendon / aponeurosis at both ends).

All numbers are authored rules recorded in the report - not anatomy, not fitted.  Permanent IDs, neutral colour, no
activation.  Bound to the anatomical chain with weights blending from the origin bone (clavicle / scapula) to the
humerus along theta.  Checks: inside the skin and below the layer, clear of the head / shaft proxies, no triangle
overlaps with each other or with the MG1 envelopes; the input blend is unchanged.  Saves a NEW blend.

usage: python3.13 build_deltoid_envelopes_blender.py -- MG1.blend MG1_SHA256 anchors.json OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, outdir = Path(args[0]), args[1], Path(args[2]), Path(args[3])
SIDE = args[4] if len(args) > 4 else "left"
SUF = "L" if SIDE == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG4_shoulder_{SIDE}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
PROP = json.loads(anchors_p.read_text())["proposals"]

FAT, GAP = 0.004, 0.0012
HEAD_R, CUFF = 0.024, 0.006          # humeral head radius proxy and the space kept for the rotator cuff (m)
T_MAX, T_END = 0.024, 0.006          # deltoid thickness: belly / tendinous ends (m)
THETA_LO = 12.0                      # belly's insertion end (deg from the humeral axis); tendon below
APONEUROSIS = 10.0                   # deg kept below each origin direction
NPHI, NTH = 12, 26
HEADS = {  # phi span at the insertion end (thirds of the tuberosity) and at the origin end
    "deltoid_anterior": {"ins": (70.0, 82.0), "orig": (-45.0, 55.0), "origin_bone": f"anat_clavicle_{SIDE}"},
    "deltoid_middle": {"ins": (83.5, 96.5), "orig": (58.0, 138.5), "origin_bone": f"anat_scapula_{SIDE}"},
    "deltoid_posterior": {"ins": (98.0, 110.0), "orig": (141.5, 210.0), "origin_bone": f"anat_scapula_{SIDE}"},
}


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


GH, EJC = LM(f"scapula_{SIDE}__GH"), LM(f"humerus_{SIDE}__EJC")
AX = (EJC - GH).normalized(); LH = (EJC - GH).length
lat = 1.0 if GH.x > 0 else -1.0
F_ = Vector((0, -1, 0)); F_ = (F_ - AX * F_.dot(AX)).normalized()
L_ = Vector((lat, 0, 0)); L_ = (L_ - AX * L_.dot(AX) - F_ * L_.dot(F_)).normalized()


def direction(theta, phi):
    t, p = math.radians(theta), math.radians(phi)
    return AX * math.cos(t) + (F_ * math.cos(p) + L_ * math.sin(p)) * math.sin(t)


def sph(p):
    q = p - GH; r = q.length
    return math.degrees(math.acos(max(-1.0, min(1.0, q.dot(AX) / r)))), math.degrees(math.atan2(q.dot(L_), q.dot(F_))), r


def r_bone(s):
    sm = lambda x: 0.0 if x <= 0 else 1.0 if x >= 1 else x * x * (3 - 2 * x)
    return 0.011 + 0.012 * sm((0.2 - s) / 0.2) + 0.010 * sm((s - 0.8) / 0.2)


# ---- the MG1 cylindrical frame (same skin sections, subcutaneous layer and deltoid reserve band as the arm envelopes,
#      so the lower deltoid sits exactly in the band MG1 left for it - no overlap by construction)
import importlib.util as _ilu                               # (MG1's functions are re-implemented, not imported: that
R_CAP, NB = 0.065, 72                                       #  script runs on import)


def _blend(x, a, b, x0, x1):
    t = min(1.0, max(0.0, (x - x0) / (x1 - x0))); t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def deltoid_reserve(s, phi):
    a0, a1 = _blend(s, -40.0, 50.0, 0.12, 0.40), _blend(s, 210.0, 130.0, 0.12, 0.40)
    x = (phi - a0) % 360.0
    if x > (a1 - a0):
        return 0.0
    e = min(1.0, min(x, (a1 - a0) - x) / 30.0)              # feathered over 30 deg inside the window edges (a hard
    e = e * e * (3 - 2 * e)                                 # edge stepped the arm envelopes' outer surface)
    return _blend(s, 0.55, 0.0, 0.20, 0.45) * e


def reserve_window(s):
    return _blend(s, -40.0, 50.0, 0.12, 0.40), _blend(s, 210.0, 130.0, 0.12, 0.40)


VW = [body.matrix_world @ v.co for v in body.data.vertices]
TRIS = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in body.data.polygons for k in range(1, len(p.vertices) - 1)]
BVH_BODY = BVHTree.FromPolygons(VW, TRIS, all_triangles=True)
GN = [g.name for g in body.vertex_groups]
RT = None
for cand in ("r", "l"):
    gi = GN.index(f"upperarm_{cand}")
    xs = [VW[v.index] for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    if xs and (sum(p.x for p in xs) / len(xs)) * lat > 0:
        RT = cand
ARMG = {GN.index(n) for n in (f"upperarm_{RT}", f"forearm_{RT}", f"shoulder_cap_{RT}", f"forearm_tw0_{RT}")}
ARMV = [sum(g.weight for g in v.groups if g.group in ARMG) > 0.5 for v in body.data.vertices]
ARM_TRIS = [t for t in TRIS if all(ARMV[i] for i in t)]
_PROF = {}


def skin_r(s_, phi):
    key = round(s_, 4)
    if key not in _PROF:
        c = GH + AX * (s_ * LH); R = [0.0] * NB
        for t in ARM_TRIS:
            d = [(VW[i] - c).dot(AX) for i in t]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                if (d[a] > 0) != (d[b] > 0):
                    q = VW[t[a]].lerp(VW[t[b]], d[a] / (d[a] - d[b])) - c
                    if q.length > R_CAP:
                        continue
                    ph = math.degrees(math.atan2(q.dot(L_), q.dot(F_))) % 360.0
                    k = int(ph / (360.0 / NB)) % NB; R[k] = max(R[k], q.length)
        known = [k for k in range(NB) if R[k] > 0]; out = []
        for k in range(NB):
            if R[k] > 0:
                out.append(R[k]); continue
            lo = max((j for j in known if j < k), default=known[-1] - NB); hi = min((j for j in known if j > k), default=known[0] + NB)
            t = (k - lo) / (hi - lo); out.append(R[lo % NB] * (1 - t) + R[hi % NB] * t)
        _PROF[key] = [(out[k - 1] + out[k] + out[(k + 1) % NB]) / 3.0 for k in range(NB)]
    P = _PROF[key]; x = (phi % 360.0) / (360.0 / NB) - 0.5; k0 = math.floor(x); t = x - k0
    return P[k0 % NB] * (1 - t) + P[(k0 + 1) % NB] * t
ARM = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects if o.name.endswith(f".{SUF}")]
dg = bpy.context.evaluated_depsgraph_get()
ARM_BVH = [BVHTree.FromObject(o, dg) for o in ARM]


def inside_arm(p):
    for t in ARM_BVH:
        loc, nrm, _i, _d = t.find_nearest(p)
        if loc is not None and (p - loc).dot(nrm) < 0 and (p - loc).length < 0.03:
            return True
    return False


def bone_limit(theta, d):
    """smallest radius along the ray clear of the head + cuff reserve and of the shaft proxy"""
    r = HEAD_R + CUFF + GAP
    st = math.sin(math.radians(theta))
    for _ in range(40):
        p = GH + d * r; s = (p - GH).dot(AX) / LH
        if not (0.0 < s < 1.0):
            return r
        rad = ((p - GH) - AX * ((p - GH).dot(AX))).length
        need = r_bone(s) + 0.002
        if rad >= need:
            return r
        r += max(0.001, (need - rad) / max(st, 0.05))
    return r


def section(spec, theta, frac, theta_hi):
    """outer / inner arcs at polar angle theta; frac 0 (insertion end) .. 1 (origin end) sets the phi span"""
    a0, a1 = span(spec, frac)
    end = min(1.0, (1.0 - frac) / 0.12)                     # tapers to the aponeurotic origin
    T = T_END + (T_MAX - T_END) * (end * end * (3 - 2 * end))
    outer, inner, flags = [], [], 0
    for j in range(NPHI):
        phi = a0 + (a1 - a0) * j / (NPHI - 1)
        d = direction(theta, phi)
        hit = BVH_BODY.ray_cast(GH, d, 0.4)
        if hit[0] is None:
            raise RuntimeError(f"no skin along theta {theta:.1f} phi {phi:.1f}")
        ro = hit[3] - FAT
        for _ in range(6):                                   # the ray meets the skin obliquely: keep the TRUE depth
            loc, nrm, _i, dist = BVH_BODY.find_nearest(GH + d * ro)
            depth = -dist if (GH + d * ro - loc).dot(nrm) > 0 else dist
            if depth >= FAT - 1e-4:
                break
            ro -= (FAT - depth)
        ri = max(bone_limit(theta, d), ro - T)
        r = ri                                               # ray-march out of the MG1 arm envelopes
        last_in = None
        while r < ro:
            if inside_arm(GH + d * r):
                last_in = r
            r += 0.001
        if last_in is not None:
            ri = max(ri, last_in + GAP + 0.001)
        if ro - ri < 0.003:
            ri = ro - 0.003; flags += 1
        outer.append(GH + d * ro); inner.append(GH + d * ri)
    return outer + inner[::-1], flags


S_INS, S_B, TH_B, U_B, NCYL, NSPH = 0.40, 0.12, 58.0, 0.35, 10, 18


def span(spec, u):
    w = u * u * (3 - 2 * u)
    return (spec["ins"][0] + (spec["orig"][0] - spec["ins"][0]) * w, spec["ins"][1] + (spec["orig"][1] - spec["ins"][1]) * w)


def section_cyl(spec, s_, u):
    """lower deltoid along the shaft: the MG1 reserve band (outer: skin - layer; inner: where MG1's envelopes stop)"""
    a0, a1 = span(spec, u); w0, w1 = reserve_window(s_)
    un = lambda a: w0 + ((a - w0) % 360.0)
    a0, a1 = max(un(a0) if un(a0) <= w1 + 1e-6 else w0, w0 + 1.5), min(un(a1) if un(a1) >= w0 else w1, w1 - 1.5)
    if a1 - a0 < 3.0:
        m_ = (a0 + a1) / 2.0; a0, a1 = m_ - 1.5, m_ + 1.5
    c = GH + AX * (s_ * LH); rb = r_bone(s_); outer, inner, flags = [], [], 0
    for j in range(NPHI):
        phi = a0 + (a1 - a0) * j / (NPHI - 1)
        avail = max(skin_r(s_, phi) - FAT - rb, 0.004)
        res = deltoid_reserve(s_, phi)
        ro = rb + avail; ri = rb + (1.0 - res) * avail + GAP
        if ro - ri < 0.002:
            ri = ro - 0.002; flags += 1
        dd = (F_ * math.cos(math.radians(phi)) + L_ * math.sin(math.radians(phi)))
        outer.append(c + dd * ro); inner.append(c + dd * ri)
    return outer + inner[::-1], flags


def build(mid, spec):
    th_o = sph(Vector(next(a["world_rest_m"] for a in PROP[mid]["anchors"] if a["role"] == "origin")))[0]
    theta_hi = th_o - APONEUROSIS
    rings, squeezed = [], 0
    for k in range(NCYL + 1):                               # along the shaft (cylindrical, MG1 band)
        u = U_B * k / NCYL
        ring, fl = section_cyl(spec, S_INS + (S_B - S_INS) * k / NCYL, u)
        rings.append(ring); squeezed += fl
    for k in range(1, NSPH + 1):                            # over the head (spherical rays from GH)
        u = U_B + (1.0 - U_B) * k / NSPH
        theta = TH_B + (theta_hi - TH_B) * k / NSPH
        ring, fl = section(spec, theta, u, theta_hi)
        rings.append(ring); squeezed += fl
    m = len(rings[0]); verts, faces = [], []
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
    me = bpy.data.meshes.new(mid); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, c0, c1, theta_hi, squeezed


def tube(name, a, b, r=0.004, n=8):
    d = (b - a); z = d.normalized(); x = z.orthogonal().normalized(); y = z.cross(x)
    verts = [a + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    verts += [b + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)] + [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, d.length


def mesh_volume(me):
    v = 0.0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        for k in range(1, len(vs) - 1):
            v += vs[0].dot(vs[k].cross(vs[k + 1])) / 6.0
    return abs(v)


C_MUS, C_TEN = bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"], bpy.data.collections["HGPT_EXPERIMENT_TENDONS"]
mat_m = bpy.data.materials.get("HGPT_EXPERIMENT_MUSCLE_NEUTRAL"); mat_t = bpy.data.materials.get("HGPT_EXPERIMENT_TENDON_NEUTRAL")
HUM = f"anat_humerus_{SIDE}"
for bn in (f"anat_clavicle_{SIDE}",):                          # copy-only, as MG1 did for scapula / arm bones
    anat.data.bones[bn].use_deform = True


def bind(ob, weights):
    for v in ob.data.vertices:
        for bn, w in weights(ob.matrix_world @ v.co).items():
            g = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
            g.add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("HGPT_ANATOMICAL_CHAIN", "ARMATURE"); mod.object = anat


REP = {"status": "ENVELOPE_PROXY_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": SIDE,
       "frame": "GH-centred spherical: theta from the humeral axis (0 down the arm), phi 0 anterior / +90 lateral",
       "rules": {"subcutaneous_layer_m": FAT, "gap_m": GAP, "head_radius_m": HEAD_R, "cuff_reserve_m": CUFF,
                 "thickness_m": [T_END, T_MAX], "theta_insertion_end_deg": THETA_LO, "aponeurotic_margin_deg": APONEUROSIS,
                 "heads_phi_spans_deg": {k: {"insertion": v["ins"], "origin": v["orig"]} for k, v in HEADS.items()}},
       "volume_source": "geometry-derived from this body (no reviewed literature volumes reachable)", "muscles": {}}
NEW = []
for m, spec in HEADS.items():
    mid = f"hgpt.muscle.{m}.{SUF}"
    anchors = {a["role"]: Vector(a["world_rest_m"]) for a in PROP[mid]["anchors"]}
    me, c0, c1, theta_hi, squeezed = build(mid, spec)
    me.materials.append(mat_m)
    ob = bpy.data.objects.new(mid, me); C_MUS.objects.link(ob); NEW.append(ob)
    ob["hgpt_muscle_id"] = mid; ob["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"; ob["hgpt_activation_display"] = False
    ob_bone = spec["origin_bone"]

    def wfun(p, th_hi=theta_hi, ob_bone=ob_bone):
        th = sph(p)[0]
        u = min(1.0, max(0.0, (th - TH_B) / max(th_hi - TH_B, 1.0)))
        u = u * u * (3 - 2 * u)                              # humerus along the shaft, origin bone towards the top
        return {k: v for k, v in {HUM: 1.0 - u, ob_bone: u}.items() if v > 1e-4}
    bind(ob, wfun)
    tend = {}
    for role, c in (("insertion", c0), ("origin", c1)):
        tm, tl = tube(f"{mid}.tendon_{role}", c, anchors[role]); tm.materials.append(mat_t)
        to = bpy.data.objects.new(tm.name, tm); C_TEN.objects.link(to)
        to["hgpt_muscle_id"] = mid; to["hgpt_tendon_role"] = role; to["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"
        bind(to, (lambda p: {HUM: 1.0}) if role == "insertion" else (lambda p, b=ob_bone: {b: 1.0}))
        tend[role] = round(tl, 4)
    vol = mesh_volume(me)
    REP["muscles"][mid] = {"belly_volume_cm3": round(vol * 1e6, 1), "belly_volume_m3": round(vol, 7),
                           "shaft_part_s": [S_INS, S_B], "cap_part_theta_deg": [TH_B, round(theta_hi, 1)], "tendon_lengths_m": tend,
                           "sections_squeezed_to_min_thickness": squeezed}
    print("MUSCLE", mid, json.dumps(REP["muscles"][mid]), flush=True)

# ------------------------------------------------------------------ checks
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
chk = {}
for ob in NEW:
    P = [ob.matrix_world @ v.co for v in ob.data.vertices]
    outside = shallow = bone = 0; min_depth = 1.0
    for p in P:
        loc, nrm, _i, dist = BVH_BODY.find_nearest(p)
        if (p - loc).dot(nrm) > 0:
            outside += 1
        else:
            min_depth = min(min_depth, dist)
            if dist < FAT - 0.0015:
                shallow += 1
        if (p - GH).length < HEAD_R - 1e-4:
            bone += 1
        s = (p - GH).dot(AX) / LH
        if 0.0 < s < 1.0 and ((p - GH) - AX * ((p - GH).dot(AX))).length < r_bone(s) - 1e-4:
            bone += 1
    chk[ob.name] = {"vertices": len(P), "outside_skin": outside, "shallower_than_layer": shallow,
                    "min_depth_below_skin_mm": round(min_depth * 1000, 2), "inside_head_or_shaft": bone}
ALL = NEW + ARM
trees = {o.name: BVHTree.FromObject(o, dg) for o in ALL}
pairs = {}
for i, a in enumerate(ALL):
    for b in ALL[i + 1:]:
        if a not in NEW and b not in NEW:
            continue
        ov = trees[a.name].overlap(trees[b.name])
        if ov:
            pairs[f"{a.name.split('.')[2]} | {b.name.split('.')[2]}"] = len(ov)
REP["checks"] = {"per_muscle": chk, "overlap_pairs_involving_deltoid": pairs}
print("CHECKS", json.dumps(REP["checks"]), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
REP["output_blend"] = OUT.name; REP["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
REP["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

# ------------------------------------------------------------------ renders
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.46
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 560; sc.render.resolution_y = 600
skin = bpy.data.materials.new("REVIEW_SKIN"); skin.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin)
TEN = list(C_TEN.objects); MUSC = list(C_MUS.objects)
for ob in sc.objects:
    if ob.type == "MESH" and ob is not body and ob not in MUSC and ob not in TEN:
        ob.hide_render = True
centre = GH + AX * 0.06
files = {}
for tag, skin_on in (("muscle", False), ("skin", True)):
    body.hide_render = not skin_on
    for o in MUSC + TEN:
        o.hide_render = skin_on
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat, 0, 0), "posterior": (0, 1, 0), "superior": (lat * 0.3, 0, 1)}.items():
        d = Vector(dv).normalized(); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        f = outdir / f"mg4_{SIDE}_{tag}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files.setdefault(tag, []).append(f.name)
REP["renders"] = files
(outdir / f"mg4_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": REP["input_unchanged"]}), flush=True)
