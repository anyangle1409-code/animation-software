"""Read-only: hash the exact mesh, weight and shape-key state of the open candidate for the Phase 4 freeze record.

Usage: blender --background --factory-startup <candidate.blend> --python scripts/hash_original_v1_shape_key_state_blender.py -- <fresh output.json>
Never saves the Blend. Evidence only; no approval.
"""
import hashlib, json, struct, sys
from pathlib import Path
import bpy

out = Path(sys.argv[sys.argv.index('--') + 1])
if out.exists():
    raise SystemExit('STOP - output collision; preserve existing evidence')

obj = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('HGPT_ORIGINAL_V1_BODY'))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
me = obj.data


def h(chunks):
    d = hashlib.sha256()
    for c in chunks:
        d.update(c)
    return d.hexdigest()


def f32(vals):
    return struct.pack('<%df' % len(vals), *vals)


basis = me.shape_keys.reference_key if me.shape_keys else None
rest = [c for v in me.vertices for c in v.co]
keys = {}
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        co = [c for p in kb.data for c in p.co]
        keys[kb.name] = {'points': len(kb.data), 'coords_sha256': h([f32(co)]), 'value': round(kb.value, 9),
                         'slider_min': kb.slider_min, 'slider_max': kb.slider_max, 'mute': kb.mute,
                         'vertex_group': kb.vertex_group, 'relative_key': kb.relative_key.name}
vg_names = [g.name for g in obj.vertex_groups]
wchunks = []
for v in me.vertices:
    row = sorted((vg_names[g.group], round(g.weight, 7)) for g in v.groups)
    wchunks.append(json.dumps(row).encode())
faces = [i for p in me.polygons for i in p.vertices]
drivers = []
if me.shape_keys and me.shape_keys.animation_data:
    for d in me.shape_keys.animation_data.drivers:
        drivers.append({'path': d.data_path, 'expression': d.driver.expression, 'type': d.driver.type})
bones = [b.name for b in arm.data.bones]
state = {
    'schema_version': 1,
    'purpose': 'Exact mesh/weight/shape-key/driver/skeleton state hashes for the Phase 4 development-freeze record. Read-only; no approval.',
    'blender_version': bpy.app.version_string,
    'mesh_object': obj.name,
    'vertex_count': len(me.vertices),
    'face_count': len(me.polygons),
    'rest_vertex_coords_f32_sha256': h([f32(rest)]),
    'topology_face_indices_sha256': h([struct.pack('<%di' % len(faces), *faces)]),
    'vertex_weights_rounded_1e-7_sha256': h(wchunks),
    'vertex_group_names_sha256': h([json.dumps(vg_names).encode()]),
    'shape_keys': keys,
    'shape_key_count_excluding_basis': max(0, len(keys) - 1),
    'shape_key_driver_fcurves_in_file': drivers,
    'armature': arm.name,
    'bone_count': len(bones),
    'bone_names_sha256': h([json.dumps(bones).encode()]),
    'bone_rest_head_tail_f32_sha256': h([f32([c for b in arm.data.bones for c in (*b.head_local, *b.tail_local)])]),
    'scene_keys': sorted(k for k in bpy.context.scene.keys() if k.startswith('hgpt_')),
    'production_approved': False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
print('SHAPE KEY STATE HASHED', out)
