"""Task 3 (head / neck / torso) production shell for the Home Gym PT Meshy male: designed quad layout, no auto-remesh.

The layout below is the design record. It follows the owner's Task-3 scaffold (HGPT_Male_Body_WIP): half body with
a Mirror modifier, planned openings for the arm socket, face, ear and pelvis.  Every loop is placed explicitly:

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

Source surface: the geometry proxy HGPT_SOURCE_PROXY_Mesh_0 until the real source is restored.  The input checkpoint is
opened and saved under a NEW name; the scaffold object is left unchanged.

usage: python3.13 build_task3_shell.py -- <in checkpoint .blend> <out NEW .blend> <report .json>
"""
import json
import math
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
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); ST = [tuple(p.vertices) for p in SRC.data.polygons]
bvh = BVHTree.FromPolygons([tuple(v) for v in SV], ST)

# ================================================================ design record
NSEG = 33                                     # segments per half loop (odd: the crown grid uses 8 + 17 + 8)
COL_STEP = 180.0 / NSEG
THETAS = [round(i * COL_STEP, 4) for i in range(NSEG + 1)]
JF, JB = 11, 22                               # arm-socket edge columns (front / back)
JFACE = 10                                    # face-opening edge column (cheekbone)
JE0, JE1 = 15, 21                             # ear-opening edge columns
X_CUT = 0.19                                  # arm-root line (m from the midline)
SOCK_FADE = 0.06
OPEN_PELVIS_Z = 0.915                         # above the gluteal cleft; pelvis / glutes = Task 5
FACE_EDGE_DEG = JFACE * COL_STEP              # 54.5 deg
EAR_DEG = (80.0, 116.0)
# jaw border measured on the source (theta deg -> z m), where horizontal rays jump from the neck onto the jaw
JAW_BORDER = [(0, 1.578), (10, 1.580), (20, 1.582), (30, 1.586), (40, 1.590), (50, 1.592), (60, 1.598), (70, 1.598), (80, 1.602)]
JAW_ABOVE = 0.003                             # the loop sits just above the jump (on the jaw / face side)
SKULL_BASE_Z = 1.588                          # behind the ear the loop runs to the base of the skull (back: 1.572 step)
HEAD_C = Vector((0.0, -0.004, 1.70))
CAP = {"rows_front_back": 17, "half_columns": 8}

torso = [("h", z) for z in np.round(np.arange(0.915, 1.2151, 0.025), 4)]          # 2.5 cm
sock = [("h", z) for z in np.round(np.arange(1.228, 1.4921, 0.012), 4)]           # armpit .. acromion, 1.2 cm
TRAP_LO, TRAP_HI = ("h", 1.492), ("h", 1.552)
trap = [("m", (TRAP_LO, TRAP_HI, i / 8, 1.44)) for i in range(1, 9)]              # trapezius: 8 loops
NECK_HI = ("jl",)
neck = [("m", (TRAP_HI, NECK_HI, i / 5, 1.50)) for i in range(1, 6)]               # neck + underside of jaw: 5 loops
JAW_ROW = neck[-1]                                                                 # t = 1: the jaw loop itself
# head: ~8 mm loops from the jaw to the forehead (the face is filled inside these by build_task3_face.py)
HEAD_Z = [1.610, 1.618, 1.626, 1.634, 1.641, 1.649, 1.657, 1.665, 1.673, 1.681, 1.689, 1.697, 1.705, 1.713, 1.722]
head = [("m", (NECK_HI, ("h", HEAD_Z[0]), 0.5, 1.55))] + [("h", z) for z in HEAD_Z]
EAR_LO, EAR_HI = ("h", 1.641), ("h", 1.713)                                        # ear-opening bounds
cranium = [("s", e) for e in (20, 27, 34, 42)]
FACE_TOP = ("s", 27)                                                               # forehead, ~1.743 m
ROWS = torso + sock + trap + neck + head + cranium
I_JAW = ROWS.index(JAW_ROW); I_BROW = ROWS.index(FACE_TOP)
I_EAR0 = ROWS.index(EAR_LO); I_EAR1 = ROWS.index(EAR_HI)


