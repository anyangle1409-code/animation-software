"""FEMALE head / neck / torso shell (Home Gym PT female, Option 4 Athletic Balanced, 1.68 m): designed quad layout on
HER OWN Meshy Pro source surface, no auto-remesh, nothing taken from the male mesh.

The loop CONVENTION is the one used for the male (scripts/retopology/build_task3_shell.py: half body + Mirror, horizontal
torso loops, socket / face / ear / pelvis openings, meridian bands, crown Coons cap) so both characters share topology
conventions; every height, width and border below is MEASURED ON HER SURFACE (design record in the output object and
the report), none is derived from the male by scaling.  Female-specific: the body axis ignores her ponytail (it hangs
behind the head and back as a separate surface; it gets its own mesh), the jaw border, skull base and ears are found
on her surface by this script.  Every loop is placed explicitly:

  * "h"  horizontal loop at height z: each column vertex is the first surface hit of a horizontal ray from the body
         axis (theta 0 = front midline, 90 = lateral, 180 = back midline);
  * "m"  meridian loop between two other loops (lower, upper) at fraction t of the surface arc measured along each
         column's vertical half-plane.  The arc is traced by a fan of rays from a point inside the body, so near-flat
         surfaces (top of the trapezius, underside of the jaw, base of the skull) are met at a steep angle;
  * "jl" the jaw / skull-base loop: on the jaw border measured on the source (chin -> jaw angle), then rising behind
         the ear to the base of the skull;
  * "s"  cranium loop at an elevation angle around the head centre; the crown is closed by a Coons-patch quad grid.

Columns: each loop is split into segments by anchor columns (socket edges, face edge, ear edges); inside a segment
the columns are spaced by equal surface arc length.

Openings (left as clean quad boundaries to be bridged by later tasks):
  ARM SOCKET  per loop, where the surface meets the arm root (x = X_CUT); the outline is smoothed and never narrower
              than the arm contact, so no shell vertex lies on the arm;
  FACE        columns < JFACE between the jaw loop and the brow loop (the eye / mouth loop system goes here);
  EAR         columns JE0..JE1 on the ear-height loops (ear modelled separately);
  PELVIS      below z = OPEN_PELVIS_Z (Task 5).

Source surface: HGPT_FEMALE_SOURCE_Mesh_0 (her verified Meshy Pro .blend, transform applied, materials stripped).
The input file is opened and saved under a NEW name.

usage: python3.13 build_f_shell.py -- <female source .blend (F00)> <out NEW .blend> <report .json>
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402  (bmesh needs bpy imported first)
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
SRC_BLEND, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND), load_ui=False)
SRC_FULL = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]
SV = np.array([v.co[:] for v in SRC_FULL.data.vertices]); ST = [tuple(p.vertices) for p in SRC_FULL.data.polygons]
bvh = BVHTree.FromPolygons([tuple(v) for v in SV], ST)
SRC = SRC_FULL                                 # the body-only target replaces it below (after the body axis exists)

# ================================================================ body axis (her ponytail excluded)
import bmesh as _bm  # noqa: E402


def _section_loops(z):
    bm = _bm.new(); bm.from_mesh(SRC_FULL.data)
    r = _bm.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z), plane_no=(0, 0, 1))
    segs = [(e.verts[0].co.copy(), e.verts[1].co.copy()) for e in r["geom_cut"] if isinstance(e, _bm.types.BMEdge)]
    bm.free(); key = lambda p: (round(p.x, 5), round(p.y, 5)); adj = {}; pos = {}
    for p, q in segs:
        A, B = key(p), key(q); pos[A] = p; pos[B] = q; adj.setdefault(A, []).append(B); adj.setdefault(B, []).append(A)
    seen = set(); out = []
    for s0 in adj:
        if s0 in seen:
            continue
        c = []; st = [s0]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); c.append(pos[x]); st += adj[x]
        if len(c) > 10:
            out.append(np.array([[p.x, p.y] for p in c]))
    return out


_CY = {}


def centre_y(z):
    """front-back centre of HER BODY loop at height z: of the LARGE loops (span > 6 cm) that cross the midline, the one
    holding the front-most point - the ponytail loops behind the head / back and the small fin of the sports bra's
    centre front (z 1.14-1.24, a few cm in front of the cleavage) are ignored; mid of its extent within 5 cm of the
    midline"""
    k = round(z, 3)
    if k not in _CY:
        L = [l for l in _section_loops(k) if l[:, 0].min() < 0 < l[:, 0].max() and np.ptp(l[:, 0]) > 0.06]
        b = min(L, key=lambda l: l[:, 1].min()); m = b[np.abs(b[:, 0]) < 0.05]
        _CY[k] = float(0.5 * (m[:, 1].min() + m[:, 1].max()))
    return _CY[k]


def _r(z, th, cy=None):
    t = math.radians(th); c = Vector((0.0, centre_y(z) if cy is None else cy, z)); h = bvh.ray_cast(c, Vector((math.sin(t), -math.cos(t), 0.0)))[0]
    return (h - c).length if h is not None else float("nan")


# ================================================================ body-only projection target
# Her ponytail hangs just behind her head, neck and upper back, and the sports bra has a thin centre-front fin in front
# of the cleavage: nearest-surface snapping (on-surface relax, the Mirror + Shrinkwrap projection of the left half) can
# land on them.  A vertex is an OUTER LAYER when a horizontal ray from it towards the body axis ENTERS another surface
# (a hit whose normal faces the ray, more than 4 mm away) before reaching the axis - skin vertices are already inside
# the body, so their rays only leave surfaces: ponytail = such vertices behind the axis (y > axis + 4 cm, |x| < 0.10 m, 1.00 < z < 1.60;
# the tie on the crown is kept so the scalp stays closed), fin = such vertices in front (|x| < 0.03 m, 1.10 < z < 1.28).
# Faces touching them are left out of the target.  The source itself is not changed.
def _outer_layer():
    out = np.zeros(len(SV), bool)
    for i, (x, y, z) in enumerate(SV):
        hair = abs(x) < 0.10 and 1.00 < z < 1.60
        fin = abs(x) < 0.03 and 1.10 < z < 1.28
        if not (hair or fin):
            continue
        cy = centre_y(round(z / 0.004) * 0.004)
        if (hair and y < cy + 0.04) or (fin and not hair and y > cy - 0.04):
            continue
        p = Vector((x, y, z)); d = Vector((0.0, cy, z)) - p; L = d.length; d.normalize(); t = 0.0005
        while t < L - 0.004:                      # outer layer: the ray ENTERS a surface (normal facing it) > 4 mm away
            h, n, _, dist = bvh.ray_cast(p + d * t, d, L - t)
            if h is None:
                break
            t += dist + 0.0003
            if n.dot(d) < 0 and t > 0.004:
                out[i] = True; break
    return out


OUTER = _outer_layer()
_keep = [f for f in ST if not OUTER[list(f)].any()]
_bme = bpy.data.meshes.new("HGPT_FEMALE_SOURCE_BODY_TARGET"); _bme.from_pydata(SV.tolist(), [], _keep); _bme.update()
SRC = bpy.data.objects.new("HGPT_FEMALE_SOURCE_BODY_TARGET", _bme); bpy.context.scene.collection.objects.link(SRC)
SRC.hide_render = True; SRC["NOTE"] = "projection target only: her source minus the hanging ponytail and the bra fin"
bvh = BVHTree.FromPolygons([tuple(v) for v in SV], _keep)
print("TARGET outer-layer vertices", int(OUTER.sum()), "faces kept", len(_keep), "of", len(ST))


# ================================================================ design record (all values measured on her surface)
NSEG = 33                                     # segments per half loop (odd: the crown grid uses 8 + 17 + 8)
COL_STEP = 180.0 / NSEG
THETAS = [round(i * COL_STEP, 4) for i in range(NSEG + 1)]
JF, JB = 11, 22                               # arm-socket edge columns (front / back)
JFACE = 10                                    # face-opening edge column (cheekbone)
JE0, JE1 = 15, 21                             # ear-opening edge columns
X_CUT = float(os.environ.get("F_X_CUT", "0.152"))   # arm-root line: her torso half-width below the armpit (0.142 m
                                              # at z 1.20) + 1 cm; her arm's inner edge there is at 0.147-0.149 m
SOCK_FADE = 0.04
OPEN_PELVIS_Z = 0.960                         # above her gluteal cleft (cleft depth < 1.5 mm from z 0.93; the lumbar
                                              # groove starts at 0.98)
# jaw border: for each column angle, the height where a horizontal ray from a FIXED neck axis (the body axis at z 1.40;
# the axis itself shifts where the section changes from neck to head) jumps from the neck onto the jaw (radius step
# > 10 mm), measured here on her surface
CY_NECK = centre_y(1.40)


# Radius profiles (mm) from the neck axis, z 1.400-1.500 every 4 mm, were read for theta 0..180 (fretopo/jaw.py,
# recorded in the F01 notes): the neck -> jaw step starts at the values below; behind the ear the back of her neck
# runs up to the occiput / hairline at 1.476 (radius minimum 31 mm at 1.460-1.468, rising from 1.476).
JAW_BORDER = [(0, 1.420), (10, 1.420), (20, 1.424), (30, 1.432), (40, 1.438), (50, 1.446), (60, 1.454), (70, 1.462),
              (80, 1.468)]
JAW_ABOVE = 0.003                             # the loop sits just above the jump (on the jaw / face side)
SKULL_BASE_Z = 1.478                          # her occiput (see above), the loop just above it
HEAD_C = Vector((0.0, centre_y(1.53), 1.53))  # head centre: body axis at the top of her ear (ear z 1.475-1.535)
CAP = {"rows_front_back": 17, "half_columns": 8}
Z_ARMPIT = 1.210                              # arms separate from the trunk below this (sections, 2 cm)
torso = [("h", float(z)) for z in np.round(np.linspace(OPEN_PELVIS_Z, 1.188, 10), 4)]
sock = [("h", float(z)) for z in np.round(np.linspace(1.212, 1.336, 17), 4)]       # armpit .. top of the shoulder, 7.75 mm
TRAP_LO, TRAP_HI = ("h", 1.336), ("h", 1.372)
trap = [("m", (TRAP_LO, TRAP_HI, i / 6, 1.30)) for i in range(1, 7)]              # trapezius / neck base: 6 loops
NECK_HI = ("jl",)
neck = [("m", (TRAP_HI, NECK_HI, i / 4, 1.34)) for i in range(1, 5)]               # neck + underside of jaw: 4 loops
JAW_ROW = neck[-1]
HEAD_Z = [float(z) for z in np.round(np.arange(1.488, 1.5521, 0.008), 4)]          # 8 mm loops, jaw .. just above the
                                                                                   # head centre (cranium loops above)
head = [("m", (NECK_HI, ("h", HEAD_Z[0]), 0.5, 1.38))] + [("h", z) for z in HEAD_Z]
EAR_LO, EAR_HI = JAW_ROW, ("h", 1.536)        # her ear z 1.475-1.535: the jaw loop (1.468-1.476 there) is its lower edge
EAR_DEG = (float(os.environ.get("F_EAR_D0", "88")), float(os.environ.get("F_EAR_D1", "124")))   # her ear: lateral,
                                                                                   # just behind the head axis
FACE_EDGE_DEG = JFACE * COL_STEP
cranium = [("s", e) for e in (20, 27, 34, 42)]
FACE_TOP = ("s", 27)
ROWS = torso + sock + trap + neck + head + cranium
I_JAW = ROWS.index(JAW_ROW); I_BROW = ROWS.index(FACE_TOP)
I_EAR0 = ROWS.index(EAR_LO); I_EAR1 = ROWS.index(EAR_HI)


def hray(z, th):
    t = math.radians(th); h = bvh.ray_cast(Vector((0.0, centre_y(z), z)), Vector((math.sin(t), -math.cos(t), 0.0)))[0]
    if h is None:
        raise RuntimeError(f"no surface at z {z} theta {th}")
    return h


def jaw_z(th):
    tmax = JAW_BORDER[-1][0]
    if th <= tmax:
        return float(np.interp(th, [p[0] for p in JAW_BORDER], [p[1] for p in JAW_BORDER])) + JAW_ABOVE
    w = min((th - tmax) / 40.0, 1.0); w = w * w * (3 - 2 * w)
    return (1 - w) * (JAW_BORDER[-1][1] + JAW_ABOVE) + w * SKULL_BASE_Z


_MER = {}


def meridian(lo, hi, oz, th):
    """surface arc for column theta from loop lo to loop hi, traced by a fan of rays from a point inside the body
    (height oz) in the plane through that point and both end points, so the arc starts and ends exactly on the loops"""
    key = (lo, hi, oz, round(th, 3))
    if key not in _MER:
        p0, p1 = place(lo, th), place(hi, th)
        A = Vector((0.0, 0.5 * (centre_y(p0.z) + centre_y(p1.z)), oz))
        e1 = (p0 - A).normalized(); nrm = (p0 - A).cross(p1 - A)
        if nrm.length < 1e-9:
            nrm = Vector((math.cos(math.radians(th)), math.sin(math.radians(th)), 0.0))
        e2 = nrm.cross(e1).normalized(); tot = (p0 - A).angle(p1 - A)
        pts = [p0]
        for al in np.linspace(0.0, tot, 241)[1:-1]:
            h = bvh.ray_cast(A, e1 * math.cos(al) + e2 * math.sin(al))[0]
            if h is not None:
                pts.append(h)
        pts.append(p1); P_ = np.array(pts)
        _MER[key] = (P_, np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))])
    return _MER[key]


def place(row, th):
    k = row[0]
    if k == "h":
        return hray(row[1], th)
    if k == "jl":
        return hray(jaw_z(th), th)
    if k == "s":
        e = math.radians(row[1]); t = math.radians(th)
        h = bvh.ray_cast(HEAD_C, Vector((math.sin(t) * math.cos(e), -math.cos(t) * math.cos(e), math.sin(e))))[0]
        return h
    if k == "m":
        lo, hi, frac, oz = row[1]
        if frac >= 1.0:
            return place(hi, th)
        P_, s = meridian(lo, hi, oz, th); x = frac * s[-1]; i = int(np.clip(np.searchsorted(s, x), 1, len(s) - 1))
        w = (x - s[i - 1]) / max(s[i] - s[i - 1], 1e-12)
        return Vector(P_[i - 1] * (1 - w) + P_[i] * w)       # on the traced arc (241 samples), stays in its plane
    raise ValueError(row)


def row_z(row, th=90.0):
    return place(row, th).z


# ================================================================ columns
def fine_hits(row, step=0.5):
    th = np.arange(0, 180 + 1e-9, step); return th, np.array([place(row, t) for t in th])


def socket_edges(row):
    """last surface points on the torso side (x < X_CUT) before the loop reaches the arm (rays at the armpit junction
    jump straight onto the arm, so the crossing point itself is not used)"""
    th, F = fine_hits(row); out = np.where(F[:, 0] >= X_CUT)[0]
    if not len(out):
        return None
    return float(th[max(out[0] - 1, 0)]), float(th[min(out[-1] + 1, len(th) - 1)])


def seg_columns(row, anchors):
    th, F = fine_hits(row); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(F, axis=0), axis=1))]
    s_at = lambda t: float(np.interp(t, th, s)); cols = {}
    for (j0, t0), (j1, t1) in zip(anchors[:-1], anchors[1:]):
        for j in range(j0, j1 + 1):
            u = (j - j0) / (j1 - j0); cols[j] = float(np.interp(s_at(t0) + u * (s_at(t1) - s_at(t0)), s, th))
    return cols


HEAD_ANCHORS = [(0, 0.0), (JFACE, FACE_EDGE_DEG), (JE0, EAR_DEG[0]), (JE1, EAR_DEG[1]), (NSEG, 180.0)]
CAND = [i for i, r in enumerate(ROWS) if r[0] in ("h", "m") and 1.19 < row_z(r) < 1.40]
EDGE = {i: socket_edges(ROWS[i]) for i in CAND}
SOCK_ROWS = [i for i in CAND if EDGE[i]]
assert SOCK_ROWS == list(range(SOCK_ROWS[0], SOCK_ROWS[-1] + 1)), "socket rows must be contiguous"
RAW_EDGES = [EDGE[i] for i in SOCK_ROWS]
_f = np.array([e[0] for e in RAW_EDGES]); _b = np.array([e[1] for e in RAW_EDGES]); _n = len(_f)
_win = lambda arr, r, fn: np.array([fn(arr[max(0, k - r):k + r + 1]) for k in range(_n)])
_fs = np.minimum(_win(_win(_f, 3, np.min), 2, np.mean), _f); _bs = np.maximum(_win(_win(_b, 3, np.max), 2, np.mean), _b)
for k, i in enumerate(SOCK_ROWS):
    EDGE[i] = (float(_fs[k]), float(_bs[k]))
zs = np.array([row_z(ROWS[i]) for i in SOCK_ROWS])
TORSO_LAST = I_JAW - len(neck)                     # rows up to the trapezius band use the torso column layout
COLS = []
LOOP_COLS = {}                                      # column layout of the loops that bound the meridian bands


def loop_cols(row, anchors_of):
    if row not in LOOP_COLS:
        i = ROWS.index(row) if row in ROWS else None
        LOOP_COLS[row] = COLS[i] if i is not None and i < len(COLS) else seg_columns(row, anchors_of)
    return LOOP_COLS[row]


for i, r in enumerate(ROWS):
    if r[0] == "m" and not EDGE.get(i):
        # meridian band: each column keeps (blends) its angle between the bounding loops, so columns run along the
        # surface meridians and quads do not shear between closely spaced loops
        lo, hi, t, _ = r[1]
        # the trapezius-top loop is spaced evenly (no face / ear anchors: those would crowd 9 columns across the
        # throat); the face / ear layout is reached only at the jaw loop
        even = [(0, 0.0), (NSEG, 180.0)]
        clo = COLS[ROWS.index(TRAP_LO)] if lo == TRAP_LO else loop_cols(lo, even if lo == TRAP_HI else HEAD_ANCHORS)
        chi = loop_cols(hi, even if hi == TRAP_HI else HEAD_ANCHORS)
        w = t * t * (3 - 2 * t) if lo == TRAP_LO else t
        COLS.append({j: (1 - w) * clo[j] + w * chi[j] for j in clo}); continue
    if i <= TORSO_LAST:
        if EDGE.get(i):
            f, b = EDGE[i]
        else:
            zv = row_z(r); zc = float(np.clip(zv, zs.min(), zs.max())); w = max(0.0, 1 - abs(zv - zc) / SOCK_FADE)
            f = w * float(np.interp(zc, zs, _fs)) + (1 - w) * THETAS[JF]; b = w * float(np.interp(zc, zs, _bs)) + (1 - w) * THETAS[JB]
        cols = seg_columns(r, [(0, 0.0), (JF, f), (JB, b), (NSEG, 180.0)])
    else:
        cols = seg_columns(r, HEAD_ANCHORS)
    COLS.append(cols)
P = np.array([[place(r, COLS[i][j]) for j in range(NSEG + 1)] for i, r in enumerate(ROWS)])
P[:, 0, 0] = 0.0; P[:, NSEG, 0] = 0.0                # midline columns exactly on the mirror plane


# ================================================================ openings
def is_hole_vert(i, j):
    if i in SOCK_ROWS and JF < j < JB:
        return True
    if I_JAW < i < I_BROW and j < JFACE:
        return True
    return I_EAR0 < i < I_EAR1 and JE0 < j < JE1


def is_hole_face(q):
    rows = {c[0] for c in q}; cols = [c[1] for c in q]
    sock = bool(rows & set(SOCK_ROWS)) and rows <= set(SOCK_ROWS) | {SOCK_ROWS[0] - 1, SOCK_ROWS[-1] + 1} and all(JF <= c <= JB for c in cols)
    face = all(I_JAW <= r <= I_BROW for r in rows) and all(c <= JFACE for c in cols)
    ear = all(I_EAR0 <= r <= I_EAR1 for r in rows) and all(JE0 <= c <= JE1 for c in cols)
    return sock or face or ear


# ================================================================ diagnostics (optional)
if os.environ.get("TASK3_DIAG"):
    for i in range(len(ROWS) - 1):
        for j in range(NSEG):
            q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
            if any(is_hole_vert(*c) for c in q) or is_hole_face(q):
                continue
            C = [Vector(P[c]) for c in q]; ang = []
            for k in range(4):
                u_, v_ = C[k - 1] - C[k], C[(k + 1) % 4] - C[k]
                ang.append(math.degrees(u_.angle(v_)) if u_.length > 1e-9 and v_.length > 1e-9 else 0.0)
            if min(ang) < 20 or max(ang) > 160:
                print("DIAG", i, ROWS[i][0], str(ROWS[i][1])[:40], "col", j, "theta %.1f" % COLS[i][j], "angles", [round(x) for x in ang],
                      "z %.3f" % C[0].z)
    for i in range(40, 50):
        print("PTS", i, ROWS[i][0], " ".join("c%d:(%.1f) %s" % (j, COLS[i][j], [round(float(x) * 1000) for x in P[i, j]]) for j in (5, 7, 13, 25)))
    for i in range(len(ROWS)):
        if 0 < P[i, 0, 2] and abs(P[i, 0, 0]) < 1e-3 and I_JAW - 7 <= i <= I_JAW + 2:
            print("FRONT", i, ROWS[i][0], str(ROWS[i][1])[:50], "front point", [round(x, 4) for x in P[i, 0]], "hole?", is_hole_vert(i, 0))

# ================================================================ mesh
bm = bmesh.new(); vid = {}
# loop / column identity of every vertex (kept through the Mirror modifier; used by build_task3_face.py). The layers
# are created before any vertex: adding a layer later invalidates existing BMVert references.
bm.verts.layers.int.new("t3_row"); bm.verts.layers.int.new("t3_col")
L_ROW = bm.verts.layers.int["t3_row"]; L_COL = bm.verts.layers.int["t3_col"]
for i in range(len(ROWS)):
    for j in range(NSEG + 1):
        if not is_hole_vert(i, j):
            vid[i, j] = bm.verts.new(Vector(P[i, j])); vid[i, j][L_ROW] = i; vid[i, j][L_COL] = j
for i in range(len(ROWS) - 1):
    for j in range(NSEG):
        q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        if all(c in vid for c in q) and not is_hole_face(q):
            bm.faces.new([vid[c] for c in reversed(q)])
# crown: Coons-patch quad grid on the last cranium loop
top = len(ROWS) - 1; NR, NC = CAP["rows_front_back"], CAP["half_columns"]
assert NC + NR + NC == NSEG
ring = [Vector(P[top, j]) for j in range(NSEG + 1)]
Bc, Rt, Tc = ring[0:NC + 1], ring[NC:NC + NR + 1], list(reversed(ring[NC + NR:NSEG + 1]))
a_f = math.atan2(ring[0].z - HEAD_C.z, -(ring[0].y - HEAD_C.y)); a_b = math.atan2(ring[NSEG].z - HEAD_C.z, -(ring[NSEG].y - HEAD_C.y))
fine = [bvh.ray_cast(HEAD_C, Vector((0.0, -math.cos(al), math.sin(al))))[0] for al in np.linspace(a_f, a_b, 400)]
F_ = np.array([ring[0]] + [p for p in fine if p is not None] + [ring[NSEG]])
s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(F_, axis=0), axis=1))]
Lt = [Vector([np.interp(u * s_[-1], s_, F_[:, d]) for d in range(3)]) for u in np.linspace(0, 1, NR + 1)]
cap = {}
for r in range(NR + 1):
    for c in range(NC + 1):
        if r == 0:
            cap[r, c] = vid[top, c]; continue
        if r == NR:
            cap[r, c] = vid[top, NSEG - c]; continue
        if c == NC:
            cap[r, c] = vid[top, NC + r]; continue
        u, v = c / NC, r / NR
        Pc = ((1 - v) * Bc[c] + v * Tc[c] + (1 - u) * Lt[r] + u * Rt[r]
              - ((1 - u) * (1 - v) * Bc[0] + u * (1 - v) * Bc[NC] + (1 - u) * v * Tc[0] + u * v * Tc[NC]))
        d = (Pc - HEAD_C)
        if c == 0:
            d.x = 0.0
        h = bvh.ray_cast(HEAD_C, d.normalized())[0]
        if c == 0:
            h.x = 0.0
        cap[r, c] = bm.verts.new(h); cap[r, c][L_ROW] = -2; cap[r, c][L_COL] = -1
for r in range(NR):
    for c in range(NC):
        bm.faces.new([cap[r, c], cap[r, c + 1], cap[r + 1, c + 1], cap[r + 1, c]])
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# loop / column identity of every vertex (kept through the Mirror modifier), used by build_task3_face.py
# on-surface relax (the retopology "relax" pass): interior vertices move halfway to their neighbours' average and are
# re-projected onto the source; opening boundaries and midline (mirror-seam) vertices stay fixed - the midline
# vertices are already spaced by arc length along the midline curve, and relaxing them can collapse two of them in the
# throat / chin angle
RELAX_IT, RELAX_W = 8, 0.5
seam = {v for v in bm.verts if abs(v.co.x) < 1e-6}
fixed = {v for v in bm.verts if v.is_boundary} | seam
for v in seam:                                    # seam vertices that also lie on an opening stay fixed
    if any(e.is_boundary and not all(abs(w.co.x) < 1e-6 for w in e.verts) for e in v.link_edges):
        fixed.add(v)
for _ in range(RELAX_IT):
    new = {}
    for v in bm.verts:
        if v in fixed:
            continue
        nb = [e.other_vert(v) for e in v.link_edges]
        if v in seam:
            nb = [w for w in nb if w in seam]
            if len(nb) < 2:
                continue
        avg = sum((w.co for w in nb), Vector()) / len(nb)
        p_ = v.co.lerp(avg, RELAX_W)
        h = bvh.find_nearest(p_)[0]
        if h.x < 0.001:                          # never drift onto / across the mirror plane
            continue
        if h.x > X_CUT + 0.012 and 1.19 < h.z < 1.40:  # never let a torso vertex snap onto the arm
            continue
        new[v] = h
    for v, h in new.items():
        v.co = h
me = bpy.data.meshes.new("HGPT_Female_Shell"); bm.to_mesh(me); bm.free()
for v in me.vertices:
    if abs(v.co.x) < 1e-4:
        v.co.x = 0.0
ob = bpy.data.objects.new("HGPT_Female_Shell", me)
bpy.data.collections["BODY_PRODUCTION"].objects.link(ob)
mir = ob.modifiers.new("Manual_Symmetry", "MIRROR"); mir.use_clip = True; mir.use_mirror_merge = True; mir.merge_threshold = 0.0005
# the source is not mirror-symmetric (head centre 4-5.5 mm towards -x, wider on -x): as in the owner's scaffold, the
# mirrored half is projected onto the real left side of the source after the Mirror modifier
sw = ob.modifiers.new("Manual_Surface_Projection", "SHRINKWRAP"); sw.target = SRC; sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.0
DESIGN = {"segments_per_half_loop": NSEG, "rows": len(ROWS), "row_spec": [list(map(str, r)) for r in ROWS],
          "x_cut": X_CUT, "socket_rows_z": [round(row_z(ROWS[i]), 4) for i in SOCK_ROWS],
          "socket_edges_raw_deg": RAW_EDGES, "socket_edges_deg": [EDGE[i] for i in SOCK_ROWS],
          "face_edge_deg": FACE_EDGE_DEG, "face_rows": [I_JAW, I_BROW], "face_cols": [0, JFACE], "ear_rows": [I_EAR0, I_EAR1], "ear_deg": EAR_DEG, "jaw_border": JAW_BORDER, "skull_base_z": SKULL_BASE_Z,
          "crown_cap": CAP, "open_pelvis_z": OPEN_PELVIS_Z, "source": SRC.name, "head_centre": list(HEAD_C), "z_armpit": Z_ARMPIT}
ob["TASK3_SHELL_DESIGN"] = json.dumps(DESIGN)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bm = bmesh.new(); bm.from_mesh(me)
L = np.array([e.calc_length() for e in bm.edges])
if L.min() < 0.002:
    raise RuntimeError(f"collapsed edge: {L.min() * 1000:.2f} mm")
rep = {"out": str(OUT), "object": ob.name, "half_vertices": len(bm.verts), "half_faces": len(bm.faces),
       "non_quads": sum(len(f.verts) != 4 for f in bm.faces), "edge_length_mm_p5_median_p95": [round(float(np.percentile(L, q)) * 1000, 1) for q in (5, 50, 95)],
       "rows": len(ROWS), "columns": NSEG + 1, "jaw_border": JAW_BORDER, "skull_base_z": SKULL_BASE_Z,
       "head_centre": [round(c, 4) for c in HEAD_C], "socket_rows_z": DESIGN["socket_rows_z"], "socket_edges_deg": DESIGN["socket_edges_deg"]}
bm.free()
REP.write_text(json.dumps(rep, indent=1)); print("SHELL", json.dumps(rep))
