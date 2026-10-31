"""Read-only check (MG9a): bone-driven, volume-preserving POSITIONING of the shoulder envelope proxies through the
press - the replacement MG6a asked for (blended bindings collapsed the deltoid to 0.22 of its volume and stretched the
fans 15x at the lockout).

Every MG4 deltoid head and MG5 armpit-fold fan is a fibre sheet: F fibres x K stations, an outer and an inner surface
(MG4: 12 phi columns x 29 rings plus two ring centres; MG5: 11 fibres x 28 stations).  Per pose, ROTATION-BLENDED
POISSON DEFORMATION of the sheet's mid-surface:

  1. each fibre's ends move rigidly with their bones: the origin end with its origin bone (the dominant vertex group at
     the origin station: clavicle, scapula, sternum, a vertebra or the hip bone), the belly end with the humerus;
  2. every station gets a rotation: the origin bone's rotation slerped to the humerus's by the station's rest humerus
     weight (the binding MG4 / MG5 authored).  Blending ROTATIONS, not positions, is what removes the collapse;
  3. the mid-surface solves L x = R (L x_rest): the grid Laplacian's along-fibre and across-fibre parts keep their
     rotated rest differentials, the ends held.  As a fibre is pulled taut (its end-to-end chord longer than at rest)
     its along-fibre differentials fade out (to zero once the chord has grown by SLACK of the fibre), so a stretched
     fibre runs straight between its neighbours;
  4. obstacles act on the DEEP surface as soft position constraints, re-solved until it is clear (least squares):
     (a) the humeral head + rotator-cuff sphere about the posed GH (MG4's head radius + cuff reserve + gap),
     (b) the MG1 arm envelopes (rigid with the humerus), by the gap,
     each clearance never stricter than the node's own at rest, so the rest pose is admissible;
     (c) for the fans, the thorax: no deeper below the STATIC trunk skin (skin with no weight on a bone the press moves;
         the thorax does not move in the press) than the fibre's deepest rest station;
     (d) optional, off by default (MG9_LAYERS=1): MG5's layering, the outer surface of a deep sheet a gap below its
         superficial neighbour, solved first (teres major under the latissimus, the clavicular pectoral head under the
         anterior deltoid, the sternocostal under the clavicular).  It cleared the start pose's overlaps (40 -> 0) but
         distorted the deep sheets (self-crossings 34 -> 435 at the start; latissimus / teres at the rack 141 -> 160):
         where the nearest superficial face is its outer surface, the push throws points over the sheet;
  5. the deep surface keeps its rotated offset from the mid-surface and the outer surface takes the thickness change,
     1 / the fibre's stretch, so each fibre strip keeps its volume and a shortening muscle bulges outward (MG2 / MG3's
     rule).

Tried first, not kept (recorded in the pass doc): one taut string per fibre wrapped over the obstacles with the rest
offsets carried along it.  Neighbouring strings slid to the same route over the head sphere, and the deltoid's rest
fibres (meridians of its spherical frame, not shortest paths) sit so far off their strings that the carried offsets
turned the sheet inside out (volume 0.03 at the rack).

At rest the construction returns the rest mesh exactly (reported).  Measured per pose: volume / rest, fibre length /
rest, edge ratios, self-crossings, overlaps with each other and with the MG1 arm envelopes (bound to the humerus, as
built), the largest station jump between steps; renders as MG6a's.  The skin is not posed (R41's anatomical master does
not drive the body).  Nothing is saved.

usage: python3.13 muscle_fibre_sweep_press_blender.py -- MG.blend SHA256 OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, outdir = Path(args[0]), args[1], Path(args[2])
S = args[3] if len(args) > 3 else "left"
SUF = "L" if S == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
MW = anat.matrix_world.copy()

# ---- posing: MG6a's coupled girdle (re-implemented, as that script runs on import)
PLANE_DEG = 30.0
MODEL = {"upward_rotation": 0.33, "posterior_tilt": 0.12, "clavicle_elevation": 0.08, "clavicle_retraction": 0.12}


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


SC, AC, GH, EJC = LM(f"clavicle_{S}__SC"), LM(f"clavicle_{S}__AC"), LM(f"scapula_{S}__GH"), LM(f"humerus_{S}__EJC")
AA, TS, AI = LM(f"scapula_{S}__AA"), LM(f"scapula_{S}__TS"), LM(f"scapula_{S}__AI")
EL, EM = LM(f"humerus_{S}__epicondyle_lateral_skin"), LM(f"humerus_{S}__epicondyle_medial_skin")
WJC = LM(f"radius_{S}__WJC")
lat = 1.0 if GH.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
SCAP_N = (AA - TS).cross(AI - TS).normalized(); SPINE = (AA - TS).normalized(); ELB_AX = (EL - EM).normalized()


def rot_about(p, axis, deg):
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p)


def signed(axis, probe, want, pivot):
    return 1.0 if ((rot_about(pivot, axis, 5.0) @ probe) - probe).dot(want) > 0 else -1.0


SIGN = {"clavicle_elevation": signed(ANT, AC, UP, SC), "clavicle_retraction": signed(UP, AC, -ANT, SC),
        "upward_rotation": signed(SCAP_N, AI, LAT, AC), "posterior_tilt": signed(SPINE, AI, ANT, AC),
        "elbow_flexion": signed(ELB_AX, WJC, ANT, EJC)}
CHAIN = [f"anat_clavicle_{S}", f"anat_scapula_{S}", f"anat_humerus_{S}", f"anat_ulna_{S}", f"anat_radius_{S}"]
REST_HT = math.degrees(math.acos((EJC - GH).normalized().dot(-UP)))
REST_ELB = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, (GH - EJC).normalized().dot((WJC - EJC).normalized())))))


def pose_T(ht_deg, elbow_deg):
    e = max(0.0, ht_deg - REST_HT); g = {k: v * e for k, v in MODEL.items()}
    elev, retr = g["clavicle_elevation"], g["clavicle_retraction"]
    Tc = rot_about(SC, UP, SIGN["clavicle_retraction"] * retr) @ rot_about(SC, ANT, SIGN["clavicle_elevation"] * elev)
    ac = Tc @ AC; R = Tc.to_3x3()
    ts = rot_about(ac, R @ SCAP_N, SIGN["upward_rotation"] * (g["upward_rotation"] - elev)) @ Tc
    ts = rot_about(ac, ts.to_3x3() @ SPINE, SIGN["posterior_tilt"] * g["posterior_tilt"]) @ ts
    ts = rot_about(ac, UP, -SIGN["clavicle_retraction"] * retr) @ ts
    gh, ejc = ts @ GH, ts @ EJC
    plane = (math.cos(math.radians(PLANE_DEG)) * LAT + math.sin(math.radians(PLANE_DEG)) * ANT).normalized()
    want = (math.cos(math.radians(ht_deg)) * -UP + math.sin(math.radians(ht_deg)) * plane).normalized()
    q = (ejc - gh).normalized().rotation_difference(want)
    Th = Matrix.Translation(gh) @ q.to_matrix().to_4x4() @ Matrix.Translation(-gh) @ ts
    Tf = Th @ rot_about(EJC, ELB_AX, SIGN["elbow_flexion"] * (elbow_deg - REST_ELB))
    return {CHAIN[0]: Tc, CHAIN[1]: ts, CHAIN[2]: Th, CHAIN[3]: Tf, CHAIN[4]: Tf}


def apply(T):
    for b in CHAIN:
        anat.pose.bones[b].matrix = MW.inverted() @ T[b] @ MW @ anat.data.bones[b].matrix_local
        bpy.context.view_layer.update()


# ---- the sheets
HEAD_R, CUFF, GAP = 0.024, 0.006, 0.0012                    # MG4's head radius proxy, cuff reserve and gap (m)
STEP_DEG = 3.0                                              # continuation step of humerothoracic elevation
SLACK = 0.15                                                # along-fibre differentials gone once the chord grows 15 %
S_CLAMP = (0.4, 2.5)                                        # thickness scale limits
OBS_ITERS, OBS_W, OBS_TOL = 12, 4.0, 0.0005                 # obstacle re-solves, constraint weight, tolerance (m)
_ENV = __import__("os").environ
THICK = _ENV.get("MG9_THICK", "grid")                       # thickness along the posed sheet normal (grid) or rotated
TAUT_DEG = float(_ENV.get("MG9_TAUT_DEG", "30"))            # along-fibre rest shape gone after this much joint rotation
ONE_DELTOID = _ENV.get("MG9_ONE_DELTOID", "1") == "1"       # the three deltoid heads solved as one 36-fibre sheet
DELTOID_MODE = _ENV.get("MG9_DELTOID", "slide")             # slide (below) or poisson (the fans' solve)
NORMAL_RULE = _ENV.get("MG9_NORMAL", "agree")              # thickness direction: grid normal where it agrees with the
                                                            # rotated rest normal (agree), or wherever defined (grid)
SRULE = _ENV.get("MG9_SRULE", "length")                     # fan thickness: 1 / fibre stretch (length) or rest / posed
                                                            # mid-surface area at each node (area: a fan that closes
                                                            # across its fibres thickens too)
EXTEND = _ENV.get("MG9_SLIDE_EXTEND", "0") == "1"           # a lengthening deltoid fibre extends straight to its origin
                                                            # (off: it keeps its rest length; the origin tendon spans the
                                                            # gap - the extension crumpled the posterior head above 120)
KIND = {"deltoid_anterior": "deltoid", "deltoid_middle": "deltoid", "deltoid_posterior": "deltoid",
        "latissimus_dorsi": "fan", "teres_major": "fan", "pectoralis_major_clavicular": "fan",
        "pectoralis_major_sternocostal": "fan"}
ARMS = ("biceps_brachii_long", "biceps_brachii_short", "brachialis", "triceps_long", "triceps_lateral", "triceps_medial")
C_MUS = bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"]; C_TEN = bpy.data.collections["HGPT_EXPERIMENT_TENDONS"]
OBJ = {m: C_MUS.objects[f"hgpt.muscle.{m}.{SUF}"] for m in KIND}
ARM_OBJ = [C_MUS.objects[f"hgpt.muscle.{m}.{SUF}"] for m in ARMS]
HUM = f"anat_humerus_{S}"
DELTOID = ["deltoid_anterior", "deltoid_middle", "deltoid_posterior"]   # in phi order: one continuous sheet
UNITS = ([("deltoid", DELTOID)] if ONE_DELTOID else [(m, [m]) for m in DELTOID]) + \
        [(m, [m]) for m in KIND if KIND[m] == "fan"]         # superficial sheets before the ones under them
UNDER = {"teres_major": "latissimus_dorsi", "pectoralis_major_clavicular": "deltoid_anterior",
         "pectoralis_major_sternocostal": "pectoralis_major_clavicular"} if _ENV.get("MG9_LAYERS", "0") == "1" else {}


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    P = np.array([e.matrix_world @ v.co for v in m.vertices], dtype=np.float64); e.to_mesh_clear(); return P


def layout(o, kind):
    """index grids (F x K, station 0 = origin end) of the outer and inner surface, and the extra vertices as
    (index, ring vertex indices whose centroid it is)"""
    n = len(o.data.vertices)
    if kind == "fan":
        NU, NT = 11, 28
        assert n == 2 * NU * NT, (o.name, n)
        io = np.array([[i * NT + k for k in range(NT)] for i in range(NU)])
        return io, io + NU * NT, []
    NP, R = 12, 29; m = 2 * NP
    assert n == R * m + 2, (o.name, n)
    io = np.array([[(R - 1 - k) * m + j for k in range(R)] for j in range(NP)])
    ii = np.array([[(R - 1 - k) * m + (m - 1 - j) for k in range(R)] for j in range(NP)])
    return io, ii, [(R * m, list(range(m))), (R * m + 1, list(range((R - 1) * m, R * m)))]


def arclen(X):
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))])


def mat_np(M):
    return np.array([list(r) for r in M], dtype=np.float64)


def xform(M, P):
    A = mat_np(M); return P @ A[:3, :3].T + A[:3, 3]


# static trunk skin: no weight on any bone the press moves (this side's arm chain, girdle and their helpers)
RS = "r" if lat > 0 else "l"                                 # the body rig's side at the same x
MOVING = {g.index for g in body.vertex_groups if g.name.endswith("_" + RS)
          and not g.name.startswith(("thigh", "shin", "foot", "toe", "hip_crease"))}
VW = [body.matrix_world @ v.co for v in body.data.vertices]
STATIC = [sum(g.weight for g in v.groups if g.group in MOVING) < 0.02 for v in body.data.vertices]
TRIS = [(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in body.data.polygons if all(STATIC[i] for i in p.vertices)
        for k in range(1, len(p.vertices) - 1)]
BVH_STATIC = BVHTree.FromPolygons(VW, TRIS, all_triangles=True)


def trunk_depth(p):
    loc, nrm, _i, dist = BVH_STATIC.find_nearest(Vector(p), 0.08)
    if loc is None:
        return None, None
    return (dist if (Vector(p) - loc).dot(nrm) < 0 else -dist), nrm


# rest data
REST = {m: evaluated(o) for m, o in OBJ.items()}
ARM_REST = [evaluated(o) for o in ARM_OBJ]
av, af = [], []
for o, P in zip(ARM_OBJ, ARM_REST):                          # MG1's faces are wound inward (negative signed volume):
    fs = [tuple(p.vertices) for p in o.data.polygons]        # oriented outward here, so the nearest face's normal
    sv = sum(np.dot(P[f[0]], np.cross(P[f[k]], P[f[k + 1]])) for f in fs for k in range(1, len(f) - 1))
    fs = [f[::-1] for f in fs] if sv < 0 else fs             # points out of the envelope
    base = len(av); av += [Vector(p) for p in P]; af += [tuple(base + i for i in f) for f in fs]
BVH_ARM = BVHTree.FromPolygons(av, af)                       # rest humerus space (MG1 is rigid with the humerus)
FACES = {m: [tuple(p.vertices) for p in o.data.polygons] for m, o in OBJ.items()}
EDGES = {m: np.array([e.vertices[:] for e in o.data.edges]) for m, o in OBJ.items()}


def dominant(o, vi):
    gs = [g.name for g in o.vertex_groups]
    return max(((g.weight, gs[g.group]) for g in o.data.vertices[vi].groups))[1]


def sheet_normals(G):
    """unit normal of a mid-surface grid (F x K x 3) and how well it is conditioned (|t x a| / |t||a|)"""
    ta = np.empty_like(G); ac = np.empty_like(G)
    ta[:, 1:-1] = G[:, 2:] - G[:, :-2]; ta[:, 0] = G[:, 1] - G[:, 0]; ta[:, -1] = G[:, -1] - G[:, -2]
    ac[1:-1] = G[2:] - G[:-2]; ac[0] = G[1] - G[0]; ac[-1] = G[-1] - G[-2]
    c = np.cross(ta, ac); cl = np.linalg.norm(c, axis=2)
    cond = cl / np.maximum(np.linalg.norm(ta, axis=2) * np.linalg.norm(ac, axis=2), 1e-12)
    return c / np.maximum(cl, 1e-12)[..., None], cond


GRID = {}                                                    # per muscle: its grids and vertex layout
for m, o in OBJ.items():
    io, ii, extra = layout(o, KIND[m]); P = REST[m]; K = io.shape[1]
    gi = o.vertex_groups[HUM].index if HUM in o.vertex_groups else -1
    wh = np.array([[sum(g_.weight for g_ in o.data.vertices[io[i][k]].groups if g_.group == gi) /
                    max(sum(g_.weight for g_ in o.data.vertices[io[i][k]].groups), 1e-9) for k in range(K)]
                   for i in range(io.shape[0])])
    GRID[m] = {"io": io, "ii": ii, "extra": extra, "O": P[io], "I": P[ii], "wh": wh,
               "ob": [dominant(o, io[i][0]) for i in range(io.shape[0])]}


def build_sheet(members):
    """the solver's data for one sheet: the members' grids side by side across the fibres"""
    O = np.concatenate([GRID[m]["O"] for m in members]); I = np.concatenate([GRID[m]["I"] for m in members])
    M = (O + I) / 2.0; F_, K = M.shape[:2]; N = F_ * K
    La, Lc = np.zeros((N, N)), np.zeros((N, N))              # grid Laplacian, along / across the fibres (node i * K + k)
    for i in range(F_):
        for k in range(K):
            n = i * K + k
            for kk in (k - 1, k + 1):
                if 0 <= kk < K:
                    La[n, n] += 1; La[n, i * K + kk] -= 1
            for j in (i - 1, i + 1):
                if 0 <= j < F_:
                    Lc[n, n] += 1; Lc[n, j * K + k] -= 1
    free = np.array([i * K + k for i in range(F_) for k in range(1, K - 1)])
    fixed = np.array([i * K + k for i in range(F_) for k in (0, K - 1)])
    Mf = M.reshape(N, 3)
    D = np.full(F_, np.nan)                                  # thorax: the deepest rest station of the deep surface
    if KIND[members[0]] == "fan":
        for i in range(F_):
            ds = [trunk_depth(I[i][k])[0] for k in range(K)]
            ds = [d for d in ds if d is not None and d > 0]
            if ds:
                D[i] = max(ds) + 0.001
    n0, _c0 = sheet_normals(M)
    sgn = np.sign(np.sum(n0 * (O - I), axis=2)); sgn[sgn == 0] = 1.0
    Ir = I.reshape(N, 3)                                     # clearances never stricter than at rest (rest admissible)
    gapn = np.full(N, GAP)
    for n in range(N):
        loc, nrm, _j, _d = BVH_ARM.find_nearest(Vector(Ir[n]), 0.04)
        if loc is not None:
            gapn[n] = min(GAP, (Vector(Ir[n]) - loc).dot(nrm))
    return {"members": members, "O": O, "I": I, "M": M, "F": F_, "K": K, "N": N,
            "wh": np.concatenate([GRID[m]["wh"] for m in members]), "ob": sum((GRID[m]["ob"] for m in members), []),
            "n0": n0 * sgn[..., None], "sgn": sgn, "D": D,
            "A": (La + Lc)[np.ix_(free, free)], "Afx": (La + Lc)[np.ix_(free, fixed)], "free": free, "fixed": fixed,
            "da": (La @ Mf)[free], "dc": (Lc @ Mf)[free],
            "Lf": np.array([arclen(M[i])[-1] for i in range(F_)]), "chord0": np.linalg.norm(M[:, -1] - M[:, 0], axis=1),
            "need": np.minimum(HEAD_R + CUFF + GAP, np.linalg.norm(Ir - np.array(GH), axis=1)), "gapn": gapn}


SH = {u: build_sheet(members) for u, members in UNITS}


def rotations(sh, Tm):
    """per-node rotation (N x 3 x 3): origin bone slerped to the humerus by the rest humerus weight"""
    qh = Tm[HUM].to_quaternion(); R = np.empty((sh["N"], 3, 3))
    for i in range(sh["F"]):
        qo = Tm.get(sh["ob"][i], Matrix.Identity(4)).to_quaternion()
        for k in range(sh["K"]):
            R[i * sh["K"] + k] = np.array(qo.slerp(qh, float(sh["wh"][i, k])).to_matrix())
    return R


def oriented_bvh(P, faces):
    sv = sum(np.dot(P[f[0]], np.cross(P[f[k]], P[f[k + 1]])) for f in faces for k in range(1, len(f) - 1))
    return BVHTree.FromPolygons([Vector(p) for p in P], [f[::-1] for f in faces] if sv < 0 else faces)


def penetration(tr, p):
    """how far p lies inside the (outward-oriented) mesh by its nearest face; <= 0 outside"""
    loc, nrm, _i, dist = tr.find_nearest(Vector(p), 0.05)
    if loc is None:
        return -1.0, None, None
    return (dist if (Vector(p) - loc).dot(nrm) < 0 else -dist), loc, nrm


def violations(sh, Tm, Mp, R, over=None):
    """per node: the correction needed (N x 3, zero where clear): the deep surface against the head + cuff sphere, the
    MG1 envelopes and the thorax; with `over` (the posed sheet this one lies under), the outer surface below it"""
    K = sh["K"]
    Ip = Mp + np.einsum("nab,nb->na", R, (sh["I"] - sh["M"]).reshape(-1, 3))
    gh = np.array(Tm[f"anat_scapula_{S}"] @ GH); H = mat_np(Tm[HUM]); Hi = np.linalg.inv(H)
    push = np.zeros_like(Ip)
    d = Ip - gh; r = np.linalg.norm(d, axis=1); need = sh["need"]
    msk = r < need - OBS_TOL
    push[msk] += d[msk] / r[msk][:, None] * (need[msk] - r[msk])[:, None]
    for n in range(sh["N"]):
        q = Vector(Hi[:3, :3] @ Ip[n] + Hi[:3, 3])
        loc, nrm, _j, _d = BVH_ARM.find_nearest(q, 0.04)
        if loc is not None:
            sd = (q - loc).dot(nrm)
            if sd < sh["gapn"][n] - OBS_TOL:
                push[n] += H[:3, :3] @ np.array(nrm) * (sh["gapn"][n] - sd)
        i = n // K
        if not np.isnan(sh["D"][i]):
            dep, n_ = trunk_depth(Ip[n])
            if dep is not None and dep > sh["D"][i] + OBS_TOL:
                push[n] += np.array(n_) * (dep - sh["D"][i])
    if over is not None:                                     # under a superficial sheet: the outer surface stays a gap
        Op = Mp + np.einsum("nab,nb->na", R, (sh["O"] - sh["M"]).reshape(-1, 3))   # below it (never stricter than
        for n in range(sh["N"]):                             # at rest)
            pen, loc, nrm = penetration(over, Op[n])
            allowed = max(sh["pen0"][n], -GAP)               # a gap clear of it, or no deeper than at rest
            if loc is not None and pen > allowed + OBS_TOL:
                push[n] += np.array(nrm) * (pen - allowed)   # out through its nearest face
    return push


def node_area(G):
    """mid-surface area carried by each grid node (F x K): each quad's area shared among its four corners"""
    a = 0.5 * np.linalg.norm(np.cross(G[1:, 1:] - G[:-1, :-1], G[:-1, 1:] - G[1:, :-1]), axis=2)
    A = np.zeros(G.shape[:2])
    for di in (0, 1):
        for dk in (0, 1):
            A[di:di + a.shape[0], dk:dk + a.shape[1]] += a / 4.0
    return A


