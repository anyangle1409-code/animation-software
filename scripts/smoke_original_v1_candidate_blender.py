"""Read-only Blender environment/candidate smoke check for ORIGINAL-v1."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from original_v1_locked_rig import blender_armature_issues,load_locked_rig
LOCKED_RIG=load_locked_rig(ROOT)


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
rig=bpy.data.objects.get(LOCKED_RIG["object_name"])
rig_issues=blender_armature_issues(rig,LOCKED_RIG)
if rig_issues:
    raise SystemExit("STOP — "+"; ".join(rig_issues))
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
    "rig":LOCKED_RIG["object_name"],
    "rig_identity":LOCKED_RIG["identity"],
    "rig_revision":LOCKED_RIG["revision"],
    "rig_structure_sha256":LOCKED_RIG["rig_structure_sha256"],
    "bone_count":len(rig.data.bones),
    "deform_bone_count":sum(bool(b.use_deform) for b in rig.data.bones),
    "rig_lock":LOCKED_RIG["lock"],
    "rig_payload":LOCKED_RIG["payload"],
    "body":body.name,
    "evaluated_vertices":len(ev.data.vertices),
    "evaluated_faces":len(ev.data.polygons),
    "numpy_version":np.__version__,
    "linked_libraries":0,
    "scene_saved":False
},indent=2))
