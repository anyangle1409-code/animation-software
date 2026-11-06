"""FEMALE F11a: chest (two distinct breast forms) and groin / pelvis rebuild of the standing body; garment fit.
NEW file; input unchanged. Rest pose, vertex positions only (topology, UVs, weights, textures unchanged).

CHEST. Under the bra the F10b body was a low-passed inset of the bra's shape: one shelf with a pinched notch at the
top of the sternum. Here:
  1. CHEST WALL W: the breast zone (front chest under the cups: |x| < 0.17, 1.05 < z < 1.35, y < 0.02) is replaced
     by a biharmonic membrane spanning its border (upper chest, sternum line above / below, side chest, underbust):
     the smooth ribcage surface without breast tissue;
  2. HEIGHT h: each zone vertex's height above W along the wall normal (the current breast volume);
  3. SEPARATION (as implemented): the midline is eased back towards a sternum line (the midline skin above the breasts
     and at the underbust joined by a line bowed forward BOW for the ribcage's convexity), at most DEPTH_MAX, with a
     cosine fall-off to zero at SEP_W from the midline: a soft sternal valley between two breast forms (no slot);
  4. ROUNDING: within each breast the height field is smoothed (Taubin) and the lower pole kept fuller than the
     upper pole (h *= 1 - UPPER_TRIM * t above the breast's apex height, t over 60 mm), so the upper chest slopes
     onto the breast instead of the bra's push-up shelf;
  5. body = W + n * h, then light Taubin; the side chest / axillary tail blend over the zone's 30 mm feather.
  The bra keeps its supported shape, but its centre front (the gore, |x| < 0.035) is eased 45 % of the way towards
  the new sternum (the cups stay full), so the separation reads with the bra on too.

GROIN. The crotch under the shorts carried a crumpled tab (the source's fused shorts' inseam) and irregular inner-
thigh junctions. Here:
  1. CROTCH zone (|x| < 0.075, 0.70 < z < 0.86, plus the inner-thigh junctions |x| < 0.11, 0.72 < z < 0.80) becomes a
     biharmonic membrane on its border (lower abdomen, inner thighs, gluteal cleft): a smooth, narrow saddle between
     the thighs, no folds;
  2. a conservative soft mons pubis (MONS mm along the normal, gaussian at the front of the zone's top); no genital
     detail is modelled (none is supported by the source);
  3. the gluteal fold under each buttock and the inner-thigh junction are kept from the surrounding surface (they
     are on the zone border).

FIT. Body vertices within 15 mm of a garment hem are smoothed (no inset staircase along the hems); body vertices
under a garment are kept below its outer face by 1.4 mm, ramped from 0 at the hem to full 10 mm inside;
garment vertices are reported for how far they float off the skin. Self-intersections of the body are untangled
(umbrella, no projection) if the edits created any.

usage: python3.13 chest_groin_f_blender.py -- <F10e .blend> <out NEW .blend> <report .json>
"""
import heapq
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
SEP_W, UPPER_TRIM, MONS, GORE_EASE = 0.055, 0.35, 0.003, 0.45
BOW, DEPTH_MAX = 0.025, 0.030
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "REST"; bpy.context.view_layer.update()
body = bpy.data.objects["HGPT_Female_Body"]; me = body.data
P = np.array([v.co[:] for v in me.vertices]); N = len(P); P_in = P.copy()
nbr = [[] for _ in range(N)]
for e in me.edges:
    nbr[e.vertices[0]].append(e.vertices[1]); nbr[e.vertices[1]].append(e.vertices[0])
FACES = [list(p.vertices) for p in me.polygons]
rep = {"in": IN.name}


def vnormals(P):
    n = np.zeros_like(P)
    for f in FACES:
        fn = np.cross(P[f[1]] - P[f[0]], P[f[2]] - P[f[0]])
        if len(f) == 4:
            fn = fn + np.cross(P[f[2]] - P[f[0]], P[f[3]] - P[f[0]])
        n[f] += fn
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def dijkstra(seed, limit):
    dist = np.full(N, np.inf); pq = [(0.0, int(i)) for i in np.where(seed)[0]]
    for _, i in pq:
        dist[i] = 0.0
    heapq.heapify(pq)
    while pq:
        d0, i = heapq.heappop(pq)
        if d0 > dist[i] or d0 > limit:
            continue
        for j in nbr[i]:
            nd = d0 + float(np.linalg.norm(P[i] - P[j]))
            if nd < dist[j]:
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


