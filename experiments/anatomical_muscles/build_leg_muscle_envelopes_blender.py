"""EXPERIMENT (copy only): thigh and calf muscle ENVELOPE PROXIES for the squat contract, one anatomical side - MG1's
method (build_arm_muscle_envelopes_blender.py) carried to the leg.

Two segments, each cut into cross-sections along a bone line, the space between a bone radius proxy and the skin (less
the subcutaneous layer) split into compartment sectors and depth bands (phi: 0 anterior, +90 lateral):

  thigh, along the femoral SHAFT line (the mechanical axis HJC -> KJC runs medial of the proximal shaft through the
      neck, so the line starts below the greater trochanter: the trochanterion landmark 45 mm medial, 30 mm down, and
      ends at KJC):
      rectus femoris        -25..25 superficial (outer 55 %),      s 0.06-0.80, tendon to the AIIS / to the tibia
      vastus intermedius   -60..115 deep (inner 45 %),             s 0.20-0.86
      vastus lateralis      25..150 (above VI's band, full where VI is absent), s 0.08-0.88
      vastus medialis      -80..-25 (above VI's band, full below it; distal-heavy), s 0.42-0.93
      biceps femoris long  150..205 full,                          s 0.14-0.84, tendons to the ischium / fibular head
      semitendinosus       205..245 superficial (outer 50 %),      s 0.12-0.78
      semimembranosus      205..258 deep (inner 50 %),             s 0.24-0.88
      adductor magnus (hamstring part) 258..278 full,              s 0.16-0.90
      (sartorius, gracilis and the other adductors are not in the contract: a superficial medial reserve is left)
  calf, along KJC -> AJC:
      gastrocnemius medial 195..262 superficial (outer 55 %),      s 0.03-0.50, origin tendon to the femur
      soleus               135..265 deep (inner 45 % under the gastrocnemius, full from s 0.60), s 0.14-0.82
      (the lateral gastrocnemius is not in the contract: its posterolateral superficial band is left as a reserve)

Bellies taper in polar terms at both ends and continue as tendon proxies to the PROPOSED (unreviewed) anchors of
proposed_anchors_lower_<side>.json.  All numbers are authored rules recorded in the report - not anatomy, not fitted.
Permanent IDs, neutral colour, no activation.  Bound to the anatomical chain: thigh bellies ride the femur, calf bellies
the tibia; only the tendons cross the hip / knee / ankle.  Checks: inside the skin and below the layer (the skin of the
trunk and legs - the hands rest on the thighs and are not the thigh's surface), clear of the bone proxy, no overlaps
with any envelope.  Saves a NEW blend; the input is unchanged.

usage: python3.13 build_leg_muscle_envelopes_blender.py -- INPUT.blend INPUT_SHA256 anchors_lower.json OUT_DIR [left|right]
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
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG7_leg_{SIDE}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
PROP = json.loads(anchors_p.read_text())["proposals"]

FAT, GAP, SECTOR_INSET, TENDON_R, STEP, NPHI, TAPER = 0.004, 0.0012, 1.5, 0.004, 0.012, 14, 0.07


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def blend(s, a, b, s0, s1):
    return a + (b - a) * sm((s - s0) / (s1 - s0))


HJC, KJC, AJC = LM(f"hip_bone_{SIDE}__HJC"), LM(f"femur_{SIDE}__KJC"), LM(f"tibia_{SIDE}__AJC")
TROCH = LM(f"hip_bone_{SIDE}__trochanterion_skin")
lat = 1.0 if HJC.x > 0 else -1.0
SHAFT_TOP = Vector((TROCH.x - lat * 0.045, 0.5 * (HJC.y + TROCH.y), TROCH.z - 0.030))


class Segment:
    def __init__(self, name, p0, p1, r_bone, groups, r_cap):
        self.name, self.P0, self.P1 = name, p0, p1
        self.AX = (p1 - p0).normalized(); self.L = (p1 - p0).length
        F = Vector((0, -1, 0)); self.F = (F - self.AX * F.dot(self.AX)).normalized()
        Lv = Vector((lat, 0, 0)); self.Lt = (Lv - self.AX * Lv.dot(self.AX) - self.F * Lv.dot(self.F)).normalized()
        self.r_bone, self.groups, self.r_cap, self.prof = r_bone, groups, r_cap, {}

    def dir(self, phi):
        p = math.radians(phi); return self.F * math.cos(p) + self.Lt * math.sin(p)

    def s_of(self, p):
        return (p - self.P0).dot(self.AX) / self.L

    def centre(self, s):
        return self.P0 + self.AX * (s * self.L)


THIGH = Segment("thigh", SHAFT_TOP, KJC,
                lambda s: 0.0135 + 0.012 * sm((0.10 - s) / 0.10) + 0.022 * sm((s - 0.80) / 0.20), ("thigh",), 0.14)
CALF = Segment("calf", KJC, AJC,
               lambda s: 0.021 + 0.016 * sm((0.12 - s) / 0.12) + 0.006 * sm((s - 0.85) / 0.15), ("shin",), 0.10)

MUS = {   # segment, sector (deg), radial band (fractions of the available thickness, inner / outer), axial range (s),
          # bones: belly, origin tendon, insertion tendon
    "rectus_femoris": (THIGH, (-25, 25), (lambda s: 0.45, lambda s: 1.0), (0.06, 0.80), ("femur", "hip_bone", "tibia")),
    "vastus_intermedius": (THIGH, (-60, 115), (lambda s: 0.0, lambda s: 0.45 - 0.0 * s), (0.20, 0.86), ("femur", "femur", "tibia")),
    "vastus_lateralis": (THIGH, (25, 150), (lambda s: 0.0, lambda s: 1.0), (0.08, 0.88), ("femur", "femur", "tibia")),
    "vastus_medialis": (THIGH, (-80, -25), (lambda s: 0.0, lambda s: 1.0), (0.42, 0.93), ("femur", "femur", "tibia")),
    "biceps_femoris_long": (THIGH, (150, 205), (lambda s: 0.0, lambda s: 1.0), (0.14, 0.84), ("femur", "hip_bone", "fibula")),
    "semitendinosus": (THIGH, (205, 245), (lambda s: 0.50, lambda s: 1.0), (0.12, 0.78), ("femur", "hip_bone", "tibia")),
    "semimembranosus": (THIGH, (205, 258), (lambda s: 0.0, lambda s: 0.50), (0.24, 0.88), ("femur", "hip_bone", "tibia")),
    "adductor_magnus_hamstring": (THIGH, (258, 278), (lambda s: 0.0, lambda s: blend(s, 0.60, 1.0, 0.30, 0.55)), (0.16, 0.90),
                                  ("femur", "hip_bone", "femur")),
    "gastrocnemius_medial": (CALF, (195, 262), (lambda s: 0.45, lambda s: 1.0), (0.03, 0.50), ("tibia", "femur", "calcaneus")),
    "soleus": (CALF, (135, 265), (lambda s: 0.0, lambda s: blend(s, 0.45, 1.0, 0.50, 0.60)), (0.14, 0.82), ("tibia", "tibia", "calcaneus")),
}
# where the vastus intermedius lies (phi -60..115, s 0.20-0.86) the lateralis and medialis start above its outer band


def _vi_outer(sc, phi):
    s0, s1 = MUS["vastus_intermedius"][3]
    tau = sm(min(1.0, (sc - s0) / TAPER, (s1 - sc) / TAPER))
    a0, a1 = -60.0 + SECTOR_INSET, 115.0 - SECTOR_INSET
    am, ah = (a0 + a1) / 2.0, (a1 - a0) / 2.0 * max(tau, 0.12)
    inside_deg = ah - abs(((phi - am + 180.0) % 360.0) - 180.0)       # > 0 inside the tapered sector
    w = sm((inside_deg + 24.0) / 12.0)
    if w <= 0.0:
        return 0.0
    rb = THIGH.r_bone(sc); avail = max(skin_r(THIGH, sc, phi) - FAT - rb, 0.004)
    ro0, ri0 = rb + 0.45 * avail - GAP, rb + 0.0005
    rm_, rh_ = (ro0 + ri0) / 2.0, (ro0 - ri0) / 2.0 * max(tau, 0.25)
    return w * (rm_ + rh_ - rb)


def vi_floor_r(s, phi):
    """height above the bone proxy (m) the lateralis / medialis must stay above at (s, phi): the intermedius's own
    (tapered) outer surface + the gap - held full for 12 deg beyond its sector edges and feathered over the next 12, and
    the largest over the neighbouring stations (a narrow feather and a single station let their faces slope through the
    intermedius's corner and its interpolated tapered ends)"""
    s0, s1 = MUS["vastus_intermedius"][3]
    if s < s0 - 0.03 or s > s1 + 0.03:
        return 0.0
    v = max(_vi_outer(min(max(s + d, s0), s1), phi) for d in (-STEP * 1.5, 0.0, STEP * 1.5))
    return v * sm(1.0 - max(s0 - s, s - s1, 0.0) / 0.03) + GAP


# ---- skin: the leg segment's own triangles for the sections; trunk + legs (no arms / hands) for the depth clamp
VW = [body.matrix_world @ v.co for v in body.data.vertices]
TRIS = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in body.data.polygons for k in range(1, len(p.vertices) - 1)]
GN = [g.name for g in body.vertex_groups]
rt = None
for cand in ("r", "l"):          # the body rig's suffix on this side (anatomical left = +x = the rig's _r)
    gi = GN.index(f"thigh_{cand}")
    xs = [VW[v.index] for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    if xs and (sum(p.x for p in xs) / len(xs)) * lat > 0:
        rt = cand


def seg_tris(seg):
    gi = {GN.index(f"{g}_{rt}") for g in seg.groups}
    W = [sum(g.weight for g in v.groups if g.group in gi) > 0.5 for v in body.data.vertices]
    return [t for t in TRIS if all(W[i] for i in t)]


SEG_TRIS = {THIGH.name: seg_tris(THIGH), CALF.name: seg_tris(CALF)}
ARMG = {i for i, g in enumerate(GN) if any(k in g for k in ("upperarm", "forearm", "hand", "thumb", "index", "middle",
                                                            "ring", "pinky", "metacarpal", "shoulder_cap"))}
ARMV = [sum(g.weight for g in v.groups if g.group in ARMG) > 0.3 for v in body.data.vertices]
BVH_SKIN = BVHTree.FromPolygons(VW, [t for t in TRIS if not any(ARMV[i] for i in t)], all_triangles=True)
NB = 72


def skin_r(seg, s, phi):
    key = round(s, 4)
    if key not in seg.prof:
        c = seg.centre(s); R = [0.0] * NB
        for t in SEG_TRIS[seg.name]:
            d = [(VW[i] - c).dot(seg.AX) for i in t]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                if (d[a] > 0) != (d[b] > 0):
                    q = VW[t[a]].lerp(VW[t[b]], d[a] / (d[a] - d[b])) - c
                    if q.length > seg.r_cap:
                        continue
                    ph = math.degrees(math.atan2(q.dot(seg.Lt), q.dot(seg.F))) % 360.0
                    k = int(ph / (360.0 / NB)) % NB; R[k] = max(R[k], q.length)
        known = [k for k in range(NB) if R[k] > 0]
        if len(known) < NB // 3:
            raise RuntimeError(f"{seg.name} skin section too sparse at s={s:.2f}")
        out = []
        for k in range(NB):
            if R[k] > 0:
                out.append(R[k]); continue
            lo = max((j for j in known if j < k), default=known[-1] - NB); hi = min((j for j in known if j > k), default=known[0] + NB)
            t = (k - lo) / (hi - lo); out.append(R[lo % NB] * (1 - t) + R[hi % NB] * t)
        seg.prof[key] = [(out[k - 1] + out[k] + out[(k + 1) % NB]) / 3.0 for k in range(NB)]
    P = seg.prof[key]; x = (phi % 360.0) / (360.0 / NB) - 0.5; k0 = math.floor(x); t = x - k0
    return P[k0 % NB] * (1 - t) + P[(k0 + 1) % NB] * t


def section(m, spec, s, tau):
    seg, sector, band = spec[0], spec[1], spec[2]
    a0, a1 = sector[0] + SECTOR_INSET, sector[1] - SECTOR_INSET
    am, ah = (a0 + a1) / 2.0, (a1 - a0) / 2.0 * max(tau, 0.12)
    a0, a1 = am - ah, am + ah
    c = seg.centre(s); rb = seg.r_bone(s); outer, inner = [], []
    for j in range(NPHI):
        phi = a0 + (a1 - a0) * j / (NPHI - 1)
        avail = max(skin_r(seg, s, phi) - FAT - rb, 0.004)
        fo, fi = band[1](s), band[0](s)
        if m in ("vastus_medialis", "adductor_magnus_hamstring") and s < 0.55:
            fo = min(fo, 1.0 - blend(s, 0.35, 0.0, 0.30, 0.55))
        ro = rb + fo * avail - (GAP if fo < 1.0 else 0.0)
        ri = rb + fi * avail + (GAP if fi > 0.0 else 0.0005)
        if m in ("vastus_lateralis", "vastus_medialis"):
            ri = max(ri, rb + vi_floor_r(s, phi))
        if ro - ri < 0.002:
            ro = ri + 0.002
        rm_, rh_ = (ro + ri) / 2.0, (ro - ri) / 2.0 * max(tau, 0.25)
        ro, ri = rm_ + rh_, rm_ - rh_
        d = seg.dir(phi); outer.append(c + d * ro); inner.append(c + d * ri)
    return outer + inner[::-1]


def clamp_depth(seg, ring, m=None):
    """keep every point at least the layer below the skin, moving it radially towards the bone line - never below the
    bone proxy, and for the lateralis / medialis never below the intermedius"""
    out = []
    for p in ring:
        for _ in range(3):
            loc, nrm, _i, dist = BVH_SKIN.find_nearest(p)
            dep = -dist if (p - loc).dot(nrm) > 0 else dist
            if dep >= FAT - 1e-4:
                break
            c = seg.P0 + seg.AX * ((p - seg.P0).dot(seg.AX)); r = p - c
            if r.length < 1e-6:
                break
            sb = seg.s_of(p); floor = seg.r_bone(sb) + 0.0015 if 0.0 < sb < 1.0 else 0.002
            if m in ("vastus_lateralis", "vastus_medialis") and 0.0 < sb < 1.0:
                ph = math.degrees(math.atan2(r.dot(seg.Lt), r.dot(seg.F)))
                floor = max(floor, seg.r_bone(sb) + vi_floor_r(sb, ph) + 0.0005)
            if r.length <= floor + 1e-6:
                break
            p = c + r.normalized() * max(r.length - (FAT - dep), floor)
        out.append(p)
    return out


def build(m, spec):
    seg = spec[0]; s0, s1 = spec[3]
    n = max(4, int(round((s1 - s0) / STEP))); rings = []
    for k in range(n + 1):
        s = s0 + (s1 - s0) * k / n
        tau = sm(min(1.0, (s - s0) / TAPER, (s1 - s) / TAPER))
        rings.append(clamp_depth(seg, section(m, spec, s, tau), m))
    verts, faces, mm = [], [], len(rings[0])
    for ring in rings:
        verts.extend(ring)
    for k in range(len(rings) - 1):
        for j in range(mm):
            a, b = k * mm + j, k * mm + (j + 1) % mm
            faces.append((a, b, b + mm, a + mm))
    c0 = sum(rings[0], Vector()) / mm; c1 = sum(rings[-1], Vector()) / mm   # (tendon roots only)
    # end caps as strips between the outer and the inner arc: a fan from the ring's centroid cut through the concave
    # side of a wide curved band (the lateralis' centroid lies over the intermedius)
    last = (len(rings) - 1) * mm
    for j in range(NPHI - 1):
        o0, o1, i0_, i1_ = j, j + 1, mm - 1 - j, mm - 2 - j
        faces.append((o1, o0, i0_, i1_))
        faces.append((last + o0, last + o1, last + i1_, last + i0_))
    me = bpy.data.meshes.new(f"hgpt.muscle.{m}.{SUF}"); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, c0, c1


def tube(name, a, b, r=TENDON_R, n=8):
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


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


C_MUS, C_TEN = coll("HGPT_EXPERIMENT_MUSCLES"), coll("HGPT_EXPERIMENT_TENDONS")
mat_m = bpy.data.materials.get("HGPT_EXPERIMENT_MUSCLE_NEUTRAL"); mat_t = bpy.data.materials.get("HGPT_EXPERIMENT_TENDON_NEUTRAL")
BONE = {k: f"anat_{k}_{SIDE}" for k in ("femur", "tibia", "fibula", "calcaneus", "hip_bone", "patella")}
DEFORM_ON = []
for bn in BONE.values():                                     # copy-only, as MG1 / MG4 / MG5 did
    if not anat.data.bones[bn].use_deform:
        anat.data.bones[bn].use_deform = True; DEFORM_ON.append(bn)


def bind(ob, weights):
    for v in ob.data.vertices:
        for bn, w in weights(ob.matrix_world @ v.co).items():
            g = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
            g.add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("HGPT_ANATOMICAL_CHAIN", "ARMATURE"); mod.object = anat


EXIST = [o for o in C_MUS.objects]
REP = {"status": "ENVELOPE_PROXY_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": SIDE,
       "runtime_suffix_of_side": rt, "copy_only_changes": {"anatomical_master_use_deform_enabled": DEFORM_ON},
       "rules": {"subcutaneous_layer_m": FAT, "gap_m": GAP, "sector_inset_deg": SECTOR_INSET, "tendon_radius_m": TENDON_R,
                 "station_step_s": STEP, "nphi": NPHI, "taper": TAPER,
                 "thigh_line": "shaft: trochanterion - 45 mm medial - 30 mm down -> KJC (the mechanical axis runs through the neck)",
                 "thigh_bone_radius_m": "13.5 mm shaft, +12 mm towards the trochanter (s<0.10), +22 mm towards the condyles (s>0.80)",
                 "calf_line": "KJC -> AJC",
                 "calf_bone_radius_m": "21 mm (tibia + fibula + interosseous), +16 mm towards the plateau (s<0.12), +6 mm towards the malleoli",
                 "medial_reserve": "35 % of the available thickness kept superficial over vastus medialis / adductor magnus for s<0.30, 0 by s=0.55 (sartorius, gracilis, adductors not in the contract)",
                 "sections": {m: {"segment": v[0].name, "sector_deg": v[1], "range_s": v[3], "bones": v[4]} for m, v in MUS.items()}},
       "volume_source": "geometry-derived from this body (no reviewed literature volumes reachable)", "muscles": {}}
NEW = []
for m, spec in MUS.items():
    mid = f"hgpt.muscle.{m}.{SUF}"
    anchors = {a["role"]: Vector(a["world_rest_m"]) for a in PROP[mid]["anchors"]}
    me, c0, c1 = build(m, spec); me.materials.append(mat_m)
    ob = bpy.data.objects.new(mid, me); C_MUS.objects.link(ob); NEW.append(ob)
    ob["hgpt_muscle_id"] = mid; ob["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"; ob["hgpt_activation_display"] = False
    belly_b, orig_b, ins_b = (BONE[k] for k in spec[4])
    bind(ob, lambda p, b=belly_b: {b: 1.0})                  # bellies ride their bone; tendons cross the joints
    tend = {}
    for role, c, far_b in (("origin", c0, orig_b), ("insertion", c1, ins_b)):
        tm, tl = tube(f"{mid}.tendon_{role}", c, anchors[role]); tm.materials.append(mat_t)
        to = bpy.data.objects.new(tm.name, tm); C_TEN.objects.link(to)
        to["hgpt_muscle_id"] = mid; to["hgpt_tendon_role"] = role; to["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"
        bind(to, lambda p, a=anchors[role], fb=far_b, bb=belly_b: ({fb: 1.0} if (p - a).length < 0.03 else {bb: 1.0}))
        tend[role] = round(tl, 4)
    vol = mesh_volume(me)
    REP["muscles"][mid] = {"belly_volume_cm3": round(vol * 1e6, 1), "belly_volume_m3": round(vol, 7),
                           "belly_length_m": round((c1 - c0).length, 4), "tendon_lengths_m": tend}
    print("MUSCLE", mid, json.dumps(REP["muscles"][mid]), flush=True)

# ------------------------------------------------------------------ checks
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
chk = {}
for ob in NEW:
    seg = MUS[ob.name.split(".")[2]][0]
    P = [ob.matrix_world @ v.co for v in ob.data.vertices]
    outside = shallow = bone = 0; min_depth = 1.0
    for p in P:
        loc, nrm, _i, dist = BVH_SKIN.find_nearest(p)
        if (p - loc).dot(nrm) > 0:
            outside += 1
        else:
            min_depth = min(min_depth, dist)
            if dist < FAT - 0.0015:
                shallow += 1
        s = seg.s_of(p); radial = ((p - seg.P0) - seg.AX * ((p - seg.P0).dot(seg.AX))).length
        if 0.0 < s < 1.0 and radial < seg.r_bone(s) - 1e-4:
            bone += 1
    tr = BVHTree.FromObject(ob, dg); polys = [set(p_.vertices) for p_ in ob.data.polygons]
    selfx = sum(1 for a, b in tr.overlap(tr) if a < b and not (polys[a] & polys[b]))
    chk[ob.name] = {"vertices": len(P), "outside_skin": outside, "shallower_than_layer": shallow,
                    "min_depth_below_skin_mm": round(min_depth * 1000, 2), "inside_bone_proxy": bone,
                    "self_intersecting_face_pairs": selfx}
ALL = NEW + EXIST
trees = {o.name: BVHTree.FromObject(o, dg) for o in ALL}
pairs = {}
for i, a in enumerate(ALL):
    for b in ALL[i + 1:]:
        if a not in NEW and b not in NEW:
            continue
        ov = trees[a.name].overlap(trees[b.name])
        if ov:
            pairs[f"{a.name.split('.')[2]} | {b.name.split('.')[2]}"] = len(ov)
REP["checks"] = {"per_muscle": chk, "overlap_pairs_involving_mg7": pairs}
print("CHECKS", json.dumps(REP["checks"]), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
REP["output_blend"] = OUT.name; REP["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
REP["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

# ------------------------------------------------------------------ renders (muscle only / skin only, same cameras)
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 1.05
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 420; sc.render.resolution_y = 900
skin = bpy.data.materials.new("REVIEW_SKIN"); skin.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin)
TEN = list(C_TEN.objects); MUSC = list(C_MUS.objects)
for ob in sc.objects:
    if ob.type == "MESH" and ob is not body and ob not in MUSC and ob not in TEN:
        ob.hide_render = True
centre = Vector((HJC.x, 0.0, 0.5 * (HJC.z + AJC.z) + 0.02))
files = {}
for tag, skin_on in (("muscle", False), ("skin", True)):
    body.hide_render = not skin_on
    for o in MUSC + TEN:
        o.hide_render = skin_on
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat, 0, 0), "posterior": (0, 1, 0), "medial": (-lat, 0, 0)}.items():
        d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        f = outdir / f"mg7_{SIDE}_{tag}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files.setdefault(tag, []).append(f.name)
REP["renders"] = files
(outdir / f"mg7_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": REP["input_unchanged"]}), flush=True)
