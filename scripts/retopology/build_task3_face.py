"""Task 3 face: fill the face opening of the Task-3 shell with a designed quad face (both sides, no mirror).

The face of the source is NOT centred on x = 0 (midline -4 mm at the chin .. -8.5 mm at the nasal bridge), so the
shell (built half + Mirror + Shrinkwrap) is first applied to a full mesh, and the face is built across the whole
opening around the face's own measured midline.

Layout (design record; positions in mm measured on the geometry proxy from 1 mm-grid front renders):
  * each half face is a grid between the shell's face-opening boundary (jaw loop below, forehead loop above, the
    cheekbone column at the side) and a designed midline chain (chin - lips - philtrum - nose - glabella - forehead);
  * EYE: a rectangle of grid cells around each eye is replaced by concentric rings (orbicularis oculi loops) that
    shrink to the measured palpebral fissure, closed by a small grid (the eyelid / eye surface of the sculpt);
  * MOUTH: a half-rectangle on each side of the midline is replaced by half-rings (orbicularis oris loops) that
    shrink to the vermilion border; the lips are closed by a grid whose middle row is the lip line (stomion);
  * all vertices are projected onto the source with front rays; interior face vertices get a light on-surface relax.

usage: python3.13 build_task3_face.py -- <shell checkpoint .blend (03d)> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; SHELL = bpy.data.objects["HGPT_Male_Task3_Shell"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); bvh = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(p.vertices) for p in SRC.data.polygons])
D = json.loads(SHELL["TASK3_SHELL_DESIGN"])
I_JAW, I_TOP = D["face_rows"]; FCOL = D["face_cols"][1]; NSEG = D["segments_per_half_loop"]

# ================================================================ design record (metres)
MM = 0.001
MIDLINE = [(1.578, 0.0), (1.600, -4.2 * MM), (1.620, -6.1 * MM), (1.640, -6.1 * MM), (1.660, -7.0 * MM), (1.680, -7.8 * MM),
           (1.700, -8.5 * MM), (1.725, -6.0 * MM), (1.745, 0.0)]             # face midline x(z), measured
EYE_R = {"inner": (3 * MM, 1.6930), "outer": (35 * MM, 1.6950), "upper": (16 * MM, 1.6985), "lower": (19 * MM, 1.6910)}
EYE_C = (19 * MM, 1.6945)                                                     # ring centre (right eye)
# left eye measured on its own (the face is asymmetric; mirroring the right eye folded quads at its corners)
EYE_L = {"inner": (-20 * MM, 1.6925), "outer": (-50 * MM, 1.6955), "upper": (-34 * MM, 1.6990), "lower": (-36 * MM, 1.6910)}
EYE_LC = (-35 * MM, 1.6945)
# nose outline relative to the face midline (alar groove / nose base): dorsum top, alar top, alar lateral point,
# alar base, subnasale.  Nostril wings measured at x +10 / -25 mm (midline -7.5), nostril base z 1.648
NOSE = {"dorsum": 1.6700, "alar_top": (12 * MM, 1.6660), "alar_lat": (17.5 * MM, 1.6550), "alar_base": (15 * MM, 1.6490),
        "subnasale": 1.6455}
NOSE_RINGS = 1                                                                # the nose base sits only ~5 mm above the shared mouth row
NOSE_MARGIN = (4.0 * MM, 3.0 * MM)
MOUTH = {"corner": (20 * MM, 1.6285), "upper_mid": 1.6370, "lower_mid": 1.6170, "stomion": 1.6275}
EYE_RINGS = 3                                                                 # rings between the rectangle and the fissure
MOUTH_RINGS = 2                                                               # 2: the philtrum (8.5 mm) also carries the nose rings
EYE_MARGIN = (5.0 * MM, 5.0 * MM)                                             # rectangle beyond the fissure (x, z)
MOUTH_MARGIN = (5.0 * MM, 3.5 * MM)


def mid_x(z):
    return float(np.interp(z, [p[0] for p in MIDLINE], [p[1] for p in MIDLINE]))


def front_hit(x, z):
    h = bvh.ray_cast(Vector((x, -0.40, z)), Vector((0, 1, 0)))[0]
    if h is None:
        raise RuntimeError(f"no surface in front at x {x} z {z}")
    return h


# ================================================================ full mesh from the shell (apply Mirror + Shrinkwrap)
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(SHELL.evaluated_get(dg), depsgraph=dg); me.name = "HGPT_Male_Task3_Body"
body = bpy.data.objects.new("HGPT_Male_Task3_Body", me); bpy.data.collections["BODY_PRODUCTION"].objects.link(body)
SHELL.hide_render = True; SHELL.hide_viewport = True
bm = bmesh.new(); bm.from_mesh(me)
LR = bm.verts.layers.int["t3_row"]; LC = bm.verts.layers.int["t3_col"]
SHV = {}
for v in bm.verts:
    side = 0 if v[LC] in (0, NSEG) else (1 if v.co.x > 0 else -1)
    SHV[(v[LR], v[LC], side)] = v


def shell_v(r, c, side):
    return SHV[(r, c, 0 if c in (0, NSEG) else side)]


R = I_TOP - I_JAW; F = FCOL                                 # half-face grid: R rows x F columns of cells
# midline chain (shared by both sides): z follows the side column's loop heights, x follows the measured midline
zs_side = [0.5 * (shell_v(I_JAW + r, F, 1).co.z + shell_v(I_JAW + r, F, -1).co.z) for r in range(R + 1)]
z_bot, z_top = shell_v(I_JAW, 0, 1).co.z, shell_v(I_TOP, 0, 1).co.z
zs_mid = [z_bot] + [zs_side[r] for r in range(1, R)] + [z_top]
for r in range(1, R):                                       # keep the chain monotonic between its fixed ends
    zs_mid[r] = min(max(zs_mid[r], zs_mid[r - 1] + 0.003), z_top - 0.003 * (R - r))
MID2 = [(mid_x(z), z) for z in zs_mid]
nv = {}                                                     # new vertices by key


def V(key, x, z):
    if key not in nv:
        nv[key] = bm.verts.new(front_hit(x, z))
    return nv[key]


def V3(key, p):
    if key not in nv:
        nv[key] = bm.verts.new(Vector(p))
    return nv[key]


def sweep_hits(O, d0, d1, n=300):
    """surface points hit by rays from O swept (slerp) from direction d0 to d1"""
    d0, d1 = d0.normalized(), d1.normalized(); om = d0.angle(d1); out = []
    for t in np.linspace(0, 1, n):
        d = (math.sin((1 - t) * om) * d0 + math.sin(t * om) * d1) / max(math.sin(om), 1e-9) if om > 1e-6 else d0
        h = bvh.ray_cast(O, d)[0]
        if h is not None:
            out.append(h)
    return out


def coons(B, T, L, Rr, u, v):
    """2D Coons patch; B, T run along u (0..1), L, Rr along v; corners shared"""
    return ((1 - v) * B(u) + v * T(u) + (1 - u) * L(v) + u * Rr(v)
            - ((1 - u) * (1 - v) * B(0) + u * (1 - v) * B(1) + (1 - u) * v * T(0) + u * v * T(1)))


def poly_fn(pts):
    P = np.array(pts, float); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; s /= s[-1]
    return lambda t: np.array([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])])


def idx_fn(pts):
    """polyline indexed by vertex count (uniform in index, not arc length) - keeps grid lines on boundary vertices"""
    P = np.array(pts, float); n = len(P) - 1
    return lambda t: P[min(int(round(t * n)), n)] if abs(t * n - round(t * n)) < 1e-9 else P[int(t * n)] + (t * n - int(t * n)) * (P[min(int(t * n) + 1, n)] - P[int(t * n)])


def build_side(side, layout=None):
    sg = 1.0 if side > 0 else -1.0
    xz = lambda v: np.array([v.co.x, v.co.z])
    Bp = [xz(shell_v(I_JAW, c, side)) for c in range(F + 1)]
    Tp = [xz(shell_v(I_TOP, c, side)) for c in range(F + 1)]
    Rp = [xz(shell_v(I_JAW + r, F, side)) for r in range(R + 1)]
    Lp = [np.array(p) for p in MID2]; Lp[0] = Bp[0]; Lp[-1] = Tp[0]
    Bf, Tf, Lf, Rf = idx_fn(Bp), idx_fn(Tp), idx_fn(Lp), idx_fn(Rp)
    G = {(r, c): coons(Bf, Tf, Lf, Rf, c / F, r / R) for r in range(R + 1) for c in range(F + 1)}

    # ---- feature curves for this side (left side mirrored about the face midline)
    def mir(p):
        x, z = p; return (x if side > 0 else 2 * mid_x(z) - x, z)
    if side > 0:
        ec = np.array(EYE_C); ei, eo, eu, el = (np.array(EYE_R[k]) for k in ("inner", "outer", "upper", "lower"))
    else:
        ec = np.array(EYE_LC); ei, eo, eu, el = (np.array(EYE_L[k]) for k in ("inner", "outer", "upper", "lower"))
    # fissure as a closed polygon (upper lid inner->outer, lower lid outer->inner), smooth quadratic arcs
    def arc(p0, pm, p1, n=40):
        t = np.linspace(0, 1, n)[:, None]; return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * (2 * pm - 0.5 * (p0 + p1)) + t ** 2 * p1
    fiss = np.vstack([arc(ei, eu, eo), arc(eo, el, ei)[1:]])
    mc = np.array([mid_x(MOUTH["stomion"]), MOUTH["stomion"]]); mcorner = np.array(mir(MOUTH["corner"]))
    mu = np.array([mid_x(MOUTH["upper_mid"]), MOUTH["upper_mid"]]); ml = np.array([mid_x(MOUTH["lower_mid"]), MOUTH["lower_mid"]])
    verm = np.vstack([arc(mu, 0.5 * (mu + mcorner) + np.array([0, 0.0015]), mcorner), arc(mcorner, 0.5 * (ml + mcorner) - np.array([0, 0.0015]), ml)[1:]])

    def ray_curve(curve, centre, ang):
        """point of a closed / open curve hit by the ray from centre at angle ang (2D)"""
        d = np.array([math.cos(ang), math.sin(ang)]); best = None
        for p0, p1 in zip(curve[:-1], curve[1:]):
            e = p1 - p0; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
            if abs(np.linalg.det(M)) < 1e-12:
                continue
            s_, t_ = np.linalg.solve(M, p0 - centre)
            if s_ > 0 and -1e-9 <= t_ <= 1 + 1e-9 and (best is None or s_ < best[0]):
                best = (s_, p0 + t_ * e)
        if best is None:                    # ray along the curve's end (e.g. the midline): closest point by angle
            ang_c = np.arctan2(curve[:, 1] - centre[1], curve[:, 0] - centre[0])
            k = int(np.argmin(np.abs((ang_c - ang + np.pi) % (2 * np.pi) - np.pi))); return curve[k].copy()
        return best[1]

    def along(curve):
        P_ = np.asarray(curve, float); sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]
        return P_, sl

    def at(curve_sl, s_):
        P_, sl = curve_sl; return np.array([np.interp(s_, sl, P_[:, 0]), np.interp(s_, sl, P_[:, 1])])

    def map_sides(curve, anchors, counts):
        """points along a curve: segment k runs from arc length anchors[k] to anchors[k+1] in counts[k] equal steps"""
        cs = along(curve); out = []
        for k, n_ in enumerate(counts):
            s0, s1 = anchors[k], anchors[k + 1]
            out += [at(cs, s0 + (s1 - s0) * i / n_) for i in range(n_)]
        return out

    # ---- choose the eye rectangle and mouth half-rectangle in grid indices
    gx = lambda r, c: G[r, c][0] * sg; gz = lambda r, c: G[r, c][1]
    xs_e = sorted([ei[0] * sg, eo[0] * sg]); zs_e = (min(el[1], ei[1], eo[1]), eu[1])
    rows_z = [np.mean([gz(r, c) for c in range(F + 1)]) for r in range(R + 1)]
    re0 = max(r for r in range(R + 1) if rows_z[r] <= zs_e[0] - EYE_MARGIN[1]); re1 = min(r for r in range(R + 1) if rows_z[r] >= zs_e[1] + EYE_MARGIN[1])
    cols_x = [np.mean([gx(r, c) for r in range(re0, re1 + 1)]) for c in range(F + 1)]
    ce0 = max(1, max(c for c in range(F + 1) if cols_x[c] <= xs_e[0] - EYE_MARGIN[0] * 0.4))
    ce1 = min(F - 1, min(c for c in range(F + 1) if cols_x[c] >= xs_e[1] + EYE_MARGIN[0]))
    if layout:
        re0, re1 = layout["eye_rect_rows"]; ce0, ce1 = layout["eye_rect_cols"]
    rm0 = max(r for r in range(R + 1) if rows_z[r] <= MOUTH["lower_mid"] - MOUTH_MARGIN[1])
    rm1 = min(r for r in range(R + 1) if rows_z[r] >= MOUTH["upper_mid"] + MOUTH_MARGIN[1])
    cols_xm = [np.mean([gx(r, c) for r in range(rm0, rm1 + 1)]) for c in range(F + 1)]
    cm = min(c for c in range(F + 1) if cols_xm[c] >= mcorner[0] * sg + MOUTH_MARGIN[0])
    if layout:
        rm0, rm1 = layout["mouth_rect_rows"]; cm = layout["mouth_rect_cols"][1]
    rn0 = rm1                                                     # nose rectangle sits on the mouth rectangle's top row
    rn1 = min(r for r in range(R + 1) if rows_z[r] >= NOSE["dorsum"] + NOSE_MARGIN[1])
    cols_xn = [np.mean([gx(r, c) for r in range(rn0, rn1 + 1)]) for c in range(F + 1)]
    cn = min(c for c in range(F + 1) if cols_xn[c] >= (mid_x(NOSE["alar_lat"][1]) * sg + NOSE["alar_lat"][0] + NOSE_MARGIN[0]))
    if layout:
        rn0, rn1 = layout["nose_rect_rows"]; cn = layout["nose_rect_cols"][1]
    assert rn1 <= re0 or cn <= ce0, f"nose {rn0}-{rn1}x{cn} and eye {re0}-{re1}x{ce0}-{ce1} rectangles overlap"
    hole = set()
    for r in range(re0 + 1, re1):
        for c in range(ce0 + 1, ce1):
            hole.add((r, c))
    for r in range(rm0 + 1, rm1):
        for c in range(0, cm):
            hole.add((r, c))
    for r in range(rn0 + 1, rn1):
        for c in range(0, cn):
            hole.add((r, c))

    # ---- grid vertices (boundary = existing shell vertices; midline shared between the sides)
    gv = {}
    for r in range(R + 1):
        for c in range(F + 1):
            if (r, c) in hole:
                continue
            if r == 0:
                gv[r, c] = shell_v(I_JAW, c, side)
            elif r == R:
                gv[r, c] = shell_v(I_TOP, c, side)
            elif c == F:
                gv[r, c] = shell_v(I_JAW + r, F, side)
            elif c == 0:
                gv[r, c] = V(("mid", r), *G[r, 0])
            else:
                gv[r, c] = V(("g", side, r, c), *G[r, c])
    faces = []
    for r in range(R):
        for c in range(F):
            q = [(r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c)]
            inside_eye = all(re0 <= qq[0] <= re1 and ce0 <= qq[1] <= ce1 for qq in q)
            inside_mouth = all(rm0 <= qq[0] <= rm1 and 0 <= qq[1] <= cm for qq in q)
            inside_nose = all(rn0 <= qq[0] <= rn1 and 0 <= qq[1] <= cn for qq in q)
            if inside_eye or inside_mouth or inside_nose or not all(qq in gv for qq in q):
                continue
            faces.append([gv[qq] for qq in q])

    # ---- eye: rectangle loop -> rings -> fissure -> closing grid
    w, h = ce1 - ce0, re1 - re0
    rect = ([(re0, c) for c in range(ce0, ce1)] + [(r, ce1) for r in range(re0, re1)] +
            [(re1, c) for c in range(ce1, ce0, -1)] + [(r, ce0) for r in range(re1, re0, -1)])      # closed, CCW (right side)
    rect2 = [G[k] for k in rect]
    # fissure correspondence by arc length: bottom side -> lower lid (25-75 %), lateral side -> around the outer
    # corner, top side -> upper lid, medial side -> around the inner corner
    low, upp = arc(ei, el, eo), arc(eo, eu, ei)
    ring_c = np.vstack([low, upp[1:]]); Llow = along(low)[1][-1]; Lupp = along(upp)[1][-1]
    anchors = [0.25 * Llow, 0.75 * Llow, Llow + 0.25 * Lupp, Llow + 0.75 * Lupp, Llow + Lupp + 0.25 * Llow]
    ring_ext = np.vstack([ring_c, low[1:]])                                   # wrap past the inner corner
    inner = map_sides(ring_ext, anchors, [w, h, w, h])
    rings = [[gv[k] for k in rect]]
    for k in range(1, EYE_RINGS + 1):
        t = k / (EYE_RINGS + 1)                                               # evenly spaced (tightening collapsed the corners)
        rings.append([V(("eye", side, k, i), *((1 - t) * rect2[i] + t * inner[i])) for i in range(len(rect))])
    rings.append([V(("eye", side, "fiss", i), *inner[i]) for i in range(len(rect))])
    n = len(rect)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for i in range(n):
            faces.append([a_[i], a_[(i + 1) % n], b_[(i + 1) % n], b_[i]])
    # closing grid inside the fissure (w x h): sides are the four arcs matching the rectangle sides
    fis = rings[-1]; fis2 = inner
    Bv = fis[0:w + 1]; Rv = fis[w:w + h + 1]; Tv = list(reversed(fis[w + h:2 * w + h + 1])); Lv = list(reversed(fis[2 * w + h:] + [fis[0]]))
    B2 = [fis2[i] for i in range(0, w + 1)]; R2 = [fis2[i] for i in range(w, w + h + 1)]
    T2 = list(reversed([fis2[i] for i in range(w + h, 2 * w + h + 1)])); L2 = list(reversed([fis2[i % n] for i in range(2 * w + h, n + 1)]))
    eg = {}
    for r in range(h + 1):
        for c in range(w + 1):
            if r == 0:
                eg[r, c] = Bv[c]
            elif r == h:
                eg[r, c] = Tv[c]
            elif c == 0:
                eg[r, c] = Lv[r]
            elif c == w:
                eg[r, c] = Rv[r]
            else:
                p = coons(idx_fn(B2), idx_fn(T2), idx_fn(L2), idx_fn(R2), c / w, r / h)
                eg[r, c] = V(("lid", side, r, c), *p)
    for r in range(h):
        for c in range(w):
            faces.append([eg[r, c], eg[r, c + 1], eg[r + 1, c + 1], eg[r + 1, c]])

    # ---- midline features (mouth, nose): half-rectangle -> half-rings -> feature outline -> closing grid
    def midline_feature(tag, r0, r1, cw, outline, fr_top, fr_bot, nrings, top_pt, bot_pt, profile_origin=None):
        """outline runs from top_pt (on the midline) round the lateral side to bot_pt (on the midline); the
        rectangle's top side maps to the outline up to fr_top of its length, the lateral side around the extreme,
        the bottom side from fr_bot.  The closing grid's midline column is shared with the other side."""
        wm, hm = cw, r1 - r0
        mrect = [(r1, c) for c in range(0, cw)] + [(r, cw) for r in range(r1, r0, -1)] + [(r0, c) for c in range(cw, -1, -1)]
        mrect2 = [G[k] for k in mrect]
        Lo = along(outline)[1][-1]
        minner = map_sides(outline, [0.0, fr_top * Lo, fr_bot * Lo, Lo], [wm, hm, wm]) + [bot_pt]
        minner[0] = top_pt
        mr = [[gv[k] for k in mrect]]
        for k in range(1, nrings + 1):
            t = k / (nrings + 1); ring = []
            for i in range(len(mrect)):
                p = (1 - t) * mrect2[i] + t * minner[i]
                key = ("mid_" + tag, "top", k) if i == 0 else (("mid_" + tag, "bot", k) if i == len(mrect) - 1 else (tag, side, k, i))
                if i in (0, len(mrect) - 1):
                    p = np.array([mid_x(p[1]), p[1]])
                ring.append(V(key, *p))
            mr.append(ring)
        mr.append([V(("mid_" + tag, "top", "rim") if i == 0 else (("mid_" + tag, "bot", "rim") if i == len(mrect) - 1 else ("rim", tag, side, i)),
                     *minner[i]) for i in range(len(mrect))])
        for a_, b_ in zip(mr[:-1], mr[1:]):
            for i in range(len(mrect) - 1):
                faces.append([a_[i], a_[i + 1], b_[i + 1], b_[i]])
        vm, vm2 = mr[-1], minner
        Tv = vm[0:wm + 1]; Rv = list(reversed(vm[wm:wm + hm + 1])); Bv = list(reversed(vm[wm + hm:]))
        T2 = vm2[0:wm + 1]; R2 = list(reversed(vm2[wm:wm + hm + 1])); B2 = list(reversed(vm2[wm + hm:]))
        L2 = [np.array([mid_x(z), z]) for z in np.linspace(bot_pt[1], top_pt[1], hm + 1)]
        lg = {}
        if profile_origin is not None:
            # profile fill (nose): rows evenly spaced along the sagittal profile (base -> underside -> tip -> bridge),
            # columns swept by rays from a point inside the nose root towards the outline - captures the underside
            O = Vector(profile_origin); b3, t3 = Bv[0].co, Tv[0].co
            prof = sweep_hits(O, b3 - O, t3 - O); prof = [b3] + prof + [t3]
            Pp = np.array([q[:] for q in prof]); sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))]
            for r in range(hm + 1):
                for c in range(wm + 1):
                    if r == 0:
                        lg[r, c] = Bv[c]
                    elif r == hm:
                        lg[r, c] = Tv[c]
                    elif c == wm:
                        lg[r, c] = Rv[r]
                    elif c == 0:
                        sp = r / hm * sl[-1]; pm = Vector([np.interp(sp, sl, Pp[:, d]) for d in range(3)]); pm.x = mid_x(pm.z)
                        lg[r, c] = V3(("mid_" + tag, "fill", r), pm)
            for r in range(1, hm):
                d0 = lg[r, 0].co - O; d1 = lg[r, wm].co - O
                hits = sweep_hits(O, d0, d1, 4 * wm + 1)
                for c in range(1, wm):
                    lg[r, c] = V3((tag + "_fill", side, r, c), hits[min(round(c / wm * (len(hits) - 1)), len(hits) - 1)])
            for r in range(hm):
                for c in range(wm):
                    faces.append([lg[r, c], lg[r, c + 1], lg[r + 1, c + 1], lg[r + 1, c]])
            return len(mrect)
        for r in range(hm + 1):
            for c in range(wm + 1):
                if r == 0:
                    lg[r, c] = Bv[c]
                elif r == hm:
                    lg[r, c] = Tv[c]
                elif c == wm:
                    lg[r, c] = Rv[r]
                elif c == 0:
                    lg[r, c] = V(("mid_" + tag, "fill", r), *L2[r])
                else:
                    lg[r, c] = V((tag + "_fill", side, r, c), *coons(idx_fn(B2), idx_fn(T2), idx_fn(L2), idx_fn(R2), c / wm, r / hm))
        for r in range(hm):
            for c in range(wm):
                faces.append([lg[r, c], lg[r, c + 1], lg[r + 1, c + 1], lg[r + 1, c]])
        return len(mrect)

    # mouth: vermilion border (upper arc to the corner, lower arc back); lips grid middle row = stomion
    up_v = arc(mu, 0.5 * (mu + mcorner) + np.array([0, 0.0015]), mcorner); lo_v = arc(mcorner, 0.5 * (ml + mcorner) - np.array([0, 0.0015]), ml)
    Lu = along(up_v)[1][-1]; verm_c = np.vstack([up_v, lo_v[1:]]); Lv_ = along(verm_c)[1][-1]
    n_m = midline_feature("m", rm0, rm1, cm, verm_c, 0.7 * Lu / Lv_, (Lu + 0.3 * (Lv_ - Lu)) / Lv_, MOUTH_RINGS, mu, ml)
    # nose: dorsum -> alar top -> alar lateral point -> alar base -> subnasale (alar-groove loops)
    nd = np.array([mid_x(NOSE["dorsum"]), NOSE["dorsum"]]); ns = np.array([mid_x(NOSE["subnasale"]), NOSE["subnasale"]])
    rel = lambda q: np.array([mid_x(q[1]) + sg * q[0], q[1]])
    n_up = arc(nd, rel(NOSE["alar_top"]), rel(NOSE["alar_lat"])); n_lo = arc(rel(NOSE["alar_lat"]), rel(NOSE["alar_base"]), ns)
    nose_c = np.vstack([n_up, n_lo[1:]]); Lnu = along(n_up)[1][-1]; Lnc = along(nose_c)[1][-1]
    n_n = midline_feature("n", rn0, rn1, cn, nose_c, 0.75 * Lnu / Lnc, (Lnu + 0.35 * (Lnc - Lnu)) / Lnc, NOSE_RINGS, nd, ns,
                          profile_origin=(mid_x(1.652), -0.085, 1.652))
    return faces, {"eye_rect_rows": [re0, re1], "eye_rect_cols": [ce0, ce1], "eye_ring_vertices": len(rect),
                   "mouth_rect_rows": [rm0, rm1], "mouth_rect_cols": [0, cm], "mouth_half_ring_vertices": n_m,
                   "nose_rect_rows": [rn0, rn1], "nose_rect_cols": [0, cn], "nose_half_ring_vertices": n_n}


