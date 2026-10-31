"""EXPERIMENT (copy only): MG11b - length response of the arm bellies (MG1's biceps x2, brachialis, triceps x3 and
MG11's brachioradialis) keyed by the belly's LENGTH RATIO k, as MG10 keyed the legs: any movement drives the keys
through the muscle's path length (Work's kernel: resolve_path / path_length, as MG2), the curl is only the test.

Keys HGPT_LEN_K_<100k> (rest space; each belly rides one bone): in the belly's segment frame (the humeral line GH -> EJC
for MG1's bellies, the forearm line EJC -> WJC for the brachioradialis) the stations move along the axis by k about the
belly's PIVOT - the end that cannot slide: the end whose anchor is on the bone the belly rides (brachialis, triceps
lateral / medial: proximal; brachioradialis: distal), else the end whose tendon is under a third of the other's, else the
centre (biceps heads, triceps long) - and each section keeps its deep surface while the outer surface takes
r_o'^2 = r_i^2 + (r_o^2 - r_i^2) / k (MG2's rule: area x 1 / k, volume kept, bulging towards the skin).

LAYERED (MG3): the biceps heads lie on the brachialis and the triceps lateral and long heads on the triceps medial head
(deep surface on the deep neighbour's new outer surface + the gap; outer by the same area rule).  The deep neighbour's
ratio at a given superficial ratio is read off elbow-only curves (elbow 0-150 deg, shoulder at rest, inverted on their
monotonic part): exact for the one-joint pairs (triceps lateral / medial), an approximation for the biceps and the
triceps long head when the shoulder also moves (recorded).

The brachioradialis (MG11 builds its belly below the elbow only; its origin tendon stands in for belly above it) counts
its origin tendon as belly: k = (path - insertion tendon) / (rest path - insertion tendon) - about 0.43 at 140 deg, near
a constant 4.5 cm moment-arm estimate (0.49).  (With both tendons fixed, k fell to 0.05; a 22 mm anterior elbow wrap of
the squat check's kind took the long way round in the deep-flexion hairpin, k 1.09 at 120 deg.)

Contact keys HGPT_CONTACT_ELBOW_<deg>, 70-150 deg (elbow angle alone, so any movement that bends the elbow drives them;
MG10's knee contact carried to the elbow, computed on the length-keyed shapes at each angle and stored as corrections):
both sides compressed off the plane bisecting the elbow angle, order-preserving, the volume given back sideways and the
biceps re-laid on the brachialis - see the block comment in the code.

Check: the curl, elbow from rest to 140 deg (shoulder at rest): per pose k, volume / rest, overlaps between the arm
bellies (and with the deltoid), renders.  Saves a NEW blend (the input copy plus the keys); the input is unchanged.

usage: python3.13 arm_muscle_length_keys_blender.py -- MG11.blend SHA256 anchors.json mg1_report.json mg11_report.json OUT_DIR [left|right]
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.anatomical_muscles import kernel  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, mg1_p, mg11_p, outdir = (Path(args[0]), args[1], Path(args[2]), Path(args[3]), Path(args[4]),
                                                   Path(args[5]))
S = args[6] if len(args) > 6 else "left"
SUF = "L" if S == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG11b_arm_length_{S}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; MW = anat.matrix_world.copy()
PROP = json.loads(anchors_p.read_text())["proposals"]
REPS = {**json.loads(mg1_p.read_text())["muscles"], **json.loads(mg11_p.read_text())["muscles"]}
NPHI = 14; MM = 2 * NPHI; GAP = 0.0012
K_SET = tuple(round(0.35 + 0.05 * i, 2) for i in range(25) if abs(0.35 + 0.05 * i - 1.0) > 1e-6)   # 0.35 .. 1.55
MUSCLES = ("biceps_brachii_long", "biceps_brachii_short", "brachialis", "triceps_long", "triceps_lateral",
           "triceps_medial", "brachioradialis")
DEEP_OF = {"biceps_brachii_long": "brachialis", "biceps_brachii_short": "brachialis",
           "triceps_lateral": "triceps_medial", "triceps_long": "triceps_medial"}
OBJ = {m: bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects[f"hgpt.muscle.{m}.{SUF}"] for m in MUSCLES}


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


GH, EJC, WJC = LM(f"scapula_{S}__GH"), LM(f"humerus_{S}__EJC"), LM(f"radius_{S}__WJC")
EL, EM = LM(f"humerus_{S}__epicondyle_lateral_skin"), LM(f"humerus_{S}__epicondyle_medial_skin")
lat = 1.0 if GH.x > 0 else -1.0
SEG = {m: ((EJC, WJC) if m == "brachioradialis" else (GH, EJC)) for m in MUSCLES}


def frame(m):
    p0, p1 = SEG[m]; ax = (p1 - p0).normalized()
    F = Vector((0, -1, 0)); F = (F - ax * F.dot(ax)).normalized()
    Lv = Vector((lat, 0, 0)); Lt = (Lv - ax * Lv.dot(ax) - F * Lv.dot(F)).normalized()
    return p0, ax, F, Lt


def cyl(m, p):
    p0, ax, F, Lt = frame(m); t = (p - p0).dot(ax); q = p - (p0 + ax * t)
    return t, math.degrees(math.atan2(q.dot(Lt), q.dot(F))), q.length, p0 + ax * t


# ---- posing (MG2's elbow flexion about the epicondyle axis) and kernel path lengths
ELB = (EL - EM).normalized()
rot = lambda p, ax, deg: Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-p)
SG = 1.0 if ((rot(EJC, ELB, 5) @ WJC) - WJC).dot(Vector((0, -1, 0))) > 0 else -1.0
REST_ELB = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, (GH - EJC).normalized().dot((WJC - EJC).normalized())))))
FOREARM = (f"anat_ulna_{S}", f"anat_radius_{S}")


def pose_elbow(deg):
    T = rot(EJC, ELB, SG * (deg - REST_ELB)) if deg > REST_ELB else Matrix()
    for bn in FOREARM:
        anat.pose.bones[bn].matrix = MW.inverted() @ T @ MW @ anat.data.bones[bn].matrix_local
        bpy.context.view_layer.update()


def transforms():
    return {b.name: [list(r) for r in (MW @ b.matrix)] for b in anat.pose.bones}


ANCH = {m: [{"bone": a["bone"], "local_m": a["local_m"]} for a in PROP[f"hgpt.muscle.{m}.{SUF}"]["anchors"]] for m in MUSCLES}
ROLEB = {m: {a["role"]: a["bone"] for a in PROP[f"hgpt.muscle.{m}.{SUF}"]["anchors"]} for m in MUSCLES}
TEND = {m: REPS[f"hgpt.muscle.{m}.{SUF}"]["tendon_lengths_m"] for m in MUSCLES}
TS = {m: TEND[m]["origin"] + TEND[m]["insertion"] for m in MUSCLES}
TS["brachioradialis"] = TEND["brachioradialis"]["insertion"]   # its origin "tendon" stands in for belly above the elbow


def path_len(m, T):
    return kernel.path_length(kernel.resolve_path(ANCH[m], T))


def riding(m):
    o = OBJ[m]; gs = [g.name for g in o.vertex_groups]
    return max(((g.weight, gs[g.group]) for g in o.data.vertices[0].groups))[1]


def _pivot(m):
    rb = riding(m)
    if ROLEB[m]["origin"] == rb:
        return "proximal"
    if ROLEB[m]["insertion"] == rb:
        return "distal"
    if TEND[m]["origin"] < TEND[m]["insertion"] / 3:
        return "proximal"
    if TEND[m]["insertion"] < TEND[m]["origin"] / 3:
        return "distal"
    return "centre"


PIVOT = {m: _pivot(m) for m in MUSCLES}
REST_P = {m: [OBJ[m].matrix_world @ v.co for v in OBJ[m].data.vertices] for m in MUSCLES}
NV = {m: len(REST_P[m]) - len(REST_P[m]) % MM for m in MUSCLES}   # ring vertices (MG1 adds two cap centres after them)


def key_positions(m, k):
    P = REST_P[m]; p0, ax, _F, _L = frame(m); t_of = lambda p: (p - p0).dot(ax); nv = NV[m]
    ta = sum(t_of(P[j]) for j in range(MM)) / MM; tb = sum(t_of(P[nv - MM + j]) for j in range(MM)) / MM
    t0 = {"proximal": min(ta, tb), "distal": max(ta, tb), "centre": 0.5 * (ta + tb)}[PIVOT[m]]
    shift = lambda p: ax * ((t0 + (t_of(p) - t0) * k) - t_of(p))
    new = list(P)
    for ring in range(nv // MM):
        b = ring * MM
        for j in range(NPHI):
            io, ii = b + j, b + MM - 1 - j
            po, pi = P[io], P[ii]
            fo, fi = p0 + ax * t_of(po), p0 + ax * t_of(pi)
            ro, ri = (po - fo).length, (pi - fi).length
            ro2 = math.sqrt(max(ri * ri + (ro * ro - ri * ri) / k, (ri + 1e-4) ** 2))
            new[io] = fo + (po - fo).normalized() * ro2 + shift(po)
            new[ii] = pi + shift(pi)
    for ci in range(nv, len(P)):                              # MG1's cap centres move with the axial map
        new[ci] = P[ci] + shift(P[ci])
    return new


def outer_lookup(m, pos):
    rings = []
    for ring in range(NV[m] // MM):
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
        x = min(max(x, lo), hi); rs = [r for _a, r in rr]
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


# elbow-only curves (shoulder at rest) for the layering
ELBOWS = list(range(0, 152, 2))
pose_elbow(0.0); T_REST = transforms()
L0 = {m: path_len(m, T_REST) for m in MUSCLES}
KC = {m: [] for m in MUSCLES}
for e in ELBOWS:
    pose_elbow(max(e, REST_ELB)); T = transforms()
    for m in MUSCLES:
        KC[m].append((path_len(m, T) - TS[m]) / (L0[m] - TS[m]))
pose_elbow(0.0)


def deep_k_at(m, k):
    """the deep neighbour's ratio at the elbow angle where superficial m has ratio k (its curve inverted on the monotonic
    part from rest)"""
    c, d = KC[m], KC[DEEP_OF[m]]; sgn = 1.0 if c[-1] >= c[0] else -1.0
    n = 1
    while n < len(c) and sgn * (c[n] - c[n - 1]) >= -1e-9:
        n += 1
    c, d = c[:n], d[:n]
    if sgn * (k - c[0]) <= 0:
        return d[0]
    for i in range(len(c) - 1):
        if min(c[i], c[i + 1]) <= k <= max(c[i], c[i + 1]):
            w = (k - c[i]) / (c[i + 1] - c[i]) if c[i + 1] != c[i] else 0.0
            return d[i] + (d[i + 1] - d[i]) * w
    return d[-1]


def layered(m, k, new):
    deep = DEEP_OF[m]; look = outer_lookup(deep, key_positions(deep, deep_k_at(m, k)))
    P = REST_P[m]; L = (SEG[m][1] - SEG[m][0]).length; pushed = 0; pmax = 0.0
    for ring in range(NV[m] // MM):
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
            new[ii] = fi + (new[ii] - fi).normalized() * ri2; new[io] = fo + (new[io] - fo).normalized() * ro2
            pushed += 1; pmax = max(pmax, ri2 - ri_new)
    return new, pushed, pmax


LAYER_LOG = {}
for m in MUSCLES:
    o = OBJ[m]
    if not o.data.shape_keys:
        o.shape_key_add(name="Basis", from_mix=False)
    Wi = o.matrix_world.inverted()
    for k in K_SET:
        new = key_positions(m, k)
        if m in DEEP_OF:
            new, n_p, p_max = layered(m, k, new)
            LAYER_LOG[f"{m} k{k}"] = {"deep_k": round(deep_k_at(m, k), 3), "pushed_points": n_p, "push_max_mm": round(p_max * 1000, 2)}
        kb = o.shape_key_add(name=f"HGPT_LEN_K_{int(round(k * 100)):03d}", from_mix=False); kb.value = 0.0
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
            for kk, w in ((a, (b - k) / (b - a)), (b, (k - a) / (b - a))):
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


# ---- contact at the elbow, keyed by elbow flexion (the upper-arm bellies ride the humerus and the brachioradialis the
#      radius, so their contact depends on the elbow angle): MG10's knee contact carried to the elbow.  Each key is
#      computed on the LENGTH-KEYED shapes at that elbow angle (shoulder at rest: the elbow flexors shorten hard while they
#      meet) and stored as a correction only, so it adds to the length keys.  On the flexion side of the elbow axis, x is
#      the signed distance from the plane bisecting the elbow angle (+ towards the upper arm).  Where the other side's
#      tissue lies in the same column (its points projected onto the plane within FOOTPRINT_R, fading out by 2 x), each
#      side's slab between its deepest point in the column (x_min, read over a SMOOTH_R disc) and ZONE beyond the plane is
#      compressed linearly onto [gap / 2, ZONE]: monotonic along x, so the bellies of one side keep their order (the
#      biceps stays on the brachialis) while both sides clear the plane.  The displacement field is then made smooth
#      over each surface (SMOOTH_IT passes, never below what the contact needs: no steps between columns).  The volume
#      taken is given back sideways: each compressed ring is stretched across the contact direction (along axis x n, so
#      no point's distance from the plane changes) until its cross-section area is back (stretch <= SPREAD_CAP, smoothed
#      along the belly), the biceps heads and the brachioradialis on their side away from the neighbour (long head
#      laterally, short head medially, brachioradialis away from the short head), the brachialis both ways; then the biceps heads are re-laid on the brachialis's corrected outer surface + the gap
#      (MG3's rule; off the contact the outer surface lifts with the inner, on it it only clears it).  MG10's radial
#      bulge (MG11B_VOLUME=radial) and no give-back (none) are kept for comparison.
CONTACT_KEYS = tuple(int(x) for x in os.environ.get("MG11B_CONTACT_KEYS", "70,80,90,100,110,120,130,140,150").split(","))
CONTACT_FROM, FOOTPRINT_R, SMOOTH_R, BULGE_RINGS = 60.0, 0.010, 0.008, 4
ZONE = float(os.environ.get("MG11B_ZONE", "0.025")); RELAYER = os.environ.get("MG11B_RELAYER", "1") == "1"
FORE = ["brachioradialis"]; UPPER = [m for m in MUSCLES if m not in FORE]
FACES = {m: [tuple(p.vertices) for p in OBJ[m].data.polygons] for m in MUSCLES}
NBR = {m: [set() for _ in OBJ[m].data.vertices] for m in MUSCLES}
for m in MUSCLES:
    for f in FACES[m]:
        for i, a in enumerate(f):
            NBR[m][a].update((f[i - 1], f[(i + 1) % len(f)]))
SMOOTH_IT = int(os.environ.get("MG11B_SMOOTH_IT", "8")); SPREAD_CAP = float(os.environ.get("MG11B_SPREAD_CAP", "2.6"))


def k_at(m, deg):
    c = KC[m]; x = min(max(deg, ELBOWS[0]), ELBOWS[-1])
    for i in range(len(ELBOWS) - 1):
        if ELBOWS[i] <= x <= ELBOWS[i + 1]:
            w = (x - ELBOWS[i]) / (ELBOWS[i + 1] - ELBOWS[i]); return c[i] + (c[i + 1] - c[i]) * w
    return c[-1]


def keyed_shape(m, deg):
    k = k_at(m, deg); new = key_positions(m, k)
    return layered(m, k, new)[0] if m in DEEP_OF else new


def bulge(m, new, hit, ref):
    if not hit:
        return new, 0.0
    V0_, V1 = volume(ref, FACES[m]), volume(new, FACES[m])
    if V1 >= V0_:
        return new, 0.0
    rings = {i // MM for i in hit if i < NV[m]}
    if not rings:
        return new, 0.0
    wr = {}
    for r in range(NV[m] // MM):
        x = max(0.0, 1.0 - min(abs(r - h) for h in rings) / (BULGE_RINGS + 1.0)); wr[r] = x * x * (3 - 2 * x)
    cand = [(r * MM + j, r * MM + MM - 1 - j, wr[r]) for r in range(NV[m] // MM) for j in range(NPHI)
            if wr[r] > 0 and r * MM + j not in hit]

    def swell(c):
        out = list(new)
        for io, ii, w in cand:
            _t, _ph, ro, fo = cyl(m, new[io]); ri = cyl(m, new[ii])[2]
            out[io] = fo + (new[io] - fo).normalized() * (ri + (ro - ri) * (1.0 + c * w))
        return out
    c1 = 0.1; Vc = volume(swell(c1), FACES[m])
    if Vc <= V1:
        return new, 0.0
    c = min(1.5, c1 * (V0_ - V1) / (Vc - V1))
    return swell(c), round(c, 3)


VOLUME_MODE = os.environ.get("MG11B_VOLUME", "side1")


SPREAD_AWAY = {"biceps_brachii_long": "biceps_brachii_short", "biceps_brachii_short": "biceps_brachii_long",
               "brachioradialis": "biceps_brachii_short"}
SPREAD_SKIP = tuple(x for x in os.environ.get("MG11B_SPREAD_SKIP", "").split(",") if x)


def side_spread(m, new, ref, hit, ax, n, away=None):
    """give back each compressed ring's cross-section area by stretching it across the contact direction (along
    ax x n, which leaves every point's distance from the contact plane unchanged): flattened tissue spreads sideways"""
    e = ax.cross(n)
    if e.length < 1e-6:
        return new, 0.0
    e.normalize(); f = ax.cross(e); one = 0.0
    if away is not None:                                       # one-sided: only the half away from the neighbour moves
        one = 1.0 if (sum(new, Vector()) / len(new) - away).dot(e) > 0 else -1.0
    area = lambda R: 0.5 * abs(sum((R[i].dot(e)) * (R[(i + 1) % len(R)].dot(f)) - (R[(i + 1) % len(R)].dot(e)) * (R[i].dot(f))
                                   for i in range(len(R))))
    nr = NV[m] // MM; hr = {i // MM for i in hit if i < NV[m]}; lf = [0.0] * nr
    for r in hr:
        a1 = area(new[r * MM:(r + 1) * MM]); a0 = area(ref[r * MM:(r + 1) * MM])
        g = a0 / max(a1, 1e-12)
        lf[r] = math.log(min(SPREAD_CAP, max(1.0, 2.0 * g - 1.0 if one else g)))
    for _ in range(4):                                         # smoothing along the belly
        lf = [0.25 * lf[max(r - 1, 0)] + 0.5 * lf[r] + 0.25 * lf[min(r + 1, nr - 1)] for r in range(nr)]
    out = list(new); smax = 1.0
    for r in range(nr):
        s_ = math.exp(lf[r])
        if s_ <= 1.0 + 1e-6:
            continue
        R = new[r * MM:(r + 1) * MM]; c = sum(R, Vector()) / MM; smax = max(smax, s_)
        for j in range(MM):
            q = new[r * MM + j]; de = (q - c).dot(e)
            if one == 0.0 or de * one > 0:
                out[r * MM + j] = q + e * (de * (s_ - 1.0))
    return out, round(smax, 3)


