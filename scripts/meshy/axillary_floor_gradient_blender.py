"""Axillary floor: graded arm share across the vault loops - writes a NEW file.

STATUS: REJECTED (round AX3). It takes the arm share from the trunk side of the vault by radial distance, which reaches
the chest wall: armpit stretch p95 rose to 6-10.6 and the 140-180 mm trunk band lifted up to 192 mm at 105 deg (the
batwing pattern). The adopted replacement keeps the torso rim fixed (axillary_ring_relax_blender.py).

After the axillary contour (06g) and arm-tube ownership, the trunk side of the axilla follows the ribcage and the arm
tube follows the arm; the step between them lands on one or two rows of the Task-4 cap loops in the vault, which then
take the whole stretch of a raised arm as long thin strips. Real axillary skin (the floor of the hollow, over the
axillary fascia) stretches progressively between the chest wall and the arm.

For vertices of the ARM topology (cap loops; not the torso shell, so the chest wall below the cap seam keeps following
the ribcage) on the trunk side of the arm tube - radial distance r from the humerus axis between TUBE_R and
TUBE_R + SPAN, along the humerus between T_MIN and T_MAX - the arm's share is set to at least
  share(r) = SHARE_MAX * smoothstep(1 - (r - TUBE_R) / SPAN)
(the vault wall next to the arm follows it most, the edge on the chest wall least). The added weight comes from the
vertex's trunk / girdle bones in proportion. Nothing else changes. At most 4 influences.

usage: python3.13 axillary_floor_gradient_blender.py -- <bound .blend> <out NEW .blend> <report .json> [share_max] [span m]
"""
import json
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
SHARE_MAX = float(a[3]) if len(a) > 3 else 0.7
SPAN = float(a[4]) if len(a) > 4 else 0.07
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
TUBE_R, T_MIN, T_MAX = 0.070, -0.02, 0.20
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
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"share_max": SHARE_MAX, "span": SPAN, "tube_r": TUBE_R}, "sides": {}}
for sd, sg in (("r", 1), ("l", -1)):
    b = rig.data.bones[f"upperarm_{sd}"]; gh = np.array(rig.matrix_world @ b.head_local); el = np.array(rig.matrix_world @ b.tail_local)
    u = (el - gh) / np.linalg.norm(el - gh); t = (V - gh) @ u; off = (V - gh) - np.outer(t, u); r = np.linalg.norm(off, axis=1)
    medial = off[:, 0] * sg < 0                                # trunk side of the arm axis
    sel = armtopo & (V[:, 0] * sg > 0.05) & medial & (r > TUBE_R) & (r < TUBE_R + SPAN) & (t > T_MIN) & (t < T_MAX)
    x = np.clip(1 - (r - TUBE_R) / SPAN, 0, 1); target = SHARE_MAX * x * x * (3 - 2 * x)
    arm_b = (f"upperarm_{sd}", f"forearm_{sd}", f"forearm_tw1_{sd}"); changed = 0; added = 0.0
    for i in np.where(sel)[0]:
        w = dict(W[i]); share = sum(w.get(n, 0.0) for n in arm_b)
        if share >= target[i] - 1e-3:
            continue
        tr = {n: y for n, y in w.items() if n.startswith(TRUNK)}; ts = sum(tr.values()); take = min(target[i] - share, ts)
        if take <= 1e-5:
            continue
        for n, y in tr.items():
            w[n] = y - take * y / ts
        w[f"upperarm_{sd}"] = w.get(f"upperarm_{sd}", 0.0) + take
        top = sorted(((n, y) for n, y in w.items() if y > 1e-5), key=lambda kv: -kv[1])[:4]; s = sum(y for _, y in top)
        W[i] = {n: y / s for n, y in top}; changed += 1; added += take
    rep["sides"][sd] = {"floor_vertices": int(sel.sum()), "vertices_changed": changed, "arm_weight_added": round(added, 2)}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, y in W[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], y, "REPLACE")
body["AXILLARY_FLOOR_GRADIENT"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("FLOOR", json.dumps({k: v for k, v in rep.items() if k != "method"}))
