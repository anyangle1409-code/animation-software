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


def measure_ring_edges(reference_vertices, posed_vertices, triangles, region, topology_sha256):
    """Measure selected within-ring triangle edges without anatomical inference.

    Coordinates must be expressed in the same length unit; returned ratios are
    dimensionless. The caller must authenticate source identity and validate
    evaluated mesh topology independently.
    """
    if not isinstance(region, dict) or not isinstance(region.get("rings"), list):
        raise ValueError("invalid region")
    base = describe(reference_vertices, triangles,
                    [{"name": region.get("name"),
                      "vertex_ids": region.get("seed_vertex_ids")}],
                    len(region["rings"]) - 1)
    if base["topology_sha256"] != topology_sha256:
        raise ValueError("topology fingerprint mismatch")
    if base["regions"][0]["rings"] != region["rings"]:
        raise ValueError("region membership mismatch")
    if not isinstance(posed_vertices, (list, tuple)) or len(posed_vertices) != len(reference_vertices):
        raise ValueError("posed vertex count mismatch")
    posed = []
    for p in posed_vertices:
        if (not isinstance(p, (list, tuple)) or len(p) != 3 or
            any(type(x) not in (int, float) or not math.isfinite(x) for x in p)):
            raise ValueError("invalid posed coordinate")
        posed.append(tuple(float(x) for x in p))
    allowed = {i for ring in region["rings"] for i in ring["vertex_ids"]}
    edges = set()
    for face in triangles:
        for a, b in ((face[0],face[1]),(face[1],face[2]),(face[2],face[0])):
            if a in allowed and b in allowed:
                edges.add(tuple(sorted((a,b))))
    if not edges:
        raise ValueError("no selected region edges")
    output = []
    for a,b in sorted(edges):
        rest = math.dist(reference_vertices[a], reference_vertices[b])
        moved = math.dist(posed[a], posed[b])
        if not math.isfinite(rest) or rest <= 1e-12 or not math.isfinite(moved):
            raise ValueError("degenerate selected edge")
        output.append({"vertex_ids":[a,b], "ratio":moved/rest})
    ratios = sorted(x["ratio"] for x in output)
    return {"status":STATUS,"anatomical_region_certified":False,
            "edge_count":len(output),"ratios":output,
            "min_ratio":ratios[0],"max_ratio":ratios[-1]}
