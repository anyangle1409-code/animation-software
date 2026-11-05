"""Shoulder corrective shape keys from an edge-length (elastic) solve - writes a NEW file.

For each side and each key elevation (90, 135, 170 deg; the arm raised in the scapular plane, elbow straight, the
clavicle lifting 25 deg at 170 - the motion of shoulder_pose_lib.arm_pose) the posed skin of the shoulder region is
solved, not smoothed:
  * every edge is pulled towards a TARGET length: its posed length clamped to [rest x (1 - MAX_COMP), rest x (1 +
    MAX_STRETCH)] - stretch above the limit is redistributed to neighbouring skin, bunching below it is released,
    edges inside the limits keep their posed length (shape detail is kept);
  * VOLUME guard: no vertex may end closer to its dominant bone's segment than it was at rest (x VOL_K), so the
    solve can neither collapse the deltoid nor sink the armpit;
  * the region is the skin within R_OUT of the posed shoulder joint on that side; the solved displacement fades from
    1 inside R_IN to 0 at R_OUT, so the boundary is untouched.
The posed-space displacement is converted to rest space with each vertex's own skinning transform (the inverse of
the weighted bone matrices) and stored as shape key CORR_<side>_<elev>. Each key is driven by the arm's elevation
relative to the trunk (ROTATION_DIFF upper arm vs arm_ref, from the scapula-glide file) with a tent function that
peaks at its elevation and is zero at the neighbouring keys (a 170 key stays on above 170; a last key below 170 fades out by its elevation + 45). The displacement field is smoothed
(DELTA_SMOOTH passes; the displacement, not the mesh) and where the key would create self-intersections (beyond those the uncorrected pose already has)
it is scaled down locally and the scale field is smoothed over the mesh, so it fades gradually (no shards).

usage: python3.13 build_shoulder_correctives_blender.py -- <glide .blend> <out NEW .blend> <report .json> [keys e.g. 90,135,170] [delta smooth passes] [scale mode vertex|smooth]
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
KEYS = tuple(int(x) for x in a[3].split(",")) if len(a) > 3 else (90, 135, 170)
MAX_STRETCH, MAX_COMP, VOL_K = 0.35, 0.15, 0.97
R_IN, R_OUT, ITERS = 0.15, 0.22, 250
DELTA_SMOOTH = int(a[4]) if len(a) > 4 else 5
SCALE_MODE = a[5] if len(a) > 5 else "smooth"   # "vertex": per-vertex halving (first build), "smooth": smoothed scale field
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; pb = rig.pose.bones
MW = np.array(rig.matrix_world)
NV = len(me.vertices); E = np.array([e.vertices[:] for e in me.edges])
P = np.array([p.vertices[:] for p in me.polygons])
GN = {g.index: g.name for g in body.vertex_groups}
WT = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5 and GN[g.group] in rig.data.bones and rig.data.bones[GN[g.group]].use_deform:
            WT[v.index][GN[g.group]] = g.weight
DOM = [max(w, key=w.get) if w else None for w in WT]
if not me.shape_keys:
    body.shape_key_add(name="Basis", from_mix=False)


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); bpy.data.meshes.remove(m); return V.reshape(-1, 3)


def skin_mats():
    """per vertex 3x3 linear part of the blended bone transform (rest -> pose)"""
    bm_ = {}
    for n in {b for w in WT for b in w}:
        b = rig.data.bones[n]; bm_[n] = np.array(pb[n].matrix @ b.matrix_local.inverted())[:3, :3]
    M = np.zeros((NV, 3, 3))
    for i, w in enumerate(WT):
        s = sum(w.values())
        for n, x in w.items():
            M[i] += bm_[n] * (x / s)
    return M


def seg_dist(X, bones):
    out = np.zeros(len(X))
    for i, (x, n) in enumerate(zip(X, bones)):
        if n is None:
            continue
        h = np.array(MW @ np.r_[np.array(pb[n].head), 1])[:3]; t = np.array(MW @ np.r_[np.array(pb[n].tail), 1])[:3]
        d = t - h; u = np.clip((x - h) @ d / max(d @ d, 1e-12), 0, 1); out[i] = np.linalg.norm(x - (h + u * d))
    return out


def intersect_verts(V):
    T = []
    for f in P:
        T += [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
    b = BVHTree.FromPolygons([Vector(p) for p in V], T, all_triangles=True); bad = set()
    for i, j in b.overlap(b):
        if not set(T[i]) & set(T[j]):
            bad |= set(T[i]) | set(T[j])
    return bad


rest = rest_capture(rig); V0 = evaluated(); L0 = np.linalg.norm(V0[E[:, 0]] - V0[E[:, 1]], axis=1)
D0 = seg_dist(V0, DOM)
base_bad = intersect_verts(V0)
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"max_stretch": MAX_STRETCH, "max_comp": MAX_COMP, "vol_k": VOL_K, "r_in": R_IN, "r_out": R_OUT, "iters": ITERS}, "keys": {}}
for sd in ("r", "l"):
    sg = 1 if sd == "r" else -1
    for el in KEYS:
        rest_restore(rig, rest); arm_pose(rig, sd, el, 30, 175, 25.0 * el / 170.0); bpy.context.view_layer.update()
        Vp = evaluated(); gh = np.array(MW @ np.r_[np.array(pb[f"upperarm_{sd}"].head), 1])[:3]
        d = np.linalg.norm(Vp - gh, axis=1); fall = np.clip((R_OUT - d) / (R_OUT - R_IN), 0, 1) * (Vp[:, 0] * sg > -0.01)
        free = fall > 0; X = Vp.copy()
        Lp = np.linalg.norm(Vp[E[:, 0]] - Vp[E[:, 1]], axis=1); Lt = np.clip(Lp, L0 * (1 - MAX_COMP), L0 * (1 + MAX_STRETCH))
        ein = free[E[:, 0]] | free[E[:, 1]]; Ei = E[ein]; Lti = Lt[ein]
        for _ in range(ITERS):
            dv = X[Ei[:, 1]] - X[Ei[:, 0]]; L = np.maximum(np.linalg.norm(dv, axis=1), 1e-9)
            corr = (dv / L[:, None]) * ((L - Lti) / 2)[:, None]
            acc = np.zeros_like(X); cnt = np.zeros(NV)
            np.add.at(acc, Ei[:, 0], corr); np.add.at(acc, Ei[:, 1], -corr); np.add.at(cnt, Ei[:, 0], 1); np.add.at(cnt, Ei[:, 1], 1)
            step = acc / np.maximum(cnt, 1)[:, None] * 0.8
            X[free] += step[free] * fall[free][:, None]
        # volume guard: not closer to the dominant bone than at rest
        idx = np.where(free)[0]; Dx = seg_dist(X[idx], [DOM[i] for i in idx])
        for k, i in enumerate(idx):
            if DOM[i] and Dx[k] < D0[i] * VOL_K and Dx[k] > 1e-6:
                n = DOM[i]; h = np.array(MW @ np.r_[np.array(pb[n].head), 1])[:3]; t = np.array(MW @ np.r_[np.array(pb[n].tail), 1])[:3]
                dd = t - h; u = np.clip((X[i] - h) @ dd / (dd @ dd), 0, 1); c = h + u * dd; X[i] = c + (X[i] - c) / Dx[k] * D0[i] * VOL_K
        delta = X - Vp
        # smooth the DISPLACEMENT field (not the mesh): neighbouring vertices get coherent corrections, no shards
        nbr = [[] for _ in range(NV)]
        for i, j in Ei:
            nbr[i].append(j); nbr[j].append(i)
        fi = np.where(free)[0]
        for _ in range(DELTA_SMOOTH):
            delta[fi] = 0.5 * delta[fi] + 0.5 * np.array([delta[nbr[i]].mean(0) if nbr[i] else delta[i] for i in fi])
        delta *= fall[:, None]
        # no new self-intersections: scale back the offending vertices, then SMOOTH the scale field over the mesh so the
        # key fades gradually around them (no shards); repeat until the pose has no contacts beyond its own
        pose_bad = intersect_verts(Vp); scale = np.ones(NV); rounds = 0
        if SCALE_MODE == "vertex":                         # first-build behaviour: halve offending vertices only
            for _ in range(6):
                bad = [i for i in intersect_verts(Vp + delta * scale[:, None]) - base_bad if free[i]]
                if not bad:
                    break
                for i in bad:
                    scale[i] *= 0.5
            rounds = 99
        while rounds < 12:
            bad = [i for i in intersect_verts(Vp + delta * scale[:, None]) - pose_bad if free[i]]
            if not bad:
                break
            for i in bad:
                scale[i] *= 0.4
            for _ in range(4):
                sm = np.array([min(scale[i], np.mean(scale[nbr[i]])) if nbr[i] else scale[i] for i in fi])
                scale[fi] = sm
            rounds += 1
        g = float(scale[fi].mean())
        M = skin_mats(); dr = np.einsum("nij,nj->ni", np.linalg.inv(M), delta * scale[:, None])
        name = f"CORR_{sd.upper()}_{el:03d}"; sk = body.shape_key_add(name=name, from_mix=False)
        co = np.array([v.co[:] for v in me.vertices]) + dr; sk.data.foreach_set("co", co.ravel())
        Lf = np.linalg.norm((Vp + delta * scale[:, None])[E[:, 0]] - (Vp + delta * scale[:, None])[E[:, 1]], axis=1) / L0
        rep["keys"][name] = {"moved_vertices": int((np.linalg.norm(delta, axis=1) > 5e-4).sum()), "max_move_mm": round(float(np.linalg.norm(delta, axis=1).max()) * 1000, 1),
                             "stretch_p99_before_after": [round(float(np.percentile((Lp / L0)[ein], 99)), 2), round(float(np.percentile(Lf[ein], 99)), 2)],
                             "compress_p1_before_after": [round(float(np.percentile((Lp / L0)[ein], 1)), 2), round(float(np.percentile(Lf[ein], 1)), 2)],
                             "mean_key_scale_in_region": round(float(g), 3), "min_key_scale": round(float(scale[fi].min()), 3)}
        print("KEY", name, json.dumps(rep["keys"][name]), flush=True)
rest_restore(rig, rest)
# drivers: tent functions of the trunk-relative elevation
kb = me.shape_keys.key_blocks
for sd in ("r", "l"):
    e0 = None
    qa = rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion(); qr = rig.data.bones[f"arm_ref_{sd}"].matrix_local.to_quaternion()
    e0 = qr.rotation_difference(qa).angle
    pts = [math.radians(45)] + [math.radians(k) for k in KEYS]
    for k_i, el in enumerate(KEYS):
        lo, mid = pts[k_i], pts[k_i + 1]; hi = pts[k_i + 2] if k_i + 2 < len(pts) else (None if el >= 170 else math.radians(el + 45))
        # elevation in the same frame as the drive: e - e0 + rest elevation of the arm from vertical (measured)
        expr = (f"max(0.0, min(1.0, (el - {lo:.5f}) / {mid - lo:.5f}))" if hi is None else
                f"max(0.0, min((el - {lo:.5f}) / {mid - lo:.5f}, ({hi:.5f} - el) / {hi - mid:.5f}))")
        fc = kb[f"CORR_{sd.upper()}_{el:03d}"].driver_add("value"); dr_ = fc.driver; dr_.type = "SCRIPTED"
        v = dr_.variables.new(); v.name = "e"; v.type = "ROTATION_DIFF"
        v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"arm_ref_{sd}"
        u = (rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].tail_local - rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local).normalized()
        el_rest = math.acos(max(-1, min(1, -u.z)))
        dr_.expression = expr.replace("el", f"(e - {e0:.5f} + {el_rest:.5f})")
    rep[f"drive_{sd}"] = {"rotation_diff_rest_rad": round(e0, 4)}
body["PHASE3_SHOULDER_CORRECTIVES"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("CORR done")
