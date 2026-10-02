"""Read-only: list the most stretched edges of a posed candidate (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/diagnose_original_v1_worst_edges_blender.py -- <pose> <out.json> [top_n=40]

Uses the pose script's own pose definition and the evaluated (shape keys + skinning) mesh, so it sees exactly what a render shows.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
pose, out = args[0], Path(args[1])
top = int(args[2]) if len(args) > 2 else 40
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
reset()
rig.location = (0, 0, 0)
ns["HANDLE"].clear()
POSES[pose]()
upd()
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
P = np.array([v.co[:] for v in ev.vertices])
rest = np.array([v.co[:] for v in body.data.vertices])
edges = np.array([e.vertices[:] for e in body.data.edges])
r = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1) / np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
gname = {vg.index: vg.name for vg in body.vertex_groups}
rows = []
for k in np.argsort(-r)[:top]:
    a, b = (int(x) for x in edges[k])
    rows.append({"edge": [a, b], "ratio": round(float(r[k]), 3), "regions": [names[int(reg[a])], names[int(reg[b])]],
                 "rest_x": [round(float(rest[a][0]), 3), round(float(rest[b][0]), 3)], "rest_z": [round(float(rest[a][2]), 3), round(float(rest[b][2]), 3)],
                 "weights": [{gname[g.group]: round(g.weight, 2) for g in body.data.vertices[v].groups if g.weight > 0.05} for v in (a, b)]})
out.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
for x in rows[:12]:
    print(x["ratio"], x["regions"], x["edge"], x["weights"])