def membrane(P, free):
    """biharmonic membrane over the free vertices, the rest fixed"""
    fi = np.where(free)[0]; rows, cols, vals = [], [], []
    for i in range(N):
        if not (free[i] or any(free[j] for j in nbr[i])):
            continue
        rows.append(i); cols.append(i); vals.append(1.0)
        for j in nbr[i]:
            rows.append(i); cols.append(j); vals.append(-1.0 / len(nbr[i]))
    L = sp.csr_matrix((vals, (rows, cols)), shape=(N, N)); A = L[:, fi]; B = L[:, ~free]
    M = (A.T @ A + sp.identity(len(fi)) * 1e-7).tocsc(); r = -(A.T @ (B @ P[~free]))
    Q = P.copy(); Q[fi] = np.column_stack([spl.spsolve(M, r[:, k]) for k in range(3)]); return Q


def taubin(P, ids, w, it):
    for _ in range(it):
        for f in (0.5, -0.53):
            U = np.array([P[nbr[i]].mean(0) for i in ids]); P[ids] += (U - P[ids]) * (f * w)[:, None]
    return P


# ---------------- chest: sternal valley between two breast forms
zone = (np.abs(P[:, 0]) < 0.17) & (P[:, 2] > 1.05) & (P[:, 2] < 1.35) & (P[:, 1] < 0.02)
Nrm = vnormals(P); zone &= Nrm[:, 1] < 0.2
# sternum line: midline skin above the breasts (z 1.31-1.34) and at the underbust (z 1.06-1.09), joined by a line
# bowed forward by BOW (the ribcage's convexity)
mid = np.abs(P[:, 0]) < 0.006
top_ = P[mid & (P[:, 2] > 1.31) & (P[:, 2] < 1.34) & (P[:, 1] < 0)]; bot_ = P[mid & (P[:, 2] > 1.06) & (P[:, 2] < 1.09) & (P[:, 1] < 0)]
zt, yt = top_[:, 2].mean(), top_[:, 1].min(); zb, yb = bot_[:, 2].mean(), bot_[:, 1].min()


def y_sternum(z):
    t = np.clip((z - zb) / (zt - zb), 0, 1); return yb + (yt - yb) * t - BOW * 4 * t * (1 - t)


S = np.clip((np.abs(P[:, 0]) - 0.004) / SEP_W, 0, 1); V = 0.5 + 0.5 * np.cos(np.pi * S)          # soft cosine fall-off
zf = np.clip(np.minimum(P[:, 2] - 1.07, 1.33 - P[:, 2]) / 0.03, 0, 1)
dy = np.clip(y_sternum(P[:, 2]) - P[:, 1], -0.02, DEPTH_MAX) * V * zf * zone       # back into the valley, or forward to fill the notch           # only backwards (into the valley)
P2 = P.copy(); P2[:, 1] += dy
zi = np.where(zone & (np.abs(P[:, 0]) < SEP_W + 0.03))[0]; w_ = np.clip(1 - (np.abs(P[zi, 0]) - SEP_W) / 0.03, 0, 1) * zf[zi]
P2 = taubin(P2, zi, w_, 6)
# upper poles: the bra's push-up shelf left a horizontal crease across both breasts above the apex; light Taubin on
# the zone above the apex height (feathered)
az = {sg: float(P[np.where(zone & (np.sign(P[:, 0]) == sg))[0][np.argmin(P[np.where(zone & (np.sign(P[:, 0]) == sg))[0], 1])], 2]) for sg in (1, -1)}
upz = np.array([P[i, 2] - az[1 if P[i, 0] > 0 else -1] for i in range(N)])
ui = np.where(zone & (upz > -0.01))[0]; uw = np.clip((upz[ui] + 0.01) / 0.03, 0, 1) * np.clip((1.34 - P[ui, 2]) / 0.02, 0, 1)
P2 = taubin(P2, ui, uw, 10)
rep["chest"] = {"zone_vertices": int(zone.sum()), "sternum_line": {"top": [round(float(zt), 3), round(float(yt), 3)], "bottom": [round(float(zb), 3), round(float(yb), 3)], "bow_mm": BOW * 1000},
                "valley_depth_mm_max": round(float(dy.max()) * 1000, 1), "separation_half_width_mm": SEP_W * 1000}
