"""Align paired medial-knee boundary vertices without changing the frozen rig."""
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
source = root / 'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved.glb'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
version = args[0] if args else 'v6_knee_seam'
target = root / f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb'
data = bytearray(source.read_bytes())
length = struct.unpack_from('<I', data, 12)[0]
document = json.loads(data[20:20 + length])
binary_offset = 28 + length
primitive = document['meshes'][0]['primitives'][0]


def attribute(name):
    accessor = document['accessors'][primitive['attributes'][name]]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype({5126: '<f4', 5123: '<u2'}[accessor['componentType']])
    columns = {'VEC3': 3, 'VEC4': 4}[accessor['type']]
    offset = binary_offset + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return np.ndarray((accessor['count'], columns), dtype, buffer=data, offset=offset,
                      strides=(view.get('byteStride', dtype.itemsize * columns), dtype.itemsize))


position = attribute('POSITION')
normal = attribute('NORMAL')
joints = attribute('JOINTS_0')
weights = attribute('WEIGHTS_0')
seams = json.loads((root / 'reports/knee_seam_v5.json').read_text())['knees']
paired = 0
max_move = 0.0
for side in ('L', 'R'):
    first, second = seams[side]['paths']
    assert len(first) == len(second) == 15
    for a, b in zip(first, second):
        assert np.array_equal(joints[a], joints[b])
        assert np.array_equal(weights[a], weights[b])
        centre = (position[a].astype(float) + position[b].astype(float)) * .5
        max_move = max(max_move, float(np.linalg.norm(position[a] - centre)))
        position[a] = centre.astype(np.float32)
        position[b] = centre.astype(np.float32)
        shade = normal[a].astype(float) + normal[b].astype(float)
        shade /= max(np.linalg.norm(shade), 1e-12)
        normal[a] = shade.astype(np.float32)
        normal[b] = shade.astype(np.float32)
        paired += 1

target.write_bytes(data)
report = {'base': source.name, 'matched_pairs': paired, 'max_rest_vertex_move_mm': max_move * 1000,
          'skin_weights_unchanged': True, 'rig_animation_materials_metadata_unchanged': True}
(root / f'reports/build_{version}.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report), flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(target))
for obj in bpy.context.scene.objects:
    if obj.type == 'ARMATURE':obj.show_in_front = True
    if obj.type == 'MESH':obj['candidate_only'] = True
bpy.ops.wm.save_as_mainfile(filepath=str(root / f'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(root / 'checkpoints' / f'{version}_aligned_pairs.blend'), copy=True)
