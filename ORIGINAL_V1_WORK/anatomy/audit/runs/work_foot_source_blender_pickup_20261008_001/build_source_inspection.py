"""Create source-only inspection scenes; never a canonical foot or master rig."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

source, output = map(Path, sys.argv[1:3])
blend = output / 'SOURCE_ONLY_Grant_M02_segments.blend'
if blend.exists():
    raise FileExistsError('Immutable diagnostic output already exists')
reference = json.loads((Path(__file__).parent.parent / 'work_zenodo_foot_source_20261008_001/blender_source_import.json').read_text())
hashes = {r['file']: r['sha256'] for r in reference['source_segments']}
bpy.ops.wm.read_factory_settings(use_empty=True)
report = []

def mesh_hash(mesh):
    vertices = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', vertices)
    indices = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', indices)
    return hashlib.sha256(vertices.tobytes() + indices.tobytes()).hexdigest()

for index, name in enumerate(hashes):
    path = source / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[name]
    scene = bpy.context.scene if index == 0 else bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.name = 'SOURCE_ONLY_' + name.removesuffix('.stl')
    scene['anatomical_status'] = 'UNVERIFIED source pose/units/contacts; NOT canonical'
    scene['source_doi'] = '10.5281/zenodo.3464747'
    scene['license'] = 'CC BY 4.0; Grant et al. 2020, PeerJ 8:e8397'
    scene.unit_settings.system = 'NONE'
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=1, use_scene_unit=False,
                         forward_axis='Y', up_axis='Z', use_mesh_validate=False)
    obj = bpy.context.object
    obj.name = name.removesuffix('.stl')
    obj['source_sha256'] = hashes[name]
    obj['coordinate_status'] = 'RAW SOURCE VALUES; physical units unverified'
    obj['joint_contacts_selected'] = False
    obj.color = (0.8, 0.72, 0.54, 1)
    coords = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = coords.min(axis=0), coords.max(axis=0)
    centre = Vector((lo + hi) / 2)
    span = float(np.linalg.norm(hi - lo))
    camera = bpy.data.objects.new('Source inspection camera', bpy.data.cameras.new('Source inspection camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = centre + Vector((1, -1, .65)).normalized() * span * 3
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = span * 1.45
    camera.data.clip_end = span * 20
    # Camera-relative labels are display annotations, never anatomical landmarks.
    for title, y in [(name + ' | SOURCE ONLY', .43), ('Units, pose and contacts UNVERIFIED', -.43)]:
        text = bpy.data.curves.new(title, type='FONT')
        text.body = title
        text.align_x = 'CENTER'
        text.size = camera.data.ortho_scale * .029
        label = bpy.data.objects.new(title, text)
        scene.collection.objects.link(label)
        label.parent = camera
        label.location = (0, y * camera.data.ortho_scale, -span * 2)
        label.color = (.92, .92, .92, 1)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'OBJECT'
    scene.display.shading.background_type = 'WORLD'
    scene.world = bpy.data.worlds.new(scene.name + '_world')
    scene.world.color = (.025, .025, .025)
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str((output / (obj.name + '_SOURCE_ONLY.png')).resolve())
    report.append({'scene': scene.name, 'object': obj.name, 'source_sha256': hashes[name],
                   'mesh_sha256': mesh_hash(obj.data), 'vertices': len(obj.data.vertices),
                   'triangles': len(obj.data.polygons), 'object_transform_identity': obj.matrix_world == obj.matrix_world.Identity(4)})

bpy.context.window.scene = bpy.data.scenes[report[0]['scene']]
readme = bpy.data.texts.new('READ_ME_SOURCE_ONLY')
readme.write('Grant et al. 2020 / Zenodo 3464747, CC BY 4.0.\nFour separate source scenes; NOT an assembled foot or canonical skeleton.\nSelect scenes to inspect each segment independently. Raw geometry preserved.\nMidfoot nominally groups nine bones; components are not identified bones.\nUnits, donor-specific stature/sex and common contact pose remain unverified.\nDo not move or scale any anatomical master from these source meshes alone.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()))
for row in report:
    obj = bpy.data.objects[row['object']]
    assert mesh_hash(obj.data) == row['mesh_sha256'], 'Save/reload changed source mesh'
    assert obj['source_sha256'] == row['source_sha256']
    assert len([o for o in bpy.data.scenes[row['scene']].objects if o.type == 'MESH']) == 1
    assert not list(bpy.data.armatures), 'Source inspection must contain no rig'
(output / 'save_reload_verification.json').write_text(json.dumps({'status': 'CONFIRMED_SOURCE_ONLY_SAVE_RELOAD', 'bpy_version': bpy.app.version_string, 'scenes': report, 'canonical_candidate': False, 'production_modified': False, 'blend_sha256': hashlib.sha256(blend.read_bytes()).hexdigest()}, indent=2) + '\n')
for row in report:
    bpy.context.window.scene = bpy.data.scenes[row['scene']]
    bpy.ops.render.render(write_still=True)
print('Source-only scenes saved, reloaded, geometry-checked and rendered')