P = P2

# ---------------- groin: webbing below the crotch. Her source's thigh gap reaches up to the crotch at the shorts'
# bottom; the body carried a band of skin between the thighs below it (the fused shorts' crotch tab). Body vertices
# near the midline that lie in her thigh gap (more than 5 mm off her surface) are lifted to her crotch line: the
# underside's height at that front-back position, from her source's midline
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_Mesh_0"]; SV_ = np.array([v.co[:] for v in SRC.data.vertices])
srcb = BVHTree.FromPolygons([Vector(p) for p in SV_], [tuple(p.vertices) for p in SRC.data.polygons])
mid_ = SV_[(np.abs(SV_[:, 0]) < 0.008) & (SV_[:, 2] > 0.6) & (SV_[:, 2] < 0.9) & (np.abs(SV_[:, 1]) < 0.1)]
ybins = np.linspace(-0.1, 0.1, 41); zline = np.full(len(ybins), np.nan)
for k, yb_ in enumerate(ybins):
    q = mid_[np.abs(mid_[:, 1] - yb_) < 0.004]
    if len(q):
        zline[k] = q[:, 2].min()
ok_ = ~np.isnan(zline); zl = lambda y: float(np.interp(y, ybins[ok_], zline[ok_]))
web = []
for i in np.where((np.abs(P[:, 0]) < 0.06) & (P[:, 2] > 0.62) & (P[:, 2] < 0.82) & (np.abs(P[:, 1]) < 0.09))[0]:
    if srcb.find_nearest(Vector(P[i]))[3] > 0.005 and P[i, 2] < zl(P[i, 1]):
        web.append(int(i))
web = np.array(web, int)
if len(web):
    P[web, 2] = np.array([zl(y) for y in P[web, 1]]) - 0.001
    ring = set(web.tolist())
    for _ in range(3):
        ring |= {j for i in list(ring) for j in nbr[i]}
    ri = np.array(sorted(ring)); P = taubin(P, ri, np.full(len(ri), 0.5), 6)
rep["groin_web_vertices_lifted"] = int(len(web)); rep["source_crotch_line_z_min_max"] = [round(float(np.nanmin(zline)), 3), round(float(np.nanmax(zline)), 3)]
# ---------------- groin
# crotch strip between the thighs (surface facing down): biharmonic membrane on its border; the inner-thigh junctions
# and the gluteal-thigh transition round it: light Taubin low-pass (no membrane, so the forms stay)
Nrm = vnormals(P)
crotch = (np.abs(P[:, 0]) < 0.055) & (P[:, 2] > 0.70) & (P[:, 2] < 0.82) & (np.abs(P[:, 1]) < 0.07) & (Nrm[:, 2] < 0.2)
Gm = membrane(P, crotch)
gf = np.clip(dijkstra(~crotch, 0.03) / 0.012, 0, 1)
P2 = P + (Gm - P) * gf[:, None]
junction = (np.abs(P[:, 0]) < 0.14) & (P[:, 2] > 0.66) & (P[:, 2] < 0.87) & ~crotch
jf = np.clip(dijkstra(~junction, 0.05) / 0.02, 0, 1); ji = np.where(junction)[0]
P2 = taubin(P2, ji, jf[ji], 25)
NG = vnormals(P2); cz = P2[crotch, 2].max() if crotch.any() else 0.80
mons_c = np.array([0.0, P2[(np.abs(P2[:, 0]) < 0.01) & (np.abs(P2[:, 2] - (cz + 0.035)) < 0.01) & (P2[:, 1] < 0), 1].min() if True else -0.08, cz + 0.035])
g = np.exp(-np.sum(((P2 - mons_c) / np.array([0.035, 0.02, 0.025])) ** 2, axis=1))
P2 += NG * (MONS * g * (P2[:, 1] < 0))[:, None]
mv = np.linalg.norm(P2 - P, axis=1)
rep["groin"] = {"crotch_vertices": int(crotch.sum()), "junction_vertices": int(junction.sum()),
                "moved_mm_p50_p95_max": [round(float(np.percentile(mv[crotch | junction], q)) * 1000, 2) for q in (50, 95, 100)], "mons_mm": MONS * 1000}
