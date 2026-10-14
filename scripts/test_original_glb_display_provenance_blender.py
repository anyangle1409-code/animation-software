"""Check actual export inventory separately from Blender's imported display aid.

Run with the source Blend open. Review-only; no source is saved.
"""
import json
import struct
import tempfile
from pathlib import Path
import bpy

body = bpy.data.objects['HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE']
rig = bpy.data.objects['HGPT_CANONICAL_V4_ORIGINAL']
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True); rig.select_set(True)
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)/'source.glb'
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
        export_skins=True, export_morph=True, export_apply=False, export_animations=False)
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    exported = [n['name'] for n in doc['nodes'] if 'mesh' in n]
    assert exported == [body.name], exported
    assert len(doc['meshes']) == len(doc['skins']) == 1
    assert len(doc['skins'][0]['joints']) == 67
    p = doc['meshes'][0]['primitives'][0]
    assert doc['accessors'][p['attributes']['POSITION']]['count'] == 17946
    assert doc['accessors'][p['indices']]['count'] == 107664
    assert len(p['targets']) == 6 and doc['meshes'][0]['weights'] == [0]*6
    source_names = {b.name for b in rig.data.bones}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    default_meshes = [o.name for o in bpy.data.objects if o.type == 'MESH']
    assert 'Icosphere' in default_meshes, default_meshes
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    assert len(meshes) == len(arms) == 1
    assert len(meshes[0].data.vertices) == 17946
    assert {b.name for b in arms[0].data.bones} == source_names
    assert len(meshes[0].data.shape_keys.key_blocks)-1 == 6
    print('GLB_DISPLAY_PROVENANCE_PASS', json.dumps({'exported':exported,
        'default_import_meshes':default_meshes, 'display_disabled_meshes':[o.name for o in meshes],
        'source_saved':False, 'production_approved':False}))
