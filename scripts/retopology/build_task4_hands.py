"""Task 4 (part 2): hands and fingers on the open 32-vertex wrist rings - designed loops, no auto-remesh.

Per side (each hand measured on its own; the source is not mirror-symmetric):
  * HAND FRAME: principal axes of the source hand beyond the wrist ring: L (wrist -> fingertips), Wd (across the
    knuckles, oriented so the thumb is on the -Wd side), N (dorsal, the thumb lies on the palmar -N side).
  * FINGERS: the source fingers touch along their length (the Meshy surface fuses them), so each finger's centre line is
    traced from the THICKNESS RIDGES of the hand (dorsal ray hit to palmar exit, sampled across the hand) and the
    grooves between ridges are the separating planes. Each finger is an 8-vertex tube (4 dorsal, 4 palmar), with three
    loops at each of the PIP and DIP joints and a 3-quad fingertip cap; side vertices stop just short of the groove
    plane so neighbouring fingers stay separate surfaces.
  * PALM: 32-vertex rings from the wrist ring to the knuckle ring. The knuckle ring is made of the fingers' base rings
    (16 dorsal + 16 palmar vertices, with one web quad between neighbouring fingers). Intermediate rings are cuts of the
    source between the wrist plane and the knuckle plane; their vertices are placed by arc length around the whole cut
    (from its radial extreme, dorsal side first), blending the wrist ring's spacing into the knuckle ring's.
  * THUMB: an 8-edge opening (a 2 x 2 block of palm quads, the vertex nearest the thumb axis removed) on the
    thenar side, between the palm rings at the thumb's base; the thumb tube follows the measured thumb axis (slice
    centroids), loops at the MCP and IP joints, 3-quad tip cap.

usage: python3.13 build_task4_hands.py -- <in .blend (04a)> <out NEW .blend> <report .json>
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
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); ST = np.array([tuple(p.vertices) for p in SRC.data.polygons])
bvh = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(t) for t in ST])
DIAG = bool(os.environ.get("HAND_DIAG"))

FINGER_F = (0.0, 0.14, 0.28, 0.36, 0.42, 0.48, 0.60, 0.67, 0.72, 0.77, 0.86, 0.93)   # finger loops, web -> tip
THUMB_F = (0.0, 0.16, 0.30, 0.40, 0.48, 0.56, 0.70, 0.82, 0.92)                       # thumb loops, crotch -> tip
F_TH = (-67.5, -22.5, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5)   # finger ring angles from dorsal (N) towards ulnar (+Wd)
CLIP_BASE, CLIP = 0.72, 0.90  # fraction of the distance to the groove plane a side vertex may reach (base ring, rest)
PALM_STEP = 0.016             # max palm ring spacing (m)
WRIST_BLEND_U = 0.3          # palm cut planes turn from the wrist-ring plane to perpendicular-to-L over this fraction
OUTER_CAP = 1.25             # outer side of the index / little finger: radius cap relative to the inner side
THUMB_ROOT_B = (0.35, 0.68)  # loops between the thenar opening and the first thumb loop (blend fractions)
CAP_PULL = 0.62               # tip cap ring: this far from the last loop towards the tip point, then on the surface


def slice_loops(o, n, tris):
    """closed polylines where the plane (o, n) cuts the triangles `tris` of the source"""
    d = (SV - o) @ n; dt = d[tris]; s = dt >= 0
    m = ~(s.all(1) | (~s).all(1)); segs = {}; pts = {}
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
        if len(lp) >= 6:
            loops.append(np.array([pts[k] for k in lp]))
    return loops


def perim(p):
    return float(np.linalg.norm(np.diff(np.r_[p, p[:1]], axis=0), axis=1).sum())


def arc_points(P, fr):
    """points at arc-length fractions `fr` along the open polyline P"""
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]; cum /= cum[-1]
    return np.array([np.interp(f, cum, P[:, k]) for k in range(3) for f in fr]).reshape(3, -1).T


def ray(o, d, dist=0.04):
    h = bvh.ray_cast(Vector(o), Vector(d), dist)
    return None if h[0] is None else np.array(h[0][:])


def snap(p):
    return np.array(bvh.find_nearest(Vector(p))[0][:])


def unit(v):
    return v / np.linalg.norm(v)


me = body.data; bm = bmesh.new(); bm.from_mesh(me)
LP = bm.verts.layers.int.get("t4_part") or bm.verts.layers.int.new("t4_part")   # 1 palm, 10+f finger f, 20 thumb root, 21 thumb
bm.verts.ensure_lookup_table()
rep = {"method": __doc__.split("usage")[0].strip(), "sides": {}}
old_verts = set(bm.verts)


def boundary_loop(sg):
    vs = {v for v in bm.verts if v.is_boundary and v.co.x * sg > 0.3}
    st = next(iter(vs)); lp = [st]; prev = None
    while True:
        nx = [e.other_vert(lp[-1]) for e in lp[-1].link_edges if e.is_boundary and e.other_vert(lp[-1]) in vs and e.other_vert(lp[-1]) is not prev]
        nx = [x for x in nx if x is not lp[0] or len(lp) < 3]
        if not nx or nx[0] is lp[0]:
            break
        prev = lp[-1]; lp.append(nx[0])
    if len(lp) != len(vs):
        raise RuntimeError(f"wrist loop walk {len(lp)} of {len(vs)}")
    return lp


for sg in (1.0, -1.0):
    side = "right" if sg > 0 else "left"; R = {}
    WR = boundary_loop(sg); WP = np.array([v.co[:] for v in WR]); Wc = WP.mean(0)
    if len(WR) != 32:
        raise RuntimeError(f"{side} wrist ring has {len(WR)} vertices")
    nw = np.linalg.svd(WP - Wc)[2][2]
    # source hand: beyond the wrist plane, near the wrist
    near = (np.linalg.norm(SV - Wc, axis=1) < 0.26) & (SV[:, 0] * sg > 0.33)
    hand_dir = SV[near & (SV[:, 2] < Wc[2] - 0.03)].mean(0) - Wc; nw = nw if nw @ hand_dir > 0 else -nw
    H = SV[near & ((SV - Wc) @ nw > 0.0)]
    U = np.linalg.svd(H - H.mean(0), full_matrices=False)[2]
    L = U[0] * np.sign(U[0] @ nw); Wd = unit(U[1] - (U[1] @ L) * L); N = np.cross(L, Wd)
    tri_c = SV[ST].mean(1); HT = ST[(np.linalg.norm(tri_c - Wc, axis=1) < 0.27) & (tri_c[:, 0] * sg > 0.33)]
    hand_len = float(((H - Wc) @ L).max())
    loc = lambda p: np.array([(p - Wc) @ L, (p - Wc) @ Wd, (p - Wc) @ N])
    # thumb side: the small separate loop of the L-slices beyond the thumb crotch
    th_c = []
    for s in np.arange(0.25, 0.60, 0.02) * hand_len:
        lps = sorted(slice_loops(Wc + L * s, L, HT), key=perim)
        if len(lps) >= 2 and perim(lps[-1]) > 2.0 * perim(lps[-2]) and perim(lps[-2]) > 0.05:
            th_c.append((s, lps[-2].mean(0)))
    if not th_c:
        raise RuntimeError(f"{side}: thumb not found")
    if loc(th_c[0][1])[1] > 0:
        Wd = -Wd; N = np.cross(L, Wd)
    if loc(th_c[0][1])[2] > 0:
        N = -N
    s_crotch = th_c[0][0]
    R.update(hand_length=round(hand_len, 4), L=L.round(4).tolist(), Wd=Wd.round(4).tolist(), N=N.round(4).tolist(), thumb_crotch_s=round(s_crotch, 4))

    # ---- thickness map (dorsal hit, palmar exit from inside) and finger ridges
    S_ = np.arange(0.45, 1.0, 0.0125) * hand_len; W_ = np.arange(-0.16, 0.12, 0.0015)
    TH = np.zeros((len(S_), len(W_))); NM = np.zeros_like(TH)
    for i, s in enumerate(S_):
        for j, w in enumerate(W_):
            p = Wc + L * s + Wd * w; hd = ray(p + N * 0.08, -N, 0.16)
            if hd is None:
                continue
            hp = ray(hd - N * 0.0004, -N, 0.08)
            if hp is None:
                continue
            TH[i, j] = (hd - hp) @ N; NM[i, j] = ((hd + hp) / 2 - Wc) @ N
    gk = np.exp(-0.5 * (np.arange(-5, 6) / 2.0) ** 2); gk /= gk.sum()       # 3 mm gaussian across the hand
    THs = np.array([np.convolve(r, gk, mode="same") for r in TH]); THs[TH <= 0] = 0

    def ridges(i):
        """finger ridges of row i: local maxima whose groove to each neighbour ridge is at least RIDGE_PROM deep"""
        r = THs[i]; pk = [j for j in range(3, len(r) - 3) if r[j] > 0.008 and r[j] >= r[j - 3:j + 4].max()]
        merged = True
        while merged and len(pk) > 1:
            merged = False
            for k in range(len(pk) - 1):
                j0, j1 = pk[k], pk[k + 1]; v = r[j0:j1 + 1].min()
                if min(r[j0], r[j1]) - v < 0.0015 or W_[j1] - W_[j0] < 0.011:
                    pk.pop(k + 1 if r[j0] >= r[j1] else k); merged = True; break
        return pk

    four = [i for i in range(len(S_)) if 0.60 * hand_len <= S_[i] <= 0.85 * hand_len and len(ridges(i)) == 4]
    if not four:
        raise RuntimeError(f"{side}: no slice with four finger ridges")
    i_ref = four[len(four) // 2]
    tracks = [[(i_ref, j)] for j in ridges(i_ref)]
    for tr in tracks:
        for direction in (1, -1):
            i, j = tr[0] if direction < 0 else tr[-1]
            while 0 <= i + direction < len(S_):
                rr = ridges(i + direction)
                near_r = [k for k in rr if abs(W_[k] - W_[j]) < 0.005]
                if not near_r or (direction < 0 and S_[i + direction] < S_[i_ref] - 0.06):
                    break
                i, j = i + direction, min(near_r, key=lambda k: abs(W_[k] - W_[j]))
                (tr.append if direction > 0 else lambda x: tr.insert(0, x))((i, j))
    fingers = []
    for f, tr in enumerate(tracks):
        s_ = np.array([S_[i] for i, _ in tr]); w_ = np.array([W_[j] for _, j in tr]); n_ = np.array([NM[i, j] for i, j in tr])
        deg = 2 if len(tr) >= 5 else 1
        cw, cn = np.polyfit(s_, w_, deg), np.polyfit(s_, n_, deg)
        fingers.append({"s_lo": s_.min(), "s_hi": s_.max(), "cw": cw, "cn": cn})
    P_at = lambda F, s: Wc + L * s + Wd * np.polyval(F["cw"], s) + N * np.polyval(F["cn"], s)
    # web (palmar): going down from the reference slice, where the groove between two neighbours fades out
    webs = []
    for f in range(3):
        s_web = S_[i_ref] - 0.03
        for i in range(i_ref, -1, -1):
            j0, j1 = [int(np.argmin(abs(W_ - np.polyval(fingers[k]["cw"], S_[i])))) for k in (f, f + 1)]
            if j1 - j0 < 3:
                break
            v = THs[i, j0:j1 + 1].min(); rmin = min(THs[i, j0], THs[i, j1])
            if rmin <= 0 or v / rmin > 0.93:
                s_web = S_[i]; break
        webs.append(float(s_web))
    for f, F in enumerate(fingers):
        nb = [webs[k] for k in (f - 1, f) if 0 <= k < 3]
        F["s_base"] = max(nb)                                  # the finger starts at its higher web
        e = P_at(F, F["s_hi"]); t = unit(P_at(F, F["s_hi"]) - P_at(F, F["s_hi"] - 0.005))
        tip = ray(e, t, 0.04); F["tip"] = tip if tip is not None else e + t * 0.008
        F["s_tip"] = F["s_hi"] + float((F["tip"] - e) @ L)
    if DIAG:
        for f, F in enumerate(fingers):
            print("FINGER", side, f, "s", round(F["s_base"], 4), round(F["s_lo"], 4), round(F["s_hi"], 4), round(F["s_tip"], 4),
                  "w@base", round(float(np.polyval(F["cw"], F["s_base"])), 4))
        print("WEBS", side, [round(w, 4) for w in webs], "i_ref s", round(S_[i_ref], 4))

    def w_of(F, s):
        return float(np.polyval(F["cw"], min(max(s, F["s_lo"] - 0.03), F["s_hi"])))

    def frame_at(F, s):
        s1 = min(max(s, F["s_lo"]), F["s_hi"]); c = P_at(F, s1)       # straight extension outside the traced range
        t = unit(P_at(F, s1 + 0.002) - P_at(F, s1 - 0.002)); n_ = unit(N - (N @ t) * t); w_ = unit(Wd - (Wd @ t) * t - (Wd @ n_) * n_)
        return c + t * (s - s1) / max(t @ L, 0.3), t, n_, w_

    finger_rings = []
    for f, F in enumerate(fingers):
        rings = []; prev_r = [0.008] * 8
        for k, fr in enumerate(FINGER_F):
            s = F["s_base"] + fr * (F["s_tip"] - F["s_base"]); c, t, n_, w_ = frame_at(F, s)
            clip = CLIP_BASE if k == 0 else CLIP; ring = []
            for q, th in enumerate(F_TH):
                d = math.cos(math.radians(th)) * n_ + math.sin(math.radians(th)) * w_
                h = ray(c, d, 0.03); r = float((h - c) @ d) if h is not None else prev_r[q]
                sn = math.sin(math.radians(th)); nbf = f + 1 if sn > 0 else f - 1
                if abs(sn) > 0.3:
                    if 0 <= nbf < 4:
                        dv = abs(0.5 * (w_of(fingers[nbf], s) - w_of(F, s)))
                    else:                                  # outer side of the index / little finger: no neighbour;
                        oth = fingers[f + 1 if f == 0 else f - 1]   # cap at OUTER_CAP x the inner half-spacing
                        dv = OUTER_CAP * abs(0.5 * (w_of(oth, s) - w_of(F, s)))
                    r = min(r, clip * dv / abs(sn))
                prev_r[q] = r; ring.append(c + d * r)
            rings.append(ring)
        c9 = np.mean(rings[-1], axis=0); cc = c9 + (F["tip"] - c9) * CAP_PULL
        rings.append([snap(cc + (p - c9) * 0.62) for p in rings[-1]])
        finger_rings.append(rings)
    # ---- knuckle ring: dorsal d0..d3 radial -> ulnar, then palmar ulnar -> radial
    KN = [p for fr_ in finger_rings for p in fr_[0][:4]] + [p for fr_ in finger_rings[::-1] for p in fr_[0][4:]]
    KNv = [None] * 32
    KP = np.array(KN); Kc = KP.mean(0); nk = np.linalg.svd(KP - Kc)[2][2]; nk = nk if nk @ L > 0 else -nk

    # ---- wrist ring in the 16 dorsal + 16 palmar layout (vertex 0 = dorsal, next to the radial side edge)
    lw = [loc(p) for p in WP]; mids = [(lw[i][1] + lw[(i + 1) % 32][1]) / 2 for i in range(32)]
    e0 = int(np.argmin(mids)); i0, i1 = e0, (e0 + 1) % 32
    if lw[i0][2] >= lw[i1][2]:
        order = [(i0 - k) % 32 for k in range(32)]
    else:
        order = [(i1 + k) % 32 for k in range(32)]
    WRo = [WR[k] for k in order]; WPo = WP[order]
    ulnar_mid = (loc(WPo[15]) + loc(WPo[16])) / 2; R["wrist_ulnar_side_w"] = round(float(ulnar_mid[1]), 4)
    R["wrist_split_check"] = "ok" if ulnar_mid[1] > 0 else "ulnar side edge not on the ulnar side"

    def fractions(P):
        """arc-length fractions of the 32 ring vertices around the whole ring, from the middle of the radial side edge"""
        a0 = (P[31] + P[0]) / 2; Q = np.r_[[a0], P, [a0]]
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
        return cum[1:-1] / cum[-1]

    fw, fk = fractions(WPo), fractions(KP)
    # ---- palm stations (planes blending the wrist plane into the knuckle plane); the thumb opening spans 3 of them
    s_k = float((Kc - Wc) @ L); hole_s = [s_crotch - 0.05, s_crotch - 0.025, s_crotch]
    st_s = list(np.linspace(0, hole_s[0], max(2, int(math.ceil(hole_s[0] / PALM_STEP)) + 1))[1:]) + hole_s[1:]
    n_tail = max(1, int(math.ceil((s_k - s_crotch) / PALM_STEP)))
    st_s += list(np.linspace(s_crotch, s_k, n_tail + 1)[1:-1])
    hole_rows = [st_s.index(hole_s[0]) + 1, st_s.index(hole_s[1]) + 1, st_s.index(hole_s[2]) + 1]   # +1: row 0 = wrist
    rings = [list(WRo)]
    for s in st_s:
        u = s / s_k; O = Wc + (Kc - Wc) * u; nrm = unit(nw * (1 - min(1.0, u / WRIST_BLEND_U)) + L * min(1.0, u / WRIST_BLEND_U))
        lps = [p for p in slice_loops(O, nrm, HT) if np.linalg.norm(p.mean(0) - O) < 0.06]
        Q = max(lps, key=perim); wq = (Q - O) @ Wd; imin = int(np.argmin(wq))
        Q = np.r_[Q[imin:], Q[:imin]]                     # start at the radial extreme, run dorsal first
        if (Q[1:len(Q) // 4] - O).mean(0) @ N < (Q[-len(Q) // 4:] - O).mean(0) @ N:
            Q = np.r_[Q[:1], Q[1:][::-1]]
        fr = fw * (1 - u) + fk * u
        rings.append([bm.verts.new(p) for p in arc_points(np.r_[Q, Q[:1]], fr)])
        for v in rings[-1]:
            v[LP] = 1
        if DIAG:
            rs = np.array([(np.array(v.co[:]) - Wc) @ L for v in rings[-1]])
            print("PALM", side, "s %.3f u %.2f" % (s, u), "ring s %.3f..%.3f" % (rs.min(), rs.max()), "loops", len(lps), "perim %.0f" % (1000 * perim(Q)))
    rings.append([bm.verts.new(p) for p in KP])
    # thumb opening: at the middle hole row, the vertex nearest the thumb axis
    TC = np.array([c for _, c in th_c]); td = np.linalg.svd(TC - TC.mean(0))[2][0]
    td = td if td @ (TC[-1] - TC[0]) > 0 else -td
    def line_d(p):
        v = p - TC[0]; return float(np.linalg.norm(v - (v @ td) * td))
    # ---- thumb: centre line by slices perpendicular to the thumb axis
    tau0 = 0.0; cents = []
    for tau in np.arange(0.0, 0.09, 0.005):
        o = TC[0] + td * tau; lps = [p for p in slice_loops(o, td, HT) if perim(p) < 0.14 and np.linalg.norm(p.mean(0) - o) < 0.02]
        if not lps:
            if cents:
                break
            continue
        cents.append(min(lps, key=lambda p: np.linalg.norm(p.mean(0) - o)).mean(0))
    C = np.array(cents); m = C.mean(0); td2 = np.linalg.svd(C - m)[2][0]; td2 = td2 if td2 @ td > 0 else -td2
    t_c = (C - m) @ td2; c_start = m + td2 * t_c.min(); c_end = m + td2 * t_c.max()
    tipT = ray(c_end, td2, 0.04); tipT = tipT if tipT is not None else c_end + td2 * 0.008
    def hole_off(k):                                   # distance of the opening's centre from the thumb axis
        P8 = np.array([rings[r][(k + dk) % 32].co[:] for r in hole_rows for dk in (-1, 0, 1)])
        v = P8.mean(0) - m; return float(np.linalg.norm(v - (v @ td2) * td2))
    rm = hole_rows[1]; kx = min(range(32), key=hole_off)
    hole_faces = {(hole_rows[0], (kx - 1) % 32), (hole_rows[0], kx), (rm, (kx - 1) % 32), (rm, kx)}
    for r in range(len(rings) - 1):
        for k in range(32):
            if (r, k) in hole_faces:
                continue
            bm.faces.new([rings[r][k], rings[r][(k + 1) % 32], rings[r + 1][(k + 1) % 32], rings[r + 1][k]])
    bm.verts.remove(rings[rm][kx])
    hole = [rings[hole_rows[0]][(kx - 1) % 32], rings[hole_rows[0]][kx], rings[hole_rows[0]][(kx + 1) % 32], rings[rm][(kx + 1) % 32],
            rings[hole_rows[2]][(kx + 1) % 32], rings[hole_rows[2]][kx], rings[hole_rows[2]][(kx - 1) % 32], rings[rm][(kx - 1) % 32]]
    # ---- fingers: reuse the knuckle-ring vertices as each finger's base ring
    KV = rings[-1]
    for f in range(4):
        base = [KV[4 * f + q] for q in range(4)] + [KV[16 + 4 * (3 - f) + q] for q in range(4)]
        fv = [base] + [[bm.verts.new(p) for p in rg] for rg in finger_rings[f][1:]]
        for rg in fv:
            for v in rg:
                v[LP] = 10 + f
        for r in range(len(fv) - 1):
            for q in range(8):
                bm.faces.new([fv[r][q], fv[r][(q + 1) % 8], fv[r + 1][(q + 1) % 8], fv[r + 1][q]])
        cap = fv[-1]
        for quad in ((0, 1, 2, 7), (2, 3, 6, 7), (3, 4, 5, 6)):
            bm.faces.new([cap[q] for q in quad])
        if f < 3:                                              # web quad to the next finger
            nxt = [KV[4 * (f + 1)], KV[16 + 4 * (2 - f) + 3]]   # next finger's d0, p0
            bm.faces.new([base[3], nxt[0], nxt[1], base[4]])
    a1 = unit(np.cross(td2, N)); a2 = np.cross(td2, a1)
    HP = np.array([v.co[:] for v in hole]); hc = HP.mean(0)
    c_h = c_start + td2 * float((hc - c_start) @ td2)          # the thumb axis point level with the opening
    # thumb loops at even angles; the opening's vertex order (cyclic shift and direction) is then matched to the
    # first loop, so the root does not twist
    ph = np.unwrap([math.atan2((p - c_h) @ a2, (p - c_h) @ a1) for p in HP]); sgn = 1 if ph[-1] > ph[0] else -1
    uni = np.array([sgn * 2 * math.pi * i / 8 for i in range(8)]); uni += np.mean(ph - uni)
    tv = [hole]; prev_r = [0.01] * 8; Ltot = float((tipT - c_start) @ td2)
    for k, fr in enumerate(THUMB_F):
        c = c_start + td2 * (fr * Ltot); ang = uni; rg = []
        for q in range(8):
            d = math.cos(ang[q]) * a1 + math.sin(ang[q]) * a2; h = ray(c, d, 0.035)
            r = float((h - c) @ d) if h is not None else prev_r[q]; prev_r[q] = r; rg.append(c + d * r)
        tv.append(rg)
    R0 = np.array(tv[1]); best = None
    for dr in (1, -1):
        for sh in range(8):
            idx = [(sh + dr * q) % 8 for q in range(8)]; cost = float(np.sum(np.linalg.norm(HP[idx] - R0, axis=1) ** 2))
            if best is None or cost < best[0]:
                best = (cost, idx)
    hole = [hole[i] for i in best[1]]; HP = HP[best[1]]; tv[0] = hole
    c9 = np.mean(tv[-1], axis=0); cc = c9 + (tipT - c9) * CAP_PULL
    tv.append([snap(cc + (p - c9) * 0.62) for p in tv[-1]])
    # thenar web: loops between the palm opening and the first thumb loop, on the surface
    # (rays from the thumb axis, between the axis point level with the opening and the first thumb loop, so the loops
    # wrap the thenar mound; capped at the blended radius of the opening and the first loop)
    root = []
    for b in THUMB_ROOT_B:
        c = c_h * (1 - b) + c_start * b; rg = []
        for q in range(8):
            tgt = HP[q] * (1 - b) + R0[q] * b; d = tgt - c; d = d - (d @ td2) * td2; rr = float(np.linalg.norm(d)); d = d / rr
            h = ray(c, d, 1.15 * rr); rg.append(h if h is not None else snap(tgt))
        root.append(rg)
    tv[1:1] = root
    tv = [tv[0]] + [[bm.verts.new(p) for p in rg] for rg in tv[1:]]
    for k, rg in enumerate(tv[1:]):
        for v in rg:
            v[LP] = 20 if k < len(THUMB_ROOT_B) else 21
    for r in range(len(tv) - 1):
        for q in range(8):
            bm.faces.new([tv[r][q], tv[r][(q + 1) % 8], tv[r + 1][(q + 1) % 8], tv[r + 1][q]])
    for quad in ((0, 1, 2, 7), (2, 3, 6, 7), (3, 4, 5, 6)):
        bm.faces.new([tv[-1][q] for q in quad])
    R.update(thumb_axis_offset_from_opening_mm=round(1000 * float(np.linalg.norm(hc - c_h)), 1), fingers=[{"base_s": round(F["s_base"], 4), "tip_s": round(F["s_tip"], 4), "length_mm": round(1000 * float(np.linalg.norm(F["tip"] - P_at(F, F["s_base"]))), 1)} for F in fingers],
             webs_s=[round(w, 4) for w in webs], palm_rings=len(rings), thumb_hole_rows=hole_rows,
             thumb_length_mm=round(1000 * float(np.linalg.norm(tipT - hc)), 1), finger_loops=len(FINGER_F) + 1, thumb_loops=len(THUMB_F) + 2)
    rep["sides"][side] = R

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
new = [v for v in bm.verts if v not in old_verts]
el = [e.calc_length() for e in bm.edges if any(v not in old_verts for v in e.verts)]
bm.to_mesh(me); me.update()
body["TASK4_HANDS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep.update({"out": str(OUT), "faces": len(bm.faces), "non_quads": sum(len(f.verts) != 4 for f in bm.faces),
            "boundary_edges": sum(e.is_boundary for e in bm.edges), "new_vertices": len(new),
            "hand_edge_mm_min_p5_p50": [round(1000 * float(x), 2) for x in (min(el), np.percentile(el, 5), np.percentile(el, 50))]})
REP.write_text(json.dumps(rep, indent=1)); print("HANDS", json.dumps({k: v for k, v in rep.items() if k != "method"}))