def contact_corrections(deg):
    Tf = rot(EJC, ELB, SG * (deg - REST_ELB)) if deg > REST_ELB else Matrix(); Tfi = Tf.inverted()
    u = (GH - EJC).normalized(); v = (Tf @ WJC - EJC).normalized()
    n = (u - v).normalized(); b = (u + v).normalized()
    shapes = {m: keyed_shape(m, deg) for m in MUSCLES}
    posed = {m: [Tf @ p for p in shapes[m]] if m in FORE else list(shapes[m]) for m in MUSCLES}
    X = lambda q: (q - EJC).dot(n); proj = lambda q: q - n * (q - EJC).dot(n)
    pts = {g: [q for m in grp for q in posed[m] if (q - EJC).dot(b) > 0] for g, grp in (("upper", UPPER), ("fore", FORE))}
    kd = {}
    for g, P in pts.items():
        t = KDTree(max(len(P), 1))
        for i, q in enumerate(P):
            t.insert(proj(q), i)
        t.balance(); kd[g] = t
    corr, log, HIT = {}, {}, {}
    for m in MUSCLES:
        g, o, sd = ("upper", "fore", 1.0) if m in UPPER else ("fore", "upper", -1.0)
        req = [0.0] * len(posed[m]); hit = set(); dmax = 0.0
        axp = (Tf.to_3x3() @ frame(m)[1]) if m in FORE else frame(m)[1]
        for vi, q in enumerate(posed[m]):
            x = sd * X(q); c = proj(q)
            if (q - EJC).dot(b) > 0 and x < ZONE and pts[o]:
                dfoot = kd[o].find(c)[2]; w = 1.0 - min(1.0, max(0.0, (dfoot - FOOTPRINT_R) / FOOTPRINT_R))
                near = kd[g].find_range(c, SMOOTH_R)
                xmin = min([sd * X(pts[g][i]) for _p, i, _d in near] + [x])
                if w > 0 and xmin < GAP / 2:
                    f = GAP / 2 + (x - xmin) * (ZONE - GAP / 2) / (ZONE - xmin)
                    dx = w * w * (3 - 2 * w) * (max(f, GAP / 2) - x)
                    if dx > 1e-6:
                        req[vi] = dx; hit.add(vi); dmax = max(dmax, dx)
        # the displacement field made smooth over the surface (never below what the contact needs): no steps between
        # neighbouring columns, and the tissue next to the contact is carried along
        dxs = list(req)
        for _ in range(SMOOTH_IT):
            dxs = [max(req[i], 0.5 * dxs[i] + 0.5 * sum(dxs[j] for j in NBR[m][i]) / max(len(NBR[m][i]), 1))
                   for i in range(len(dxs))]
        new = [q + n * sd * d for q, d in zip(posed[m], dxs)]
        if m in SPREAD_SKIP:
            cb = 0.0
        elif VOLUME_MODE in ("side", "side1"):
            aw = None
            if VOLUME_MODE == "side1" and m in SPREAD_AWAY:
                aw = sum(posed[SPREAD_AWAY[m]], Vector()) / len(posed[SPREAD_AWAY[m]])
            new, cb = side_spread(m, new, posed[m], hit, axp, n, aw)
        elif VOLUME_MODE == "radial":
            new = [Tfi @ q for q in new] if m in FORE else new
            new, cb = bulge(m, new, hit, shapes[m])
        else:
            cb = 0.0
        if m in FORE and VOLUME_MODE != "radial":
            new = [Tfi @ q for q in new]
        corr[m] = [p - r for p, r in zip(new, shapes[m])]; HIT[m] = hit
        if hit:
            log[m] = {"moved": len(hit), "max_mm": round(dmax * 1000, 1), "volume_give_back": VOLUME_MODE, "scale": cb}
    if RELAYER:
        for m, deep in DEEP_OF.items():
            if m not in UPPER or not log.get(m):
                continue
            dpos = [r + c for r, c in zip(shapes[deep], corr[deep])]; look = outer_lookup(deep, dpos)
            new = [r + c for r, c in zip(shapes[m], corr[m])]; L = (SEG[m][1] - SEG[m][0]).length; np_ = 0
            for ring in range(NV[m] // MM):
                for j in range(NPHI):
                    ii, io = ring * MM + MM - 1 - j, ring * MM + j
                    t, ph, ri, fi = cyl(m, new[ii])
                    win = [w for w in (look(t + dt * L, ph) for dt in (-0.012, -0.006, 0.0, 0.006, 0.012)) if w is not None]
                    if not win or max(win) + GAP <= ri:
                        continue
                    ri2 = max(win) + GAP; new[ii] = fi + (new[ii] - fi).normalized() * ri2; np_ += 1
                    _t, _p, ro, fo = cyl(m, new[io])
                    # off the contact the outer surface lifts with the inner (thickness kept); on it, it only clears it
                    ro2 = ro + (ri2 - ri) if io not in HIT[m] else max(ro, ri2 + 0.0008)
                    new[io] = fo + (new[io] - fo).normalized() * ro2
            corr[m] = [p - r for p, r in zip(new, shapes[m])]; log[m]["relayered_points"] = np_
    return corr, log


CONTACT_LOG = {}
for deg in CONTACT_KEYS:
    corr, CONTACT_LOG[deg] = contact_corrections(deg)
    for m in MUSCLES:
        o = OBJ[m]; Wi3 = o.matrix_world.inverted().to_3x3()
        kb = o.shape_key_add(name=f"HGPT_CONTACT_ELBOW_{deg:03d}", from_mix=False); kb.value = 0.0
        for i, dv in enumerate(corr[m]):
            kb.data[i].co = o.data.vertices[i].co + Wi3 @ dv


def set_contact(deg):
    ks = [CONTACT_FROM] + list(CONTACT_KEYS); x = min(max(deg, ks[0]), ks[-1])
    for m in MUSCLES:
        kbs = OBJ[m].data.shape_keys.key_blocks
        for kd in CONTACT_KEYS:
            kbs[f"HGPT_CONTACT_ELBOW_{kd:03d}"].value = 0.0
        for a, b in zip(ks, ks[1:]):
            if a <= x <= b:
                for kk, w in ((a, (b - x) / (b - a)), (b, (x - a) / (b - a))):
                    if kk != CONTACT_FROM:
                        kbs[f"HGPT_CONTACT_ELBOW_{int(kk):03d}"].value = w
                break


OTHERS = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects if o.name.endswith(f".{SUF}")
          and o.name.split(".")[2].startswith("deltoid")]


