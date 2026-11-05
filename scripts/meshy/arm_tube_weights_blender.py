"""Inner-arm ownership: the skin of the upper-arm tube follows the arm - writes a NEW file.

STATUS: TRIAL, NOT ADOPTED (round AX3). Anatomically sound and no chest lift, but the renders at 105-170 deg are almost
identical to 06g while armpit stretch p95 rose (90 deg 4.53, 170 deg 7.8); the inner-arm strips are a ring-gradient
problem, fixed by axillary_ring_relax_blender.py.

Measured on 06g: on the INNER (medial) face of the upper arm, 6-12 cm down the humerus, the arm bones carry only
0.58-0.59 of the weight (0.84 at 15 cm), the rest is trunk / girdle weight that bone-heat blended in because the inner
arm lies against the chest at rest. Raising the arm leaves that strip behind with the trunk, which stretches it into
long thin faces and the sharp crease on the inner arm at 135 deg. Anatomically that skin covers biceps,
coracobrachialis and triceps - it is the lateral wall of the axilla and belongs to the arm.

For vertices of the arm topology (not the torso shell, hand or leg parts) inside the arm tube - radial distance from the
humerus axis < TUBE_R, position along the humerus t between 0 and its length - the arm's share (upper arm + forearm)
is raised to at least ramp(t) = smoothstep((t - T0) / (T1 - T0)); the added weight comes out of the vertex's trunk /
girdle bones (spine, clavicle, scapula, scapula glide) in proportion. Vertices already above the ramp are untouched,
so the deltoid cap (top of the tube), the fold contour and the chest wall do not change. At most 4 influences.

usage: python3.13 arm_tube_weights_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
TUBE_R, T0, T1 = 0.070, 0.02, 0.08
TRUNK = ("spine_", "clavicle_", "scapula_", "scap_glide_", "pelvis")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
LR, LC = bm.verts.layers.int["t3_row"], bm.verts.layers.int["t3_col"]; L4, L5 = bm.verts.layers.int["t4_part"], bm.verts.layers.int["t5_part"]
armtopo = np.array([not (v[LR] > 0 or v[LC] > 0) and v[L4] == 0 and v[L5] == 0 and v.co.z > 0.9 for v in bm.verts])
V = np.array([v.co[:] for v in me.vertices]); NV = len(V)
GN = {g.index: g.name for g in body.vertex_groups}
W = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        W[v.index][GN[g.group]] = g.weight
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"tube_r": TUBE_R, "t0": T0, "t1": T1}, "sides": {}}
for sd, sg in (("r", 1), ("l", -1)):
    b = rig.data.bones[f"upperarm_{sd}"]; gh = np.array(rig.matrix_world @ b.head_local); el = np.array(rig.matrix_world @ b.tail_local)
    u = (el - gh) / np.linalg.norm(el - gh); L = np.linalg.norm(el - gh)
    t = (V - gh) @ u; rad = np.linalg.norm((V - gh) - np.outer(t, u), axis=1)
    sel = armtopo & (V[:, 0] * sg > 0.05) & (rad < TUBE_R) & (t > 0) & (t < L)
    tt = np.clip((t - T0) / (T1 - T0), 0, 1); ramp = tt * tt * (3 - 2 * tt)
    arm_b = (f"upperarm_{sd}", f"forearm_{sd}", f"forearm_tw1_{sd}"); changed = 0; added = 0.0
    for i in np.where(sel)[0]:
        w = dict(W[i]); share = sum(w.get(n, 0.0) for n in arm_b)
        if share >= ramp[i] - 1e-3:
            continue
        need = ramp[i] - share; tr = {n: x for n, x in w.items() if n.startswith(TRUNK)}; ts = sum(tr.values())
        take = min(need, ts)
        if take <= 1e-5:
            continue
        for n, x in tr.items():
            w[n] = x - take * x / ts
        w[f"upperarm_{sd}"] = w.get(f"upperarm_{sd}", 0.0) + take
        top = sorted(((n, x) for n, x in w.items() if x > 1e-5), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        W[i] = {n: x / s for n, x in top}; changed += 1; added += take
    rep["sides"][sd] = {"tube_vertices": int(sel.sum()), "vertices_changed": changed, "arm_weight_added": round(added, 2)}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, x in W[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], x, "REPLACE")
body["ARM_TUBE_WEIGHTS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("TUBE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
