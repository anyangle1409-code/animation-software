"""Read-only: locate the local crumpled 'knot' at the axilla pit of a posed candidate (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/diagnose_original_v1_pit_knot_blender.py -- <out.json> <pose[,pose...]> [side=l]

For every pose, scores each shoulder-zone vertex by the worst of: collapsed incident triangle (area ratio), crease (posed dihedral cos < 0.0 where rest > 0.5),
and posed roughness (distance from neighbour mean / edge length, minus rest). The top-scoring connected cluster is reported with rest positions, regions,
LBS weights, incident triangle ids and the pose that exposes it, so a declared local edit mask can be derived from evidence.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out, poses = Path(args[0]), args[1].split(",")
side = args[2] if len(args) > 2 else "l"
ps = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = ps.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": ps.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
me = body.data
rest = np.array([v.co[:] for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([t.vertices[:] for t in me.loop_triangles])
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in me.attributes["hgpt_region"].data])
gname = {vg.index: vg.name for vg in body.vertex_groups}
EDG = np.array([e.vertices[:] for e in me.edges])
DEG = np.bincount(EDG.ravel(), minlength=len(rest)).astype(float)
EL = (np.bincount(EDG[:, 0], np.linalg.norm(rest[EDG[:, 0]] - rest[EDG[:, 1]], axis=1), len(rest)) +
      np.bincount(EDG[:, 1], np.linalg.norm(rest[EDG[:, 0]] - rest[EDG[:, 1]], axis=1), len(rest))) / DEG
sgn = -1.0 if side == "l" else 1.0
head = np.array(rig.data.bones[f"upperarm_{side}"].head_local)
near = (np.linalg.norm(rest - head, axis=1) < 0.30) & (np.sign(rest[:, 0]) * sgn >= 0)


def nrm(P):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    ar = np.linalg.norm(n, axis=1)
    return n / np.maximum(ar, 1e-18)[:, None], 0.5 * ar


def lap(Q):
    s = np.zeros_like(Q)
    np.add.at(s, EDG[:, 0], Q[EDG[:, 1]])
    np.add.at(s, EDG[:, 1], Q[EDG[:, 0]])
    return np.linalg.norm(Q - s / DEG[:, None], axis=1) / EL


n0, A0 = nrm(rest)
em = {}
for t, (x, y, z) in enumerate(tris):
    for e in ((x, y), (y, z), (z, x)):
        em.setdefault((min(e), max(e)), []).append(t)
ADJ = np.array([v for v in em.values() if len(v) == 2])
cos0 = (n0[ADJ[:, 0]] * n0[ADJ[:, 1]]).sum(axis=1)
res = {}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    P = np.array([v.co[:] for v in ev.vertices])
    n1, A1 = nrm(P)
    ratio = A1 / np.maximum(A0, 1e-18)
    cos1 = (n1[ADJ[:, 0]] * n1[ADJ[:, 1]]).sum(axis=1)
    score = np.zeros(len(rest))
    small = np.nonzero(ratio < 0.2)[0]
    for t in small:
        score[tris[t]] = np.maximum(score[tris[t]], 1.0 - ratio[t] / 0.2)
    fold = np.nonzero((cos1 < 0.0) & (cos0 > 0.5))[0]
    for k in fold:
        for t in ADJ[k]:
            score[tris[t]] = np.maximum(score[tris[t]], 1.0)
    score = np.maximum(score, np.clip(lap(P) - lap(rest) - 0.5, 0, 1))
    score[~near] = 0
    bad = np.nonzero(score > 0.3)[0]
    res[name] = {"n_bad_vertices": int(len(bad)), "bad": [{"v": int(v), "score": round(float(score[v]), 2), "region": names[int(reg[v])],
                 "rest": [round(float(c), 4) for c in rest[v]], "weights": {gname[g.group]: round(g.weight, 2) for g in me.vertices[v].groups if g.weight > 0.05}} for v in bad]}
    print("KNOT", name, len(bad), "bad vertices near the", side, "pit; regions", {names[r]: int(c) for r, c in zip(*np.unique(reg[bad], return_counts=True))} if len(bad) else {})
reset()
out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
