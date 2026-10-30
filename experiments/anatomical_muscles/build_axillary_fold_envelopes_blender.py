"""EXPERIMENT (copy only): axillary-fold muscle ENVELOPE PROXIES - pectoralis major (clavicular and sternocostal
heads), latissimus dorsi and teres major - on top of the MG4 blend (MG1 arm envelopes + MG4 deltoid).

These are broad, flat muscles that run from the trunk through the two armpit folds onto the humerus, so each is built
as a fan sheet of NU fibres.  Fibre u runs from a point O(u) on an authored origin line, through a via point V(u) on its
armpit fold, to a point I(u) on an insertion line along the humerus (with each muscle's twist: the fibres that start
lowest insert highest, except the clavicular head, which inserts most distally).  Along a fibre:

  O -> V (on the trunk): the chord is cast radially from the thorax axis (mid-way between front and back skin at x=0)
      onto the TRUNK skin (arm skin excluded); the mid-surface lies the subcutaneous layer + half the thickness below it;
  V -> I (across the fold): the mid-surface follows the chord; where the chord leaves the skin (the closed rest armpit)
      it is snapped below the nearest skin.

V(u) is where the trunk skin meets the arm skin at the fold's height: rays from the thorax axis swept from straight
ahead (or behind) towards the side; the last trunk hit before the first arm hit.  The sheet is thickened along its own
normal (authored profiles), its outer surface clamped below the skin by nearest-point depth, and each fibre's belly
ends one station before it would enter an existing envelope (MG1 arm, MG4 deltoid, fans already built) or at the
authored tendon fraction; a tendon proxy runs on to the insertion anchor.  Teres major lies deep to the latissimus:
its outer surface is pushed below the latissimus.

There is no rib-cage surface in R41 (the ribs are guide segments), so the depth floor is the authored thickness; the
report counts vertices within 6 mm of a rib guide segment.  All numbers are authored rules recorded in the report - not
anatomy, not fitted.  Permanent IDs, neutral colour, no activation.  Bound to the anatomical chain: origin bone(s) on
the trunk part, blending to the humerus from the via point to the insertion.  Saves a NEW blend; the input is unchanged.

usage: python3.13 build_axillary_fold_envelopes_blender.py -- MG4.blend MG4_SHA256 anchors.json OUT_DIR [left|right]
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
OUT = outdir / f"HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG5_axilla_{SIDE}.blend"
if OUT.exists():
    raise ValueError("output blend must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
PROP = json.loads(anchors_p.read_text())["proposals"]

FAT, GAP, T_MIN, T_END = 0.004, 0.0012, 0.003, 0.004
NU, NT = 11, 28


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


def bone(n, end="head"):
    b = anat.data.bones[n]
    return anat.matrix_world @ (b.head_local if end == "head" else b.tail_local)


GH, EJC = LM(f"scapula_{SIDE}__GH"), LM(f"humerus_{SIDE}__EJC")
AX = (EJC - GH).normalized(); LH = (EJC - GH).length
lat = 1.0 if GH.x > 0 else -1.0
SC, AC, AI = LM(f"clavicle_{SIDE}__SC"), LM(f"clavicle_{SIDE}__AC"), LM(f"scapula_{SIDE}__AI")
ST0, ST1 = bone("anat_sternum"), bone("anat_sternum", "tail")


def X(x, y, z):                                             # authored for the left side (+x lateral); mirrored
    return Vector((lat * x, y, z))


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


# ---- skin: whole body, and the trunk only (no arm / hand / shoulder-cap skin, either side)
VW = [body.matrix_world @ v.co for v in body.data.vertices]
TRIS = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in body.data.polygons for k in range(1, len(p.vertices) - 1)]
BVH_BODY = BVHTree.FromPolygons(VW, TRIS, all_triangles=True)
GN = [g.name for g in body.vertex_groups]
ARMG = {i for i, g in enumerate(GN) if any(k in g for k in ("upperarm", "forearm", "shoulder_cap", "hand", "thumb", "index",
                                                            "middle", "ring", "pinky", "metacarpal"))}
ARMV = [sum(g.weight for g in v.groups if g.group in ARMG) > 0.5 for v in body.data.vertices]
ARM_TRI = {i for i, t in enumerate(TRIS) if sum(ARMV[j] for j in t) >= 2}
TRUNK_TRIS = [t for i, t in enumerate(TRIS) if i not in ARM_TRI]
BVH_TRUNK = BVHTree.FromPolygons(VW, TRUNK_TRIS, all_triangles=True)
_YC = {}


def y_c(z):
    """thorax axis: mid-way between the front and back trunk skin at x = 0"""
    k = round(z, 3)
    if k not in _YC:
        f = BVH_TRUNK.ray_cast(Vector((0, 0.0, k)), Vector((0, -1, 0)), 0.5)
        b = BVH_TRUNK.ray_cast(Vector((0, 0.0, k)), Vector((0, 1, 0)), 0.5)
        _YC[k] = 0.5 * (f[0].y + b[0].y) if (f[0] is not None and b[0] is not None) else 0.0
    return _YC[k]


def radial_hit(p):
    c = Vector((0.0, y_c(p.z), p.z)); d = Vector((p.x, p.y - c.y, 0.0))
    if d.length < 1e-6:
        return None
    d.normalize()
    h = BVH_TRUNK.ray_cast(c, d, 0.6)
    return (h[0], h[1], (h[0] - c).length, d) if h[0] is not None else None


def depth(p):
    """signed depth below the skin (m): > 0 inside"""
    loc, nrm, _i, dist = BVH_BODY.find_nearest(p)
    return (-dist if (p - loc).dot(nrm) > 0 else dist), loc, nrm


SWEEP = 70                                                  # deg from straight ahead / behind towards the side


def junction(z, back):
    """where the trunk skin meets the arm skin at height z, on the front (pectoralis) or back (latissimus) fold; below
    the armpit apex (no arm hit within the sweep) the trunk's front- / back-lateral corner at SWEEP deg"""
    c = Vector((0.0, y_c(z), z)); prev = None
    for k in range(0, SWEEP + 1, 2):
        a = math.radians(k)
        d = Vector((lat * math.sin(a), (1.0 if back else -1.0) * math.cos(a), 0.0))
        h = BVH_BODY.ray_cast(c, d, 0.6)
        if h[0] is None:
            continue
        if h[2] in ARM_TRI:
            return (prev[0], prev[1]) if prev else (h[0], h[1]), k
        prev = h
    return (prev[0], prev[1]), SWEEP


