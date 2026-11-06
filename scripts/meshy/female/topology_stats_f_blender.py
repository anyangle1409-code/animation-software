"""FEMALE topology / self-intersection statistics of a candidate (read-only).

Per mesh: vertices, faces, quads / triangles / n-gons, boundary edges, non-manifold edges, loose parts. Body
self-intersections (non-adjacent face pairs that intersect, rest pose) by region: hands (t4_part >= 1), feet (t5_part
>= 6), armpits, chest / under the bra, pelvis / under the shorts, other.

usage: python3.13 topology_stats_f_blender.py -- <candidate .blend> <out .json>
"""
import json
import sys
from collections import Counter

import bpy
import bmesh  # noqa: E402
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0], load_ui=False)
rig = bpy.data.objects.get("HGPT_FEMALE_RIG")
if rig:
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()
out = {"in": a[0].split("/")[-1]}
for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail"):
    me = bpy.data.objects[n].data; bm = bmesh.new(); bm.from_mesh(me)
    sides = Counter(len(f.verts) for f in bm.faces)
    seen = set(); parts = 0
    for v0 in bm.verts:
        if v0 in seen:
            continue
        parts += 1; st = [v0]; seen.add(v0)
        while st:
            v = st.pop()
            for e in v.link_edges:
                w = e.other_vert(v)
                if w not in seen:
                    seen.add(w); st.append(w)
    out[n] = {"vertices": len(bm.verts), "faces": len(bm.faces), "quads": sides.get(4, 0), "triangles": sides.get(3, 0),
              "ngons": sum(c for k, c in sides.items() if k > 4), "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
              "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary), "parts": parts}
    if n == "HGPT_Female_Body":
        L4 = bm.verts.layers.int["t4_part"]; L5 = bm.verts.layers.int["t5_part"]; bm.faces.ensure_lookup_table()
        t = BVHTree.FromBMesh(bm); c = Counter(); tot = 0
        for i, j in t.overlap(t):
            if i < j and not (set(bm.faces[i].verts) & set(bm.faces[j].verts)):
                tot += 1; f = bm.faces[i]; p = f.calc_center_median()
                if max(v[L4] for v in f.verts) >= 1:
                    r = "hands"
                elif max(v[L5] for v in f.verts) >= 6:
                    r = "feet"
                elif 0.09 < abs(p.x) < 0.25 and 1.05 < p.z < 1.32:
                    r = "armpits"
                elif 1.05 < p.z < 1.40:
                    r = "chest_upper_back"
                elif 0.65 < p.z < 1.05:
                    r = "pelvis"
                else:
                    r = "other"
                c[r] += 1
        out[n]["self_intersecting_face_pairs"] = tot; out[n]["self_intersections_by_region"] = dict(c)
    bm.free()
json.dump(out, open(a[1], "w"), indent=1); print("TOPO", json.dumps(out))