def overlaps():
    dg = bpy.context.evaluated_depsgraph_get()
    tr = {o.name.split(".")[2]: BVHTree.FromObject(o, dg) for o in list(OBJ.values()) + OTHERS}
    pairs, nm = {}, list(tr)
    for i, a in enumerate(nm):
        for b in nm[i + 1:]:
            if a.startswith("deltoid") and b.startswith("deltoid"):
                continue
            ov = tr[a].overlap(tr[b])
            if ov:
                pairs[f"{a} | {b}"] = len(ov)
    return pairs


V0 = {m: volume(*evaluated(OBJ[m])) for m in MUSCLES}
rep = {"status": "PROXY_LENGTH_RESPONSE_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": S,
       "keys": [f"HGPT_LEN_K_{int(round(k * 100)):03d}" for k in K_SET], "pivot": PIVOT,
       "rule": "stations along the segment axis about the pivot x k; deep surface kept; outer r_o'^2 = r_i^2 + "
               "(r_o^2 - r_i^2) / k (MG2); rest-space keys keyed by belly length ratio k",
       "path_model": "Work's kernel: resolve_path / path_length (straight between the proposed anchors), as MG2; the "
                     "brachioradialis's origin tendon counted as belly",
       "layered": {"deep_of": DEEP_OF, "per_key": LAYER_LOG,
                   "elbow_curves_k": {m: [round(x, 4) for x in v[::10]] for m, v in KC.items()}, "elbow_deg": ELBOWS[::10],
                   "approximation": "the biceps heads and the triceps long head also cross the shoulder: their deep "
                                    "neighbour's ratio is read with the shoulder at rest"},
       "rest_path_m": {m: round(v, 4) for m, v in L0.items()}, "tendons_m": {m: round(v, 4) for m, v in TS.items()},
       "rest_elbow_deg": round(REST_ELB, 1),
       "contact": {"keys": [f"HGPT_CONTACT_ELBOW_{d:03d}" for d in CONTACT_KEYS], "from_deg": CONTACT_FROM,
                   "footprint_radius_m": FOOTPRINT_R, "smoothing_radius_m": SMOOTH_R, "zone_m": ZONE,
                   "bulge_rings": BULGE_RINGS,
                   "computed_on": "the length-keyed shapes at each key's elbow angle (shoulder at rest); stored as a "
                                  "correction", "per_key": {str(k): v for k, v in CONTACT_LOG.items()}},
       "poses": {}}
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 520; sc.render.resolution_y = 620
ARMN = ("biceps_brachii", "brachialis", "triceps", "brachioradialis")
TEN = [o for o in bpy.data.collections["HGPT_EXPERIMENT_TENDONS"].objects if o.name.split(".")[3] == SUF
       and o.name.split(".")[2].startswith(ARMN)]
