"""Measure the paired open boundary strips at each inherited medial knee."""
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
reference = json.loads((root / 'reports/squat_sculpt_reference_v5.json').read_text())
points = np.asarray(reference['points'])
triangles = np.asarray(reference['indices']).reshape(-1, 3)
counts = Counter(tuple(sorted((int(a), int(b)))) for face in triangles
                 for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])))
source = root / 'HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved.glb'
data = source.read_bytes()
json_length = struct.unpack_from('<I', data, 12)[0]
document = json.loads(data[20:20 + json_length])
binary = data[28 + json_length:]
primitive = document['meshes'][0]['primitives'][0]


def attribute(name):
    accessor = document['accessors'][primitive['attributes'][name]]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype({5126: '<f4', 5123: '<u2'}[accessor['componentType']])
    columns = {'VEC3': 3, 'VEC4': 4}[accessor['type']]
    return np.ndarray((accessor['count'], columns), dtype, buffer=binary,
                      offset=view.get('byteOffset', 0) + accessor.get('byteOffset', 0),
                      strides=(view.get('byteStride', dtype.itemsize * columns), dtype.itemsize)).copy()


rest = attribute('POSITION')
normal = attribute('NORMAL')
joints = attribute('JOINTS_0')
weights = attribute('WEIGHTS_0')
result = {'asset': source.name, 'squat_time': reference['time'], 'knees': {}}


def ordered_path(edges):
    links = defaultdict(set)
    for a, b in edges:
        links[a].add(b)
        links[b].add(a)
    endpoints = [index for index, neighbours in links.items() if len(neighbours) == 1]
    assert len(endpoints) == 2
    path = [endpoints[0]]
    while path[-1] != endpoints[1]:
        following = links[path[-1]] - set(path[-2:])
        assert len(following) == 1
        path.append(following.pop())
    return path


for side, centre_list in reference['knees'].items():
    centre = np.asarray(centre_list)
    edges = [edge for edge, count in counts.items() if count == 1
             and np.linalg.norm(points[edge[0]] - centre) < .11
             and np.linalg.norm(points[edge[1]] - centre) < .11]
    links = defaultdict(set)
    for a, b in edges:
        links[a].add(b)
        links[b].add(a)
    components = []
    remaining = set(links)
    while remaining:
        stack = [next(iter(remaining))]
        vertices = set()
        while stack:
            current = stack.pop()
            if current in vertices:
                continue
            vertices.add(current)
            stack.extend(links[current] - vertices)
        remaining -= vertices
        components.append(ordered_path([edge for edge in edges if edge[0] in vertices and edge[1] in vertices]))
    assert len(components) == 2 and len(components[0]) == len(components[1])
    first, second = components
    if np.linalg.norm(points[first] - points[second], axis=1).sum() > np.linalg.norm(points[first] - points[second[::-1]], axis=1).sum():
        second = second[::-1]
    gap_pose = np.linalg.norm(points[first] - points[second], axis=1) * 1000
    gap_rest = np.linalg.norm(rest[first] - rest[second], axis=1) * 1000
    normal_dot = np.clip(np.einsum('ij,ij->i', normal[first], normal[second]), -1, 1)
    result['knees'][side] = {
        'boundary_edges': len(edges), 'parallel_paths': 2, 'vertices_per_path': len(first),
        'max_gap_at_squat_mm': float(gap_pose.max()), 'mean_gap_at_squat_mm': float(gap_pose.mean()),
        'max_gap_at_rest_mm': float(gap_rest.max()),
        'paired_joint_sets_equal': bool(np.array_equal(joints[first], joints[second])),
        'max_paired_weight_difference': float(np.abs(weights[first] - weights[second]).max()),
        'max_paired_normal_angle_deg': float(np.rad2deg(np.arccos(normal_dot)).max()),
        'paths': [first, second],
    }
    print(side, {key: value for key, value in result['knees'][side].items() if key != 'paths'})

(root / 'reports/knee_seam_v5.json').write_text(json.dumps(result, indent=2))