def solve(sh, Tm, over=None):
    """posed outer / inner / mid grids of a sheet under the pose transforms Tm"""
    F_, K = sh["F"], sh["K"]
    R = rotations(sh, Tm); Rf = R[sh["free"]]
    ends = np.empty((sh["N"], 3))
    for i in range(F_):
        ends[i * K] = np.array(Tm.get(sh["ob"][i], Matrix.Identity(4)) @ Vector(sh["M"][i, 0]))
        ends[i * K + K - 1] = xform(Tm[HUM], sh["M"][i, -1][None])[0]
    xfix = ends[sh["fixed"]]
    chord = np.linalg.norm(ends[np.arange(F_) * K + K - 1] - ends[np.arange(F_) * K], axis=1)
    g = np.clip(1.0 - np.maximum(chord - sh["chord0"], 0.0) / (SLACK * sh["Lf"]), 0.0, 1.0)
    if TAUT_DEG > 0:                                         # active muscles pull taut as the joint turns
        qh = Tm[HUM].to_quaternion()
        for i in range(F_):
            ang = math.degrees(Tm.get(sh["ob"][i], Matrix.Identity(4)).to_quaternion().rotation_difference(qh).angle)
            x = min(1.0, ang / TAUT_DEG); g[i] = min(g[i], 1.0 - x * x * (3 - 2 * x))
    gn = np.repeat(g, K - 2)
    rhs = (gn[:, None] * np.einsum("nab,nb->na", Rf, sh["da"]) + np.einsum("nab,nb->na", Rf, sh["dc"])
           - sh["Afx"] @ xfix)
    A = sh["A"]; AtA = A.T @ A; Atb = A.T @ rhs
    W = np.zeros(len(sh["free"])); T = np.zeros((len(sh["free"]), 3))
    pos = {int(n): j for j, n in enumerate(sh["free"])}
    x = np.linalg.solve(A, rhs); n_con = 0
    for _ in range(OBS_ITERS):
        Mp = np.empty((sh["N"], 3)); Mp[sh["free"]] = x; Mp[sh["fixed"]] = xfix
        push = violations(sh, Tm, Mp, R, over)
        hit = [pos[n] for n in np.nonzero(np.linalg.norm(push, axis=1) > OBS_TOL)[0] if n in pos]
        if not hit:
            break
        for j in hit:
            W[j] = OBS_W ** 2; T[j] = x[j] + push[sh["free"][j]]
        x = np.linalg.solve(AtA + np.diag(W), Atb + W[:, None] * T); n_con = int((W > 0).sum())
    Mp = np.empty((sh["N"], 3)); Mp[sh["free"]] = x; Mp[sh["fixed"]] = xfix
    left = int((np.linalg.norm(violations(sh, Tm, Mp, R, over), axis=1) > 0.002).sum())
    M1 = Mp.reshape(F_, K, 3); R4 = R.reshape(F_, K, 3, 3)
    rot = lambda V: np.einsum("fkab,fkb->fka", R4, V)
    lam = np.array([arclen(M1[i])[-1] for i in range(F_)]) / sh["Lf"]
    s = np.clip(1.0 / lam, *S_CLAMP)
    if SRULE == "area" and F_ > 1:
        s = np.clip(node_area(sh["M"]) / np.maximum(node_area(M1), 1e-12), *S_CLAMP)
        for _ in range(2):                                   # light smoothing over the grid
            sp = np.pad(s, 1, mode="edge"); s = 0.5 * s + 0.125 * (sp[:-2, 1:-1] + sp[2:, 1:-1] + sp[1:-1, :-2] + sp[1:-1, 2:])
    if THICK == "rot":
        I1 = M1 + rot(sh["I"] - sh["M"])
        O1 = I1 + (s[..., None] if s.ndim == 2 else s[:, None, None]) * rot(sh["O"] - sh["I"])
        return O1, I1, M1, g, s, n_con, left
    n0 = sh["n0"]; nr = rot(n0)                              # thickness along the POSED sheet normal; where the grid
    ng, cond = sheet_normals(M1); ng = ng * sh["sgn"][..., None]   # degenerates, the rotated rest normal
    wgt = np.clip((cond - 0.15) / 0.25, 0.0, 1.0); wgt = wgt * wgt * (3 - 2 * wgt)
    if NORMAL_RULE == "grid":                                # the sheet's own normal wherever it is defined; the
        ag = np.sign(np.sum(ng * nr, axis=2)); ag[ag == 0] = 1.0  # rotated rest normal only where the grid degenerates,
        nr = nr * ag[..., None]                              # turned to the sheet's side (a sheet that hinges more than
    else:                                                    # 90 deg about its origin line keeps its true side)
        wgt = np.where(np.sum(ng * nr, axis=2) > 0, wgt, 0.0)
    nn = wgt[..., None] * ng + (1 - wgt[..., None]) * nr; nn /= np.maximum(np.linalg.norm(nn, axis=2, keepdims=True), 1e-12)
    if _ENV.get("MG9_DIAG_NORMAL"):
        flip = np.sum(ng * nr, axis=2) <= 0
        print("NORMAL", sh["members"][0], "nodes", flip.size, "grid_normal_against_rotated", int(flip.sum()),
              "by_station", [int(x) for x in flip.sum(axis=0)], "degenerate(cond<0.15)", int((cond < 0.15).sum()), flush=True)
    di, do = sh["I"] - sh["M"], sh["O"] - sh["I"]
    dn, tn = np.sum(di * n0, 2), np.sum(do * n0, 2)
    I1 = M1 + rot(di - dn[..., None] * n0) + dn[..., None] * nn
    O1 = I1 + rot(do - tn[..., None] * n0) + ((s if s.ndim == 2 else s[:, None]) * tn)[..., None] * nn
    return O1, I1, M1, g, s, n_con, left


