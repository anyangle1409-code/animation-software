#!/usr/bin/env python3
"""Read-only contract for anatomical bone-surface assets (NOT anatomy acceptance).

Validate mesh topology, rigid registration, skeleton head/tail correspondence,
and articular-patch participants. Mesh vertices must be in metres in their own
local frame. No skin or procedural bone-shape generator is consulted. Passing
here proves only numerical consistency, never the anatomical truth of a shape.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _vec(v):
    return isinstance(v, list) and len(v) == 3 and all(_number(x) for x in v)


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _sub(a, b):
    return [x-y for x, y in zip(a, b)]


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _dist(a, b):
    return math.dist(a, b)


def _frame(frame):
    if (not isinstance(frame, list) or len(frame) != 4 or
            any(not isinstance(r, list) or len(r) != 4 or not all(_number(x) for x in r) for r in frame)):
        raise ValueError('world_from_local must be a finite 4x4 matrix')
    if max(abs(x-y) for x, y in zip(frame[3], [0, 0, 0, 1])) > 1e-9:
        raise ValueError('invalid homogeneous last row')
    rot = [r[:3] for r in frame[:3]]
    for i in range(3):
        for j in range(3):
            expected = 1.0 if i == j else 0.0
            if abs(_dot(rot[i], rot[j])-expected) > 1e-6:
                raise ValueError('bone-surface registration is scaled or sheared')
    if abs(_dot(rot[0], _cross(rot[1], rot[2])) - 1) > 1e-6:
        raise ValueError('bone-surface frame is mirrored or not a proper rotation')


def _world(frame, point):
    return [sum(frame[i][j]*point[j] for j in range(3)) + frame[i][3] for i in range(3)]


def _triangles(vertices, triangles, closed):
    if not isinstance(vertices, list) or len(vertices) < 3 or not all(_vec(v) for v in vertices):
        raise ValueError('vertices_m must contain >=3 finite 3D points')
    if not isinstance(triangles, list) or not triangles:
        raise ValueError('triangles must be nonempty')
    edges = Counter()
    for i, face in enumerate(triangles):
        if (not isinstance(face, list) or len(face) != 3 or
                any(type(v) is not int or v < 0 or v >= len(vertices) for v in face) or
                len(set(face)) != 3):
            raise ValueError(f'invalid triangle {i}')
        a, b, c = (vertices[x] for x in face)
        if math.sqrt(_dot(_cross(_sub(b, a), _sub(c, a)), _cross(_sub(b, a), _sub(c, a)))) < 1e-12:
            raise ValueError(f'degenerate triangle {i}')
        for x, y in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edges[tuple(sorted((x, y)))] += 1
    if closed and any(n != 2 for n in edges.values()):
        raise ValueError('closed bone mesh is not edge-manifold')
    return {'vertices': len(vertices), 'triangles': len(triangles),
            'boundary_edges': sum(n == 1 for n in edges.values()),
            'nonmanifold_edges': sum(n > 2 for n in edges.values())}


def validate(asset, skeleton, articulation_inventory):
    """Fail closed for malformed geometry; NEVER approve anatomical correctness."""
    if asset.get('schema_version') != 1 or asset.get('status') != 'AUDIT_ONLY':
        raise ValueError('assets must be schema 1 and AUDIT_ONLY')
    if asset.get('units') != 'm':
        raise ValueError('only metre-scale geometry is permitted')
    bone_id = asset.get('bone_id')
    bones = skeleton.get('bones', skeleton.get('record', {}).get('bones', {}))
    if bone_id not in bones:
        raise ValueError('unrecognised bone ID')
    frame = asset.get('world_from_local')
    _frame(frame)
    anchors = asset.get('rig_anchors_local_m')
    if not isinstance(anchors, dict) or set(anchors) != {'head', 'tail'}:
        raise ValueError('missing rig anchors')
    errors = {}
    for name, key in [('head', 'head_m'), ('tail', 'tail_m')]:
        if not _vec(anchors[name]) or not _vec(bones[bone_id][key]):
            raise ValueError(f'invalid {name} reference anchor')
        errors[name] = _dist(_world(frame, anchors[name]), bones[bone_id][key]) * 1000
        if errors[name] > 0.01:  # 10 micron numerical registration tolerance; not anatomical tolerance
            raise ValueError(f'{name} anchor differs from reference skeleton by {errors[name]:.6f} mm')
    mesh = _triangles(asset.get('vertices_m'), asset.get('triangles'),
                      asset.get('surface_type') == 'closed_bone')
    if asset.get('surface_type') not in ('closed_bone', 'open_review_patch'):
        raise ValueError('unsupported surface type')
    arts = articulation_inventory.get('articulations', [])
    extra = articulation_inventory.get('additional_structures', {})
    joint_bones = {a['id']: {extra.get(p, {}).get('owner_bone', p) for p in a['participants']}
                   for a in arts}
    patches = asset.get('articular_patches', [])
    if not isinstance(patches, list):
        raise ValueError('articular_patches must be a list')
    ids = set()
    for patch in patches:
        pid, jid, faces = patch.get('id'), patch.get('joint_id'), patch.get('triangle_indices')
        if not isinstance(pid, str) or not pid or pid in ids:
            raise ValueError('missing or duplicate surface-patch ID')
        ids.add(pid)
        if jid not in joint_bones or bone_id not in joint_bones[jid]:
            raise ValueError(f'{pid}: joint is absent or bone is not an articulation participant')
        if not isinstance(faces, list) or not faces or any(type(f) is not int or f not in range(len(asset['triangles'])) for f in faces):
            raise ValueError(f'{pid}: invalid triangle indices')
    landmarks = asset.get('attachment_landmarks', [])
    if not isinstance(landmarks, list):
        raise ValueError('attachment_landmarks must be a list')
    seen = set()
    for landmark in landmarks:
        lid = landmark.get('id')
        if not isinstance(lid, str) or not lid or lid in seen or not _vec(landmark.get('point_local_m')):
            raise ValueError('invalid or duplicate attachment landmark')
        seen.add(lid)
    # Evidence declarations are not scientifically verified by software. In
    # particular, "reviewed" strings do not grant canonical acceptance.
    return {'schema_version': 1, 'bone_id': bone_id,
            'status': 'GEOMETRY_CONSISTENT_ANATOMY_UNVERIFIED',
            'canonical_promotion_allowed': False, 'mesh_skin_used': False,
            'rig_anchors_max_error_mm': max(errors.values()),
            'mesh': mesh, 'articular_patches_checked': len(patches),
            'attachment_landmarks_checked': len(landmarks),
            'missing_anatomical_acceptance': [
                'Independent shape provenance/coordinate registration review',
                'Source-bound articular geometry and joint contact analysis',
                'Muscle/ligament attachment validation and motion clearance',
                'Bone-wide regional and programme acceptance gates']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--skeleton', type=Path, required=True)
    parser.add_argument('--articulations', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.asset.read_text()),
                      json.loads(args.skeleton.read_text()),
                      json.loads(args.articulations.read_text()))
    payload = json.dumps(result, indent=2) + '\n'
    if args.out:
        with args.out.open('x', encoding='utf-8') as f:
            f.write(payload)
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
