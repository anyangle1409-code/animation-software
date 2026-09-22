"""Measure the inherited underarm deformation on frozen and V3 meshes."""
import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VERSION = sys.argv[1] if len(sys.argv) > 1 else 'v3'
SOURCE = next((ROOT / 'reference').iterdir()) / 'HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb'
data = SOURCE.read_bytes()
json_length = struct.unpack_from('<I', data, 12)[0]
gltf = json.loads(data[20:20 + json_length])
blob = data[28 + json_length:]


def accessor(index):
    entry = gltf['accessors'][index]
    view = gltf['bufferViews'][entry['bufferView']]
    dtype = np.dtype({5126: '<f4', 5123: '<u2', 5125: '<u4'}[entry['componentType']])
    columns = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[entry['type']]
    return np.ndarray((entry['count'], columns), dtype,
                      buffer=blob,
                      offset=view.get('byteOffset', 0) + entry.get('byteOffset', 0),
                      strides=(view.get('byteStride', dtype.itemsize * columns), dtype.itemsize)).copy()


primitive = gltf['meshes'][0]['primitives'][0]
rest = accessor(primitive['attributes']['POSITION']).astype(float)
triangles = accessor(primitive['indices']).reshape(-1, 3)
edges = np.unique(np.sort(np.concatenate((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]])), axis=1), axis=0)
reference = json.loads((ROOT / 'reports/sculpt_reference.json').read_text())
curl_points = np.asarray(reference['points'])
ownership = reference['ownership']
shoulders = reference['shoulders']
poses = ROOT / f'reports/poses_{VERSION}'
results = {'source': str(SOURCE.relative_to(ROOT)), 'zones': {}}

for side in ('L', 'R'):
    shoulder = np.asarray(shoulders[side])
    rel = curl_points - shoulder
    medial = rel[:, 0] * (1 if side == 'L' else -1)
    # Define the axilla using the *frozen curl reference*, then track the same
    # original vertex IDs through every pose. This keeps sampling unbiased by
    # V3's extra subdivision vertices and altered shoulder silhouette.
    zone = ((medial > -.015) & (medial < .095) &
            (rel[:, 1] > -.145) & (rel[:, 1] < -.015) &
            (np.abs(rel[:, 2]) < .15))
    selected = zone[edges].all(axis=1)
    zone_edges = edges[selected]
    base_length = np.linalg.norm(rest[zone_edges[:, 0]] - rest[zone_edges[:, 1]], axis=1)
    valid = base_length > 1e-6
    zone_edges = zone_edges[valid]
    base_length = base_length[valid]
    output = {'vertex_count': int(zone.sum()), 'edge_count': len(zone_edges), 'poses': {}}
    for exercise in ('dumbbell_bicep_curl', 'dumbbell_shoulder_press', 'pull_up', 'push_up'):
        for phase in ('bottom', 'sample_12', 'peak'):
            row = {}
            for kind in ('baseline', 'candidate'):
                path = poses / f'{exercise}_{phase}_{kind}.json'
                if not path.exists():
                    continue
                pose = json.loads(path.read_text())
                points = np.asarray(pose['meshes'][0]['positions'])[:len(rest)]
                ratio = np.linalg.norm(points[zone_edges[:, 0]] - points[zone_edges[:, 1]], axis=1) / base_length
                order = np.argsort(ratio)
                row[kind] = {
                    'median_ratio': float(np.median(ratio)),
                    'p05_ratio': float(np.quantile(ratio, .05)),
                    'p95_ratio': float(np.quantile(ratio, .95)),
                    'severe_compression_under_0_8': int(np.sum(ratio < .8)),
                    'severe_stretch_over_1_2': int(np.sum(ratio > 1.2)),
                    'worst_edges': [{'ids': zone_edges[i].tolist(), 'ratio': float(ratio[i]),
                                     'curl_local_mm': (rel[zone_edges[i]].mean(axis=0) * 1000).round(1).tolist(),
                                     'arm_ownership': [ownership[k][side] for k in zone_edges[i]]}
                                    for i in order[:5]],
                }
            if row:
                output['poses'][f'{exercise}_{phase}'] = row
    results['zones'][side] = output

destination = ROOT / f'reports/axilla_audit_{VERSION}.json'
destination.write_text(json.dumps(results, indent=2))
for side, zone in results['zones'].items():
    print(f'{side}: {zone["vertex_count"]} vertices, {zone["edge_count"]} edges')
    for name, row in zone['poses'].items():
        if 'press_peak' in name or 'pull_up_peak' in name or 'curl_bottom' in name:
            print(name, {kind: {key: value for key, value in values.items() if key != 'worst_edges'}
                         for kind, values in row.items()})