def assemble(m, O1, I1):
    gr = GRID[m]; P = REST[m].copy()
    P[gr["io"]] = O1; P[gr["ii"]] = I1
    for vi, ring in gr["extra"]:
        P[vi] = P[ring].mean(axis=0)
    return P


def volume(P, F):
    v = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            v += np.dot(P[f[0]], np.cross(P[f[k]], P[f[k + 1]])) / 6.0
    return abs(float(v))


def _interp_arc(G, arc, a):
    """points of polyline rows G (K x 3) at arc positions a (from the row's start), linear"""
    return np.stack([np.interp(a, arc, G[:, c]) for c in range(3)], 1)


def solve_slide(sh, Tm):
    """the deltoid SLIDES along its own rest shape: in the humerus' frame the posed origin of each fibre moves down
    roughly along the rest fibre as the arm rises (theta from about 150 deg at rest to about 40 at the lockout), so the
    posed fibre is the rest fibre's portion from the insertion to the point nearest the posed origin (the whole rest
    fibre when the origin lies beyond its rest position - the origin tendon spans the gap; MG9_SLIDE_EXTEND=1 extends
    it straight instead), its stations at their rest arc fractions, the deep surface
    where the rest deep surface is, the outer surface swollen by a per-head factor that keeps the head's volume.  The
    posed deltoid is a subset of its rest shape carried by the humerus and thickened outward: it cannot fold, turn
    inside out, enter the MG1 envelopes (rigid with the humerus) or move one head onto another"""
    F_, K = sh["F"], sh["K"]; H = Tm[HUM]; Hi = mat_np(H.inverted()); Hn = mat_np(H)
    M, I, O = sh["M"][:, ::-1], sh["I"][:, ::-1], sh["O"][:, ::-1]   # rows from the insertion end
    M1 = np.empty_like(M); I1 = np.empty_like(M); O1 = np.empty_like(M); lam = np.empty(F_)
    for i in range(F_):
        og = np.array(Tm.get(sh["ob"][i], Matrix.Identity(4)) @ Vector(sh["M"][i, 0]))
        oh = Hi[:3, :3] @ og + Hi[:3, 3]                     # the posed origin in the humerus' rest frame
        arc = arclen(M[i]); A = arc[-1]
        best = (1e9, A, K - 2, 1.0)                          # nearest point of the rest fibre (arc, segment, param)
        for k in range(K - 1):
            a_, b_ = M[i, k], M[i, k + 1]; d = b_ - a_; L2 = float(d @ d)
            t = float(np.clip((oh - a_) @ d / max(L2, 1e-12), 0.0, 1.0))
            dist = float(np.linalg.norm(oh - (a_ + d * t)))
            if dist < best[0]:
                best = (dist, arc[k] + t * np.sqrt(L2), k, t)
        ds, a_star, kk, tt = best
        d_end = M[i, -1] - M[i, -2]                          # beyond the rest origin (the fibre lengthens): on straight
        beyond = kk == K - 2 and float((oh - M[i, -2]) @ d_end) > float(d_end @ d_end)   # to it from the rest origin;
        if not beyond or not EXTEND:                         # otherwise truncated where it is nearest (its sideways
            ds = 0.0                                         # offset is the origin tendon's)
        p_star = _interp_arc(M[i], arc, np.array([a_star]))[0]
        Lc = a_star + ds; lam[i] = Lc / A
        a_pos = arc / A * Lc
        on = a_pos <= a_star + 1e-12
        q = np.minimum(a_pos, a_star)
        M1[i], I1[i], O1[i] = _interp_arc(M[i], arc, q), _interp_arc(I[i], arc, q), _interp_arc(O[i], arc, q)
        if (~on).any() and ds > 1e-6:                        # the extension: the end section turned from the fibre's
            dirn = (oh - p_star) / ds                        # tangent onto the extension, the turn fading in over its
            tan = M[i, kk + 1] - M[i, kk]; tan = tan / max(np.linalg.norm(tan), 1e-12)   # first 10 mm
            x = min(1.0, ds / 0.010); w = x * x * (3 - 2 * x)
            Rq = np.array(Quaternion().slerp(Vector(tan).rotation_difference(Vector(dirn)), w).to_matrix())
            ip, op = _interp_arc(I[i], arc, np.array([a_star]))[0], _interp_arc(O[i], arc, np.array([a_star]))[0]
            base = p_star + (a_pos[~on] - a_star)[:, None] * dirn
            M1[i][~on] = base; I1[i][~on] = base + Rq @ (ip - p_star); O1[i][~on] = base + Rq @ (op - p_star)
    s = np.ones(F_)
    f0 = 0
    for m in sh["members"]:                                  # per head: the outer swelling that keeps its volume
        f1 = f0 + GRID[m]["io"].shape[0]; sl = slice(f0, f1); f0 = f1
        V0 = volume(REST[m], FACES[m])
        def vol_at(c):
            Ob = (I1[sl] + c * (O1[sl] - I1[sl]))[:, ::-1]; return volume(assemble(m, Ob, I1[sl][:, ::-1]), FACES[m])
        v1, v2 = vol_at(1.0), vol_at(1.5)
        s[sl] = np.clip(1.0 + 0.5 * (V0 - v1) / (v2 - v1), *S_CLAMP) if abs(v2 - v1) > 1e-12 else 1.0
    O1 = I1 + s[:, None, None] * (O1 - I1)
    to_w = lambda G: G @ Hn[:3, :3].T + Hn[:3, 3]
    return to_w(O1)[:, ::-1], to_w(I1)[:, ::-1], to_w(M1)[:, ::-1], np.ones(F_), s, 0, 0


