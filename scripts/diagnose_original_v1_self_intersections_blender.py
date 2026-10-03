"""Read-only: where do the self-intersecting face pairs of a posed candidate sit? (never saves the .blend)

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/diagnose_original_v1_self_intersections_blender.py -- <out.json> <pose[,pose...]>

Uses exactly the pose-test definition (evaluated bare mesh, polygon BVH overlap, pairs sharing a vertex excluded). For each pose it reports the pair
count by side (x<0 = left), by pair type (same-region / cross-region), the posed centroid bounding boxes of each side, the dominant skin bones of the
participating vertices, and the vertex ids that take part most often (the candidates for a targeted collision-resolution mask).
"""
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
out, poses = Path(args[0]), args[1].split(",")
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
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in me.attributes["hgpt_region"].data])
polys = [tuple(p.vertices) for p in me.polygons]
psets = [set(p) for p in polys]
gname = {vg.index: vg.name for vg in body.vertex_groups}
dom = []
for v in me.vertices:
    gs = sorted(((g.weight, gname[g.group]) for g in v.groups), reverse=True)
    dom.append(gs[0][1] if gs else "none")
res = {}
for name in poses:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    V = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
    tree = BVHTree.FromPolygons([Vector(p) for p in V], polys)
    pairs = {tuple(sorted((a, b))) for a, b in tree.overlap(tree) if a != b and not (psets[a] & psets[b])}
    side = Counter()
    kind = Counter()
    vcount = Counter()
    bones = Counter()
    cent = {"left": [], "right": [], "mid": []}
    for a, b in pairs:
        ca, cb = V[list(polys[a])].mean(axis=0), V[list(polys[b])].mean(axis=0)
        mid = (ca + cb) / 2
        s = "left" if mid[0] < -0.02 else ("right" if mid[0] > 0.02 else "mid")
        side[s] += 1
        cent[s].append(mid)
        ra, rb = names[int(reg[polys[a][0]])], names[int(reg[polys[b][0]])]
        kind[ra + "|" + rb if ra != rb else ra] += 1
        for v in set(polys[a]) | set(polys[b]):
            vcount[v] += 1
            bones[dom[v]] += 1
    res[name] = {"pairs": len(pairs), "by_side": dict(side), "by_region_pair": dict(kind), "dominant_bones": bones.most_common(8),
                 "bbox_posed": {k: ([round(float(x), 3) for x in np.min(v, axis=0)], [round(float(x), 3) for x in np.max(v, axis=0)]) for k, v in cent.items() if v},
                 "top_vertices": [[int(v), int(c)] for v, c in vcount.most_common(40)]}
    print("SI", name, len(pairs), dict(side), dict(kind), bones.most_common(4))
reset()
out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
