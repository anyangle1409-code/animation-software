"""Renderer-independent neutral mesh measurements, with no legacy asset input."""
from collections import Counter, defaultdict
from itertools import product
import math


def inspect_mesh(vertices, faces, symmetry_tolerance=.001):
    if symmetry_tolerance <= 0:
        raise ValueError('Symmetry tolerance must be positive')
    buckets = defaultdict(list)
    for x, y, z in vertices:
        buckets[tuple(round(v / symmetry_tolerance) for v in (x, y, z))].append((x, y, z))
    unmatched = 0
    for x, y, z in vertices:
        target = (-x, y, z)
        key = tuple(round(v / symmetry_tolerance) for v in target)
        if not any(math.dist(target, p) <= symmetry_tolerance
                   for offset in product((-1, 0, 1), repeat=3)
                   for p in buckets[tuple(a + b for a, b in zip(key, offset))]):
            unmatched += 1

    edges = Counter()
    directed = Counter()
    used = set()
    seen_faces = set()
    duplicate = degenerate = 0
    for face in faces:
        if len(face) < 3 or len(set(face)) != len(face):
            degenerate += 1
            continue
        key = tuple(sorted(face))
        if key in seen_faces:
            duplicate += 1
        seen_faces.add(key)
        used.update(face)
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))] += 1
            directed[(a, b)] += 1
        anchor = vertices[face[0]]
        area = 0.0
        for i in range(1, len(face) - 1):
            u = [vertices[face[i]][j] - anchor[j] for j in range(3)]
            v = [vertices[face[i + 1]][j] - anchor[j] for j in range(3)]
            cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            area += math.sqrt(sum(c*c for c in cross)) / 2
        if area < 1e-10:
            degenerate += 1
    return {
        'vertex_count': len(vertices), 'polygon_count': len(faces),
        'height_m': max((p[2] for p in vertices), default=0) - min((p[2] for p in vertices), default=0),
        'unmatched_mirror_vertices': unmatched,
        'boundary_edges': sum(n == 1 for n in edges.values()),
        'nonmanifold_edges': sum(n > 2 for n in edges.values()),
        'inconsistent_winding_edges': sum(n == 2 and directed[(a, b)] != 1 for (a, b), n in edges.items()),
        'loose_vertices': len(vertices) - len(used),
        'degenerate_faces': degenerate, 'duplicate_faces': duplicate,
    }