IDENT = {b: Matrix.Identity(4) for b in CHAIN}
prevM_rest = {m: (GRID[m]["O"] + GRID[m]["I"]) / 2 for m in KIND}
rep = {"status": "READ_ONLY_CHECK", "input": src.name, "input_sha256": expected, "side": S,
       "method": "rotation-blended Poisson deformation of each sheet's mid-surface (bone-driven ends; rotations slerped "
                 "by the rest humerus weight; along-fibre differentials fade as the fibre is pulled taut; head + cuff "
                 "sphere, MG1 arm envelopes and static thorax as deep-surface constraints; volume-preserving thickness)",
       "girdle": {"model": MODEL, "plane_deg": PLANE_DEG, "rest_ht_deg": round(REST_HT, 1)},
       "rules": {"head_radius_m": HEAD_R, "cuff_m": CUFF, "gap_m": GAP, "step_deg": STEP_DEG, "slack": SLACK,
                 "thickness_scale_clamp": S_CLAMP, "obstacle_resolves_weight_tolerance": [OBS_ITERS, OBS_W, OBS_TOL],
                 "static_skin_triangles": len(TRIS), "thickness_direction": THICK, "taut_after_joint_rotation_deg": TAUT_DEG,
                 "deltoid_one_sheet": ONE_DELTOID, "layered_under": UNDER, "deltoid_mode": DELTOID_MODE,
                 "fan_thickness_rule": SRULE, "thickness_normal_rule": NORMAL_RULE},
       "origin_bones": {m: sorted(set(GRID[m]["ob"])) for m in KIND}, "poses": {}}

