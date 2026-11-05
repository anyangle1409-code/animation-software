"""Anatomical axillary boundary for the upper-arm weights (fixes the "batwing") - writes a NEW file.

Cause found (see review README, AX2): the upper arm carries weight on the side of the ribcage down to ~30 cm below the
shoulder joint (mean 0.19-0.20 at 6-18 cm), and the Task-4 shoulder cap's loops start on the chest wall up to 18 cm
below the joint. Raising the arm lifts the chest wall (80 mm average at 105 deg, 14-18 cm below the joint), which reads
as a triangular sheet of skin from the arm to the ribs.

In a real body the skin of the chest wall below the axilla stays with the ribcage; only the two axillary folds and the
axillary hollow between them go with the arm:
  * anterior fold = lower border of pectoralis major, leaving the chest wall about FRONT_Z below the joint;
  * posterior fold = latissimus dorsi + teres major, leaving the chest / back wall about BACK_Z below the joint;
  * the hollow (apex of the axilla) between them, about APEX_Z below the joint.
Here, for vertices on the trunk side of the arm root (medial of the shoulder joint by more than MEDIAL), the upper arm's
weight is limited by that contour: full (unchanged) above it, fading to zero over FADE below it, zero further down.
The same contour limits the SCAPULA's weight on the lateral chest wall in front of the posterior axillary line
(POST_AX_Y behind the joint): that skin lies on the ribs (serratus anterior), and bone-heat gave it 0.3-0.5 scapula
weight, so the girdle lifted it with the arm. The back over the shoulder blade keeps its scapula weight. Weight taken
from the upper arm / scapula goes to the vertex's spine / pelvis bones in their existing proportions (spine_02 if none). The arm itself (lateral of the arm root) and everything above the contour are untouched, so
the deltoid, the folds and the upper pectoral / latissimus keep their weights. At most 4 influences, normalised.

usage: python3.13 axillary_fold_weights_blender.py -- <bound .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
FRONT_Z, APEX_Z, BACK_Z = 0.110, 0.090, 0.130    # depth of the fold line below the shoulder joint (m)
FRONT_Y, BACK_Y = 0.045, 0.045                    # front / back reach from the joint's y where the folds lie
MEDIAL = 0.025                                     # trunk side = more than this medial of the shoulder joint
FADE = 0.030
POST_AX_Y = 0.030                                  # posterior axillary line: this far behind the joint's y
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
V = np.array([v.co[:] for v in me.vertices]); NV = len(V)
GN = {g.index: g.name for g in body.vertex_groups}
W = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        W[v.index][GN[g.group]] = g.weight
rep = {"method": __doc__.split("usage")[0].strip(), "params": {"front_z": FRONT_Z, "apex_z": APEX_Z, "back_z": BACK_Z, "medial": MEDIAL, "fade": FADE}, "sides": {}}


def smooth01(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


for sd, sg in (("r", 1), ("l", -1)):
    gh = np.array(rig.matrix_world @ rig.data.bones[f"upperarm_{sd}"].head_local); arm = f"upperarm_{sd}"
    dy = V[:, 1] - gh[1]                                      # -y is front
    # contour depth below the joint as a function of front-back position (front fold -> apex -> back fold)
    tf = smooth01(-dy / FRONT_Y); tb = smooth01(dy / BACK_Y)
    depth = APEX_Z + (FRONT_Z - APEX_Z) * tf + (BACK_Z - APEX_Z) * tb
    below = (gh[2] - V[:, 2]) - depth                          # > 0: below the fold line
    medial = (gh[0] - V[:, 0]) * sg - MEDIAL                   # > 0: on the trunk side of the arm root
    side = V[:, 0] * sg > 0.02
    keep = 1.0 - smooth01(below / FADE) * smooth01(medial / 0.02)
    # the lateral chest wall in front of the posterior axillary line lies on the ribs (serratus anterior), not on the
    # shoulder blade: below the fold line it does not follow the scapula either
    scap = f"scapula_{sd}"
    keep_s = 1.0 - smooth01(below / FADE) * smooth01(medial / 0.02) * (1.0 - smooth01((dy - POST_AX_Y) / 0.03))
    changed = 0; moved_w = 0.0; moved_s = 0.0
    for i in np.where(side & ((keep < 0.999) | (keep_s < 0.999)))[0]:
        w = dict(W[i]); give = 0.0
        for bone, k in ((arm, keep[i]), (scap, keep_s[i])):
            wb = w.get(bone, 0.0)
            if wb > 1e-5 and k < 0.999:
                nb = wb * float(k); give += wb - nb
                if bone == arm:
                    moved_w += wb - nb
                else:
                    moved_s += wb - nb
                w[bone] = nb
        if give <= 1e-6:
            continue
        trunk = {n: x for n, x in w.items() if n.startswith(("spine_", "pelvis"))}; st = sum(trunk.values())
        if st > 1e-9:
            for n, x in trunk.items():
                w[n] = x + give * x / st
        else:
            w["spine_02"] = w.get("spine_02", 0.0) + give
        top = sorted(((n, x) for n, x in w.items() if x > 1e-5), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        W[i] = {n: x / s for n, x in top}; changed += 1
    rep["sides"][sd] = {"vertices_changed": changed, "arm_weight_moved_to_trunk": round(moved_w, 2), "scapula_weight_moved_to_trunk": round(moved_s, 2)}
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {}
for i in range(NV):
    for n, x in W[i].items():
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
        groups[n].add([i], x, "REPLACE")
body["AXILLARY_FOLD_WEIGHTS"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("AXFOLD", json.dumps({k: v for k, v in rep.items() if k != "method"}))
