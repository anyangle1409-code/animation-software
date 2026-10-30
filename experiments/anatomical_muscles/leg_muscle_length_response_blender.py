"""EXPERIMENT (copy only): MG10 - length response of the MG7 leg envelopes, keyed by the belly's LENGTH RATIO k, not by
exercise or joint angle, so any movement drives it through the muscle's own path length (the kernel's job at runtime).

LAYERED (MG3's rule): the vastus lateralis and medialis keep their deep surface on the vastus intermedius's new outer
surface (+ the gap) and take their outer surface by the same area rule.  The three cross only the knee, so the
intermedius's ratio at a given lateralis / medialis ratio is fixed by the knee angle (sampled 0-150 deg, inverted):
each layered key is valid for any movement, not only the squat.  (Without it the bellies, stretched about different
proximal rings, slide into each other: 21-96 face pairs through the squat.)

For each MG7 belly, in its segment's cylindrical frame as built (thigh along the femoral shaft line SHAFT_TOP -> KJC,
calf along KJC -> AJC), a rest-space shape key HGPT_LEN_K_<100 k> per k in K_SET: the stations move along the axis
by k about the belly's PIVOT, and each section keeps its deep surface while the outer surface takes
r_o'^2 = r_i^2 + (r_o^2 - r_i^2) / k (section area x 1 / k: the volume is kept and the belly bulges towards the skin,
not into the bone) - MG2's rule.  The pivot is the belly end that cannot slide: the one whose tendon attaches to the bone the
belly rides (proximal for the vasti and the soleus, distal for the adductor magnus on the femur's adductor tubercle);
else the one whose tendon is under a third of the other's, attaching next to the joint (proximal for the
gastrocnemius: 24 mm heads against a 267 mm Achilles); else the belly's centre (rectus femoris, hamstrings).
(Pivoting every belly at its proximal ring pushed the adductor magnus 41 % down into the gastrocnemius' heads at full
depth; pivoting the gastrocnemius at its centre pushed its heads up into the hamstrings.)  The bellies are rigid with one bone (femur or tibia), so the keys hold in any pose.
Between keys the two bracketing keys are mixed linearly.

Check (after keying): the squat as muscle_squat_pose_check_blender.py (hip 5 -> 100, knee 5 -> 102, ankle 2 -> 17 deg)
in eighths.  Per pose, each muscle's path length by the squat path-length check's model (straight, or the knee / hip
cylinder wrap of its proposal's wrap_hint); belly k = (path - MG7 tendons) / (rest path - MG7 tendons); keys mixed;
measured: volume / rest, overlaps between all leg envelopes (MG7 and the MG8 glutes) against the same pose without
keys; renders (lateral / posterior / medial) at the start, half and full depth.  Saves a NEW blend (the input copy plus
the keys); the input is unchanged.

usage: python3.13 leg_muscle_length_response_blender.py -- MG8.blend SHA256 anchors_lower.json mg7_report.json OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, mg7_p, outdir = Path(args[0]), args[1], Path(args[2]), Path(args[3]), Path(args[4])
S = args[5] if len(args) > 5 else "left"
SUF = "L" if S == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG10_leg_length_{S}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; MW = anat.matrix_world.copy()
PROP = json.loads(anchors_p.read_text())["proposals"]
MG7 = json.loads(mg7_p.read_text())
NPHI = int(MG7["rules"]["nphi"]); MM = 2 * NPHI
K_SET = (0.85, 0.92, 1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.35, 1.40, 1.45, 1.50)


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


HJC, KJC, AJC = LM(f"hip_bone_{S}__HJC"), LM(f"femur_{S}__KJC"), LM(f"tibia_{S}__AJC")
TROCH = LM(f"hip_bone_{S}__trochanterion_skin")
EL, EM = LM(f"femur_{S}__epicondyle_lateral_skin"), LM(f"femur_{S}__epicondyle_medial_skin")
ML, MMal = LM(f"tibia_{S}__malleolus_lateral_skin"), LM(f"tibia_{S}__malleolus_medial_skin")
TOE = MW @ anat.data.bones[f"anat_metatarsal_2_{S}"].tail_local
lat = 1.0 if HJC.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
KNEE_AX, ANK_AX = (EL - EM).normalized(), (ML - MMal).normalized()
SHAFT_TOP = Vector((TROCH.x - lat * 0.045, 0.5 * (HJC.y + TROCH.y), TROCH.z - 0.030))   # as MG7
SEG = {"thigh": (SHAFT_TOP, KJC), "calf": (KJC, AJC)}
MUS = {m: v["segment"] for m, v in MG7["rules"]["sections"].items()}


def _pivot(m, v):
    """the belly end that cannot slide: the one whose tendon attaches to the bone the belly rides; else the one whose
    tendon is under a third of the other's (it attaches next to the joint); else the centre"""
    belly, ob, ib = v["bones"]                               # bones: belly, origin tendon, insertion tendon
    t = MG7["muscles"][f"hgpt.muscle.{m}.{SUF}"]["tendon_lengths_m"]
    if ob == belly:
        return "proximal"
    if ib == belly:
        return "distal"
    if t["origin"] < t["insertion"] / 3:
        return "proximal"
    if t["insertion"] < t["origin"] / 3:
        return "distal"
    return "centre"


