"""FEMALE pelvis, glutes, legs and feet from her shell's pelvis opening - designed loops, no auto-remesh.

Same method as the male (scripts/retopology/build_task5_legs.py: hip loops split at the midline with the opening's
column fractions, a midline crotch strip shared by both legs, measured leg centre lines with rounded knee / ankle
corners, rings perpendicular to the line, heel-sweep foot rings, toe loops and a Coons grid), with HER landmarks from
sections of her source:
  * pelvis opening 0.960 m (above her gluteal cleft); her body is one loop down to 0.800 m and two legs from 0.780 m
    (crotch ~0.79 m; the shorts' inseam hem is lower, ~0.70 m): hip loops every 2.2 cm from 0.938 to 0.806 m;
  * crotch strip vertices stay above 0.775 m;
  * knee = narrowest leg section at 0.38-0.54 m, ankle = narrowest at 0.09-0.20 m, upper-thigh centroid 0.72-0.775 m.

usage: python3.13 build_f_legs.py -- <in .blend (F03b)> <out NEW .blend> <report .json>
"""
import json
import math
import os
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
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]; body = bpy.data.objects["HGPT_Female_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); ST = np.array([tuple(p.vertices) for p in SRC.data.polygons])
bvh = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(t) for t in ST])
DIAG = bool(os.environ.get("LEG_DIAG"))
D = json.loads(body["TASK3_SHELL_DESIGN"]); NSEG = D["segments_per_half_loop"]; Z_OPEN = D["open_pelvis_z"]

HIP_Z = (0.938, 0.916, 0.894, 0.872, 0.850, 0.828, 0.806)  # hip loops below the opening (the last one just above the crotch)
CHAIN = 7                      # crotch strip edges (front midline -> back midline)
CHAIN_FLOOR = 0.775            # crotch strip vertices stay above this height (the shorts' seam hangs lower at y = 0)
NL = NSEG + CHAIN              # leg ring vertices (40)
TOP_GAP = 0.045                # first leg ring this far below the last hip loop (along the thigh line)
STEP = {"thigh": 0.025, "knee": 0.0175, "shank": 0.025, "ankle": 0.009, "foot": 0.018}
KNEE_R, ANKLE_R = 0.06, 0.085  # corner rounding (m of line on each side of the corner)
ANGLE_EVEN = 4                 # leg rings over which the crotch ring's vertex angles become even
MID_GUARD = 0.003              # inner-thigh vertices keep |x| >= this
CAP_W, CAP_H = 14, 6           # toe cap grid (2 * (14 + 6) = 40)
TOE_BASE = 0.74               # foot rings end at this fraction of the heel -> toe-tip length
TOE_RINGS = (0.88, 0.72, 0.52)      # concentric loops over the toes (scale of the last foot ring), then the grid


