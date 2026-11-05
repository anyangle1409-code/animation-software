"""Muscle-definition audit: is the definition in the GEOMETRY? Current body vs the approved source surface (read-only).

Probes: 60,000 points uniform on the SOURCE surface, and for each the nearest point on the current surface (probing at
current vertices would hide a coarse face cutting across a groove between them, because the vertices lie on the
source by construction). At every probe the local 'relief' of each surface is measured at muscle scale:
relief_R(p) = (p - mean of the surface points within radius R) along the local PCA normal. Positive = bulge (muscle
belly), negative = groove (separation between muscles). Both surfaces are sampled densely and area-uniformly - a coarse
face of the current body therefore counts as flat, which is what it is - so the measure depends neither on vertex
count nor on shading or lighting.

Per region (dominant bone of the nearest current vertex; trunk split into chest / abdomen / upper back / lower back /
pelvis by height and front/back):
  * signed distance of the current surface from the source (+ outside, - inside): filled grooves or lost volume;
  * relief amplitude ratio current/source (std of relief; 1.0 = all definition kept) and correlation, at R = 15 mm
    (grooves: abdominal lines, deltoid/biceps separation) and R = 30 mm (muscle bellies);
  * groove depth: mean of the 10 % deepest source grooves vs the current surface at the same probes.

usage: python3.13 muscle_relief_audit_blender.py -- <bound .blend> <retopo checkpoint with source proxy> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCBLEND, REP = Path(a[0]), Path(a[1]), Path(a[2])
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
with bpy.data.libraries.load(str(SRCBLEND), link=False) as (src, dst):
    dst.objects = ["HGPT_SOURCE_PROXY_Mesh_0"]
S = dst.objects[0]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; rig = bpy.data.objects["MESHY_RIG"]
rng = np.random.default_rng(1)


def tri_mesh(m, mw):
    m.calc_loop_triangles(); V = np.array([mw @ v.co for v in m.vertices]); T = np.array([t.vertices[:] for t in m.loop_triangles]); return V, T


def sample(V, T, n):
    A = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
    k = rng.choice(len(T), n, p=A / A.sum()); r1 = np.sqrt(rng.random(n)); r2 = rng.random(n)
    return V[T[k, 0]] * (1 - r1)[:, None] + V[T[k, 1]] * (r1 * (1 - r2))[:, None] + V[T[k, 2]] * (r1 * r2)[:, None]


Vs, Ts = tri_mesh(S.data, S.matrix_world); Vc, Tc = tri_mesh(me, body.matrix_world)
Ps = sample(Vs, Ts, 1_500_000); Pc = sample(Vc, Tc, 1_500_000); Ks = cKDTree(Ps); Kc = cKDTree(Pc)
sb = BVHTree.FromPolygons([tuple(p) for p in Vs], Ts.tolist(), all_triangles=True)
cb = BVHTree.FromPolygons([tuple(p) for p in Vc], Tc.tolist(), all_triangles=True)
probe_s = sample(Vs, Ts, 60_000); probe_c = np.zeros_like(probe_s); sd = np.zeros(len(probe_s)); nrm = np.zeros_like(probe_s)
for i, p in enumerate(probe_s):
    _, n, _, _ = sb.find_nearest(p); loc, _, _, _ = cb.find_nearest(p)
    nrm[i] = n; probe_c[i] = loc; sd[i] = (np.array(loc) - p) @ np.array(n)
near_v = cKDTree(Vc).query(probe_s)[1]


def relief(K, P, probes, R, nrm_ref):
    out = np.zeros(len(probes))
    for i, idx in enumerate(K.query_ball_point(probes, R)):
        Q = P[idx]
        if len(Q) < 20:
            continue
        m = Q.mean(0); w, v = np.linalg.eigh(np.cov((Q - m).T)); n = v[:, 0]
        if n @ nrm_ref[i] < 0:
            n = -n
        out[i] = (probes[i] - m) @ n
    return out


GN = {g.index: g.name for g in body.vertex_groups}
DOM = [GN[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in me.vertices]
TRUNK = ("spine_", "pelvis", "clavicle_", "scapula_", "scap_glide_", "root")
LIMB = (("upperarm_", None), ("forearm", "forearm"), ("hand", "hand"), ("thumb", "hand"), ("index", "hand"), ("middle", "hand"),
        ("ring", "hand"), ("pinky", "hand"), ("thigh", "thigh"), ("calf", "calf"), ("shin", "calf"), ("foot", "foot"), ("ball", "foot"),
        ("toe", "foot"), ("neck", "neck"), ("head", "head"))


def region(i):
    d = DOM[i]; x, y, z = Vc[i]
    if d.startswith(TRUNK):
        if z > 1.18:
            return "chest" if y < -0.02 else "upper_back"
        if z > 0.95:
            return "abdomen" if y < -0.02 else "lower_back"
        return "pelvis_glutes"
    for k, nm in LIMB:
        if d.startswith(k):
            if nm is None:
                gh = np.array(rig.matrix_world @ rig.data.bones[d].head_local)
                if z > gh[2] - 0.11:
                    return "deltoid"
                return "biceps_front" if y < gh[1] else "triceps_back"
            return nm
    return "other:" + d.split("_")[0]


REGV = np.array([region(i) for i in range(len(Vc))]); REG = REGV[near_v]
rep = {"method": __doc__.split("usage")[0].strip(), "vertices_current": len(Vc), "vertices_source": len(Vs), "probes": len(probe_s), "regions": {}}
for R in (0.015, 0.030):
    rc = relief(Kc, Pc, probe_c, R, nrm); rs = relief(Ks, Ps, probe_s, R, nrm)
    for g in sorted(set(REG)):
        m = REG == g
        if m.sum() < 100:
            continue
        e = rep["regions"].setdefault(g, {"probes": int(m.sum()), "signed_dist_mm_mean_p5_p95": [round(float(np.mean(sd[m])) * 1000, 2), round(float(np.percentile(sd[m], 5)) * 1000, 2), round(float(np.percentile(sd[m], 95)) * 1000, 2)]})
        deep = m & (rs < np.percentile(rs[m], 10))
        e[f"R{int(R * 1000)}"] = {"relief_std_mm_source": round(float(rs[m].std()) * 1000, 2), "relief_std_mm_current": round(float(rc[m].std()) * 1000, 2),
                                   "amplitude_ratio": round(float(rc[m].std() / max(rs[m].std(), 1e-9)), 2), "correlation": round(float(np.corrcoef(rc[m], rs[m])[0, 1]), 2),
                                   "deepest10pct_groove_mm_source_vs_current": [round(float(rs[deep].mean()) * 1000, 2), round(float(rc[deep].mean()) * 1000, 2)]}
    print("R", R, flush=True)
REP.write_text(json.dumps(rep, indent=1))
for g, e in rep["regions"].items():
    print("H %-14s n%5d dist %-22s | R15 amp %.2f corr %.2f groove %s | R30 amp %.2f corr %.2f groove %s" % (
        g, e["probes"], e["signed_dist_mm_mean_p5_p95"], e["R15"]["amplitude_ratio"], e["R15"]["correlation"], e["R15"]["deepest10pct_groove_mm_source_vs_current"],
        e["R30"]["amplitude_ratio"], e["R30"]["correlation"], e["R30"]["deepest10pct_groove_mm_source_vs_current"]))