# ---- renders (as MG6a)
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.75
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 480; sc.render.resolution_y = 560
MUS = list(OBJ.values()) + ARM_OBJ
TEN = [o for o in C_TEN.objects if o.name.split(".")[3] == SUF and o.name.split(".")[2] in tuple(KIND) + ARMS]
for ob in sc.objects:
    if ob.type == "MESH" and ob not in MUS and ob not in TEN:
        ob.hide_render = True
for m, o in OBJ.items():                                     # in memory only: the swept positions replace the binding
    for md in o.modifiers:
        if md.type == "ARMATURE":
            md.show_viewport = md.show_render = False
MWI = {m: np.array(o.matrix_world.inverted()) for m, o in OBJ.items()}


def set_mesh(m, P):
    A = MWI[m]; L = P @ A[:3, :3].T + A[:3, 3]
    OBJ[m].data.vertices.foreach_set("co", L.astype(np.float32).ravel()); OBJ[m].data.update()


RECORD = {REST_HT: ("start", REST_ELB), 60.0: ("ht60", 45.0), 90.0: ("rack90", 90.0), 120.0: ("ht120", 45.0),
          160.0: ("lockout160", 0.0)}                       # "start" is MG6a's "rest": the humerus turned into the plane
hts = sorted(set([REST_HT] + [float(h) for h in np.arange(math.ceil(REST_HT / STEP_DEG) * STEP_DEG, 160.0, STEP_DEG)]
                 + list(RECORD)))
