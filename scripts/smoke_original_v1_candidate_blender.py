"""Read-only Blender environment/candidate smoke check for ORIGINAL-v1."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


source=Path(bpy.data.filepath);manifest_path=source.with_suffix(".json")
if not source.is_file() or not manifest_path.is_file():raise SystemExit("STOP — candidate Blend/manifest missing")
manifest=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
if manifest.get("candidate")!=source.name or manifest.get("candidate_sha256")!=digest(source):
    raise SystemExit("STOP — candidate Blend/manifest identity differs")
if not bpy.context.scene.get("hgpt_not_production"):raise SystemExit("STOP — candidate-only scene marker missing")
rig=bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
if rig is None or rig.type!="ARMATURE" or len(rig.data.bones)!=63:
    raise SystemExit("STOP — canonical 63-bone v4 rig missing")
bodies=[o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==rig and "SHORTS" not in o.name]
if len(bodies)!=1:raise SystemExit("STOP — expected exactly one owned body mesh bound to canonical rig")
body=bodies[0]
dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg)
if len(ev.data.vertices)<=0 or len(ev.data.polygons)<=0:raise SystemExit("STOP — evaluated body mesh empty")
# Prove the APIs used by later deterministic tooling are available.
_ = np.array([0.0,1.0,2.0],dtype=float)
tree=BVHTree.FromPolygons([v.co.copy() for v in ev.data.vertices],[tuple(p.vertices) for p in ev.data.polygons])
if tree is None:raise SystemExit("STOP — BVHTree construction unavailable")
if bpy.data.libraries:raise SystemExit("STOP — linked Blender libraries present in candidate scene")
print(json.dumps({
    "status":"BLENDER_SMOKE_PASS",
    "blender_version":bpy.app.version_string,
    "candidate":source.name,
    "candidate_sha256":manifest["candidate_sha256"],
    "rig":"HGPT_CANONICAL_V4_ORIGINAL",
    "bone_count":len(rig.data.bones),
    "body":body.name,
    "evaluated_vertices":len(ev.data.vertices),
    "evaluated_faces":len(ev.data.polygons),
    "numpy_version":np.__version__,
    "linked_libraries":0,
    "scene_saved":False
},indent=2))
