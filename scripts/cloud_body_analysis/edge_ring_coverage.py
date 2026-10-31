"""Read-only topological rings around pinned model edges; NOT anatomical approval."""
from collections import deque
import hashlib
import json
import math

STATUS = "READ_ONLY_EDGE_RINGS_NOT_ANATOMICAL_APPROVAL"

def describe(vertices, triangles, seeds, max_ring=3):
    if type(max_ring) is not int or not 0 <= max_ring <= 12:
        raise ValueError("invalid ring depth")
    if not isinstance(vertices, (list, tuple)) or len(vertices) < 3:
        raise ValueError("invalid vertices")
    points = []
    for p in vertices:
        if (not isinstance(p, (list, tuple)) or len(p) != 3 or
                any(type(x) not in (int, float) or not math.isfinite(x) for x in p)):
            raise ValueError("invalid coordinate")
        points.append(tuple(float(x) for x in p))
    if not isinstance(triangles, (list, tuple)) or not triangles:
        raise ValueError("missing triangles")
    neighbors = [set() for _ in points]
    faces = []
    for face in triangles:
        if (not isinstance(face, (list, tuple)) or len(face) != 3 or
                any(type(i) is not int or not 0 <= i < len(points) for i in face) or
                len(set(face)) != 3):
            raise ValueError("invalid triangle")
        faces.append(list(face))
        a, b, c = face
        for i, j in ((a, b), (b, c), (c, a)):
            if math.dist(points[i], points[j]) <= 1e-12:
                raise ValueError("degenerate edge")
            neighbors[i].add(j)
            neighbors[j].add(i)
    if not isinstance(seeds, list) or not seeds:
        raise ValueError("missing seeds")
    names = set()
    regions = []
    for seed in seeds:
        if (not isinstance(seed, dict) or type(seed.get("name")) is not str or
                not seed["name"] or seed["name"] in names):
            raise ValueError("invalid seed name")
        names.add(seed["name"])
        edge = seed.get("vertex_ids")
        if (not isinstance(edge, list) or len(edge) != 2 or
                any(type(i) is not int or not 0 <= i < len(points) for i in edge) or
                edge[0] == edge[1] or edge[1] not in neighbors[edge[0]]):
            raise ValueError("invalid pinned edge")
        seen = {edge[0]: 0, edge[1]: 0}
        queue = deque([(edge[0], 0), (edge[1], 0)])
        while queue:
            u, depth = queue.popleft()
            if depth == max_ring:
                continue
            for v in sorted(neighbors[u]):
                if v not in seen:
                    seen[v] = depth + 1
                    queue.append((v, depth + 1))
        rings = [{"ring": k, "vertex_ids": sorted(i for i, d in seen.items() if d == k)}
                 for k in range(max_ring + 1)]
        regions.append({"name": seed["name"], "seed_vertex_ids": edge[:],
                        "rings": rings, "total_unique_vertices": len(seen)})
    return {"status": STATUS,
            "topology_sha256": hashlib.sha256(json.dumps(faces, separators=(",", ":")).encode()).hexdigest(),
            "vertex_count": len(points), "ring_depth": max_ring,
            "anatomical_region_certified": False, "anatomical_side_certified": False,
            "movement_approved": False, "regions": regions}