def s_on_humerus(p):
    return (p - GH).dot(AX) / LH


def anchor(mid, role):
    return Vector(next(a["world_rest_m"] for a in PROP[mid]["anchors"] if a["role"] == role))


def ins_line(mid, s_a, s_b):
    """the insertion anchor slid along the humeral axis to s_a .. s_b"""
    a = anchor(mid, "insertion"); s0 = s_on_humerus(a)
    return a + AX * ((s_a - s0) * LH), a + AX * ((s_b - s0) * LH)


def sternal(z, dx=0.015, dy=-0.013):
    t = (ST0.z - z) / (ST0.z - ST1.z)
    p = lerp(ST0, ST1, t); return Vector((lat * dx, p.y + dy, z))


def polyline(pts, u):
    """point at fraction u of arc length along a polyline"""
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    s = u * L[-1]
    for k in range(len(pts) - 1):
        if s <= L[k + 1] or k == len(pts) - 2:
            return lerp(pts[k], pts[k + 1], (s - L[k]) / max(L[k + 1] - L[k], 1e-9))


# ---- the four fans (authored for the left side; X() mirrors).  origin(u), insertion s-range (u=0 -> u=1), via height
#      range, belly thickness (trunk part, fold part), tendon fraction, deep-to list, origin bone(s)
LAT_ORIGIN = [X(0.015, 0.12, 1.395), X(0.022, 0.12, 1.25), X(0.06, 0.12, 1.12), X(0.10, 0.11, 1.075), X(0.135, 0.09, 1.085)]
AA_, TS_ = LM(f"scapula_{SIDE}__AA"), LM(f"scapula_{SIDE}__TS")
_SCN = (AA_ - TS_).cross(AI - TS_).normalized()               # scapular-plane normal
_TMF = (anchor(f"hgpt.muscle.teres_major.{SUF}", "insertion") - AI).normalized()   # teres fibre direction
_TMP = _TMF.cross(_SCN).normalized()                         # across the fibres, in the scapular plane
_TMC = AI + _TMF * 0.022                                     # the dorsal inferior angle, 22 mm up the fibre line
TM_ORIGIN = [_TMC - _TMP * 0.0175, _TMC + _TMP * 0.0175]
FANS = {
    "latissimus_dorsi": {
        "origin": lambda u: polyline(LAT_ORIGIN, u),
        "ins_s": (0.20, 0.10), "via_z": (1.415, 1.375), "back": True,
        "T": (0.006, 0.016), "tendon_t": 0.86, "deep_to": [], "separate_from": ["triceps_long"],
        "origin_bone": lambda p: "anat_hip_bone_" + SIDE if p.z < 1.09 else min(
            ("anat_t7", "anat_t8", "anat_t9", "anat_t10", "anat_t11", "anat_t12", "anat_l1", "anat_l2", "anat_l3", "anat_l4", "anat_l5"),
            key=lambda n: abs(bone(n).z - p.z)),
        "rule": "origin line: T7 spinous level 15 mm lateral -> T12 -> L3 70 mm lateral -> posterior iliac crest (the belly's "
                "medial edge; the thoracolumbar aponeurosis medial to it is not modelled); twist: upper fibres insert lowest"},
    "teres_major": {
        "origin": lambda u: lerp(TM_ORIGIN[0], TM_ORIGIN[1], u),
        "ins_s": (0.25, 0.15), "via_z": (1.385, 1.405), "back": True,
        "T": (0.020, 0.022), "tendon_t": 0.88, "deep_to": ["latissimus_dorsi"], "separate_from": ["triceps_long"],
        "origin_bone": lambda p: f"anat_scapula_{SIDE}",
        "rule": "origin: 35 mm across the dorsal inferior angle, perpendicular to the fibres in the scapular plane, centred 22 mm "
                "from AI along the fibre line (an origin along the lateral border ran parallel to the fibres and folded the "
                "sheet); deep to the latissimus"},
    "pectoralis_major_sternocostal": {
        "origin": lambda u: (sternal(lerp(1.495, 1.33, u / 0.78)) if u <= 0.78 else
                             lerp(sternal(1.33), X(0.075, -0.10, 1.315), (u - 0.78) / 0.22)),
        "ins_s": (0.24, 0.12), "via_z": (1.445, 1.395), "back": False,
        "T": (0.010, 0.018), "tendon_t": 0.90, "deep_to": ["deltoid_anterior", "pectoralis_major_clavicular"],
        "origin_bone": lambda p: "anat_sternum",
        "rule": "origin: sternum 15 mm lateral / 13 mm anterior of the guide line, z 1.495 -> 1.33, then along the 6th costal "
                "cartilage to 75 mm lateral; twist: the lowest fibres insert highest"},
    "pectoralis_major_clavicular": {
        "origin": lambda u: lerp(SC, AC, 0.08 + 0.40 * u) + Vector((0, -0.008, 0)),
        "ins_s": (0.28, 0.18), "via_z": (1.455, 1.48), "back": False,
        "T": (0.010, 0.014), "tendon_t": 0.90, "deep_to": ["deltoid_anterior"],
        "origin_bone": lambda p: f"anat_clavicle_{SIDE}",
        "rule": "origin: anterior clavicle 8 % -> 48 % SC -> AC, 8 mm anterior; inserts most distally (anterior lamina); the "
                "medial fibres reach the fold lowest, so the fibres run inferolaterally, oblique to the origin line"},
}
ORDER = ["latissimus_dorsi", "teres_major", "pectoralis_major_clavicular", "pectoralis_major_sternocostal"]

