"""Arms-down contact correction (upper arm against latissimus / chest wall) - writes a NEW file.

Result on 06g -> rig 06h: shoulder-region intersecting pairs at 8 / 5 deg from vertical 17 / 129 -> 0 / 0; stand pose
17 -> 0; curl 347 -> 216 (the rest is forearm against biceps at the elbow, not the shoulder); 45-170 deg identical (the
key is zero there); continuous sweep unchanged (max 4 pairs, 5.8 mm/deg).

Since the axillary contour weights (06g) the chest wall no longer moves away with the arm, so bringing the arm closer
to the body than its rest angle (17.5 deg from vertical) pushes inner-arm skin into the latissimus: 0 / 34 / 258
intersecting pairs at 12 / 8 / 5 deg. That is real tissue contact, not a weighting error, so it is corrected as contact:
  * pose: both arms at E_KEY deg from vertical (10 deg forwards, elbow at its rest bend) - the arms-down limit;
  * contact is taken ONLY from triangle pairs that really intersect (non-adjacent, facing each other) near the shoulder:
    each vertex of one triangle that lies behind the other triangle's plane is pushed out along that normal by half
    the depth (+ GAP), and vice versa, so both skins meet at a shared contact surface (mutual flattening); repeated up to
    ITERS times until no pair intersects. (A first version split the mesh into arm / trunk by dominant bone and pushed
    every vertex 'inside' the other part: next to the part border, where both are one continuous surface, that found
    false contacts and tore notches into the front axillary fold - rejected.)
  * ROUNDS times: resolve contact, then smooth the correction FIELD twice over the shoulder region (the field, not the
    surface - each vertex's displacement takes half its neighbours' mean), so the push spreads into a broad, even
    flattening instead of a dent or ridge; a final contact solve ends it. (A second version excluded vertices near the
    dominant-bone border and zeroed the field there: clean, but the real contacts sit 3-10 edges apart across that
    border, so it removed almost nothing - rejected.)
  * the posed-space displacement is converted to rest space with each vertex's skinning transform (shape key
    CONTACT_ADD_<S>) and driven by the arm's elevation: 0 at and above E_ON (3 deg below the rest angle), 1 at E_KEY,
    held at 1 below. Above E_ON the key is exactly zero, so the raised-arm range (45-170 deg) cannot change.

usage: python3.13 build_adduction_contact_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
sys.path.insert(0, str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402
E_KEY, ON_MARGIN, GAP, ITERS, ROUNDS = 4.0, 3.0, 0.0008, 25, 6
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; pb = rig.pose.bones
NV = len(me.vertices); P = [tuple(p.vertices) for p in me.polygons]
E = np.array([e.vertices[:] for e in me.edges]); nbr = [[] for _ in range(NV)]
for i, j in E:
    nbr[i].append(j); nbr[j].append(i)
GN = {g.index: g.name for g in body.vertex_groups}
WT = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        if g.weight > 1e-5 and GN[g.group] in rig.data.bones and rig.data.bones[GN[g.group]].use_deform:
            WT[v.index][GN[g.group]] = g.weight
if not me.shape_keys:
    body.shape_key_add(name="Basis", from_mix=False)


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); bpy.data.meshes.remove(m); return V.reshape(-1, 3)


def skin_inv():
    bm_ = {n: np.array(pb[n].matrix @ rig.data.bones[n].matrix_local.inverted())[:3, :3] for n in {b for w in WT for b in w}}
    M = np.zeros((NV, 3, 3))
    for i, w in enumerate(WT):
        s = sum(w.values())
        for n, x in w.items():
            M[i] += bm_[n] * (x / s)
    return np.linalg.inv(M)


def count_hits(V, region):
    T = []
    for f in P:
        T += [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
    b = BVHTree.FromPolygons([Vector(p) for p in V], T, all_triangles=True); n = 0
    for i, j in b.overlap(b):
        if not set(T[i]) & set(T[j]) and (region[T[i][0]] or region[T[j][0]]):
            n += 1
    return n


rest = rest_capture(rig); rep = {"method": __doc__.split("usage")[0].strip(), "e_key_deg": E_KEY, "sides": {}}
REST_EL = {}
for sd in ("l", "r"):
    u = (rig.matrix_world @ pb[f"upperarm_{sd}"].tail - rig.matrix_world @ pb[f"upperarm_{sd}"].head).normalized()
    REST_EL[sd] = math.degrees(math.acos(max(-1, min(1, -u.z))))
for sd in ("r", "l"):
    sg = 1 if sd == "r" else -1
    rest_restore(rig, rest); arm_pose(rig, sd, E_KEY, 10, 170, 0); bpy.context.view_layer.update()
    Vp = evaluated(); gh = np.array(rig.matrix_world @ pb[f"upperarm_{sd}"].head)
    region = (np.linalg.norm(Vp - gh, axis=1) < 0.30) & (Vp[:, 0] * sg > 0.03)
    hits0 = count_hits(Vp, region); X = Vp.copy()
    TRI = []
    for f in P:
        TRI += [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
    TRI = np.array(TRI); TS = [set(t) for t in TRI]; treg = region[TRI].all(1)

    def solve(X, iters):
        for it in range(iters):                               # collision-driven: only vertices of truly intersecting,
            b = BVHTree.FromPolygons([Vector(p) for p in X], TRI.tolist(), all_triangles=True)   # non-adjacent triangles
            Nf = np.cross(X[TRI[:, 1]] - X[TRI[:, 0]], X[TRI[:, 2]] - X[TRI[:, 0]]); Nf /= np.maximum(np.linalg.norm(Nf, axis=1)[:, None], 1e-12)
            pairs = [(i, j) for i, j in b.overlap(b) if i < j and treg[i] and treg[j] and not (TS[i] & TS[j]) and Nf[i] @ Nf[j] < 0.3]
            if not pairs:
                return X, it
            acc = np.zeros_like(X); cnt = np.zeros(NV)
            for i, j in pairs:
                for A, B in ((i, j), (j, i)):
                    for v in TRI[A]:
                        d = (X[v] - X[TRI[B][0]]) @ Nf[B]
                        if d < GAP:                            # behind (inside) the other surface: push out half-way
                            acc[v] += Nf[B] * ((GAP - d) / 2); cnt[v] += 1
            m = cnt > 0; X = X.copy(); X[m] += acc[m] / cnt[m][:, None]
        return X, iters

    def smooth_field(delta):                                   # smooth the correction FIELD (not the surface): each
        nd = delta.copy()                                      # vertex in the region takes half its neighbours' mean
        for i in np.where(region)[0]:
            nb = [j for j in nbr[i] if region[j]]
            if nb:
                nd[i] = 0.5 * delta[i] + 0.5 * np.mean(delta[nb], axis=0)
        return nd
    X = Vp.copy()
    for rnd in range(ROUNDS):                                  # alternate: resolve contact, then let it spread smoothly
        X, _ = solve(X, ITERS); X = Vp + smooth_field(smooth_field(X - Vp))
    X, _ = solve(X, ITERS)                                     # end on a contact solve
    delta = X - Vp
    hits1 = count_hits(Vp + delta, region)
    dr = np.einsum("nij,nj->ni", skin_inv(), delta)
    name = f"CONTACT_ADD_{sd.upper()}"; sk = body.shape_key_add(name=name, from_mix=False)
    co = np.array([v.co[:] for v in me.vertices]) + dr; sk.data.foreach_set("co", co.ravel())
    rep["sides"][sd] = {"intersections_at_key_pose_before_after": [hits0, hits1], "moved_vertices": int((np.linalg.norm(delta, axis=1) > 1e-4).sum()),
                        "max_move_mm": round(float(np.linalg.norm(delta, axis=1).max()) * 1000, 1)}
    print("KEY", name, json.dumps(rep["sides"][sd]), flush=True)
rest_restore(rig, rest)
kb = me.shape_keys.key_blocks
for sd in ("r", "l"):
    qa = rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion(); qr = rig.data.bones[f"arm_ref_{sd}"].matrix_local.to_quaternion()
    e0 = qr.rotation_difference(qa).angle; on = math.radians(REST_EL[sd] - ON_MARGIN); key = math.radians(E_KEY)
    el = f"(e - {e0:.5f} + {math.radians(REST_EL[sd]):.5f})"
    fc = kb[f"CONTACT_ADD_{sd.upper()}"].driver_add("value"); d = fc.driver; d.type = "SCRIPTED"
    v = d.variables.new(); v.name = "e"; v.type = "ROTATION_DIFF"
    v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"arm_ref_{sd}"
    d.expression = f"max(0.0, min(1.0, ({on:.5f} - {el}) / {on - key:.5f}))"
    rep["sides"][sd]["drive_on_deg"] = round(REST_EL[sd] - ON_MARGIN, 1)
body["ADDUCTION_CONTACT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("CONTACT done")
