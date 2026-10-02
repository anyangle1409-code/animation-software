"""Read-only mesh connectivity audit (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 --python scripts/audit_original_v1_mesh_connectivity_blender.py -- <out.json>

Reports connected components (by shared vertices), boundary edges (one face), non-manifold edges (>2 faces), coincident-but-unshared vertex pairs
(within 1e-5 m at rest) and, for the shoulder zone, how many of them sit within 0.30 m of a glenohumeral joint. Tearing at the axilla can come from
open seams (coincident unwelded vertices that LBS pulls apart) rather than from deformation, so this is checked before any weight/corrective work.
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

out = Path(sys.argv[sys.argv.index("--") + 1])
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
rest = np.array([v.co[:] for v in me.vertices])
names = json.loads(bpy.context.scene["hgpt_region_names"])
reg = np.array([d.value for d in me.attributes["hgpt_region"].data])
nV = len(rest)
cnt = {}
for p in me.polygons:
    vs = p.vertices
    for i in range(len(vs)):
        e = (min(vs[i], vs[(i + 1) % len(vs)]), max(vs[i], vs[(i + 1) % len(vs)]))
        cnt[e] = cnt.get(e, 0) + 1
boundary = [e for e, c in cnt.items() if c == 1]
nonman = [e for e, c in cnt.items() if c > 2]
parent = list(range(nV))


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


for (a, b) in cnt:
    parent[find(a)] = find(b)
comp = {}
for v in range(nV):
    comp.setdefault(find(v), []).append(v)
# coincident unshared vertices
key = {}
for i in range(nV):
    key.setdefault(tuple(np.round(rest[i] / 1e-5).astype(int)), []).append(i)
coinc = [v for v in key.values() if len(v) > 1]
hl = np.array(rig.data.bones["upperarm_l"].head_local)
hr = np.array(rig.data.bones["upperarm_r"].head_local)
near = np.minimum(np.linalg.norm(rest - hl, axis=1), np.linalg.norm(rest - hr, axis=1)) < 0.30
rec = {"vertices": nV, "faces": len(me.polygons), "components": len(comp), "component_sizes": sorted((len(v) for v in comp.values()), reverse=True)[:20],
       "boundary_edges": len(boundary), "boundary_edges_near_shoulder": sum(1 for a, b in boundary if near[a] or near[b]),
       "boundary_edge_regions": {names[r]: int(c) for r, c in zip(*np.unique(np.array([reg[a] for a, b in boundary]), return_counts=True))} if boundary else {},
       "non_manifold_edges": len(nonman), "coincident_vertex_groups": len(coinc), "coincident_near_shoulder": sum(1 for g in coinc if near[g[0]]),
       "coincident_examples": [{"vertices": g, "region": names[int(reg[g[0]])], "pos": [round(float(x), 4) for x in rest[g[0]]]} for g in coinc[:20]],
       "boundary_examples": [{"edge": list(e), "region": names[int(reg[e[0]])], "pos": [round(float(x), 4) for x in rest[e[0]]]} for e in boundary[:30]]}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
print("CONNECTIVITY", {k: rec[k] for k in ("components", "boundary_edges", "boundary_edges_near_shoulder", "non_manifold_edges", "coincident_vertex_groups", "coincident_near_shoulder", "boundary_edge_regions")})