# ---- existing envelopes on this side (MG1 arm + MG4 deltoid)
C_MUS, C_TEN = bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"], bpy.data.collections["HGPT_EXPERIMENT_TENDONS"]
EXIST = [o for o in C_MUS.objects if o.name.endswith(f".{SUF}")]
dg = bpy.context.evaluated_depsgraph_get()
EX_BVH = {o.name: BVHTree.FromObject(o, dg) for o in EXIST}


RAY = Vector((0.0123, 0.0217, 1.0)).normalized()


def inside_tree(p, tr):
    """ray parity: an odd number of crossings along a fixed ray means inside (independent of face orientation)"""
    n, q = 0, p.copy()
    for _ in range(64):
        h = tr.ray_cast(q, RAY, 2.0)
        if h[0] is None:
            break
        n += 1; q = h[0] + RAY * 1e-5
    return n % 2 == 1


def inside(p, names=None):
    for nm, t in EX_BVH.items():
        if names is not None and nm not in names:
            continue
        if inside_tree(p, t):
            return nm
    return None


def thickness(spec, t, tv, u, t_end):
    t0, t1 = spec["T"]
    base = t0 + (t1 - t0) * smooth((t / max(tv, 1e-3) - 0.4) / 0.8)   # thin on the trunk, full in the fold
    ends = smooth(t / 0.08) * smooth((t_end - t) / 0.12)            # tapers to the origin and to the tendon
    edge = 0.65 + 0.35 * math.sin(math.pi * u)                      # thinner borders
    return max(T_END, T_END + (base - T_END) * ends * edge)


def fibre(spec, u, mid):
    """origin, via (on the fold), insertion and the via's arc fraction for fibre u"""
    O = spec["origin"](u)
    zv = lerp(spec["via_z"][0], spec["via_z"][1], u)
    (jp, jn), _k = junction(zv, spec["back"])
    V = jp - jn * (FAT + 0.006)
    c = Vector((0.0, y_c(V.z), V.z))
    for _ in range(40):                                     # clear of the arm / deltoid envelopes, towards the trunk
        if inside(V) is None:
            break
        V = V + (c - V).normalized() * 0.002
    ia, ib = ins_line(mid, *spec["ins_s"]); I = lerp(ia, ib, u)
    l1, l2 = (V - O).length, (I - V).length
    return O, V, I, l1 / (l1 + l2)