info = {}
allf = []
f_, inf = build_side(1); allf += f_; info["right"] = inf                     # right side picks the layout
f_, inf = build_side(-1, inf); allf += f_; info["left"] = inf                  # left side uses the same (symmetric topology)
made = 0
for f in allf:
    if len(set(f)) < 4:
        raise RuntimeError("degenerate face in the face patch")
    if bm.faces.get(f) is None:
        bm.faces.new(f); made += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# light on-surface relax of the new face vertices (front-ray re-projection); boundary / midline / features fixed
newv = set(nv.values()); # fixed in both relax passes: midline chain, feature outlines (eyelid line, vermilion, nose outline) and the designed
# rings themselves (nearest-surface relax collapsed neighbouring rings into the nose-lip and eye-corner creases)
fixedkeys = {v for k, v in nv.items() if k[0] in ("mid", "mid_m", "mid_n", "rim", "eye", "m", "n", "n_fill")}
_ring = {v for k, v in nv.items() if k[0] in ("eye", "m", "n", "rim")}
fixedkeys |= {v for k, v in nv.items() if k[0] == "g" and any(e.other_vert(v) in _ring for e in v.link_edges)}  # rectangle outlines
for _ in range(6):
    upd = {}
    for v in newv - fixedkeys:
        nb = [e.other_vert(v) for e in v.link_edges]
        avg = sum((w.co for w in nb), Vector()) / len(nb); p = v.co.lerp(avg, 0.4)
        upd[v] = front_hit(p.x, p.z)
    for v, p in upd.items():
        v.co = p
