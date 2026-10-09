"""Topological and orientation checks for independently sourced bone surfaces.

This is a first-party geometric *integrity* checker, not an anatomy validator:
it cannot establish bony landmarks, articular congruence or muscle attachments.

The upstream bone_surface_contract validator checks vertex/face bounds and
triangle degeneracy before calling inspect(). This module independently rejects
duplicate triangles, non-manifold edge fans and inconsistent face winding.
For declared closed surfaces, every used vertex must belong to one connected
triangle shell, every edge must have two oppositely directed incidences, and
the oriented enclosed volume must be positive.

Self-intersections and bone-to-bone clashes are NOT checked here.
"""
from collections import defaultdict
import math


def inspect(vertices, triangles, closed):
    if not isinstance(closed, bool):
        raise ValueError('closed must be boolean')
    faces_seen = set()
    edge_faces = defaultdict(list)
    vertex_faces = defaultdict(list)
    volume6 = 0.0
    for fi, tri in enumerate(triangles):
        # Index/face validation is duplicated lightly for stand-alone use.
        if (not isinstance(tri, list) or len(tri) != 3 or
                any(type(x) is not int or x < 0 or x >= len(vertices) for x in tri)
                or len(set(tri)) != 3):
            raise ValueError(f'invalid triangle {fi}')
        undirected = tuple(sorted(tri))
        if undirected in faces_seen:
            raise ValueError(f'duplicate triangle {fi}')
        faces_seen.add(undirected)
        for x in tri:
            vertex_faces[x].append(fi)
        for a, b in zip(tri, tri[1:] + tri[:1]):
            edge_faces[(min(a, b), max(a, b))].append((fi, a, b))
        a, b, c = (vertices[x] for x in tri)
        volume6 += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )

    # Traverse triangles connected by complete shared edges, not isolated
    # vertex contacts (two closed shells touching at a point are disconnected).
    neighbours = [set() for _ in triangles]
    boundary_edges = 0
    for edge, uses in edge_faces.items():
        if len(uses) > 2:
            raise ValueError(f'non-manifold edge with {len(uses)} incident faces')
        if len(uses) == 1:
            boundary_edges += 1
            continue
        (fi, a, b), (fj, c, d) = uses
        if a != d or b != c:
            raise ValueError('inconsistent face winding across an edge')
        neighbours[fi].add(fj)
        neighbours[fj].add(fi)

    visited = set()
    components = 0
    for initial in range(len(triangles)):
        if initial in visited:
            continue
        components += 1
        stack = [initial]
        while stack:
            fi = stack.pop()
            if fi in visited:
                continue
            visited.add(fi)
            stack.extend(neighbours[fi] - visited)

    unused = len(vertices) - len(vertex_faces)
    # Detect pinch points: two independently wound triangle fans may share
    # one vertex while every edge still has exactly two faces. Such vertices
    # are non-manifold despite a single edge-connected global shell.
    vertex_face_links = defaultdict(lambda: defaultdict(set))
    for (va, vb), uses in edge_faces.items():
        if len(uses) == 2:
            fi, fj = uses[0][0], uses[1][0]
            for vid in (va, vb):
                vertex_face_links[vid][fi].add(fj)
                vertex_face_links[vid][fj].add(fi)

    if closed:
        if boundary_edges:
            raise ValueError(f'closed surface has {boundary_edges} boundary edges')
        if components != 1:
            raise ValueError(f'closed surface has {components} disconnected shells')
        if unused:
            raise ValueError(f'closed surface contains {unused} unreferenced vertices')
    for vid, incident in vertex_faces.items():
        if len(incident) < 2:
            continue
        seen = set()
        stack = [incident[0]]
        while stack:
            fi = stack.pop()
            if fi in seen:
                continue
            seen.add(fi)
            stack.extend(vertex_face_links[vid].get(fi, set()) - seen)
        if len(seen) != len(incident):
            raise ValueError(f'pinched/non-manifold vertex {vid}')

    if closed and (not math.isfinite(volume6) or volume6 <= 0):
        raise ValueError('closed surface has nonpositive signed enclosed volume')

    return {
        'edge_connected_components': components,
        'boundary_edges': boundary_edges,
        'unused_vertices': unused,
        'signed_enclosed_volume_m3': volume6 / 6 if closed else None,
        'self_intersection_checked': False,
        'joint_contact_checked': False,
        'anatomical_shape_verified': False,
    }