def axis_dir(p):
    """horizontal unit vector from p towards the thorax axis (inward)"""
    d = Vector((-p.x, y_c(p.z) - p.y, 0.0))
    return d.normalized() if d.length > 1e-9 else Vector((0, 0, 0))


def mid_point(O, V, I, tv, t, T, ceil=None):
    """mid-surface point at fraction t along the fibre.  ceil: superficial envelopes this muscle lies under - on the
    trunk the radial cast stops at the first of them (less the gap) instead of the skin; across the fold the point
    moves towards the thorax axis until it is clear of them"""
    if t <= tv:
        b = lerp(O, V, t / tv)
        h = radial_hit(b)
        if h is None:
            return b, "chord"
        hp, hn, r_skin, d = h
        c = Vector((0.0, y_c(b.z), b.z)); r_top = r_skin - FAT; under = False
        for tr in (ceil or []):
            hh = tr.ray_cast(c, d, r_skin)
            if hh[0] is not None and (hh[0] - c).length - GAP < r_top:
                r_top = (hh[0] - c).length - GAP; under = True
        if under:
            return c + d * (r_top - T / 2), "under"
        return hp - hn * (FAT + T / 2), "trunk"
    b = lerp(V, I, (t - tv) / (1 - tv))
    dep, loc, nrm = depth(b)
    md = "fold"
    if dep < FAT + T / 2:                                     # outside / too near the skin (the closed rest armpit)
        b = loc - nrm * (FAT + T / 2); md = "snapped"
    for _ in range(40):
        if not any(inside_tree(b + axis_dir(b) * 0.0, tr) for tr in (ceil or [])):
            break
        b = b + axis_dir(b) * 0.002; md = "under"
    return b, md


def grid(spec, mid, t_ends, deep_bvh=None):
    """outer / inner grids (NU x NT) and per-fibre bookkeeping.  deep_bvh: envelopes this muscle lies under (outer pushed
    inward along the sheet normal)"""
    Mg, Tg, MD, modes, F = [], [], [], {"trunk": 0, "under": 0, "fold": 0, "snapped": 0, "chord": 0}, []
    for i in range(NU):
        u = i / (NU - 1); O, V, I, tv = fibre(spec, u, mid); F.append((O, V, I, tv))
        row, trow, mrow = [], [], []
        for k in range(NT):
            t = t_ends[i] * k / (NT - 1)
            T = thickness(spec, t, tv, u, t_ends[i])
            p, md = mid_point(O, V, I, tv, t, T, deep_bvh); modes[md] += 1
            row.append(p); trow.append(T); mrow.append(md)
        Mg.append(row); Tg.append(trow); MD.append(mrow)
    # Laplacian smoothing of the mid-surface (the radial cast and the snapping are point-wise)
    for _ in range(3):
        new = [[Mg[i][k].copy() for k in range(NT)] for i in range(NU)]
        for i in range(NU):
            for k in range(1, NT - 1):
                nb = [Mg[i][k - 1], Mg[i][k + 1]] + ([Mg[i - 1][k]] if i > 0 else []) + ([Mg[i + 1][k]] if i < NU - 1 else [])
                new[i][k] = Mg[i][k] * 0.5 + sum(nb, Vector()) * (0.5 / len(nb))
        Mg = new
    # sheet normal: on the trunk (and under a superficial muscle) the skin normal - the sheet lies parallel to the skin,
    # and the grid's own cross product degenerates where fibres start along their origin line (the clavicular head);
    # across the fold the grid normal, kept continuous along the fibre
    Ng = [[None] * NT for _ in range(NU)]
    for i in range(NU):
        for k in range(NT):
            if MD[i][k] in ("trunk", "under") or k == 0:
                _d, _loc, n = depth(Mg[i][k]); n = n.normalized()
            else:
                dt = Mg[i][min(k + 1, NT - 1)] - Mg[i][max(k - 1, 0)]
                du = Mg[min(i + 1, NU - 1)][k] - Mg[max(i - 1, 0)][k]
                n = dt.cross(du)
                n = n.normalized() if n.length > 1e-12 else Ng[i][k - 1]
                if n.dot(Ng[i][k - 1]) < 0:
                    n = -n
                n = (n + Ng[i][k - 1]).normalized() if (n + Ng[i][k - 1]).length > 1e-9 else n
            Ng[i][k] = n
    Og, Ig, squeezed, pushed = [], [], 0, 0
    SQ = [[False] * NT for _ in range(NU)]
    for i in range(NU):
        orow, irow = [], []
        for k in range(NT):
            m, n, T = Mg[i][k], Ng[i][k], Tg[i][k]
            o = m + n * (T / 2); inn = m - n * (T / 2)
            for _ in range(8):                                # outer: at least the layer below the skin (true depth)
                dep, _l, _n = depth(o)
                if dep >= FAT - 1e-4:
                    break
                o = o - n * (FAT - dep + 0.0005)
            if deep_bvh is not None:                          # deep muscles: below the superficial one(s)
                moved = False
                for _ in range(60):
                    if not any(inside_tree(o, tr) for tr in deep_bvh):
                        break
                    o = o + axis_dir(o) * 0.001; moved = True
                if moved:
                    o = o + axis_dir(o) * GAP; pushed += 1
            if (o - inn).dot(n) < T_MIN:
                inn = o - n * T_MIN; squeezed += 1; SQ[i][k] = True
            orow.append(o); irow.append(inn)
        Og.append(orow); Ig.append(irow)
    for g in (Og, Ig):                                        # light smoothing of each surface, then the skin clamp
        for _ in range(2):
            new = [[g[i][k].copy() for k in range(NT)] for i in range(NU)]
            for i in range(1, NU - 1):
                for k in range(1, NT - 1):
                    new[i][k] = g[i][k] * 0.5 + (g[i - 1][k] + g[i + 1][k] + g[i][k - 1] + g[i][k + 1]) * 0.125
            for i in range(NU):
                g[i][:] = new[i]
    for i in range(NU):
        for k in range(NT):
            dep, loc, nrm = depth(Og[i][k])
            if dep < FAT:
                Og[i][k] = loc - nrm * FAT
            if (Og[i][k] - Ig[i][k]).dot(Ng[i][k]) < T_MIN:
                Ig[i][k] = Og[i][k] - Ng[i][k] * T_MIN
    return Og, Ig, Mg, F, modes, squeezed, pushed, SQ, Ng


