"""Read-only: which vertices differ between the corrective shape keys of two candidates (never saves either .blend).

blender --background --factory-startup <candidate A.blend> --python-exit-code 1 --python scripts/diff_original_v1_shape_keys_blender.py -- <candidate B.blend> <out.json>

Reports, per key, the number of vertices whose key data differ (> 1e-9 m), the maximum difference, their rest-space bounding box, and the weight
and topology equality of the two bodies, so a 'local' edit can be audited for stray changes.
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

b_path, out = Path(sys.argv[sys.argv.index("--") + 1]), Path(sys.argv[sys.argv.index("--") + 2])
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]


def grab():
    me = body.data
    keys = {k.name: np.array([d.co[:] for d in k.data]) for k in me.shape_keys.key_blocks}
    w = {v.index: sorted((g.group, round(g.weight, 9)) for g in v.groups) for v in me.vertices}
    return keys, w, len(me.vertices), len(me.polygons)


ka, wa, nva, npa = grab()
a_name = Path(bpy.data.filepath).name
bpy.ops.wm.open_mainfile(filepath=str(b_path))
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
kb, wb, nvb, npb = grab()
rest = ka["Basis"]
res = {"a": a_name, "b": b_path.name, "same_vertex_count": nva == nvb, "same_face_count": npa == npb, "weights_identical": wa == wb, "keys": {}}
for name in ka:
    if name == "Basis" or name not in kb:
        continue
    d = np.abs(kb[name] - ka[name]).max(axis=1)
    idx = np.nonzero(d > 1e-9)[0]
    res["keys"][name] = {"changed_vertices": int(len(idx)), "max_change_m": round(float(d.max()), 6),
                         "bbox_min": [round(float(x), 4) for x in rest[idx].min(axis=0)] if len(idx) else None,
                         "bbox_max": [round(float(x), 4) for x in rest[idx].max(axis=0)] if len(idx) else None,
                         "vertex_ids": [int(i) for i in idx]}
res["basis_identical"] = bool(np.abs(ka["Basis"] - kb["Basis"]).max() < 1e-12)
out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print("SHAPEKEY DIFF", {k: v for k, v in res.items() if k != "keys"}, {n: (v["changed_vertices"], v["max_change_m"], v["bbox_min"], v["bbox_max"]) for n, v in res["keys"].items()})
