"""FIRST-PARTY reshape of the Body v2 mesh to an approved PROPORTION target, by cross-section statistics.

The owner approved (3 Nov 2026) the MPFB benchmark M13/M14's proportions (legs, waist, width, arms; chest excluded)
as the target for the independent first-party model.  Per the first-party rule no MPFB vertex, topology, rig, weight or
texture may enter the production mesh.  So the target is reduced to NUMBERS: for each body region (trunk, upper arm,
forearm, thigh, shin) the skin's distance from the region's axis at NT stations along it x NA directions around it.
Our own mesh (Body v2, our topology, already bound to the canonical skeleton) is then scaled radially, region by
region, towards those numbers.  Only ratios of our own section radii are applied; nothing is projected onto the other
surface.  The chest band is smoothed more strongly (the pectoral shape is to be sculpted, not inherited).

  measure: python3.13 section_fit_blender.py -- measure <blend> <canonical|mpfb> <out.json>
  apply:   python3.13 section_fit_blender.py -- apply <our blend> <target.json> <out dir>
           (V2_FIT_STRENGTH 0..1, default 1; V2_FIT_CLAMP "lo,hi" ratio clamp, default 0.8,1.3)
"""
import json
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from scipy.sparse import csr_matrix

a = sys.argv[sys.argv.index("--") + 1:]
MODE = a[0]
NT, NA = 16, 24
NAMES = {"canonical": dict(ua="upperarm_{}", fa="forearm_{}", hand="hand_{}", thigh="thigh_{}", shin="shin_{}", foot="foot_{}",
                           neck="neck", armk=("upperarm", "forearm", "hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal"),
                           legk=("thigh", "shin", "foot", "toe"), faG="forearm_{}", uaG="upperarm_{}"),
         "mpfb": dict(ua="upperarm_{}", fa="lowerarm_{}", hand="hand_{}", thigh="thigh_{}", shin="calf_{}", foot="foot_{}",
                      neck="neck_01", armk=("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky"),
                      legk=("thigh", "calf", "foot", "ball"), faG="lowerarm_{}", uaG="upperarm_{}")}


def load(blend, kind):
    bpy.ops.wm.open_mainfile(filepath=blend)
    if kind == "canonical":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import character_profile
        bn, rn = character_profile.blender_names()
        body, rig = bpy.data.objects[bn], bpy.data.objects[rn]
    else:
        rig = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
        body = max((o for o in bpy.data.objects if o.type == "MESH" and "FLOOR" not in o.name), key=lambda o: len(o.data.vertices))
    return body, rig


def evaluated(body):
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    mw = np.array(body.matrix_world); V = V @ mw[:3, :3].T + mw[:3, 3]
    GN = {g.index: g.name for g in body.vertex_groups}; G = {}
    for v in m.vertices:
        for g in v.groups:
            nm = GN.get(g.group)
            if nm:
                G.setdefault(nm, np.zeros(len(V)))[v.index] = g.weight
    ev.to_mesh_clear()
    return V, G


def regions(body, rig, kind, V, G):
    """per region: (axis start, axis end, lateral ref, weight array)"""
    N = NAMES[kind]; n = len(V)
    P = lambda nm: np.array(rig.matrix_world @ rig.pose.bones[nm].head)
    gw = lambda ks: sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n))
    armw, legw = gw(N["armk"]), gw(N["legk"])
    R = {}
    hipc = (P(N["thigh"].format("l")) + P(N["thigh"].format("r"))) / 2
    R["trunk"] = (hipc - np.array([0, 0, 0.12]), P(N["neck"]), np.array([1.0, 0, 0]), np.clip(1 - armw - legw, 0, 1))
    for s in ("l", "r"):
        lat = np.array([np.sign(P(N["ua"].format(s))[0]), 0, 0])
        R[f"upperarm_{s}"] = (P(N["ua"].format(s)), P(N["fa"].format(s)), lat, gw((N["uaG"].format(s),)))
        R[f"forearm_{s}"] = (P(N["fa"].format(s)), P(N["hand"].format(s)), lat, gw((N["faG"].format(s),)))
        R[f"thigh_{s}"] = (P(N["thigh"].format(s)), P(N["shin"].format(s)), lat, G.get(N["thigh"].format(s), np.zeros(n)))
        R[f"shin_{s}"] = (P(N["shin"].format(s)), P(N["foot"].format(s)), lat, G.get(N["shin"].format(s), np.zeros(n)))
    return R


def frame(h, t, lat):
    ax_ = t - h; L = np.linalg.norm(ax_); ax_ = ax_ / L
    la = lat - ax_ * (lat @ ax_); la /= np.linalg.norm(la)
    fr = np.cross(ax_, la)
    if fr[1] > 0:
        fr = -fr
    return ax_, L, la, fr


def coords(V, h, t, lat, trunk):
    ax_, L, la, fr = frame(h, t, lat)
    rel = V - h; tt = rel @ ax_ / L; rad = rel - np.outer(rel @ ax_, ax_)
    if trunk:                                                  # trunk: radius from the station's own centre
        rad = rad.copy()
    ang = np.arctan2(rad @ fr, rad @ la)
    return tt, ang, rad, ax_, L


