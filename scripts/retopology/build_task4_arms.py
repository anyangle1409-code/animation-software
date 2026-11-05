"""Task 4 (part 1): arms from the Task-3 arm sockets to the wrists - designed loops, no auto-remesh.

Per side (the left side is built on its own measured axis and surface; the body is not mirror-symmetric):
  * AXIS: the arm's centre line is MEASURED on the source (slice centroids; the owner's LM_*_shoulder / elbow / wrist
    landmarks lie up to 5 cm off this mesh's arms). Lines are fitted to the upper-arm and forearm centroids; the
    shoulder-joint point is the upper-arm line at z = 1.42, the elbow the closest approach of the two lines, the wrist the
    narrowest forearm slice.
  * SHOULDER CAP: CAP_RINGS loops lofted from the 64-vertex socket loop (Task 3) to ring A0, the first ring where the arm
    is free of the torso. Correspondence follows anatomy: socket top (acromion) -> lateral arm (deltoid), socket bottom
    (armpit) -> medial arm, front fold -> anterior (biceps), back fold -> posterior (triceps). Cap vertices are projected
    by rays from a centre moving from the shoulder joint down the axis.
  * 64 -> 32: one transition row (all-quad 4:2 unit, one extra vertex per 4 dense edges) right after the first cap
    ring, so the deltoid / armpit cap and the arm carry 32 vertices around.
  * ARM: 32-vertex rings perpendicular to the bone axis (upper arm; 6 elbow rings whose planes rotate over +-4 cm; forearm), vertex
    angles evened out over the first rings below the transition; vertices placed by rays from the axis.
  * The wrist ring is left open for the hand (Task 4 part 2).

usage: python3.13 build_task4_arms.py -- <in .blend (03j)> <out NEW .blend> <report .json>
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
SRC = bpy.data.objects["HGPT_SOURCE_PROXY_Mesh_0"]; body = bpy.data.objects["HGPT_Male_Task3_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); bvh = BVHTree.FromPolygons([tuple(v) for v in SV], [tuple(p.vertices) for p in SRC.data.polygons])

CAP_RINGS = 12            # loops from the socket loop to A0 (A0 included)
A0_TILT = 0.10            # A0 sits this much further down the arm on the medial (armpit) side
TILT_RINGS = 4            # arm rings over which the tilt returns to perpendicular
UPPER_STEP = 0.020        # ring spacing on the upper arm (m)
ELBOW_RINGS = 6           # rings around the elbow; planes rotate from upper arm to forearm over +-ELBOW_HALF
ELBOW_HALF = 0.04
FORE_STEP = 0.020
ANGLE_EVEN_RINGS = 4      # rings over which the vertex angles become even after the transition


def measure_axis(sg):
    A = SV[(SV[:, 0] * sg > 0.215) & (SV[:, 2] > 0.84) & (SV[:, 2] < 1.42)]
    c = A.mean(0); u = np.linalg.svd(A - c)[2][0]; u = u if u[2] < 0 else -u
    t = (A - c) @ u; cents = []
    for tt in np.arange(t.min() + 0.01, t.max(), 0.01):
        s = A[np.abs(t - tt) < 0.004]
        if len(s) >= 20:
            cc = s.mean(0); r = np.median(np.linalg.norm((s - cc) - np.outer((s - cc) @ u, u), axis=1)); cents.append((cc, r))
    C = np.array([c_ for c_, _ in cents]); Rr = np.array([r for _, r in cents])

    def fit(zlo, zhi):
        P = C[(C[:, 2] >= zlo) & (C[:, 2] <= zhi)]; m = P.mean(0); d = np.linalg.svd(P - m)[2][0]
        return m, (d if d[2] < 0 else -d)
    mu, du = fit(1.18, 1.33); mf, df = fit(0.99, 1.10)
    gh = mu + du * ((1.42 - mu[2]) / du[2])
    # closest approach of the two lines -> elbow
    w0 = mu - mf; aa, bb, cc_, dd, ee = du @ du, du @ df, df @ df, du @ w0, df @ w0
    s_ = (bb * ee - cc_ * dd) / (aa * cc_ - bb * bb); t_ = (aa * ee - bb * dd) / (aa * cc_ - bb * bb)
    el = 0.5 * ((mu + s_ * du) + (mf + t_ * df))
    fore = (C[:, 2] < 1.06) & (C[:, 2] > 0.95); k = np.argmin(np.where(fore, Rr, 9)); wz = C[k, 2]
    wr = mf + df * ((wz - mf[2]) / df[2])
    return Vector(gh), Vector(el), Vector(wr)


def frame(ax, sg):
    ax = ax.normalized(); f = Vector((0, -1, 0)); f = (f - ax * f.dot(ax)).normalized(); lat = ax.cross(f)
    if lat.x * sg < 0:
        lat = -lat
    return ax, f, lat


def radial_hit(c, d):
    h = bvh.ray_cast(c, d.normalized())[0]
    if h is None:
        raise RuntimeError(f"no arm surface from {tuple(round(x, 3) for x in c)}")
    return h


me = body.data; bm = bmesh.new(); bm.from_mesh(me)
OLD_VERTS = set(bm.verts)                                  # the Task-3 body is not moved by the arm relax
RELAX_IT = 6
report = {}
for sg in (1.0, -1.0):
    GH, E, W = measure_axis(sg)
    # socket loop (boundary loop on this side)
    bnd = [e for e in bm.edges if e.is_boundary]
    adj = {}
    for e in bnd:
        for v in e.verts:
            adj.setdefault(v, []).append(e.other_vert(v))
    start = max((v for v in adj if v.co.x * sg > 0.12 and 1.2 < v.co.z < 1.6), key=lambda v: v.co.z)
    loop = [start]; prev = None
    while True:
        nxt = [w for w in adj[loop[-1]] if w is not prev and w is not loop[0]] if len(loop) > 1 else adj[loop[-1]][:1]
        if not nxt:
            break
        prev = loop[-1]; loop.append(nxt[0])
        if len(loop) > 400:
            raise RuntimeError("socket loop walk failed")
    n = len(loop)
    assert n % 4 == 0, f"socket loop has {n} vertices; the 4:2 transition needs a multiple of 4"
    P = np.array([v.co[:] for v in loop]); cs = P.mean(0)
    ns = np.linalg.svd(P - cs)[2][2]; ns = ns if ns[0] * sg > 0 else -ns
    up = np.array([0, 0, 1.0]); up = up - ns * (up @ ns); up /= np.linalg.norm(up)
    fr = np.cross(ns, up); fr = fr if fr[1] < 0 else -fr                      # anterior (-y) in the socket plane
    th = np.unwrap(np.arctan2((P - cs) @ fr, (P - cs) @ up))
    if th[-1] < th[0]:
        loop = loop[::-1]; P = P[::-1]; th = np.unwrap(np.arctan2((P - cs) @ fr, (P - cs) @ up))
    # A0: first station below the shoulder where every radial ray stays within the arm
    ax_u, f_u, lat_u = frame(E - GH, sg)
    t0 = None
    for t in np.arange(0.25, 0.7, 0.01):
        c = GH.lerp(E, t); ok = True
        for k in range(72):                                    # every direction must stay on the arm (not the lat / back)
            ang = 2 * math.pi * k / 72; h = bvh.ray_cast(c, lat_u * math.cos(ang) + f_u * math.sin(ang))
            if h[0] is None or h[3] > 0.10 or h[0].x * sg < 0.17:
                ok = False; break
        if ok:
            t0 = t; break
    A0c = GH.lerp(E, t0); Lu = (E - GH).length
    tilt = lambda q: A0_TILT * 0.5 * (1 - math.cos(q))                    # 0 lateral (deltoid) .. A0_TILT medial (armpit)
    A0 = [radial_hit(GH.lerp(E, t0 + tilt(q) / Lu), lat_u * math.cos(q) + f_u * math.sin(q)) for q in th]
    # cap: each socket vertex -> its A0 vertex along a surface meridian traced by a fan of rays from the shoulder joint
    # (in the plane through the joint and both ends), rings at equal fractions of each meridian's length
    # fan origin: the shoulder joint lies almost on the line between the socket-top and A0-lateral ends (~175 deg),
    # so the arc direction would be ambiguous; an origin moved medially and down the arm makes every arc sweep over
    # the outside of the shoulder (top lines) or under through the armpit (bottom lines)
    FO = GH - lat_u * 0.035 + ax_u * 0.03

    def _inside(p_):
        k_, o_, d_ = 0, Vector(p_), Vector((0.31, 0.53, 0.79)).normalized()
        while True:
            h_ = bvh.ray_cast(o_, d_)
            if h_[0] is None:
                return k_ % 2 == 1
            k_ += 1; o_ = h_[0] + d_ * 1e-5
    assert _inside(FO), "cap fan origin is not inside the body"
    rings = [loop]; mer = []
    for i in range(n):
        p0, p1 = Vector(P[i]), A0[i]; e1 = (p0 - FO).normalized(); nrm = (p0 - FO).cross(p1 - FO)
        e2 = nrm.cross(e1).normalized(); tot = (p0 - FO).angle(p1 - FO); pts = [p0]
        for al in np.linspace(0, tot, 160)[1:-1]:
            h = bvh.ray_cast(FO, e1 * math.cos(al) + e2 * math.sin(al))[0]
            if h is not None:
                pts.append(h)
        pts.append(p1); Pm = np.array([q[:] for q in pts])
        # remove spikes (a ray that jumps to a distant surface and back): such samples inflate the arc length and
        # put interpolated cap vertices on the jump segment, inside the body
        for _ in range(3):
            st_ = np.linalg.norm(np.diff(Pm, axis=0), axis=1); med = np.median(st_) + 1e-6; keep = [0]
            for j in range(1, len(Pm) - 1):
                a_, b_, c_ = Pm[keep[-1]], Pm[j], Pm[j + 1]
                if np.linalg.norm(b_ - a_) > 4 * med and np.linalg.norm(c_ - a_) < np.linalg.norm(b_ - a_):
                    continue
                keep.append(j)
            keep.append(len(Pm) - 1); Pm = Pm[keep]
        mer.append((Pm, np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pm, axis=0), axis=1))]))
    import os
    if os.environ.get("ARM_DIAG") and sg > 0:
        for i in range(0, n, 8):
            Pm, sl = mer[i]
            print("MER", i, "th %.0f" % math.degrees(th[i]), "p0", [round(x, 3) for x in Pm[0]], "p1", [round(x, 3) for x in Pm[-1]],
                  "len %.3f" % sl[-1], "max x %.3f" % Pm[:, 0].max(), "n", len(Pm), "GH", [round(x, 3) for x in GH])
    def mer_pt(i, frac):
        Pm, sl = mer[i % n]; x = frac * sl[-1]
        return bvh.find_nearest(Vector([np.interp(x, sl, Pm[:, d]) for d in range(3)]))[0]

    def mid_pt(i, j, frac):                                   # between two meridians, snapped to the surface
        return bvh.find_nearest(mer_pt(i, frac).lerp(mer_pt(j, frac), 0.5))[0]
    # ring 1 keeps the socket's 64 vertices; the 4:2 transition sits between ring 1 and ring 2, so the rest of the
    # cap (deltoid, armpit dome) and A0 carry 32 vertices around (64 there gave long thin quads)
    F1, F2 = 1 / CAP_RINGS, 2 / CAP_RINGS
    r1 = [bm.verts.new(mer_pt(i, F1)) for i in range(n)]
    for i in range(n):
        bm.faces.new([loop[i], loop[(i + 1) % n], r1[(i + 1) % n], r1[i]])

    def coarse_ring(frac):
        out = []
        for m in range(n // 4):
            out.append(mer_pt(4 * m, frac) if frac < 1 else A0[4 * m])
            out.append(mid_pt(4 * m + 2, 4 * m + 3, frac) if frac < 1 else bvh.find_nearest(A0[4 * m + 2].lerp(A0[(4 * m + 3) % n], 0.5))[0])
        return out
    coarse = [bm.verts.new(p) for p in coarse_ring(F2)]; nc = len(coarse)
    extra = [bm.verts.new(mid_pt(4 * m + 1, 4 * m + 2, 0.5 * (F1 + F2))) for m in range(n // 4)]
    for m in range(n // 4):
        d0, d1, d2, d3, d4 = (r1[(4 * m + j) % n] for j in range(5))
        c0, c1, c2 = coarse[2 * m], coarse[2 * m + 1], coarse[(2 * m + 2) % nc]; p = extra[m]
        for f in ([d0, d1, p, c0], [d1, d2, d3, p], [d3, d4, c2, c1], [c0, p, d3, c1]):
            bm.faces.new(f)
    if os.environ.get("ARM_DIAG") and sg > 0:
        for k in range(0, CAP_RINGS + 1):
            pt = mer_pt(0, k / CAP_RINGS); print("CAPM0", k, [round(x, 3) for x in pt], "len", round(float(mer[0][1][-1]), 3), "npts", len(mer[0][0]))
    prev = coarse
    for k in range(3, CAP_RINGS + 1):
        ring = [bm.verts.new(p) for p in coarse_ring(k / CAP_RINGS)]
        for i in range(nc):
            bm.faces.new([prev[i], prev[(i + 1) % nc], ring[(i + 1) % nc], ring[i]])
        prev = ring
    thc = []
    for m in range(n // 4):
        q2, q3 = th[4 * m + 2], th[(4 * m + 3) % n] + (2 * math.pi if 4 * m + 3 >= n else 0)
        thc += [th[4 * m], 0.5 * (q2 + q3)]
    # arm stations below A0: upper arm, elbow (planes rotate over +-4 cm), forearm, wrist
    ax_f, f_f, lat_f = frame(W - E, sg)
    st = []
    t = t0 + (A0_TILT * 0.5 + UPPER_STEP) / Lu
    while (E - GH.lerp(E, t)).length > ELBOW_HALF + 0.5 * UPPER_STEP:
        st.append((GH.lerp(E, t), ax_u)); t += UPPER_STEP / Lu
    for k in range(ELBOW_RINGS):
        sd = -ELBOW_HALF + 2 * ELBOW_HALF * k / (ELBOW_RINGS - 1)
        w = (sd + ELBOW_HALF) / (2 * ELBOW_HALF); w = w * w * (3 - 2 * w)
        c = E + ax_u * sd if sd < 0 else E + ax_f * sd
        st.append((c, ax_u.slerp(ax_f, w) if hasattr(ax_u, "slerp") else ax_u.lerp(ax_f, w).normalized()))
    Lf = (W - E).length; t = (ELBOW_HALF + FORE_STEP) / Lf
    while t < 1.0 - 0.5 * FORE_STEP / Lf:
        st.append((E.lerp(W, t), ax_f)); t += FORE_STEP / Lf
    st.append((W, ax_f))
    q0 = np.array(thc); qe = q0[0] + np.arange(nc) * 2 * math.pi / nc
    for k, (c, axk) in enumerate(st):
        w = min(1.0, (k + 1) / ANGLE_EVEN_RINGS); qs = (1 - w) * q0 + w * qe
        a_, f_, l_ = frame(axk, sg); wt = max(0.0, 1 - (k + 1) / TILT_RINGS)
        # first rings keep part of the A0 tilt (centred on the mean tilt) so they do not cross the tilted A0
        ring = [bm.verts.new(radial_hit(c + a_ * (wt * (tilt(q) - 0.5 * A0_TILT)), l_ * math.cos(q) + f_ * math.sin(q))) for q in qs]
        for i in range(nc):
            bm.faces.new([prev[i], prev[(i + 1) % nc], ring[(i + 1) % nc], ring[i]])
        prev = ring
    report["right" if sg > 0 else "left"] = {
        "shoulder_joint": [round(x, 4) for x in GH], "elbow": [round(x, 4) for x in E], "wrist": [round(x, 4) for x in W],
        "socket_loop_vertices": n, "A0_axis_t": round(float(t0), 3), "cap_rings": CAP_RINGS, "arm_ring_vertices": nc,
        "arm_rings": len(st), "wrist_ring_open": True}
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# light on-surface relax of the new arm vertices (socket loop and wrist rings fixed). Guard: a vertex may not move
# further than 1 cm from its own arm axis than it was (keeps the armpit / cap from sliding onto the torso)
AXES = {sg_: [Vector(report["right" if sg_ > 0 else "left"][k]) for k in ("shoulder_joint", "elbow", "wrist")] for sg_ in (1.0, -1.0)}


def axis_dist(p_, sg_):
    a0, a1, a2 = AXES[sg_]; best = 9.0
    for u0, u1 in ((a0, a1), (a1, a2)):
        d_ = u1 - u0; t_ = max(0.0, min(1.0, (p_ - u0).dot(d_) / d_.length_squared)); best = min(best, (p_ - (u0 + d_ * t_)).length)
    return best


fixed = {v for v in bm.verts if v.is_boundary} | OLD_VERTS
for _ in range(RELAX_IT):
    upd = {}
    for v in bm.verts:
        if v in fixed:
            continue
        nb = [e.other_vert(v) for e in v.link_edges]; avg = sum((w_.co for w_ in nb), Vector()) / len(nb)
        h = bvh.find_nearest(v.co.lerp(avg, 0.35))[0]; sg_ = 1.0 if v.co.x > 0 else -1.0
        if axis_dist(h, sg_) <= axis_dist(v.co, sg_) + 0.01 and h.x * sg_ > 0.12:
            upd[v] = h
    for v, h in upd.items():
        v.co = h
bm.to_mesh(me); me.update()
body["TASK4_ARMS"] = json.dumps(report)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
L = np.array([e.calc_length() for e in bm.edges])
rep = {"out": str(OUT), "faces": len(bm.faces), "non_quads": sum(len(f.verts) != 4 for f in bm.faces),
       "boundary_edges": sum(e.is_boundary for e in bm.edges), "min_edge_mm": round(float(L.min()) * 1000, 2),
       "edge_mm_p5_p50_p95": [round(float(np.percentile(L, q)) * 1000, 1) for q in (5, 50, 95)], "sides": report}
REP.write_text(json.dumps(rep, indent=1)); print("ARMS", json.dumps(rep))
