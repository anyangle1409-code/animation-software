"""Read-only audit of the current ORIGINAL-v1 Blender skinning mode.

Never saves the Blend.

Usage:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/audit_original_v1_skinning_mode_blender.py -- <out.json>

Records every Armature modifier on the body, including Blender's preserve-volume
(Dual Quaternion) flag, vertex-group/envelope settings and target rig identity.
This is evidence only; it does not recommend or change the skinning mode.
"""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import bpy

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=1:
    raise SystemExit("Usage: ... -- <out.json>")
OUT=Path(args[0]).resolve()
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")
candidate=Path(bpy.data.filepath)
if not candidate.is_file():
    raise SystemExit("candidate filepath missing")

rig=bpy.data.objects.get("HGPT_CANONICAL_V4_ORIGINAL")
if rig is None:
    raise SystemExit("canonical rig missing")
body=next((o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==rig and "SHORTS" not in o.name.upper()),None)
if body is None:
    raise SystemExit("body mesh not found")

mods=[]
for m in body.modifiers:
    if m.type!="ARMATURE":
        continue
    mods.append({
        "name":m.name,
        "type":m.type,
        "target_object":m.object.name if m.object else None,
        "use_vertex_groups":bool(getattr(m,"use_vertex_groups",False)),
        "use_bone_envelopes":bool(getattr(m,"use_bone_envelopes",False)),
        "use_deform_preserve_volume":bool(getattr(m,"use_deform_preserve_volume",False)),
        "use_multi_modifier":bool(getattr(m,"use_multi_modifier",False)),
        "invert_vertex_group":bool(getattr(m,"invert_vertex_group",False)),
        "vertex_group":str(getattr(m,"vertex_group","") or ""),
        "show_viewport":bool(m.show_viewport),
        "show_render":bool(m.show_render),
    })

result={
    "schema_version":1,
    "status":"READ_ONLY_SKINNING_MODE_AUDIT",
    "candidate":candidate.name,
    "candidate_sha256":hashlib.sha256(candidate.read_bytes()).hexdigest(),
    "body_object":body.name,
    "rig_object":rig.name,
    "armature_modifier_count":len(mods),
    "armature_modifiers":mods,
    "shape_key_count":0 if body.data.shape_keys is None else len(body.data.shape_keys.key_blocks),
    "shape_key_names":[] if body.data.shape_keys is None else [k.name for k in body.data.shape_keys.key_blocks],
    "source_saved_or_modified":False,
    "interpretation":"Evidence only. Do not change LBS/DQ/preserve-volume or modifier order without candidate-bound A/B evidence and full anatomical/regression review."
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print("SKINNING MODE AUDIT",json.dumps({"candidate":result["candidate"],"modifiers":mods},indent=2))