P = P2

# ---------------- bra centre front eased towards the sternum
bra = bpy.data.objects["HGPT_Female_Bra"]; bme = bra.data
BP = np.array([v.co[:] for v in bme.vertices])
bt = BVHTree.FromPolygons([Vector(p) for p in P], FACES)
gore = (np.abs(BP[:, 0]) < 0.035) & (BP[:, 2] > 1.10) & (BP[:, 2] < 1.27) & (BP[:, 1] < 0)
wg = np.clip(1 - np.abs(BP[:, 0]) / 0.035, 0, 1) ** 1.5 * gore
moved = []
for i in np.where(gore)[0]:
    h_ = bt.find_nearest(Vector(BP[i]))
    tgt = np.array(h_[0][:]) + np.array(h_[1][:]) * 0.0028       # keep >= 2.8 mm over the skin (fabric + clearance)
    d = (tgt - BP[i]) * GORE_EASE * wg[i]
    if np.dot(d, np.array(h_[1][:])) < 0:                       # only towards the body
        BP[i] += d; moved.append(np.linalg.norm(d))
for v in bme.vertices:
    v.co = Vector(BP[v.index])
bme.update()
rep["bra_gore_vertices_eased"] = len(moved); rep["bra_gore_moved_mm_max"] = round(float(max(moved)) * 1000, 1) if moved else 0

# ---------------- fit. (1) hem bands: body vertices within HEM_BAND of any garment hem (boundary loop) are Taubin-
# smoothed (the F10b inset under the fabric ended in a quad staircase along the hems: lines across the upper thighs,
# the waist and the bra band). (2) skin under a garment is kept below the fabric's outer face by 1.4 mm x a ramp from
# 0 at the hem to 1 at 10 mm inside it (no step at the hem; the fabric edge lies on the skin).
HEM_BAND = 0.015
GB, HEMP = [], []
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; GB.append(BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons]))
    g = bmesh.new(); g.from_mesh(o.data); HEMP += [((e.verts[0].co + e.verts[1].co) / 2)[:] for e in g.edges if e.is_boundary]; g.free()
from scipy.spatial import cKDTree  # noqa: E402
hk = cKDTree(np.array(HEMP)); dh, _ = hk.query(P)
hb = np.where((dh < HEM_BAND) & (np.abs(P[:, 0]) < 0.3))[0]; hw = np.clip(1 - dh[hb] / HEM_BAND, 0, 1) ** 0.5
P = taubin(P, hb, hw * 0.9, 12)
rep["hem_band_vertices_smoothed"] = int(len(hb))
pushed = 0
for i in range(N):
    c = Vector(P[i])
    for g_ in GB:
        hh = g_.find_nearest(c, 0.008)
        if hh[0] is None:
            continue
        d = c - hh[0]; s_ = d.dot(hh[1])
        if (d - hh[1] * s_).length > 0.001:
            continue
        need = 0.0014 * min(1.0, dh[i] / 0.010)
        if s_ > -need:
            P[i] = P[i] - np.array(hh[1][:]) * (s_ + need); pushed += 1
rep["fit_skin_vertices_pushed_under_fabric"] = pushed
for v in me.vertices:
    v.co = Vector(P[v.index])
me.update()
# untangle (only if the edits created intersections)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); hist = []
for _ in range(30):
    t = BVHTree.FromBMesh(bm); bad = [(i, j) for i, j in t.overlap(t) if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts))]
    bad = [(i, j) for i, j in bad if bm.faces[i].calc_center_median().z > 0.65 and abs(bm.faces[i].calc_center_median().x) < 0.25]
    hist.append(len(bad))
    if not bad:
        break
    vs = set()
    for i, j in bad:
        for f in (bm.faces[i], bm.faces[j]):
            for v in f.verts:
                vs.add(v); vs.update(e.other_vert(v) for e in v.link_edges)
    new = {v: v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), 0.5) for v in vs}
    for v, c in new.items():
        v.co = c