for ob in sc.objects:
    if ob.type == "MESH" and ob not in OBJ.values() and ob not in TEN:
        ob.hide_render = True
# the R121 curl's 17 frames (0 -> 140 -> 0 in 17.5 deg steps) plus 90 and 130 (between contact keys)
for deg in tuple(float(x) for x in os.environ.get("MG11B_POSES", "0,17.5,35,52.5,70,87.5,90,105,122.5,130,140").split(",")):
    pose_elbow(max(deg, REST_ELB)); T = transforms()
    for m in MUSCLES:
        set_k(m, 1.0)
    set_contact(0.0)
    bpy.context.view_layer.update(); base = overlaps()
    per = {}
    for m in MUSCLES:
        k = (path_len(m, T) - TS[m]) / (L0[m] - TS[m]); set_k(m, k); per[m] = {"belly_k": round(k, 3)}
    bpy.context.view_layer.update(); length_only = overlaps()
    set_contact(deg); bpy.context.view_layer.update()
    for m in MUSCLES:
        per[m]["volume_ratio"] = round(volume(*evaluated(OBJ[m])) / V0[m], 4)
    keyed = overlaps()
    rep["poses"][str(deg)] = {"muscles": per, "overlaps_keyed": keyed, "overlaps_keyed_total": sum(keyed.values()),
                              "overlaps_length_keys_only_total": sum(length_only.values()),
                              "overlaps_length_keys_only": length_only,
                              "overlaps_without_keys_total": sum(base.values()), "overlaps_without_keys": base}
    print("ELBOW", deg, json.dumps({"k": {m: v["belly_k"] for m, v in per.items()},
                                    "vol": {m: v["volume_ratio"] for m, v in per.items()},
                                    "ov_keyed": keyed, "ov_base": base, "ov_length_only": length_only}), flush=True)
    if os.environ.get("MG11B_CLOSE") and deg >= 120:
        Tf = rot(EJC, ELB, SG * (deg - REST_ELB)); fc = EJC + (Tf @ WJC - EJC).normalized() * 0.07
        cd.ortho_scale = 0.22
        for view, dv in {"lateral": (lat, 0, 0), "front": (0, -1, 0), "below": (0, -0.3, -1)}.items():
            d = Vector(dv).normalized(); cam.location = fc + d * 2.5; cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = str(outdir / f"close_{S}_{int(deg * 10):04d}_{view}.png"); bpy.ops.render.render(write_still=True)
        cd.ortho_scale = 0.62
    if deg in (0, 90, 122.5, 140):
        centre = EJC + (GH - EJC) * 0.35
        for view, dv in {"lateral": (lat, 0, 0), "medial": (-lat, 0, 0)}.items():
            d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = str(outdir / f"mg11b_{S}_{int(deg * 10):04d}_{view}.png"); bpy.ops.render.render(write_still=True)
for m in MUSCLES:
    set_k(m, 1.0)
set_contact(0.0)
pose_elbow(REST_ELB)
for o in list(bpy.data.objects):
    if o.name == "C":
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
rep["output_blend"] = OUT.name; rep["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
rep["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected
(outdir / f"mg11b_{S}_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": rep["input_unchanged"]}), flush=True)
