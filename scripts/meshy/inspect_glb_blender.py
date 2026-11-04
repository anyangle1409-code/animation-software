"""Import the Meshy GLB (read-only source), verify its structure, report pose / proportions, save a working .blend.
usage: python3.13 inspect_glb_blender.py -- <source.glb> <out dir>"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
ob = meshes[0]; me = ob.data
V = np.array([ob.matrix_world @ v.co for v in me.vertices])
z0, z1 = V[:, 2].min(), V[:, 2].max(); H = z1 - z0
f = (V[:, 2] - z0) / H
rep = {"objects": [o.name for o in bpy.data.objects], "armatures": [o.name for o in bpy.data.objects if o.type == "ARMATURE"],
       "vertices": len(me.vertices), "triangles": sum(len(p.vertices) - 2 for p in me.polygons), "uv_layers": len(me.uv_layers),
       "materials": [m.name for m in me.materials], "bbox_min": V.min(0).round(4).tolist(), "bbox_max": V.max(0).round(4).tolist(),
       "stature_m": round(float(H), 4)}
# which way it faces: nose / toes side.  Feet: lowest 3 % -> toes extend towards the front
feet = V[f < 0.03]; rep["feet_y_range"] = [round(float(feet[:, 1].min()), 3), round(float(feet[:, 1].max()), 3)]
# arm pose: widest extent and the height at which it occurs
rep["max_width_m"] = round(float(np.ptp(V[:, 0])), 3)
lv = {}
for fr in (0.95, 0.90, 0.87, 0.84, 0.80, 0.75, 0.70, 0.60, 0.50, 0.45, 0.40, 0.30, 0.20, 0.10):
    s = np.abs(f - fr) < 0.004
    xs = np.sort(V[s, 0]); br = np.nonzero(np.diff(xs) > 0.01)[0]
    runs = [(round(float(p), 3), round(float(q), 3)) for p, q in zip(np.r_[xs[0], xs[br + 1]], np.r_[xs[br], xs[-1]])]
    lv[f"{fr:.2f}"] = {"runs_x": runs, "y_range": [round(float(V[s, 1].min()), 3), round(float(V[s, 1].max()), 3)]}
rep["levels"] = lv
# mesh health
import bmesh  # noqa: E402
bm = bmesh.new(); bm.from_mesh(me)
rep["boundary_edges"] = sum(1 for e in bm.edges if e.is_boundary); rep["nonmanifold_edges"] = sum(1 for e in bm.edges if not e.is_manifold)
seen = set(); comps = []
bm.verts.ensure_lookup_table()
for v0 in bm.verts:
    if v0.index in seen:
        continue
    st = [v0]; seen.add(v0.index); c = 0
    while st:
        v = st.pop(); c += 1
        for e in v.link_edges:
            o = e.other_vert(v)
            if o.index not in seen:
                seen.add(o.index); st.append(o)
    comps.append(c)
rep["connected_components"] = len(comps); rep["largest_components"] = sorted(comps)[-5:]
el = np.array([e.calc_length() for e in bm.edges]); rep["edge_len_mm_p5_p50_p95"] = (np.percentile(el, [5, 50, 95]) * 1000).round(2).tolist()
bm.free()
ob.name = "MESHY_SOURCE"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "meshy_import.blend"))
(OUT / "inspect_report.json").write_text(json.dumps(rep, indent=1)); print("INSPECT", json.dumps({k: rep[k] for k in list(rep)[:9]}))