STEPS = [("rest", IDENT)] + [(ht, pose_T(ht, RECORD.get(ht, (None, 0.0))[1])) for ht in hts]
prevM = {m: (GRID[m]["O"] + GRID[m]["I"]) / 2 for m in KIND}; jump = {m: 0.0 for m in KIND}
for u, members in UNITS:                                     # rest penetration of each layered sheet's outer surface
    sh = SH[u]                                               # into its superficial neighbour (rest stays admissible)
    if u in UNDER:
        tr0 = oriented_bvh(REST[UNDER[u]], FACES[UNDER[u]])
        sh["pen0"] = np.array([penetration(tr0, p)[0] for p in sh["O"].reshape(-1, 3)])
for key, Tm in STEPS:
    posed = {}
    for u, members in UNITS:
        over = oriented_bvh(posed[UNDER[u]][0], FACES[UNDER[u]]) if u in UNDER else None
        if u.startswith("deltoid") and DELTOID_MODE == "slide":
            O1, I1, M1, g, s, n_con, left = solve_slide(SH[u], Tm)
        else:
            O1, I1, M1, g, s, n_con, left = solve(SH[u], Tm, over)
        f0 = 0
        for m in members:
            f1 = f0 + GRID[m]["io"].shape[0]; sl = slice(f0, f1); f0 = f1
            jump[m] = max(jump[m], float(np.linalg.norm(M1[sl] - prevM[m], axis=2).max())); prevM[m] = M1[sl]
            posed[m] = (assemble(m, O1[sl], I1[sl]), M1[sl], g[sl], s[sl], n_con, left)
    tag = "rest" if key == "rest" else RECORD.get(key, (None,))[0]
    if tag is None:
        continue
    if _ENV.get("MG9_DIAG_TWIST"):
        for m in KIND:
            if KIND[m] != "fan":
                continue
            M1 = posed[m][1]; M0 = prevM_rest[m]
            def tw(G):
                fd = G[:, -1].mean(0) - G[:, 0].mean(0); fd /= np.linalg.norm(fd)
                pr = lambda v: v - fd * np.dot(v, fd)
                a_, b_ = pr(G[-1, 0] - G[0, 0]), pr(G[-1, -1] - G[0, -1])
                c = np.dot(a_, b_) / max(np.linalg.norm(a_) * np.linalg.norm(b_), 1e-12)
                return round(math.degrees(math.acos(max(-1.0, min(1.0, c)))), 1)
            w = np.linalg.norm(M1[-1] - M1[0], axis=1) / np.maximum(np.linalg.norm(M0[-1] - M0[0], axis=1), 1e-9)
            print("TWIST", tag, m, "twist_deg", tw(M0), "->", tw(M1), "width_ratio_min_at_station", round(float(w.min()), 3),
                  int(w.argmin()), "of", len(w), flush=True)
    ht = REST_HT if key == "rest" else key
    apply(Tm)
    per, trees = {}, {}
    for m in KIND:
        P, M1, g, s, n_con, left = posed[m]; P0 = REST[m]; E = EDGES[m]
        L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
        r = L / np.maximum(L0, 1e-9)
        tr = BVHTree.FromPolygons([Vector(p) for p in P], FACES[m]); trees[m] = tr
        selfx = sum(1 for a, b in tr.overlap(tr) if a < b and not (set(FACES[m][a]) & set(FACES[m][b])))
        fl = np.array([arclen(M1[i])[-1] for i in range(M1.shape[0])]) / np.array([arclen(r_)[-1] for r_ in prevM_rest[m]])
        per_extra = {"sheet_obstacle_constrained_nodes": n_con, "sheet_nodes_still_over_2mm_into_an_obstacle": left}
        per[m] = {"volume_ratio": round(volume(P, FACES[m]) / volume(P0, FACES[m]), 3),
                  "fibre_length_ratio_min_mean_max": [round(float(fl.min()), 3), round(float(fl.mean()), 3), round(float(fl.max()), 3)],
                  "edge_ratio_p1_p99": [round(float(np.percentile(r, 1)), 3), round(float(np.percentile(r, 99)), 3)],
                  "edge_ratio_min_max": [round(float(r.min()), 3), round(float(r.max()), 3)],
                  "thickness_scale_min_max": [round(float(s.min()), 2), round(float(s.max()), 2)],
                  "along_fibre_shape_kept_min_max": [round(float(g.min()), 2), round(float(g.max()), 2)],
                  "self_intersecting_face_pairs": selfx,
                  "rest_round_trip_max_mm": round(float(np.abs(P - P0).max()) * 1000, 4) if tag == "rest" else None,
                  **per_extra}
        set_mesh(m, P)
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    for o in ARM_OBJ:
        trees[o.name.split(".")[2]] = BVHTree.FromObject(o, dg)
    pairs, names = {}, list(trees)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a not in KIND and b not in KIND:
                continue
            ov = trees[a].overlap(trees[b])
            if ov:
                pairs[f"{a} | {b}"] = len(ov)
    rep["poses"][tag] = {"humerothoracic_deg": round(ht, 1), "muscles": per, "overlap_pairs": pairs,
                         "overlap_total": sum(pairs.values()),
                         "largest_station_jump_per_step_mm_so_far": {m: round(v * 1000, 2) for m, v in jump.items()}}
    print("POSE", tag, json.dumps({"overlap_total": rep["poses"][tag]["overlap_total"],
                                   "volume": {m: v["volume_ratio"] for m, v in per.items()},
                                   "fibre_len_mean": {m: v["fibre_length_ratio_min_mean_max"][1] for m, v in per.items()},
                                   "edge_max": {m: v["edge_ratio_min_max"][1] for m, v in per.items()},
                                   "self": sum(v["self_intersecting_face_pairs"] for v in per.values())}), flush=True)
    gh = anat.matrix_world @ anat.pose.bones[HUM].head
    centre = Vector((gh.x * 0.55, 0.0, gh.z - 0.05))
    if _ENV.get("MG9_CLOSE"):                                 # (diagnostics) the deltoid alone, close up, heads coloured
        for o in MUS + TEN:
            o.hide_render = not o.name.split(".")[2].startswith("deltoid")
        for nm, col in (("anterior", (0.85, 0.35, 0.3, 1)), ("middle", (0.35, 0.75, 0.35, 1)), ("posterior", (0.3, 0.45, 0.9, 1))):
            mt = bpy.data.materials.new("DBG_" + nm); mt.diffuse_color = col
            OBJ["deltoid_" + nm].data.materials.clear(); OBJ["deltoid_" + nm].data.materials.append(mt)
        cd.ortho_scale = 0.30; centre = np.array(Tm[HUM] @ (GH + (EJC - GH) * 0.2)); centre = Vector(centre)
    if _ENV.get("MG9_FANCOL"):                                # (diagnostics) the fans coloured, the rest grey
        for nm, col in (("latissimus_dorsi", (0.3, 0.45, 0.9, 1)), ("teres_major", (0.35, 0.75, 0.35, 1)),
                        ("pectoralis_major_clavicular", (0.9, 0.6, 0.2, 1)),
                        ("pectoralis_major_sternocostal", (0.85, 0.3, 0.3, 1))):
            if "DBGF_" + nm not in bpy.data.materials:
                mt = bpy.data.materials.new("DBGF_" + nm); mt.diffuse_color = col
                OBJ[nm].data.materials.clear(); OBJ[nm].data.materials.append(mt)
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat, 0, 0), "posterior": (0, 1, 0)}.items():
        d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        sc.render.filepath = str(outdir / f"mg9a_{S}_{tag}_{view}.png"); bpy.ops.render.render(write_still=True)
rep["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected
(outdir / f"mg9a_{S}_press_sweep_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", flush=True)
