"""Check the O2 armature against the committed clean-room numerical payload."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from validate_original_v4_payload import validate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json'
raw = DATA.read_bytes()
payload = json.loads(raw)
errors = validate(payload)
scene = bpy.context.scene
if not scene.get('hgpt_clean_room') or scene.get('hgpt_legacy_geometry_imported'):
    errors.append('clean-room scene')
rig = bpy.data.objects.get('HGPT_CANONICAL_V4_ORIGINAL')
old = bpy.data.objects.get('HGPT_CLEAN_HISTORICAL_REFERENCE_RIG')
if old is None or old.type != 'ARMATURE' or len(old.data.bones) != 53 or not old.get('hgpt_reference_only'):
    errors.append('historical reference rig')
body = bpy.data.objects.get('HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD')
if body is None or body.type != 'MESH' or body.modifiers or body.vertex_groups:
    errors.append('scaffold must be unbound, with no historical skin groups')
if rig is None or rig.type != 'ARMATURE':
    errors.append('v4 armature missing')
else:
    if rig.get('hgpt_rig_identity') != payload['identity'] or rig.get('hgpt_payload_sha256') != hashlib.sha256(raw).hexdigest():
        errors.append('v4 provenance marker')
    if {b.name for b in rig.data.bones} != {b['name'] for b in payload['bones']} or len(rig.data.bones) != 63:
        errors.append('v4 exact names/count')
    for item in payload['bones']:
        bone = rig.data.bones.get(item['name'])
        if bone is None:
            continue
        if (bone.parent.name if bone.parent else None) != item['parent']:
            errors.append(f"{item['name']} parent")
        for key in ('head', 'tail'):
            p = item[key]
            target = (p[0], -p[2], p[1])
            if math.dist(getattr(bone, key + '_local'), target) > 1e-6:
                errors.append(f"{item['name']} {key}")
    if rig.modifiers or rig.animation_data:
        errors.append('v4 armature must remain unbound and unanimated at O2')
if len(bpy.data.libraries) or bpy.data.actions:
    errors.append('linked library or imported animation')
if any(img.name not in ('Render Result', 'Viewer Node') for img in bpy.data.images):
    errors.append('external/embedded image')
for obj in bpy.data.objects:
    if any(token in obj.name.lower() for token in ('v8', 'v13', 'v15', 'makehuman', 'meshy', 'corner_final')):
        errors.append(f'forbidden object name: {obj.name}')
for mesh in bpy.data.meshes:
    if mesh.uv_layers or mesh.shape_keys:
        errors.append(f'UV or shape key source requires provenance review: {mesh.name}')
for material in bpy.data.materials:
    if material.use_nodes and material.node_tree and any(node.type == 'TEX_IMAGE' for node in material.node_tree.nodes):
        errors.append(f'image texture source requires provenance review: {material.name}')
report = {'pass': not errors, 'blockers': errors, 'rig_identity': payload['identity'],
          'payload_sha256': hashlib.sha256(raw).hexdigest(), 'blend': bpy.data.filepath}
out = ROOT / 'reports/original_v4_blender_audit.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
sys.exit(0 if not errors else 1)