def toe_envelope(sg, base_ring):
    """closed toe envelope: her source forefoot ahead of the last foot ring, voxel-remeshed (4 mm)"""
    cl = np.mean(base_ring, axis=0)
    keep = [f for f in ST if all(SV[i, 2] < 0.07 and SV[i, 0] * sg > 0.05 and SV[i, 1] < cl[1] + 0.02 for i in f)]
    me_ = bpy.data.meshes.new("toe_env"); me_.from_pydata(SV.tolist(), [], [list(f) for f in keep]); me_.update()
    ob_ = bpy.data.objects.new("toe_env", me_); bpy.context.scene.collection.objects.link(ob_)
    rm = ob_.modifiers.new("R", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.004; rm.adaptivity = 0.0
    sm = ob_.modifiers.new("S", "SMOOTH"); sm.iterations = 2; sm.factor = 0.5
    dg = bpy.context.evaluated_depsgraph_get(); oe = ob_.evaluated_get(dg); m = oe.to_mesh()
    t = BVHTree.FromPolygons([v.co.copy() for v in m.vertices], [tuple(q.vertices) for q in m.polygons]); oe.to_mesh_clear()
    bpy.data.objects.remove(ob_); return t


def ray(o, d, dist=0.2):
    h = bvh.ray_cast(Vector(o), Vector(d), dist)
    return None if h[0] is None else np.array(h[0][:])


def unit(v):
    return v / np.linalg.norm(v)


def slice_loops(o, n, tris):
    d = (SV - o) @ n; s = d[tris] >= 0; m = ~(s.all(1) | (~s).all(1)); segs = {}; pts = {}
    for tri in tris[m]:
        e = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            ia, ib = tri[i], tri[j]
            if (d[ia] >= 0) != (d[ib] >= 0):
                k = (min(ia, ib), max(ia, ib)); pts[k] = SV[ia] + (SV[ib] - SV[ia]) * (d[ia] / (d[ia] - d[ib])); e.append(k)
        if len(e) == 2:
            segs.setdefault(e[0], []).append(e[1]); segs.setdefault(e[1], []).append(e[0])
    loops, seen = [], set()
    for st in segs:
        if st in seen:
            continue
        lp, prev, cur = [st], None, st; seen.add(st)
        while True:
            nx = [x for x in segs[cur] if x != prev and x not in seen]
            if not nx:
                break
            prev, cur = cur, nx[0]; seen.add(cur); lp.append(cur)
        if len(lp) >= 8:
            loops.append(np.array([pts[k] for k in lp]))
    return loops


def arc_points(P, fr):
    cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; cum /= cum[-1]
    return np.array([[np.interp(f, cum, P[:, k]) for k in range(3)] for f in fr])


tri_c = SV[ST].mean(1); BODY_T = ST[np.abs(tri_c[:, 0]) < 0.3]                 # excludes the hands beside the hips
me = body.data; bm = bmesh.new(); bm.from_mesh(me)
LR = bm.verts.layers.int["t3_row"]; LC = bm.verts.layers.int["t3_col"]
LP5 = bm.verts.layers.int.get("t5_part") or bm.verts.layers.int.new("t5_part")  # 1 hips, 2 crotch, 3 thigh, 4 knee, 5 shank, 6 ankle/heel, 7 foot, 8 toe cap
bm.verts.ensure_lookup_table(); old_verts = set(bm.verts)
rep = {"method": __doc__.split("usage")[0].strip(), "hip_z": HIP_Z}

# ---- the opening: right half cols 0..NSEG, left half cols 0..NSEG (cols 0 / NSEG are the shared midline vertices)
opn = [v for v in bm.verts if v.is_boundary and abs(v.co.z - Z_OPEN) < 0.01]
mid = {v[LC]: v for v in opn if abs(v.co.x) < 1e-5}
half = {sg: [mid[0]] + sorted([v for v in opn if v.co.x * sg > 1e-5], key=lambda v: v[LC]) + [mid[NSEG]] for sg in (1, -1)}
for sg in (1, -1):
    if len(half[sg]) != NSEG + 1:
        raise RuntimeError(f"pelvis opening half {sg}: {len(half[sg])} vertices")


def half_fracs(vs):
    P = np.array([v.co[:] for v in vs]); cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return cum / cum[-1]


FR = {sg: half_fracs(half[sg]) for sg in (1, -1)}


def midline_halves(z):
    """the body cut at height z, split at x = 0 into the right / left halves, each ordered front midline -> back"""
    lps = [p for p in slice_loops(np.array([0, 0, z]), np.array([0, 0, 1.0]), BODY_T)]
    Q = max(lps, key=lambda p: len(p)); Q = np.r_[Q, Q[:1]]
    cr = []
    for i in range(len(Q) - 1):
        if (Q[i, 0] >= 0) != (Q[i + 1, 0] >= 0):
            t = Q[i, 0] / (Q[i, 0] - Q[i + 1, 0]); cr.append((i, Q[i] + (Q[i + 1] - Q[i]) * t))
    if len(cr) != 2:
        raise RuntimeError(f"hip cut at z {z}: {len(cr)} midline crossings")
    (i0, p0), (i1, p1) = cr; A = np.r_[[p0], Q[i0 + 1:i1 + 1], [p1]]; B = np.r_[[p1], Q[i1 + 1:-1], Q[:i0 + 1], [p0]]
    out = {}
    for arc in (A, B):
        sg = 1 if arc[1:-1, 0].mean() > 0 else -1
        out[sg] = arc if arc[0, 1] < arc[-1, 1] else arc[::-1]
    return out


rows = [{sg: half[sg] for sg in (1, -1)}]
for z in HIP_Z:
    hh = midline_halves(z); row = {}
    pts = {sg: arc_points(hh[sg], FR[sg]) for sg in (1, -1)}
    m0 = bm.verts.new((pts[1][0] + pts[-1][0]) / 2); m1 = bm.verts.new((pts[1][-1] + pts[-1][-1]) / 2)
    for v in (m0, m1):
        v.co.x = 0.0
    for sg in (1, -1):
        row[sg] = [m0] + [bm.verts.new(p) for p in pts[sg][1:-1]] + [m1]
    for v in set(row[1] + row[-1]):
        v[LP5] = 1
    rows.append(row)
for r in range(len(rows) - 1):
    for sg in (1, -1):
        A_, B_ = rows[r][sg], rows[r + 1][sg]
        for c in range(NSEG):
            bm.faces.new([A_[c], A_[c + 1], B_[c + 1], B_[c]])
# ---- crotch strip in the midline plane
lastr = rows[-1]; F0 = np.array(lastr[1][0].co[:]); B0 = np.array(lastr[1][-1].co[:])
O = np.array([0.0, (F0[1] + B0[1]) / 2, HIP_Z[-1] + 0.02])
a0 = math.atan2(F0[2] - O[2], F0[1] - O[1]); a1 = math.atan2(B0[2] - O[2], B0[1] - O[1])
a0, a1 = (x - 2 * math.pi if x > math.pi / 2 else x for x in (a0, a1))   # sweep from the front through "down" to the back
chain = []
for k in range(1, CHAIN):
    an = a0 + (a1 - a0) * k / CHAIN; d = np.array([0.0, math.cos(an), math.sin(an)]); h = ray(O, d, 0.3)
    if h is None or h[2] < CHAIN_FLOOR:
        t = (CHAIN_FLOOR - O[2]) / d[2] if d[2] < -1e-6 else 0.1; h = O + d * t
    h[0] = 0.0; v = bm.verts.new(h); v[LP5] = 2; chain.append(v)
rep["crotch_strip_z"] = [round(v.co.z, 4) for v in chain]


# ---- legs
def measure_leg(sg):
    def cents(zlo, zhi, step=0.01):
        out = []
        for z in np.arange(zlo, zhi, step):
            lps = [p for p in slice_loops(np.array([0, 0, z]), np.array([0, 0, 1.0]), BODY_T) if p[:, 0].mean() * sg > 0.03]
            if lps:
                out.append(max(lps, key=len).mean(0))
        return np.array(out)

    def fit(P):
        m = P.mean(0); d = np.linalg.svd(P - m)[2][0]; return m, (d if d[2] < 0 else -d)
    # joints from the cross-sections: knee = the narrowest cut between thigh and calf, ankle = the narrowest cut above
    # the malleoli; the thigh line runs from the upper-thigh centroid to the knee, the shank line from knee to ankle
    def narrowest(zlo, zhi):
        best = None
        for z in np.arange(zlo, zhi, 0.005):
            lps = [p for p in slice_loops(np.array([0, 0, z]), np.array([0, 0, 1.0]), BODY_T) if p[:, 0].mean() * sg > 0.03]
            if lps:
                p = max(lps, key=len); per = float(np.linalg.norm(np.diff(np.r_[p, p[:1]], axis=0), axis=1).sum())
                if best is None or per < best[0]:
                    best = (per, p.mean(0))
        return best[1]
    K = narrowest(0.38, 0.54); Ak = narrowest(0.09, 0.20); Tu = cents(0.72, 0.775, 0.01).mean(0)
    mt, dt = K, unit(K - Tu); ms, ds = K, unit(Ak - K)
    # forefoot line: centroids of vertical cuts across the foot, in front of the shin
    foot = SV[(SV[:, 2] < 0.03) & (SV[:, 0] * sg > 0.1)]; fm = foot.mean(0)
    fd = np.linalg.svd(foot[:, :2] - fm[:2])[2][0]; fd = np.array([fd[0], fd[1], 0.0]); fd = fd if fd[1] < 0 else -fd
    ft = (foot - fm) @ fd; heel = fm + fd * ft.min(); toe = fm + fd * ft.max()
    FT = ST[(np.abs(tri_c[:, 0] - fm[0]) < 0.12) & (tri_c[:, 2] < 0.2)]
    fc = []
    for t in np.arange(0.04, 0.85, 0.05) * (ft.max() - ft.min()) + ft.min():
        o = fm + fd * (t - 0.0); o = np.array([o[0], o[1], 0.03])
        lps = [p for p in slice_loops(o, fd, FT) if np.abs(p[:, 0].mean() - o[0]) < 0.07 and p[:, 2].max() < 0.16]
        if lps:
            fc.append((t, max(lps, key=len).mean(0)))
    FC = np.array([c for _, c in fc]); fl_m, fl_d = FC.mean(0), np.linalg.svd(FC - FC.mean(0))[2][0]; fl_d = fl_d if fl_d @ fd > 0 else -fl_d
    # ankle corner: closest approach of the shank line and the forefoot line
    w0 = ms - fl_m; a_, b_, c_ = ds @ ds, ds @ fl_d, fl_d @ fl_d; d_, e_ = ds @ w0, fl_d @ w0
    den = a_ * c_ - b_ * b_; t1 = (b_ * e_ - c_ * d_) / den; t2 = (a_ * e_ - b_ * d_) / den
    A = ((ms + ds * t1) + (fl_m + fl_d * t2)) / 2
    tip = ray(FC[-1], fl_d, 0.2); tip = tip if tip is not None else toe
    return {"thigh": (mt, dt), "shank": (ms, ds), "knee": K, "ankle": A, "ankle_joint": Ak, "foot": (fl_m, fl_d), "toe_tip": tip, "heel": heel,
            "foot_centroids": FC}


def corner(P0, Pc, P1, n=24):
    """quadratic Bezier from P0 through the corner control Pc to P1"""
    t = np.linspace(0, 1, n)[:, None]; return (1 - t) ** 2 * P0 + 2 * t * (1 - t) * Pc + t ** 2 * P1


for sg in (1, -1):
    side = "right" if sg > 0 else "left"; M = measure_leg(sg)
    (mt, dt), (ms, ds), K, A, (fm, fdir) = M["thigh"], M["shank"], M["knee"], M["ankle"], M["foot"]
    top = mt + dt * ((HIP_Z[-1] - TOP_GAP - mt[2]) / dt[2])
    tip = M["toe_tip"]
    # the foot rings run to the toe bases (TOE_BASE of the heel -> toe-tip length: the source toes touch each other, so
    # they cannot be found as separate cuts); the toes are covered by the loops and grid of the toe cap
    heel = M["heel"]; flen = float((tip - heel) @ fdir); p_end = heel + fdir * (TOE_BASE * flen)
    end = fm + fdir * float((p_end - fm) @ fdir)
    # centre line: thigh line, knee corner, shank line, ankle corner, forefoot line
    kin, kout = K - dt * KNEE_R, K + ds * KNEE_R; ain, aout = A - ds * ANKLE_R, A + fdir * ANKLE_R
    C = np.r_[np.linspace(top, kin, 40)[:-1], corner(kin, K, kout)[:-1], np.linspace(kout, ain, 60)[:-1], corner(ain, A, aout)[:-1],
              np.linspace(aout, end, 60)]
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]
    s_kin = cum[39]; s_kout = cum[39 + 23]; s_ain = cum[39 + 23 + 59]; s_aout = cum[39 + 23 + 59 + 23]
    marks = [(0.0, "thigh"), (s_kin - 0.02, "knee"), (s_kout + 0.02, "shank"), (s_ain - 0.01, "ankle"), (s_aout + 0.01, "foot"), (cum[-1], None)]
    st = []
    for (s0, reg), (s1, _) in zip(marks[:-1], marks[1:]):
        n = max(1, int(round((s1 - s0) / STEP[reg]))); st += [(s0 + (s1 - s0) * i / n, reg) for i in range(n)]
    st.append((cum[-1], "foot"))
    at = lambda s: np.array([np.interp(s, cum, C[:, k]) for k in range(3)])
    tan = lambda s: unit(at(min(s + 0.003, cum[-1])) - at(max(s - 0.003, 0.0)))
    # crotch ring (40): this side's half of the last hip loop, front -> back, then the strip back -> front
    L0 = lastr[sg] + chain[::-1]
    P0 = np.array([v.co[:] for v in L0]); c0 = P0.mean(0)
    t0 = tan(0.0); e1 = np.array([0, -1.0, 0]); e1 = unit(e1 - (e1 @ t0) * t0); e2 = np.cross(t0, e1)
    ph = np.unwrap([math.atan2((p - c0) @ e2, (p - c0) @ e1) for p in P0]); sgn = 1 if ph[-1] > ph[0] else -1
    uni = np.array([sgn * 2 * math.pi * i / NL for i in range(NL)]); uni += np.mean(ph - uni)
    rings = [L0]; prev_t = t0; prev_r = [0.08] * NL; reg_of = []
    for k, (s, reg) in enumerate(st):
        t = tan(s); e1 = unit(e1 - (e1 @ t) * t); e2 = np.cross(t, e1)        # parallel transport of the frame
        c = at(s); b = min(1.0, (k + 1) / ANGLE_EVEN); ang = ph * (1 - b) + uni * b; rg = []
        for q in range(NL):
            d = math.cos(ang[q]) * e1 + math.sin(ang[q]) * e2; h = ray(c, d, 0.2)
            p = h if h is not None else c + d * prev_r[q]
            if p[0] * sg < MID_GUARD:                                          # never across the midline
                tt_ = (MID_GUARD * sg - c[0]) / d[0] if abs(d[0]) > 1e-6 else 0.0; p = c + d * max(tt_, 0.0)
            prev_r[q] = float(np.linalg.norm(p - c)); rg.append(p)
        rings.append(rg); reg_of.append(reg)
    # toe cap: concentric loops over the toes, then a Coons grid; all projected forward along the foot axis
    tdir = tip - M["heel"]; tdir = unit(np.array([tdir[0], tdir[1], 0.0]))   # the toes lie flat and point heel -> tip
    cl = np.mean(rings[-1], axis=0); base_ring = list(rings[-1])
    # FEMALE: her toes are separate (the male's touched): rays along the foot axis ran into the gaps between them and
    # the cap crumpled. The cap is projected (forward rays, as the male) onto a closed TOE ENVELOPE: her forefoot
    # (source, z < 0.07 m, ahead of the last foot ring) voxel-remeshed at 4 mm, which fills the narrow gaps between the
    # toes. Individual toes are therefore not separated in the geometry (left to the colour / normal detail).
    env_b = toe_envelope(sg, base_ring)

    def fwd(p):
        h = env_b.ray_cast(Vector(p - tdir * 0.04), Vector(tdir), 0.12)
        return np.array(h[0][:]) if h[0] is not None else p
    for f_ in TOE_RINGS:
        rings.append([fwd(cl + (p - cl) * f_) for p in base_ring])
        reg_of.append("toes")
    i0 = int(np.argmin(np.abs(((uni + math.pi) % (2 * math.pi)) - math.pi)))   # the vertex at angle 0 (top of the foot)
    order = [(i0 - CAP_W // 2 + j) % NL for j in range(NL)]                       # top side starts here
    last = rings[-1]; Pl = np.array([last[i] for i in order])
    Bt = Pl[0:CAP_W + 1]; Rt = Pl[CAP_W:CAP_W + CAP_H + 1]; Bb = Pl[CAP_W + CAP_H:2 * CAP_W + CAP_H + 1][::-1]
    Lt = np.r_[Pl[2 * CAP_W + CAP_H:], Pl[:1]][::-1]
    grid = {}
    for i in range(1, CAP_H):
        for j in range(1, CAP_W):
            u, w = j / CAP_W, i / CAP_H
            p = ((1 - w) * Bt[j] + w * Bb[j] + (1 - u) * Lt[i] + u * Rt[i]
                 - ((1 - u) * (1 - w) * Bt[0] + u * (1 - w) * Bt[-1] + (1 - u) * w * Bb[0] + u * w * Bb[-1]))
            grid[i, j] = fwd(p)
    # ---- build
    vrings = [L0]
    for rg, reg in zip(rings[1:], reg_of):
        vr = [bm.verts.new(p) for p in rg]
        for v in vr:
            v[LP5] = {"thigh": 3, "knee": 4, "shank": 5, "ankle": 6, "foot": 7, "toes": 8}[reg]
        vrings.append(vr)
    for r in range(len(vrings) - 1):
        for q in range(NL):
            bm.faces.new([vrings[r][q], vrings[r][(q + 1) % NL], vrings[r + 1][(q + 1) % NL], vrings[r + 1][q]])
    LV = vrings[-1]; G = {}
    for j in range(CAP_W + 1):
        G[0, j] = LV[order[j]]; G[CAP_H, j] = LV[order[(2 * CAP_W + CAP_H - j) % NL]]
    for i in range(CAP_H + 1):
        G[i, CAP_W] = LV[order[CAP_W + i]]; G[i, 0] = LV[order[(NL - i) % NL]]
    for (i, j), p in grid.items():
        G[i, j] = bm.verts.new(p); G[i, j][LP5] = 8
    for i in range(CAP_H):
        for j in range(CAP_W):
            bm.faces.new([G[i, j], G[i, j + 1], G[i + 1, j + 1], G[i + 1, j]])
    rep[side] = {"knee": K.round(4).tolist(), "ankle_joint_level": M["ankle_joint"].round(4).tolist(), "ankle_corner": A.round(4).tolist(), "toe_tip": np.round(tip, 4).tolist(),
                 "heel": M["heel"].round(4).tolist(), "thigh_dir": dt.round(3).tolist(), "shank_dir": ds.round(3).tolist(),
                 "foot_dir": fdir.round(3).tolist(), "centre_line_m": round(float(cum[-1]), 3), "leg_rings": len(vrings) - 1,
                 "rings_by_region": {r: reg_of.count(r) for r in list(STEP) + ["toes"]}, "foot_rings_end_before_tip_mm": round(1000 * float((tip - end) @ fdir), 1)}
    if DIAG:
        print("LEG", side, json.dumps(rep[side]))

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
new = [v for v in bm.verts if v not in old_verts]
el = [e.calc_length() for e in bm.edges if any(v not in old_verts for v in e.verts)]
bm.to_mesh(me); me.update()
body["TASK5_LEGS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep.update({"out": str(OUT), "faces": len(bm.faces), "non_quads": sum(len(f.verts) != 4 for f in bm.faces),
            "boundary_edges": sum(e.is_boundary for e in bm.edges), "new_vertices": len(new),
            "edge_mm_min_p5_p50_p95": [round(1000 * float(x), 2) for x in (min(el), *np.percentile(el, [5, 50, 95]))]})
REP.write_text(json.dumps(rep, indent=1)); print("LEGS", json.dumps({k: v for k, v in rep.items() if k != "method"}))