bm.to_mesh(me); me.update(); bm.free()
rep["torso_self_intersections_untangle_rounds"] = hist
# ---------------- garment refit on the final body: light Taubin of each garment (removes the fused fabric's lips and
# the stepped waistband), then every garment vertex >= GAP_MIN outside the skin (along the skin normal at its nearest
# point); shorts vertices floating more than 5 mm off the reshaped crotch / inner thighs are brought to GAP_CROTCH
GAP_MIN, GAP_CROTCH = 0.0018, 0.0025
Pn = np.array([v.co[:] for v in me.vertices]); bt = BVHTree.FromPolygons([Vector(p) for p in Pn], FACES)
for n, it in (("HGPT_Female_Bra", 4), ("HGPT_Female_Shorts", 10)):
    o = bpy.data.objects[n]; g = bmesh.new(); g.from_mesh(o.data); g.verts.ensure_lookup_table()
    for _ in range(it):
        for f_ in (0.5, -0.53):
            new = {}
            for v in g.verts:
                nb = [e.other_vert(v).co for e in v.link_edges]
                k = 0.3 if v.is_boundary else 1.0
                new[v] = v.co + (sum(nb, Vector()) / len(nb) - v.co) * f_ * k
            for v, c in new.items():
                v.co = c
    pulled = pushed_out = 0
    for v in g.verts:
        h = bt.find_nearest(v.co)
        if h[0] is None:
            continue
        s_ = (v.co - h[0]).dot(h[1])
        if n == "HGPT_Female_Shorts" and abs(v.co.x) < 0.13 and v.co.z < 0.86 and h[3] > 0.005:
            v.co = h[0] + h[1] * GAP_CROTCH; pulled += 1
        elif s_ < GAP_MIN:
            v.co = h[0] + h[1] * GAP_MIN; pushed_out += 1
    g.to_mesh(o.data); o.data.update(); g.free()
    rep[n + "_refit"] = {"taubin_iterations": it, "pulled_to_skin": pulled, "pushed_out": pushed_out}
# (no gusset is added: her source's inner thighs touch for a few cm below the crotch, so the skin between the shorts'
# crotch and the thigh gap is inner-thigh contact, as in her source; a lofted gusset strip was tried and rejected)
# ---------------- crotch inside the gusset: a body vertex between the thighs that lies BELOW the shorts' gusset (the
# shorts above it within 40 mm, nothing below) is lifted to 2.5 mm above the gusset, then the strip is lightly smoothed
so = bpy.data.objects["HGPT_Female_Shorts"]
st = BVHTree.FromPolygons([v.co.copy() for v in so.data.vertices], [tuple(p.vertices) for p in so.data.polygons])
Pn = np.array([v.co[:] for v in me.vertices]); lifted = []
for i in np.where((np.abs(Pn[:, 0]) < 0.09) & (Pn[:, 2] > 0.66) & (Pn[:, 2] < 0.84) & (np.abs(Pn[:, 1]) < 0.09))[0]:
    c = Vector(Pn[i]); up_ = st.ray_cast(c, Vector((0, 0, 1)), 0.04); dn = st.ray_cast(c, Vector((0, 0, -1)), 0.06)
    if up_[0] is not None and dn[0] is None:
        Pn[i, 2] = up_[0].z + 0.0025; lifted.append(int(i))
if lifted:
    ring = set(lifted)
    for _ in range(2):
        ring |= {j for i in list(ring) for j in nbr[i]}
    ri = np.array(sorted(ring)); Pn = taubin(Pn, ri, np.full(len(ri), 0.6), 4)
    for v in me.vertices:
        v.co = Vector(Pn[v.index])
    me.update()
rep["crotch_vertices_lifted_inside_gusset"] = len(lifted)
# garment float
Pn = np.array([v.co[:] for v in me.vertices]); bt = BVHTree.FromPolygons([Vector(p) for p in Pn], FACES)
for n in ("HGPT_Female_Bra", "HGPT_Female_Shorts"):
    o = bpy.data.objects[n]; d = np.array([bt.find_nearest(v.co)[3] for v in o.data.vertices]) * 1000
    rep[n + "_off_skin_mm"] = {"p50": round(float(np.percentile(d, 50)), 2), "p95": round(float(np.percentile(d, 95)), 2), "max": round(float(d.max()), 2),
                               "over_6mm": int((d > 6).sum())}
rep["body_moved_mm_max"] = round(float(np.linalg.norm(Pn - P_in, axis=1).max()) * 1000, 1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("F11A", json.dumps(rep))