PIVOT = {m: _pivot(m, v) for m, v in MG7["rules"]["sections"].items()}
OBJ = {m: bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects[f"hgpt.muscle.{m}.{SUF}"] for m in MUS}


# ---- posing and path lengths: the squat path-length check's model (re-implemented; that script runs on import)
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
    return T


def wrapped_length(p, q, c, axis, side, r):
    a = axis.normalized()
    e1 = (side - a * side.dot(a)).normalized(); e2 = a.cross(e1)
    P = Vector(((p - c).dot(e1), (p - c).dot(e2))); Q = Vector(((q - c).dot(e1), (q - c).dot(e2)))
    dz = (q - p).dot(a); d = Q - P
    n = Vector((-d.y, d.x)).normalized()
    if n.x < 0:
        n = -n
    if P.dot(n) >= r or P.length <= r or Q.length <= r:
        return (q - p).length

    def tangent_angle(X):
        th, be = math.atan2(X.y, X.x), math.acos(r / X.length)
        return max((th + be, th - be), key=lambda t: math.cos(t))
    ap, aq = tangent_angle(P), tangent_angle(Q)
    arc = abs(math.atan2(math.sin(aq - ap), math.cos(aq - ap)))
    return math.hypot(math.sqrt(P.length ** 2 - r * r) + math.sqrt(Q.length ** 2 - r * r) + r * arc, dz)


def path_length(T, mid):
    rec = PROP[mid]; w = rec.get("wrap_hint")
    pts = {a["role"]: MW @ anat.pose.bones[a["bone"]].matrix @ Vector(a["local_m"]) for a in rec["anchors"]}
    o, i = pts["origin"], pts["insertion"]
    if w and w["joint"] == "knee":
        R = T[CHAIN[0]].to_3x3()
        return wrapped_length(o, i, T[CHAIN[0]] @ KJC, R @ KNEE_AX, R @ (ANT if w["side"] == "anterior" else -ANT), w["radius_m"])
    if w and w["joint"] == "hip":
        return wrapped_length(o, i, HJC, LAT, ANT if w["side"] == "anterior" else -ANT, w["radius_m"])
    return (i - o).length


