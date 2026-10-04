"""Read-only: the EXACT self-intersecting polygon pairs of one posed candidate, plus the full skin-weight matrix (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/diagnose_original_v1_pair_list_blender.py -- <out.json> <pose> [<out weights.npz>]

Same pair definition as the pose test (evaluated bare mesh, polygon BVH overlap, pairs sharing a vertex excluded). For every pair: the two polygon ids,
their vertex ids, regions, dominant bones, posed centroid, and the rest-pose distance between the two polygons (large = a genuine contact, small = a
neighbouring-surface pair). The optional npz holds the (vertex, bone) weight matrix and rest positions for weight-level comparison between candidates.
"""
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
out, pose = Path(args[0]), args[1]
wout = Path(args[2]) if len(args) > 2 else None
ps = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = ps.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": ps.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "defs", "exec"), ns)
import importlib.util as _ilu   # flexion driver (r86+), outside the frozen section; no-op without the keys
_sp = _ilu.spec_from_file_location("original_v1_flexion_driver", str(ps.with_name("original_v1_flexion_driver.py")))
_fd = _ilu.module_from_spec(_sp)
_sp.loader.exec_module(_fd)
_fd.install(ns)
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
rest = np.array([v.co[:] for v in me.vertices])
nV = len(rest)
bone_names = sorted(gname.values())
bidx = {n: i for i, n in enumerate(bone_names)}
W = np.zeros((nV, len(bone_names)))
dom = []
for v in me.vertices:
    gs = sorted(((g.weight, gname[g.group]) for g in v.groups), reverse=True)
    dom.append(gs[0][1] if gs else "none")
    for g in v.groups:
        W[v.index, bidx[gname[g.group]]] = g.weight
reset()
rig.location = (0, 0, 0)
ns["HANDLE"].clear()
POSES[pose]()
upd()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
V = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
tree = BVHTree.FromPolygons([Vector(p) for p in V], polys)
pairs = sorted({tuple(sorted((a, b))) for a, b in tree.overlap(tree) if a != b and not (psets[a] & psets[b])})
rows = []
for a, b in pairs:
    ca, cb = V[list(polys[a])].mean(axis=0), V[list(polys[b])].mean(axis=0)
    ra, rb = rest[list(polys[a])].mean(axis=0), rest[list(polys[b])].mean(axis=0)
    rows.append({"polys": [a, b], "verts": [list(polys[a]), list(polys[b])], "regions": [names[int(reg[polys[a][0]])], names[int(reg[polys[b][0]])]],
                 "dominant_bones": [dom[polys[a][0]], dom[polys[b][0]]], "posed_mid": [round(float(x), 4) for x in (ca + cb) / 2],
                 "rest_distance_m": round(float(np.linalg.norm(ra - rb)), 4)})
out.write_text(json.dumps({"pose": pose, "candidate": Path(bpy.data.filepath).name, "pair_count": len(rows), "pairs": rows}, indent=1) + "\n", encoding="utf-8")
if wout is not None:
    np.savez_compressed(wout, W=W, rest=rest, bones=np.array(bone_names), region=reg)
print("PAIR LIST", len(rows), out)