def faces_of():
    o = lambda i, k: i * NT + k
    n = lambda i, k: NU * NT + i * NT + k
    faces = []
    for i in range(NU - 1):
        for k in range(NT - 1):
            faces.append((o(i, k), o(i + 1, k), o(i + 1, k + 1), o(i, k + 1)))
            faces.append((n(i, k), n(i, k + 1), n(i + 1, k + 1), n(i + 1, k)))
    for k in range(NT - 1):
        faces.append((o(0, k), o(0, k + 1), n(0, k + 1), n(0, k)))
        faces.append((o(NU - 1, k), n(NU - 1, k), n(NU - 1, k + 1), o(NU - 1, k + 1)))
    for i in range(NU - 1):
        faces.append((o(i, 0), n(i, 0), n(i + 1, 0), o(i + 1, 0)))
        faces.append((o(i, NT - 1), o(i + 1, NT - 1), n(i + 1, NT - 1), n(i, NT - 1)))
    return faces


FACES = faces_of()


def flat(Og, Ig):
    return [Og[i][k] for i in range(NU) for k in range(NT)] + [Ig[i][k] for i in range(NU) for k in range(NT)]


def oriented_faces(verts):
    """FACES, reversed if their signed volume is negative (as solid() stores them)"""
    vol = 0.0
    for f in FACES:
        vs = [verts[j] for j in f]
        for q in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[q].cross(vs[q + 1])) / 6.0
    return [f[::-1] for f in FACES] if vol < 0 else list(FACES)


def tri_bvh(verts):
    """the solid triangulated by Blender itself (a temporary mesh's loop triangles, faces oriented as solid() stores
    them), so the build-time overlap tests agree with the final BVHTree.FromObject check; returns the tree and each
    triangle's face index"""
    me = bpy.data.meshes.new("_hgpt_tmp"); me.from_pydata([tuple(v) for v in verts], [], oriented_faces(verts))
    me.calc_loop_triangles()
    tris = [tuple(t.vertices) for t in me.loop_triangles]; owner = [t.polygon_index for t in me.loop_triangles]
    bpy.data.meshes.remove(me)
    return BVHTree.FromPolygons(verts, tris, all_triangles=True), owner


def separate(Og, Ig, Ng, trees, iters=60, step=0.001):
    """deep muscle: move the grid vertices of faces that still cross the superficial envelope(s) towards the thorax
    axis (whole thickness) until no face crosses; returns the remaining crossings"""
    for it in range(iters):
        verts = flat(Og, Ig)
        mine, owner = tri_bvh(verts)
        bad = set()
        for tr in trees:
            for a, _b in mine.overlap(tr):
                bad.update(FACES[owner[a]])
        if not bad:
            return 0
        for vi in bad:                                        # both surfaces, towards the thorax axis
            j = vi % (NU * NT); i, k = divmod(j, NT)
            Og[i][k] = Og[i][k] + axis_dir(Og[i][k]) * step; Ig[i][k] = Ig[i][k] + axis_dir(Ig[i][k]) * step
    verts = flat(Og, Ig); mine, _owner = tri_bvh(verts)
    return sum(len(mine.overlap(tr)) for tr in trees)