# ---- keys
def key_positions(m, k):
    """rest-space positions of belly m at length ratio k (world coordinates of the rest mesh)"""
    o = OBJ[m]; P = [o.matrix_world @ v.co for v in o.data.vertices]
    if len(P) % MM:
        raise RuntimeError(f"unexpected MG7 layout: {m}")
    p0, p1 = SEG[MUS[m]]; ax = (p1 - p0).normalized()
    t_of = lambda p: (p - p0).dot(ax)
    ta = sum((t_of(P[j]) for j in range(MM)), 0.0) / MM              # proximal ring
    tb = sum((t_of(P[len(P) - MM + j]) for j in range(MM)), 0.0) / MM   # distal ring
    t0 = {"proximal": ta, "distal": tb, "centre": 0.5 * (ta + tb)}[PIVOT[m]]
    new = [None] * len(P)
    for ring in range(len(P) // MM):
        b = ring * MM
        for j in range(NPHI):
            io, ii = b + j, b + MM - 1 - j
            po, pi = P[io], P[ii]
            fo, fi = p0 + ax * t_of(po), p0 + ax * t_of(pi)
            ro, ri = (po - fo).length, (pi - fi).length
            ro2 = math.sqrt(max(ri * ri + (ro * ro - ri * ri) / k, (ri + 1e-4) ** 2))
            new[io] = fo + (po - fo).normalized() * ro2 + ax * ((t0 + (t_of(po) - t0) * k) - t_of(po))
            new[ii] = pi + ax * ((t0 + (t_of(pi) - t0) * k) - t_of(pi))
    return new


GAP = float(MG7["rules"]["gap_m"])
DEEP_OF = {"vastus_lateralis": "vastus_intermedius", "vastus_medialis": "vastus_intermedius"}


def cyl(m, p):
    """(axial t, phi deg (0 anterior, +90 lateral), radius) in segment m's frame, as MG7 built it"""
    p0, p1 = SEG[MUS[m]]; ax = (p1 - p0).normalized()
    F = Vector((0, -1, 0)); F = (F - ax * F.dot(ax)).normalized()
    Lv = Vector((lat, 0, 0)); Lt = (Lv - ax * Lv.dot(ax) - F * Lv.dot(F)).normalized()
    t = (p - p0).dot(ax); q = p - (p0 + ax * t)
    return t, math.degrees(math.atan2(q.dot(Lt), q.dot(F))), q.length, p0 + ax * t


def outer_lookup(m, pos):
    """deep belly's outer radius as a function of (t, phi) from its (new) rings; None outside it (MG3's lookup)"""
    rings = []
    for ring in range(len(pos) // MM):
        pts = [cyl(m, pos[ring * MM + j]) for j in range(NPHI)]
        rings.append((pts[0][0], [(ph, r) for _t, ph, r, _c in pts]))
    rings.sort(key=lambda x: x[0])

    def at_ring(rr, phi):
        mid = rr[len(rr) // 2][0]
        un = lambda a: mid + ((a - mid + 180.0) % 360.0 - 180.0)
        ph = [un(a) for a, _r in rr]; x = un(phi)
        lo, hi = min(ph), max(ph)
        if x < lo - 3.0 or x > hi + 3.0:
            return None
        x = min(max(x, lo), hi)
        rs = [r for _a, r in rr]
        for (a0, r0), (a1, r1) in zip(zip(ph, rs), zip(ph[1:], rs[1:])):
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


T_REST = apply(pose(0, 0, 0))
KNEES = list(range(0, 152, 2))                               # the knee-only muscles' ratios against the knee angle
_L0 = {m: path_length(T_REST, f"hgpt.muscle.{m}.{SUF}") for m in ("vastus_intermedius",) + tuple(DEEP_OF)}
_TS = {m: sum(MG7["muscles"][f"hgpt.muscle.{m}.{SUF}"]["tendon_lengths_m"].values()) for m in _L0}
KCURVE = {m: [] for m in _L0}
for kn in KNEES:
    Tk = apply(pose(0, kn, 0))
    for m in _L0:
        KCURVE[m].append((path_length(Tk, f"hgpt.muscle.{m}.{SUF}") - _TS[m]) / (_L0[m] - _TS[m]))
apply(T_REST)
# the wrap model's lengths peak near 110 deg of knee flexion and fall after it (the path-length check's knee cylinder,
# beyond the squat's 102 deg): only the rising part is inverted
KN_MAX = min(max(range(len(KNEES)), key=lambda i: KCURVE[m][i]) for m in KCURVE)
KCURVE = {m: v[:KN_MAX + 1] for m, v in KCURVE.items()}


def deep_k_at(m, k):
    """the deep neighbour's ratio at the knee angle where muscle m has ratio k (curves are monotonic in the knee)"""
    c, d = KCURVE[m], KCURVE[DEEP_OF[m]]
    if k <= c[0]:
        return d[0]
    for i in range(len(c) - 1):
        if c[i] <= k <= c[i + 1]:
            w = (k - c[i]) / max(c[i + 1] - c[i], 1e-12); return d[i] + (d[i + 1] - d[i]) * w
    return d[-1]


def layered(m, k, new):
    """MG3: m's deep surface on its deep neighbour's new outer surface + the gap; outer by the area rule"""
    deep = DEEP_OF[m]; look = outer_lookup(deep, key_positions(deep, deep_k_at(m, k)))
    o = OBJ[m]; P = [o.matrix_world @ v.co for v in o.data.vertices]
    L = (SEG[MUS[m]][1] - SEG[MUS[m]][0]).length; pushed = 0; push_max = 0.0
    for ring in range(len(P) // MM):
        b = ring * MM
        for j in range(NPHI):
            io, ii = b + j, b + MM - 1 - j
            t, ph, ri_new, fi = cyl(m, new[ii])
            win = [look(t + dt * L, ph) for dt in (-0.012, -0.006, 0.0, 0.006, 0.012)]
            win = [w for w in win if w is not None]
            rd = max(win) if win else None
            if rd is None or rd + GAP <= ri_new:
                continue
            ri_rest, ro_rest = cyl(m, P[ii])[2], cyl(m, P[io])[2]
            ri2 = rd + GAP; ro2 = math.sqrt(ri2 * ri2 + (ro_rest * ro_rest - ri_rest * ri_rest) / k)
            fo = cyl(m, new[io])[3]
            new[ii] = fi + (new[ii] - fi).normalized() * ri2
            new[io] = fo + (new[io] - fo).normalized() * ro2
            pushed += 1; push_max = max(push_max, ri2 - ri_new)
    return new, pushed, push_max


LAYER_LOG = {}
for m, o in OBJ.items():
    if not o.data.shape_keys:
        o.shape_key_add(name="Basis", from_mix=False)
    Wi = o.matrix_world.inverted()
    for k in K_SET:
        kb = o.shape_key_add(name=f"HGPT_LEN_K_{int(round(k * 100)):03d}", from_mix=False); kb.value = 0.0
        new = key_positions(m, k)
        if m in DEEP_OF:
            new, n_p, p_max = layered(m, k, new)
            LAYER_LOG[f"{m} k{k}"] = {"deep_k": round(deep_k_at(m, k), 3), "pushed_points": n_p, "push_max_mm": round(p_max * 1000, 2)}
        for i, p in enumerate(new):
            kb.data[i].co = Wi @ p
    o["hgpt_length_response"] = "HGPT_LEN_K_<100k>: belly length ratio k, mixed between bracketing keys"


def set_k(m, k):
    kbs = OBJ[m].data.shape_keys.key_blocks
    for kb in kbs[1:]:
        if kb.name.startswith("HGPT_LEN_K_"):
            kb.value = 0.0
    ks = sorted(K_SET + (1.0,)); k = min(max(k, ks[0]), ks[-1])
    for a, b in zip(ks, ks[1:]):
        if a <= k <= b:
            wa, wb = (b - k) / (b - a), (k - a) / (b - a)
            for kk, w in ((a, wa), (b, wb)):
                if kk != 1.0:
                    kbs[f"HGPT_LEN_K_{int(round(kk * 100)):03d}"].value = w
            return


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    P = [e.matrix_world @ v.co for v in me.vertices]; F = [p.vertices[:] for p in me.polygons]; e.to_mesh_clear()
    return P, F


def volume(P, F):
    v = 0.0
    for f in F:
        for q in range(1, len(f) - 1):
            v += P[f[0]].dot(P[f[q]].cross(P[f[q + 1]])) / 6.0
    return abs(v)


# ---- contact behind the knee, keyed by knee flexion (the thigh bellies ride the femur and the calf bellies the tibia,
#      so their contact depends on the knee angle alone): beyond the plane through the knee axis bisecting the knee
#      angle, posterior of the axis, each side is flattened onto the plane less half the gap (the body's hinge contact),
#      only within the other side's FOOTPRINT: where the other side's tissue within NEAR of the plane (or beyond it)
#      projects onto the plane within FOOTPRINT_R.  (Flattening the whole plane cost the gastrocnemius 8 % of its volume
#      from 80 deg: its femoral heads lie above the knee axis and cross the plane where nothing meets them.  A footprint
#      of crossing tissue only missed the semimembranosus / adductor magnus, which the heads reach without either
#      crossing.)  Then calf points still inside a thigh belly (the gastrocnemius' femoral heads, bound to the tibia,
#      swing into the thigh at deep flexion) go out to its surface + the gap - a stand-in for a biarticular binding.
#      The volume the contact takes is given back as an outward bulge of the outer surface around the contact rings.
KNEE_KEYS, CONTACT_FROM, FOOTPRINT_R, NEAR = (80, 90, 100, 110, 120, 135), 70.0, 0.010, 0.015
THIGH_M = [m for m in MUS if MUS[m] == "thigh"]; CALF_M = [m for m in MUS if MUS[m] == "calf"]


RESOLVE = __import__("os").environ.get("MG10_RESOLVE", "1") == "1"
_RAYS = [Vector(v).normalized() for v in ((0.0123, 0.0217, 1.0), (1.0, 0.0311, -0.0173), (-0.0257, 1.0, 0.0419))]


def _inside(tr, p):
    """three-ray parity majority (as the fan builder)"""
    votes = 0
    for d in _RAYS:
        n, o = 0, p.copy()
        for _ in range(64):
            hit = tr.ray_cast(o, d, 1.0)
            if hit[0] is None:
                break
            n += 1; o = hit[0] + d * 1e-5
        votes += n % 2
    return votes >= 2


THIGH_BVH = {}
for m in [m for m in MUS if MUS[m] == "thigh"]:              # rest = femur frame; faces oriented outward
    P = [OBJ[m].matrix_world @ v.co for v in OBJ[m].data.vertices]; fs = [tuple(p.vertices) for p in OBJ[m].data.polygons]
    sv = sum(P[f[0]].dot(P[f[k]].cross(P[f[k + 1]])) for f in fs for k in range(1, len(f) - 1))
    THIGH_BVH[m] = BVHTree.FromPolygons(P, [f[::-1] for f in fs] if sv < 0 else fs)


def contact_positions(knee):
    Tt = pose(0, knee, 0)[CHAIN[1]]; Tti = Tt.inverted()
    u = (HJC - KJC).normalized(); v = (Tt @ AJC - KJC).normalized()
    n = (u - v).normalized(); b = (u + v).normalized()
    posed = {m: [Tt @ (OBJ[m].matrix_world @ v_.co) if m in CALF_M else OBJ[m].matrix_world @ v_.co
                 for v_ in OBJ[m].data.vertices] for m in THIGH_M + CALF_M}
    proj = lambda q: q - n * (q - KJC).dot(n)                # onto the plane

    def crossing(group, side):                               # the group's points beyond the plane, posterior of the axis
        pts = [q for m in group for q in posed[m] if (q - KJC).dot(b) > 0 and side * (q - KJC).dot(n) < NEAR]
        kd = KDTree(max(len(pts), 1))
        for i, q in enumerate(pts):
            kd.insert(proj(q), i)
        kd.balance(); return kd, len(pts)
    foot = {"thigh": crossing(CALF_M, -1.0), "calf": crossing(THIGH_M, 1.0)}   # what each side meets
    out, moved, resolved, bulged = {}, {}, {}, {}
    for m in THIGH_M + CALF_M:
        side, kd = (1.0, foot["thigh"]) if m in THIGH_M else (-1.0, foot["calf"])
        new = []; cnt = 0; hit = set()
        for vi, q in enumerate(posed[m]):
            d = q - KJC; dn = side * d.dot(n)
            if d.dot(b) > 0 and dn < GAP / 2 and kd[1] and kd[0].find(proj(q))[2] < FOOTPRINT_R:
                q = q + n * side * (GAP / 2 - dn); cnt += 1; hit.add(vi)
            if m in CALF_M and RESOLVE:                       # the gastrocnemius' femoral heads, bound to the tibia, swing
                for tm, tr in THIGH_BVH.items():             # into the thigh bellies: out to the surface + the gap
                    loc, nrm, _i, dist = tr.find_nearest(q, 0.03)
                    if loc is not None and (q - loc).dot(nrm) < GAP and _inside(tr, q):
                        q = loc + nrm * GAP; resolved[m] = resolved.get(m, 0) + 1; hit.add(vi)
            new.append(Tti @ q if m in CALF_M else q)
        out[m], bulged[m] = bulge(m, new, hit); moved[m] = cnt
    return out, {**moved, **{f"{k} (resolved out of the thigh)": v for k, v in resolved.items()},
                 **{f"{k} (bulge scale)": v for k, v in bulged.items() if v}}


BULGE_RINGS = 4


def bulge(m, new, hit):
    """the volume the contact took, given back as an outward radial bulge of the outer surface over the contact rings
    (+- BULGE_RINGS, tapered), in the segment's frame; the contact points themselves stay on the plane"""
    if not hit:
        return new, 0.0
    F = [tuple(p.vertices) for p in OBJ[m].data.polygons]
    P0 = [OBJ[m].matrix_world @ v.co for v in OBJ[m].data.vertices]
    V0, V1 = volume(P0, F), volume(new, F)
    if V1 >= V0:
        return new, 0.0
    rings = {i // MM for i in hit}
    wr = {}
    for r in range(len(new) // MM):
        dmin = min(abs(r - h) for h in rings)
        x = max(0.0, 1.0 - dmin / (BULGE_RINGS + 1.0)); wr[r] = x * x * (3 - 2 * x)
    cand = [(r * MM + j, r * MM + MM - 1 - j, wr[r]) for r in range(len(new) // MM) for j in range(NPHI)
            if wr[r] > 0 and r * MM + j not in hit]

    def swell(c):
        out = list(new)
        for io, ii, w in cand:
            _t, _ph, ro, fo = cyl(m, new[io]); ri = cyl(m, new[ii])[2]
            out[io] = fo + (new[io] - fo).normalized() * (ri + (ro - ri) * (1.0 + c * w))
        return out
    c1 = 0.1; Vc = volume(swell(c1), F)
    if Vc <= V1:
        return new, 0.0
    c = min(1.5, c1 * (V0 - V1) / (Vc - V1))
    return swell(c), round(c, 3)


CONTACT_LOG = {}
for kn in KNEE_KEYS:
    pos, moved = contact_positions(kn)
    CONTACT_LOG[kn] = {m: c for m, c in moved.items() if c}
    for m, new in pos.items():
        o = OBJ[m]; Wi = o.matrix_world.inverted()
        kb = o.shape_key_add(name=f"HGPT_CONTACT_KNEE_{kn:03d}", from_mix=False); kb.value = 0.0
        for i, p in enumerate(new):
            kb.data[i].co = Wi @ p


def set_contact(knee):
    ks = [CONTACT_FROM] + list(KNEE_KEYS); x = min(max(knee, ks[0]), ks[-1])
    for m in THIGH_M + CALF_M:
        kbs = OBJ[m].data.shape_keys.key_blocks
        for kn in KNEE_KEYS:
            kbs[f"HGPT_CONTACT_KNEE_{kn:03d}"].value = 0.0
        for a, b in zip(ks, ks[1:]):
            if a <= x <= b:
                for kk, w in ((a, (b - x) / (b - a)), (b, (x - a) / (b - a))):
                    if kk != CONTACT_FROM:
                        kbs[f"HGPT_CONTACT_KNEE_{int(kk):03d}"].value = w
                break


# ---- check through the squat
LEG = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects if o.name.endswith(f".{SUF}")
       and o.name.split(".")[2] in tuple(MUS) + ("gluteus_maximus", "gluteus_medius")]


def overlaps():
    dg = bpy.context.evaluated_depsgraph_get(); tr = {o.name.split(".")[2]: BVHTree.FromObject(o, dg) for o in LEG}
    pairs, nm = {}, list(tr)
    for i, a in enumerate(nm):
        for b in nm[i + 1:]:
            ov = tr[a].overlap(tr[b])
            if ov:
                pairs[f"{a} | {b}"] = len(ov)
    return pairs


T0 = apply(pose(0, 0, 0))
TEND = {m: MG7["muscles"][f"hgpt.muscle.{m}.{SUF}"]["tendon_lengths_m"] for m in MUS}
TS = {m: TEND[m]["origin"] + TEND[m]["insertion"] for m in MUS}
L0 = {m: path_length(T0, f"hgpt.muscle.{m}.{SUF}") for m in MUS}
V0 = {m: volume(*evaluated(OBJ[m])) for m in MUS}
rep = {"status": "PROXY_LENGTH_RESPONSE_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": S,
       "keys": [f"HGPT_LEN_K_{int(round(k * 100)):03d}" for k in K_SET],
       "pivot": PIVOT,
       "rule": "stations along the segment axis about the pivot x k; deep surface kept; outer r_o'^2 = r_i^2 + "
               "(r_o^2 - r_i^2) / k (MG2); rest-space keys keyed by belly length ratio k",
       "layered": {"deep_of": DEEP_OF, "per_key": LAYER_LOG,
                   "knee_curves_k": {m: [round(x, 4) for x in v[::5]] for m, v in KCURVE.items()}, "knee_deg": KNEES[:KN_MAX + 1:5],
                   "knee_curve_used_to_deg": KNEES[KN_MAX]},
       "contact": {"keys": [f"HGPT_CONTACT_KNEE_{kn:03d}" for kn in KNEE_KEYS], "from_deg": CONTACT_FROM,
                   "rule": "posterior of the knee axis, beyond the plane bisecting the knee angle, within the other side's "
                           "footprint: flattened onto it less half the gap, each side in its own bone's rest frame",
                   "footprint_radius_m": FOOTPRINT_R, "footprint_band_m": NEAR,
                   "calf_points_resolved_out_of_thigh_bellies": RESOLVE,
                   "volume_kept_by_bulge": "outer surface swollen radially over the contact rings +- 4 (tapered)", "moved_vertices_per_key": CONTACT_LOG},
       "path_model": "squat path-length check: straight, or the knee / hip cylinder wrap of the proposal's wrap_hint",
       "rest_path_m": {m: round(v, 4) for m, v in L0.items()}, "tendons_m": {m: round(v, 4) for m, v in TS.items()},
       "poses": {}}
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 1.1
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 640
TEN = [o for o in bpy.data.collections["HGPT_EXPERIMENT_TENDONS"].objects if o.name.split(".")[3] == SUF
       and o.name.split(".")[2] in tuple(MUS) + ("gluteus_maximus", "gluteus_medius")]
for ob in sc.objects:
    if ob.type == "MESH" and ob not in LEG and ob not in TEN:
        ob.hide_render = True
for e in range(9):
    q = e / 8.0
    h, kn, a = 5 + 95 * q, 5 + 97 * q, 2 + 15 * q
    T = apply(pose(h, kn, a))
    for m in MUS:
        set_k(m, 1.0)
    set_contact(0.0)
    bpy.context.view_layer.update(); base = overlaps()
    per = {}
    for m in MUS:
        L = path_length(T, f"hgpt.muscle.{m}.{SUF}"); k = (L - TS[m]) / (L0[m] - TS[m]); set_k(m, k)
        per[m] = {"path_m": round(L, 4), "belly_k": round(k, 3)}
    bpy.context.view_layer.update(); length_only = overlaps()
    set_contact(kn); bpy.context.view_layer.update()
    for m in MUS:
        per[m]["volume_ratio"] = round(volume(*evaluated(OBJ[m])) / V0[m], 4)
    keyed = overlaps(); tag = f"q{int(q * 1000):04d}"
    rep["poses"][tag] = {"hip_knee_ankle_deg": [round(h, 1), round(kn, 1), round(a, 1)], "muscles": per,
                         "overlaps_keyed": keyed, "overlaps_keyed_total": sum(keyed.values()),
                         "overlaps_length_keys_only_total": sum(length_only.values()),
                         "overlaps_without_keys_total": sum(base.values())}
    print("POSE", tag, json.dumps({"k": {m: v["belly_k"] for m, v in per.items()}, "vol": {m: v["volume_ratio"] for m, v in per.items()},
                                   "ov_keyed": keyed, "ov_base": sum(base.values()), "ov_length_only": sum(length_only.values())}), flush=True)
    if e in (0, 4, 8):
        centre = T[CHAIN[0]] @ (KJC + (HJC - KJC) * 0.35); cd.ortho_scale = 0.8
        for view, dv in {"lateral": (lat, 0, 0), "posterior": (0, 1, 0), "medial": (-lat, 0, 0)}.items():
            d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = str(outdir / f"mg10_{S}_{tag}_{view}.png"); bpy.ops.render.render(write_still=True)
for m in MUS:
    set_k(m, 1.0)
set_contact(0.0)
apply(pose(0, 0, 0))
for o in bpy.data.objects:                                   # the review camera is not part of the experiment copy
    if o.name == "C":
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
rep["output_blend"] = OUT.name; rep["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
rep["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected
(outdir / f"mg10_{S}_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": rep["input_unchanged"]}), flush=True)