def profile(V, R):
    out = {}
    for name, (h, t, lat, w) in R.items():
        trunk = name == "trunk"
        tt, ang, rad, ax_, L = coords(V, h, t, lat, trunk)
        sel = (w > 0.5) & (tt > -0.02) & (tt < 1.02)
        grid = np.full((NT, NA), np.nan); cen = np.zeros((NT, 3))
        for i in range(NT):
            t0, t1 = i / NT, (i + 1) / NT
            s_ = sel & (tt >= t0) & (tt < t1)
            if s_.sum() < 20:
                continue
            c = rad[s_].mean(0) if trunk else np.zeros(3); cen[i] = c
            r_ = rad[s_] - c; aa = np.arctan2(r_ @ frame(h, t, lat)[3], r_ @ frame(h, t, lat)[2]); rr = np.linalg.norm(r_, axis=1)
            k = ((aa + np.pi) / (2 * np.pi) * NA).astype(int) % NA
            for j in range(NA):
                m_ = k == j
                if m_.any():
                    grid[i, j] = np.percentile(rr[m_], 95)
        out[name] = {"radius": grid.tolist(), "centre": cen.tolist(), "length_m": float(L)}
    return out


if MODE == "measure":
    blend, kind, outp = a[1], a[2], a[3]
    body, rig = load(blend, kind); V, G = evaluated(body)
    res = {"kind": kind, "blend": Path(blend).name, "NT": NT, "NA": NA, "regions": profile(V, regions(body, rig, kind, V, G))}
    Path(outp).write_text(json.dumps(res)); print("MEASURED", list(res["regions"]))
    sys.exit(0)

# ---------------------------------------------------------------- apply
blend, tgt, OUT = a[1], a[2], Path(a[3]); OUT.mkdir(parents=True, exist_ok=True)
STR = float(os.environ.get("V2_FIT_STRENGTH", "1.0"))
LO, HI = (float(v) for v in os.environ.get("V2_FIT_CLAMP", "0.8,1.3").split(","))
T = json.loads(Path(tgt).read_text())["regions"]
body, rig = load(blend, "canonical")
me = body.data; n = len(me.vertices)
R0 = np.empty(n * 3); me.vertices.foreach_get("co", R0); R0 = R0.reshape(-1, 3)
V, G = evaluated(body)                                         # rest pose, world space (keys at 0)
mwi = np.linalg.inv(np.array(body.matrix_world))[:3, :3]
Rg = regions(body, rig, "canonical", V, G)
own = profile(V, Rg)
D = np.zeros((n, 3)); wsum = np.zeros(n); rep = {}


def smooth_grid(g, rt, ra):
    g = g.copy()
    for _ in range(rt):
        g[1:-1] = 0.5 * g[1:-1] + 0.25 * (g[:-2] + g[2:])
    for _ in range(ra):
        g = 0.5 * g + 0.25 * (np.roll(g, 1, 1) + np.roll(g, -1, 1))
    return g


for name, (h, t, lat, w) in Rg.items():
    if name not in T:
        continue
    go, gt = np.array(own[name]["radius"]), np.array(T[name]["radius"])
    ratio = gt / go
    ratio[~np.isfinite(ratio)] = 1.0
    ratio = np.clip(ratio, LO, HI)
    trunk = name == "trunk"
    ratio = smooth_grid(ratio, 2, 2)
    if trunk:                                                  # chest band (upper half, front): heavier angular smoothing
        ratio[NT // 2:] = smooth_grid(ratio[NT // 2:], 0, 6)
    ratio = 1 + STR * (ratio - 1)
    tt, ang, rad, ax_, L = coords(V, h, t, lat, trunk)
    cen = np.array(own[name]["centre"])
    ti = np.clip(tt * NT - 0.5, 0, NT - 1.001); i0 = np.floor(ti).astype(int); ft = ti - i0
    c_ = cen[i0] * (1 - ft)[:, None] + cen[np.minimum(i0 + 1, NT - 1)] * ft[:, None] if trunk else 0
    r_ = rad - c_
    aa = np.arctan2(r_ @ frame(h, t, lat)[3], r_ @ frame(h, t, lat)[2])
    aj = (aa + np.pi) / (2 * np.pi) * NA - 0.5; j0 = np.floor(aj).astype(int); fa = aj - j0
    j0m, j1m = j0 % NA, (j0 + 1) % NA
    i1 = np.minimum(i0 + 1, NT - 1)
    rr = (ratio[i0, j0m] * (1 - ft) * (1 - fa) + ratio[i1, j0m] * ft * (1 - fa) + ratio[i0, j1m] * (1 - ft) * fa + ratio[i1, j1m] * ft * fa)
    inside = (tt > -0.05) & (tt < 1.05)
    ww = np.where(inside, np.clip(w, 0, 1), 0)
    D += ww[:, None] * (r_ * (rr - 1)[:, None])
    wsum += ww
    rep[name] = {"ratio_min": round(float(ratio.min()), 3), "ratio_max": round(float(ratio.max()), 3),
                 "ratio_mean": round(float(np.nanmean(ratio)), 3)}
D = D / np.maximum(wsum, 1.0)[:, None]
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
for _ in range(int(os.environ.get("V2_FIT_SMOOTH", "15"))):
    D = 0.5 * D + 0.5 * (A @ D) * Dinv[:, None]
Dl = D @ mwi.T                                                  # world -> object
for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
    c = np.empty(n * 3); kb.data.foreach_get("co", c); kb.data.foreach_set("co", (c.reshape(-1, 3) + Dl).ravel())
me.vertices.foreach_set("co", (R0 + Dl).ravel()); me.update()
rep["max_move_mm"] = round(float(np.linalg.norm(D, axis=1).max()) * 1000, 1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "body_v2_r121_arms.blend"), copy=True)
(OUT / "section_fit_report.json").write_text(json.dumps(rep, indent=1)); print("FIT", json.dumps(rep))
