"""EXPERIMENT (copy only): MG11 - the brachioradialis ENVELOPE PROXY, one anatomical side, with MG7's compartment
method (build_leg_muscle_envelopes_blender.py) carried to the forearm.  It completes the curl contract's elbow flexors
(the rotator cuff muscles of that contract need a scapula surface, which R41 does not have).

The forearm is cut into cross-sections along EJC -> WJC; the space between a two-bone radius proxy (radius + ulna +
interosseous membrane) and the skin less the subcutaneous layer is the compartment.  The brachioradialis takes the
superficial band (outer 60 %) of a 70 deg sector centred on the RADIUS as it lies in R41's rest pose (its direction from
the forearm axis at mid-forearm, measured, not assumed - the rest forearm is near mid-prone), from s 0.04 to 0.55, tapering
at both ends; tendons run to the PROPOSED (unreviewed) anchors: origin on the lateral supracondylar ridge of the humerus,
insertion at the radial styloid.

Simplification (recorded): the real belly begins on the supracondylar ridge above the elbow; here it begins just below
the elbow and the origin tendon crosses the joint, so the belly rides one bone (the radius) and the length response
(MG10's rule) can key it.  All numbers are authored rules recorded in the report - not anatomy, not fitted.  Permanent
ID, neutral colour, no activation.  Checks: inside the arm skin and below the layer, clear of the bone proxy, no overlaps
with any envelope.  Saves a NEW blend; the input is unchanged.

usage: python3.13 build_forearm_muscle_envelopes_blender.py -- INPUT.blend INPUT_SHA256 anchors.json OUT_DIR [left|right]
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
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG11_forearm_{SIDE}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; MW = anat.matrix_world.copy()
PROP = json.loads(anchors_p.read_text())["proposals"]

FAT, GAP, SECTOR_INSET, TENDON_R, STEP, NPHI, TAPER = 0.004, 0.0012, 1.5, 0.0035, 0.012, 14, 0.07
SECTOR_HALF, BAND_INNER, RANGE = 35.0, 0.40, (0.04, 0.55)


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


EJC, WJC = LM(f"humerus_{SIDE}__EJC"), LM(f"radius_{SIDE}__WJC")
lat = 1.0 if EJC.x > 0 else -1.0


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

    def phi_of(self, p):
        q = p - self.centre(self.s_of(p)); return math.degrees(math.atan2(q.dot(self.Lt), q.dot(self.F)))


FOREARM = Segment("forearm", EJC, WJC,
                  lambda s: 0.012 + 0.008 * sm((0.15 - s) / 0.15), ("forearm", "forearm_tw0", "forearm_tw1"), 0.07)
# the radius's direction from the forearm axis at mid-forearm, in R41's rest pose (centre of the sector)
RB = anat.data.bones[f"anat_radius_{SIDE}"]
r_mid = MW @ ((RB.head_local + RB.tail_local) / 2.0)
PHI_R = FOREARM.phi_of(r_mid)
SECTOR = (PHI_R - SECTOR_HALF, PHI_R + SECTOR_HALF)

VW = [body.matrix_world @ v.co for v in body.data.vertices]
TRIS = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in body.data.polygons for k in range(1, len(p.vertices) - 1)]
GN = [g.name for g in body.vertex_groups]
rt = None
for cand in ("r", "l"):                                       # anatomical left = +x = the rig's _r
    gi = GN.index(f"forearm_{cand}")
    xs = [VW[v.index] for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)]
    if xs and (sum(p.x for p in xs) / len(xs)) * lat > 0:
        rt = cand
gi = {GN.index(f"{g}_{rt}") for g in FOREARM.groups}
W = [sum(g.weight for g in v.groups if g.group in gi) > 0.5 for v in body.data.vertices]
SEG_TRIS = [t for t in TRIS if all(W[i] for i in t)]
ARMG = {GN.index(f"{g}_{rt}") for g in ("upperarm", "forearm", "forearm_tw0", "forearm_tw1", "hand") if f"{g}_{rt}" in GN}
ARMV = [sum(g.weight for g in v.groups if g.group in ARMG) > 0.3 for v in body.data.vertices]
BVH_SKIN = BVHTree.FromPolygons(VW, [t for t in TRIS if all(ARMV[i] for i in t)], all_triangles=True)   # the arm's skin
NB = 72


def skin_r(seg, s, phi):
    key = round(s, 4)
    if key not in seg.prof:
        c = seg.centre(s); R = [0.0] * NB
        for t in SEG_TRIS:
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


def section(s, tau):
    seg = FOREARM
    a0, a1 = SECTOR[0] + SECTOR_INSET, SECTOR[1] - SECTOR_INSET
    am, ah = (a0 + a1) / 2.0, (a1 - a0) / 2.0 * max(tau, 0.12)
    a0, a1 = am - ah, am + ah
    c = seg.centre(s); rb = seg.r_bone(s); outer, inner = [], []
    for j in range(NPHI):
        phi = a0 + (a1 - a0) * j / (NPHI - 1)
        avail = max(skin_r(seg, s, phi) - FAT - rb, 0.004)
        ro, ri = rb + avail, rb + BAND_INNER * avail + GAP
        if ro - ri < 0.002:
            ro = ri + 0.002
        rm_, rh_ = (ro + ri) / 2.0, (ro - ri) / 2.0 * max(tau, 0.25)
        ro, ri = rm_ + rh_, rm_ - rh_
        d = seg.dir(phi); outer.append(c + d * ro); inner.append(c + d * ri)
    return outer + inner[::-1]


def clamp_depth(ring):
    """every point at least the layer below the arm's skin, moved radially towards the bone line (never below the
    bone proxy)"""
    seg = FOREARM; out = []
    for p in ring:
        for _ in range(3):
            loc, nrm, _i, dist = BVH_SKIN.find_nearest(p)
            dep = -dist if (p - loc).dot(nrm) > 0 else dist
            if dep >= FAT - 1e-4:
                break
            c = seg.P0 + seg.AX * ((p - seg.P0).dot(seg.AX)); r = p - c
            if r.length < 1e-6:
                break
            sb = seg.s_of(p); floor = seg.r_bone(sb) + 0.0015
            if r.length <= floor + 1e-6:
                break
            p = c + r.normalized() * max(r.length - (FAT - dep), floor)
        out.append(p)
    return out


def build(mid):
    s0, s1 = RANGE
    n = max(4, int(round((s1 - s0) / STEP))); rings = []
    for k in range(n + 1):
        s = s0 + (s1 - s0) * k / n
        tau = sm(min(1.0, (s - s0) / TAPER, (s1 - s) / TAPER))
        rings.append(clamp_depth(section(s, tau)))
    verts, faces, mm = [], [], len(rings[0])
    for ring in rings:
        verts.extend(ring)
    for k in range(len(rings) - 1):
        for j in range(mm):
            a, b = k * mm + j, k * mm + (j + 1) % mm
            faces.append((a, b, b + mm, a + mm))
    c0 = sum(rings[0], Vector()) / mm; c1 = sum(rings[-1], Vector()) / mm
    last = (len(rings) - 1) * mm
    for j in range(NPHI - 1):                                 # end caps as strips between the outer and the inner arc
        o0, o1, i0_, i1_ = j, j + 1, mm - 1 - j, mm - 2 - j
        faces.append((o1, o0, i0_, i1_))
        faces.append((last + o0, last + o1, last + i1_, last + i0_))
    me = bpy.data.meshes.new(mid); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
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


C_MUS = bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"]; C_TEN = bpy.data.collections["HGPT_EXPERIMENT_TENDONS"]
mat_m = bpy.data.materials.get("HGPT_EXPERIMENT_MUSCLE_NEUTRAL"); mat_t = bpy.data.materials.get("HGPT_EXPERIMENT_TENDON_NEUTRAL")
RAD, HUM = f"anat_radius_{SIDE}", f"anat_humerus_{SIDE}"
DEFORM_ON = []
for bn in (RAD, HUM):                                         # copy-only, as MG1 / MG4 / MG5 / MG7 did
    if not anat.data.bones[bn].use_deform:
        anat.data.bones[bn].use_deform = True; DEFORM_ON.append(bn)


def bind(ob, weights):
    for v in ob.data.vertices:
        for bn, w in weights(ob.matrix_world @ v.co).items():
            g = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
            g.add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("HGPT_ANATOMICAL_CHAIN", "ARMATURE"); mod.object = anat


EXIST = list(C_MUS.objects)
mid = f"hgpt.muscle.brachioradialis.{SUF}"
anchors = {a["role"]: Vector(a["world_rest_m"]) for a in PROP[mid]["anchors"]}
me, c0, c1 = build(mid); me.materials.append(mat_m)
ob = bpy.data.objects.new(mid, me); C_MUS.objects.link(ob)
ob["hgpt_muscle_id"] = mid; ob["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"; ob["hgpt_activation_display"] = False
bind(ob, lambda p: {RAD: 1.0})                                # the belly rides the radius; the origin tendon crosses the elbow
tend = {}
for role, c, far_b in (("origin", c0, HUM), ("insertion", c1, RAD)):
    tm, tl = tube(f"{mid}.tendon_{role}", c, anchors[role]); tm.materials.append(mat_t)
    to = bpy.data.objects.new(tm.name, tm); C_TEN.objects.link(to)
    to["hgpt_muscle_id"] = mid; to["hgpt_tendon_role"] = role; to["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"
    bind(to, lambda p, a=anchors[role], fb=far_b: ({fb: 1.0} if (p - a).length < 0.03 else {RAD: 1.0}))
    tend[role] = round(tl, 4)
vol = mesh_volume(me)
REP = {"status": "ENVELOPE_PROXY_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": SIDE,
       "runtime_suffix_of_side": rt, "copy_only_changes": {"anatomical_master_use_deform_enabled": DEFORM_ON},
       "rules": {"subcutaneous_layer_m": FAT, "gap_m": GAP, "sector_inset_deg": SECTOR_INSET, "tendon_radius_m": TENDON_R,
                 "station_step_s": STEP, "nphi": NPHI, "taper": TAPER, "forearm_line": "EJC -> WJC",
                 "forearm_bone_radius_m": "12 mm (radius + ulna + interosseous), +8 mm towards the elbow (s<0.15)",
                 "radius_direction_phi_deg": round(PHI_R, 1),
                 "sections": {"brachioradialis": {"segment": "forearm", "sector_deg": [round(SECTOR[0], 1), round(SECTOR[1], 1)],
                                                  "band_inner_fraction": BAND_INNER, "range_s": list(RANGE),
                                                  "bones": ["radius", "humerus", "radius"]}},
                 "simplification": "belly below the elbow only; the origin tendon crosses the joint"},
       "volume_source": "geometry-derived from this body (no reviewed literature volumes reachable)",
       "muscles": {mid: {"belly_volume_cm3": round(vol * 1e6, 1), "belly_volume_m3": round(vol, 7),
                         "belly_length_m": round((c1 - c0).length, 4), "tendon_lengths_m": tend}}}
print("MUSCLE", mid, json.dumps(REP["muscles"][mid]), "phi_radius", round(PHI_R, 1), flush=True)

bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
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
    s = FOREARM.s_of(p); radial = ((p - FOREARM.P0) - FOREARM.AX * ((p - FOREARM.P0).dot(FOREARM.AX))).length
    if 0.0 < s < 1.0 and radial < FOREARM.r_bone(s) - 1e-4:
        bone += 1
tr = BVHTree.FromObject(ob, dg); polys = [set(p_.vertices) for p_ in ob.data.polygons]
selfx = sum(1 for a, b in tr.overlap(tr) if a < b and not (polys[a] & polys[b]))
pairs = {}
for o in EXIST:
    ov = tr.overlap(BVHTree.FromObject(o, dg))
    if ov:
        pairs[f"brachioradialis | {o.name.split('.')[2]}"] = len(ov)
REP["checks"] = {"per_muscle": {mid: {"vertices": len(P), "outside_skin": outside, "shallower_than_layer": shallow,
                                      "min_depth_below_skin_mm": round(min_depth * 1000, 2), "inside_bone_proxy": bone,
                                      "self_intersecting_face_pairs": selfx}}, "overlap_pairs": pairs}
print("CHECKS", json.dumps(REP["checks"]), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
REP["output_blend"] = OUT.name; REP["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
REP["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 420; sc.render.resolution_y = 720
skin = bpy.data.materials.new("REVIEW_SKIN"); skin.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin)
ARM = ("biceps_brachii", "brachialis", "triceps", "brachioradialis")
MUSC = [o for o in C_MUS.objects if o.name.endswith(f".{SUF}") and o.name.split(".")[2].startswith(ARM)]
TEN = [o for o in C_TEN.objects if o.name.split(".")[3] == SUF and o.name.split(".")[2].startswith(ARM)]
for o in sc.objects:
    if o.type == "MESH" and o is not body and o not in MUSC and o not in TEN:
        o.hide_render = True
centre = EJC + (WJC - EJC) * 0.15
files = {}
for tag, skin_on in (("muscle", False), ("skin", True)):
    body.hide_render = not skin_on
    for o in MUSC + TEN:
        o.hide_render = skin_on
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat, 0, 0), "posterior": (0, 1, 0)}.items():
        d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        f = outdir / f"mg11_{SIDE}_{tag}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files.setdefault(tag, []).append(f.name)
REP["renders"] = files
(outdir / f"mg11_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": REP["input_unchanged"]}), flush=True)