def self_pairs(verts):
    """face pairs of the solid that cross each other and share no vertex"""
    tr, owner = tri_bvh(verts)
    out = set()
    for a, b in tr.overlap(tr):
        fa, fb = owner[a], owner[b]
        if fa < fb and not (set(FACES[fa]) & set(FACES[fb])):
            out.add((fa, fb))
    return out


def unfold(Og, Ig, Ng, iters=25):
    """where the solid crosses itself (an offset sheet thicker than its bend radius): thin it towards the minimum and
    smooth the outer surface locally; returns the face pairs left"""
    for _ in range(iters):
        bad = self_pairs(flat(Og, Ig))
        if not bad:
            return 0
        vs = set()
        for fa, fb in bad:
            vs.update(FACES[fa]); vs.update(FACES[fb])
        cells = {divmod(v % (NU * NT), NT) for v in vs}
        for i, k in cells:
            Ig[i][k] = Ig[i][k].lerp(Og[i][k] - Ng[i][k] * T_MIN, 0.5)
            nb = [Og[a][b] for a, b in ((i - 1, k), (i + 1, k), (i, k - 1), (i, k + 1)) if 0 <= a < NU and 0 <= b < NT]
            Og[i][k] = Og[i][k] * 0.5 + sum(nb, Vector()) * (0.5 / len(nb))
            nb = [Ig[a][b] for a, b in ((i - 1, k), (i + 1, k), (i, k - 1), (i, k + 1)) if 0 <= a < NU and 0 <= b < NT]
            Ig[i][k] = Ig[i][k] * 0.5 + sum(nb, Vector()) * (0.5 / len(nb))
    return len(self_pairs(flat(Og, Ig)))


def solid(name, Og, Ig):
    verts = flat(Og, Ig); faces = oriented_faces(verts)
    vol = 0.0
    for f in faces:
        vs = [verts[j] for j in f]
        for q in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[q].cross(vs[q + 1])) / 6.0
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, abs(vol)