def centre_y(z):
    s = SV[(np.abs(SV[:, 2] - z) < 0.004) & (np.abs(SV[:, 0]) < 0.06)]
    return float(0.5 * (s[:, 1].min() + s[:, 1].max())) if len(s) > 5 else 0.0


def hray(z, th):
    t = math.radians(th); h = bvh.ray_cast(Vector((0.0, centre_y(z), z)), Vector((math.sin(t), -math.cos(t), 0.0)))[0]
    if h is None:
        raise RuntimeError(f"no surface at z {z} theta {th}")
    return h


def jaw_z(th):
    if th <= 80:
        return float(np.interp(th, [p[0] for p in JAW_BORDER], [p[1] for p in JAW_BORDER])) + JAW_ABOVE
    w = min((th - 80) / 40.0, 1.0); w = w * w * (3 - 2 * w)
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
CAND = [i for i, r in enumerate(ROWS) if r[0] in ("h", "m") and 1.20 < row_z(r) < 1.56]
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
import os  # noqa: E402
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
        if h.x > X_CUT + 0.012 and 1.2 < h.z < 1.56:   # never let a torso vertex snap onto the arm
            continue
        new[v] = h
    for v, h in new.items():
        v.co = h
me = bpy.data.meshes.new("HGPT_Male_Task3_Shell"); bm.to_mesh(me); bm.free()
for v in me.vertices:
    if abs(v.co.x) < 1e-4:
        v.co.x = 0.0
ob = bpy.data.objects.new("HGPT_Male_Task3_Shell", me)
bpy.data.collections["BODY_PRODUCTION"].objects.link(ob)
mir = ob.modifiers.new("Manual_Symmetry", "MIRROR"); mir.use_clip = True; mir.use_mirror_merge = True; mir.merge_threshold = 0.0005
# the source is not mirror-symmetric (head centre 4-5.5 mm towards -x, wider on -x): as in the owner's scaffold, the
# mirrored half is projected onto the real left side of the source after the Mirror modifier
sw = ob.modifiers.new("Manual_Surface_Projection", "SHRINKWRAP"); sw.target = SRC; sw.wrap_method = "NEAREST_SURFACEPOINT"; sw.offset = 0.0
DESIGN = {"segments_per_half_loop": NSEG, "rows": len(ROWS), "row_spec": [list(map(str, r)) for r in ROWS],
          "x_cut": X_CUT, "socket_rows_z": [round(row_z(ROWS[i]), 4) for i in SOCK_ROWS],
          "socket_edges_raw_deg": RAW_EDGES, "socket_edges_deg": [EDGE[i] for i in SOCK_ROWS],
          "face_edge_deg": FACE_EDGE_DEG, "face_rows": [I_JAW, I_BROW], "face_cols": [0, JFACE], "ear_rows": [I_EAR0, I_EAR1], "ear_deg": EAR_DEG, "jaw_border": JAW_BORDER, "skull_base_z": SKULL_BASE_Z,
          "crown_cap": CAP, "open_pelvis_z": OPEN_PELVIS_Z, "source": SRC.name, "source_is_geometry_proxy": True}
ob["TASK3_SHELL_DESIGN"] = json.dumps(DESIGN); ob["PROXY_SOURCE_ONLY"] = True
bpy.data.objects["HGPT_Male_Body_WIP"].hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
bm = bmesh.new(); bm.from_mesh(me)
L = np.array([e.calc_length() for e in bm.edges])
if L.min() < 0.002:
    raise RuntimeError(f"collapsed edge: {L.min() * 1000:.2f} mm")
rep = {"out": str(OUT), "object": ob.name, "half_vertices": len(bm.verts), "half_faces": len(bm.faces),
       "non_quads": sum(len(f.verts) != 4 for f in bm.faces), "edge_length_mm_p5_median_p95": [round(float(np.percentile(L, q)) * 1000, 1) for q in (5, 50, 95)],
       "rows": len(ROWS), "columns": NSEG + 1}
bm.free()
REP.write_text(json.dumps(rep, indent=1)); print("SHELL", json.dumps(rep))