# final relax across the whole head / neck (z > 1.50): smooths the junctions where loop systems meet (jaw angle,
# forehead-temple corner, eye / mouth corners). Fixed: opening boundaries, eyelid line, vermilion line, face midline.
fixed2 = {v for v in bm.verts if v.is_boundary} | fixedkeys | {v for v in bm.verts if v.co.z <= 1.50}
EAR_X = 0.074
for _ in range(10):
    upd = {}
    for v in bm.verts:
        if v in fixed2:
            continue
        nb = [e.other_vert(v) for e in v.link_edges]
        avg = sum((w.co for w in nb), Vector()) / len(nb); p = v.co.lerp(avg, 0.35)
        in_face = abs(p.x) < 0.07 and p.y < -0.05 and 1.585 < p.z < 1.745
        h = front_hit(p.x, p.z) if in_face else bvh.find_nearest(p)[0]   # face: front rays, as built (no crease snapping)
        if abs(h.x) > EAR_X and 1.63 < h.z < 1.72 and abs(h.x) > abs(v.co.x) + 0.002:
            continue                                      # never slide onto the ear
        upd[v] = h
    for v, h in upd.items():
        v.co = h
bm.to_mesh(me); me.update()
body["TASK3_FACE_DESIGN"] = json.dumps({"midline": MIDLINE, "eye_right": EYE_R, "eye_centre": EYE_C, "mouth": MOUTH,
                                        "eye_left": EYE_L, "nose": NOSE, "eye_rings": EYE_RINGS, "mouth_rings": MOUTH_RINGS, "nose_rings": NOSE_RINGS, "layout": info, "source_is_geometry_proxy": True})
body["PROXY_SOURCE_ONLY"] = True; body["TASK3_SHELL_DESIGN"] = SHELL["TASK3_SHELL_DESIGN"]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
L = np.array([e.calc_length() for e in bm.edges])
import os  # noqa: E402
if os.environ.get("FACE_DIAG"):
    inv = {v: k for k, v in nv.items()}
    for e in sorted(bm.edges, key=lambda e: e.calc_length())[:8]:
        print("DIAG %.2f mm" % (e.calc_length() * 1000), [inv.get(v, ("shell",)) for v in e.verts], [round(c * 1000, 1) for c in e.verts[0].co])
rep = {"out": str(OUT), "object": body.name, "faces_added": made, "new_vertices": len(nv), "vertices": len(bm.verts), "faces": len(bm.faces),
       "non_quads": sum(len(f.verts) != 4 for f in bm.faces), "min_edge_mm": round(float(L.min()) * 1000, 2), "layout": info}
REP.write_text(json.dumps(rep, indent=1)); print("FACE", json.dumps(rep))
