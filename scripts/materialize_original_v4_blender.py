"""Add an unbound v4 ORIGINAL armature to the clean O1 scene; never import a mesh."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector
from validate_original_v4_payload import validate

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / 'ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend'
DATA = ROOT / 'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json'
RIG_NAME = 'HGPT_CANONICAL_V4_ORIGINAL'
payload_bytes = DATA.read_bytes()
payload = json.loads(payload_bytes)
errors = validate(payload)
if errors:
    raise RuntimeError(f'Invalid v4 rig payload: {errors}')
scene = bpy.context.scene
if not scene.get('hgpt_clean_room') or scene.get('hgpt_legacy_geometry_imported'):
    raise RuntimeError('Refusing non-clean-room or legacy-imported scene')
body = bpy.data.objects.get('HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD')
reference = bpy.data.objects.get('HGPT_CLEAN_HISTORICAL_REFERENCE_RIG')
if body is None or body.type != 'MESH' or reference is None or reference.type != 'ARMATURE':
    raise RuntimeError('Expected O1 scaffold and historical reference rig')
if len(body.data.vertices) != 3890 or len(reference.data.bones) != 53 or not reference.get('hgpt_reference_only'):
    raise RuntimeError('O1 baseline changed; inspect before materializing v4')
if bpy.data.objects.get(RIG_NAME) or len(bpy.data.objects) != 2:
    raise RuntimeError('Scene already has an additional object; inspect manually')
if len(bpy.data.libraries) or any(i.name not in ('Render Result', 'Viewer Node') for i in bpy.data.images):
    raise RuntimeError('Linked libraries or images found')

checkpoint = ROOT / 'ORIGINAL_V1_WORK/checkpoints'
checkpoint.mkdir(parents=True, exist_ok=True)
backup = checkpoint / f'PRE_V4_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.blend'
shutil.copy2(BLEND, backup)

# O1's clean historical rig was used to generate scaffold skin rows. Remove
# that live binding now: the 53-bone armature remains only an inert reference.
for modifier in list(body.modifiers):
    if modifier.type != 'ARMATURE' or modifier.object != reference:
        raise RuntimeError(f'Unexpected scaffold modifier: {modifier.name}')
    body.modifiers.remove(modifier)
for group in list(body.vertex_groups):
    body.vertex_groups.remove(group)

armature = bpy.data.armatures.new(RIG_NAME)
obj = bpy.data.objects.new(RIG_NAME, armature)
bpy.data.collections['ORIGINAL_RIG'].objects.link(obj)
obj['hgpt_rig_identity'] = payload['identity']
obj['hgpt_payload_sha256'] = hashlib.sha256(payload_bytes).hexdigest()
obj['hgpt_reference_only'] = False
obj['hgpt_unbound_o2_target'] = True
reference.hide_viewport = True
reference.hide_render = True
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
for item in payload['bones']:
    bone = armature.edit_bones.new(item['name'])
    # Project +Y up, +Z forward -> Blender +Z up, -Y forward.
    bone.head = Vector((item['head'][0], -item['head'][2], item['head'][1]))
    bone.tail = Vector((item['tail'][0], -item['tail'][2], item['tail'][1]))
    bone.use_connect = False
for item in payload['bones']:
    if item['parent']:
        armature.edit_bones[item['name']].parent = armature.edit_bones[item['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
record = {
    'asset_id': scene.get('hgpt_asset_id'),
    'rig_identity': payload['identity'],
    'stage': 'O2_unbound_target',
    'source': 'src/rig/canonicalV4Original.ts',
    'rig_payload_sha256': hashlib.sha256(payload_bytes).hexdigest(),
    'pre_v4_blend_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
    'blend_sha256': hashlib.sha256(BLEND.read_bytes()).hexdigest(),
    'historical_53_bone_rig': 'reference_only_unbound',
    'legacy_geometry_imported': False,
}
(ROOT / 'ORIGINAL_V1_WORK/O2_RIG_PROVENANCE.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'Created unbound {RIG_NAME} (63 bones); backup: {backup}')