def tube(name, a, b, r=0.004, n=8):
    d = (b - a); z = d.normalized(); x = z.orthogonal().normalized(); y = z.cross(x)
    verts = [a + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    verts += [b + (x * math.cos(2 * math.pi * k / n) + y * math.sin(2 * math.pi * k / n)) * r for k in range(n)]
    faces = [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)] + [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.validate(); me.update()
    return me, d.length


mat_m = bpy.data.materials.get("HGPT_EXPERIMENT_MUSCLE_NEUTRAL"); mat_t = bpy.data.materials.get("HGPT_EXPERIMENT_TENDON_NEUTRAL")
HUM = f"anat_humerus_{SIDE}"
DEFORM_ON = []
for bn in ["anat_sternum", f"anat_hip_bone_{SIDE}"] + [f"anat_t{k}" for k in range(7, 13)] + [f"anat_l{k}" for k in range(1, 6)]:
    if not anat.data.bones[bn].use_deform:                  # copy-only, as MG1 / MG4 did for the limb bones
        anat.data.bones[bn].use_deform = True; DEFORM_ON.append(bn)


def bind(ob, weights):
    for v in ob.data.vertices:
        for bn, w in weights(v.index).items():
            g = ob.vertex_groups.get(bn) or ob.vertex_groups.new(name=bn)
            g.add([v.index], w, "REPLACE")
    mod = ob.modifiers.new("HGPT_ANATOMICAL_CHAIN", "ARMATURE"); mod.object = anat


REP = {"status": "ENVELOPE_PROXY_UNREVIEWED", "input": src.name, "input_sha256": expected, "side": SIDE,
       "frame": "fan sheets: origin line -> via point on the armpit fold -> insertion line on the humerus",
       "rules": {"subcutaneous_layer_m": FAT, "gap_m": GAP, "min_thickness_m": T_MIN, "end_thickness_m": T_END,
                 "fibres": NU, "stations": NT,
                 "fans": {k: {"insertion_s_u0_u1": v["ins_s"], "via_height_m_u0_u1": v["via_z"],
                              "thickness_trunk_fold_m": v["T"], "tendon_fraction": v["tendon_t"], "deep_to": v["deep_to"],
                              "separated_from": v["deep_to"] + v.get("separate_from", []),
                              "rule": v["rule"]} for k, v in FANS.items()}},
       "copy_only_changes": {"anatomical_master_use_deform_enabled": DEFORM_ON},
       "volume_source": "geometry-derived from this body (no reviewed literature volumes reachable)", "muscles": {}}
NEW = []
for m in ORDER:
    spec = FANS[m]; mid = f"hgpt.muscle.{m}.{SUF}"
    deep_names = {f"hgpt.muscle.{d}.{SUF}" for d in spec["deep_to"]}
    deep = [EX_BVH[nm] for nm in deep_names] or None
    others = [nm for nm in EX_BVH if nm not in deep_names]
    # pass 1: full length to the tendon fraction; each fibre's belly ends a station before it would enter another
    # envelope (MG1 arm, MG4 deltoid unless it lies under it, the fans already built) - the tendon runs on from there
    t_ends = [spec["tendon_t"]] * NU
    Og, Ig, Mg, F, modes, sq, pu, SQ, Ng = grid(spec, mid, t_ends, deep)
    stops = {}
    for i in range(NU):
        for k in range(1, NT):
            hit = inside(Og[i][k], others) or inside(Ig[i][k], others) or inside(Mg[i][k], others)
            if hit:
                t_ends[i] = spec["tendon_t"] * max(k - 1, 1) / (NT - 1)
                stops[i] = hit.split(".")[2]
                break
    step_t = spec["tendon_t"] / (NT - 1)                     # neighbouring fibres end within a station of each other
    for _ in range(NU):
        for i in range(NU):
            for j in (i - 1, i + 1):
                if 0 <= j < NU and t_ends[i] > t_ends[j] + step_t:
                    t_ends[i] = t_ends[j] + step_t
    sep = [EX_BVH[f"hgpt.muscle.{d}.{SUF}"] for d in spec["deep_to"] + spec.get("separate_from", [])]

    def finish(t_ends):
        Og, Ig, Mg, F, modes, sq, pu, SQ, Ng = grid(spec, mid, t_ends, deep)
        unfold(Og, Ig, Ng)
        left_cross = separate(Og, Ig, Ng, sep) if sep else 0
        clamped = 0
        for _round in range(10):                              # alternate: every vertex at least the layer below the
            n_cl = 0                                          # skin, then the separation again, until both hold
            for g in (Og, Ig):
                for i in range(NU):
                    for k in range(NT):
                        dep, loc, nrm = depth(g[i][k])
                        if dep < FAT - 1e-4:
                            g[i][k] = loc - nrm * (FAT + 0.0005); n_cl += 1
            clamped += n_cl
            if not (sep and n_cl):
                break
            left_cross = separate(Og, Ig, Ng, sep)
        selfp = unfold(Og, Ig, Ng, iters=10)
        bad = set()                                           # fibres that cannot hold all three: shortened and rebuilt
        for fa, fb in self_pairs(flat(Og, Ig)):              # (only crossings near the belly end shorten a fibre)
            for vi in FACES[fa] + FACES[fb]:
                i_, k_ = divmod(vi % (NU * NT), NT)
                if k_ >= NT - 6:
                    bad.add(i_)
        for i in range(NU):
            if any(depth(g[i][k])[0] < FAT - 1e-4 for g in (Og, Ig) for k in range(NT)):
                bad.add(i)
        if sep:
            mine, owner = tri_bvh(flat(Og, Ig))
            for tr in sep:
                for fa, _fb in mine.overlap(tr):
                    for vi in FACES[owner[fa]]:
                        bad.add((vi % (NU * NT)) // NT)
        return (Og, Ig, Mg, F, modes, sq, pu, Ng, left_cross, clamped, selfp), bad

    shortened = {}
    for _attempt in range(5):
        (Og, Ig, Mg, F, modes, sq, pu, Ng, left_cross, clamped, selfp), bad = finish(t_ends)
        if not bad:
            break
        for i in bad:
            t_ends[i] = max(t_ends[i] - spec["tendon_t"] / (NT - 1), F[i][3] * 0.6)
            shortened[i] = shortened.get(i, 0) + 1
    left_inside = {}
    for i in range(NU):
        for k in range(NT):
            for p in (Og[i][k], Ig[i][k]):
                hit = inside(p, others)
                if hit:
                    left_inside[hit.split(".")[2]] = left_inside.get(hit.split(".")[2], 0) + 1
    me, vol = solid(mid, Og, Ig); me.materials.append(mat_m)
    ob = bpy.data.objects.new(mid, me); C_MUS.objects.link(ob); NEW.append(ob)
    ob["hgpt_muscle_id"] = mid; ob["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"; ob["hgpt_activation_display"] = False
    # weights: origin bone on the trunk part, blending to the humerus from the via point to the insertion
    W = {}
    for gtag, g in (("o", Og), ("i", Ig)):
        for i in range(NU):
            tv = F[i][3]; ob_b = spec["origin_bone"](F[i][0])
            for k in range(NT):
                t = t_ends[i] * k / (NT - 1); h = smooth((t - tv) / max(1.0 - tv, 1e-3))
                W[len(W)] = {b_: w_ for b_, w_ in {ob_b: 1.0 - h, HUM: h}.items() if w_ > 1e-4}
    bind(ob, lambda vi: W[vi])
    end_mid = Mg[NU // 2][NT - 1]; ins = anchor(mid, "insertion")
    tm, tl = tube(f"{mid}.tendon_insertion", end_mid, ins); tm.materials.append(mat_t)
    to = bpy.data.objects.new(tm.name, tm); C_TEN.objects.link(to)
    to["hgpt_muscle_id"] = mid; to["hgpt_tendon_role"] = "insertion"; to["hgpt_status"] = "ENVELOPE_PROXY_UNREVIEWED"
    bind(to, lambda vi: {HUM: 1.0})
    REP["muscles"][mid] = {"belly_volume_cm3": round(vol * 1e6, 1), "belly_volume_m3": round(vol, 7),
                           "belly_end_t_per_fibre": [round(t, 3) for t in t_ends], "stopped_by": stops,
                           "via_fraction_per_fibre": [round(f[3], 3) for f in F],
                           "via_points": [[round(c, 4) for c in f[1]] for f in (F[0], F[NU // 2], F[-1])],
                           "station_modes": modes, "sections_squeezed_to_min_thickness": sq,
                           "points_left_inside_other_envelopes": left_inside,
                           "face_crossings_left_with_superficial": left_cross, "vertices_clamped_below_skin_at_end": clamped,
                           "fibres_shortened_stations": shortened, "fibres_still_failing": sorted(bad),
                           "self_crossing_face_pairs_left": selfp,
                           "outer_points_pushed_below_superficial": pu, "tendon_length_m": round(tl, 4)}
    print("MUSCLE", mid, json.dumps(REP["muscles"][mid]), flush=True)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    EX_BVH[mid] = BVHTree.FromObject(ob, dg)

# ------------------------------------------------------------------ checks
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
RIBS = [(bone(f"anat_rib_{k:02d}_{SIDE}"), bone(f"anat_rib_{k:02d}_{SIDE}", "tail")) for k in range(1, 13)]


def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length


chk = {}
for ob in NEW:
    P = [ob.matrix_world @ v.co for v in ob.data.vertices]
    outside = shallow = rib = 0; min_depth = 1.0
    for p in P:
        dep, _l, _n = depth(p)
        if dep < 0:
            outside += 1
        else:
            min_depth = min(min_depth, dep)
            if dep < FAT - 0.0015:
                shallow += 1
        if min(seg_dist(p, a, b) for a, b in RIBS) < 0.006:
            rib += 1
    tr = BVHTree.FromObject(ob, dg); polys = [set(p_.vertices) for p_ in ob.data.polygons]
    selfx = sum(1 for a, b in tr.overlap(tr) if a < b and not (polys[a] & polys[b]))
    chk[ob.name] = {"vertices": len(P), "outside_skin": outside, "shallower_than_layer": shallow,
                    "min_depth_below_skin_mm": round(min_depth * 1000, 2), "within_6mm_of_rib_guide": rib,
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
REP["checks"] = {"per_muscle": chk, "overlap_pairs_involving_mg5": pairs}
print("CHECKS", json.dumps(REP["checks"]), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), copy=True)
REP["output_blend"] = OUT.name; REP["output_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
REP["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected

# ------------------------------------------------------------------ renders (muscle only / skin only, same cameras)
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 560; sc.render.resolution_y = 640
skin = bpy.data.materials.new("REVIEW_SKIN"); skin.diffuse_color = (0.80, 0.68, 0.58, 1)
body.data.materials.clear(); body.data.materials.append(skin)
TEN = list(C_TEN.objects); MUSC = list(C_MUS.objects)
for ob in sc.objects:
    if ob.type == "MESH" and ob is not body and ob not in MUSC and ob not in TEN:
        ob.hide_render = True
centre = Vector((lat * 0.12, 0.0, 1.30))
files = {}
for tag, skin_on in (("muscle", False), ("skin", True)):
    body.hide_render = not skin_on
    for o in MUSC + TEN:
        o.hide_render = skin_on
    for view, dv in {"anterior": (0, -1, 0), "anterolateral": (lat * 0.7, -0.7, 0), "lateral": (lat, 0, 0),
                     "posterolateral": (lat * 0.7, 0.7, 0), "posterior": (0, 1, 0)}.items():
        d = Vector(dv).normalized(); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        f = outdir / f"mg5_{SIDE}_{tag}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files.setdefault(tag, []).append(f.name)
REP["renders"] = files
(outdir / f"mg5_{SIDE}_report.json").write_text(json.dumps(REP, indent=1))
print("DONE", json.dumps({"out": OUT.name, "input_unchanged": REP["input_unchanged"]}), flush=True)
