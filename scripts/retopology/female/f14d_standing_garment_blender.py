"""Refine the F13a standing garment meshes in a separate checkpoint."""
import sys
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
if output.exists():
    raise FileExistsError(output)
body, shorts, bra = (bpy.data.objects["HGPT_Female_" + n] for n in ("Body", "Shorts", "Bra"))
skin = BVHTree.FromPolygons([v.co for v in body.data.vertices], [tuple(f.vertices) for f in body.data.polygons])
mesh = bmesh.new()
mesh.from_mesh(shorts.data)
points = {v: v.co.copy() for v in mesh.verts}
hems = {v for v in mesh.verts if v.co.z < .85 and any(e.is_boundary for e in v.link_edges)}
waist = {v for v in mesh.verts if v.co.z > .90 and any(e.is_boundary for e in v.link_edges)}

def smoothstep(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)

def spread(seeds, depth):
    distances = dict.fromkeys(seeds, 0)
    queue = deque(seeds)
    while queue:
        vertex = queue.popleft()
        if distances[vertex] >= depth:
            continue
        for edge in vertex.link_edges:
            other = edge.other_vert(vertex)
            if other not in distances:
                distances[other] = distances[vertex] + 1
                queue.append(other)
    return distances

for vertex, ring in spread(hems, 12).items():
    p = points[vertex]
    if abs(p.x) < .019:
        continue
    influence = smoothstep((12 - ring) / 12) * smoothstep((abs(p.x) - .019) / .017)
    shift = min(.082, max(0, p.z - .735)) * influence
    if shift < .0001:
        continue
    lowered = p - Vector((0, 0, shift))
    centre = Vector((.101 if p.x > 0 else -.101, -.014, lowered.z))
    radial = lowered - centre
    if radial.length < .003:
        continue
    radial.normalize()
    hit, normal, _, _ = skin.ray_cast(centre, radial, .16)
    if hit is None:
        continue
    target = hit + normal * .004
    # Preserve the original fabric contour away from the leg opening.
    vertex.co = lowered.lerp(target, min(1, influence * 2.0))

for _ in range(8):
    updates = {}
    for vertex in waist:
        adjacent = [e.other_vert(vertex) for e in vertex.link_edges if e.is_boundary]
        if len(adjacent) == 2:
            centre = (adjacent[0].co + adjacent[1].co) / 2
            updates[vertex] = vertex.co.lerp(centre, .42)
    for vertex, point in updates.items():
        hit, normal, _, _ = skin.find_nearest(point)
        distance = (point - hit).dot(normal)
        vertex.co = point + normal * max(0, .0025 - distance)
# Relax the leg-opening curve and the first rows of fabric together.
band = spread(hems, 4)
for _ in range(10):
    targets = {}
    for vertex, ring in band.items():
        if ring >= 4:
            continue
        neighbours = [e.other_vert(vertex) for e in vertex.link_edges if ring or e.is_boundary]
        if len(neighbours) < 2:
            continue
        centre = sum((v.co for v in neighbours), Vector()) / len(neighbours)
        targets[vertex] = vertex.co.lerp(centre, .42 * (1 - ring / 4))
    for vertex, point in targets.items():
        hit, normal, _, _ = skin.find_nearest(point)
        signed = (point - hit).dot(normal)
        vertex.co = point + normal * max(0, .0034 - signed)
# Ease the two seat contact areas and both front waistband contacts.
contacts = [body.data.vertices[i].co for i in (29020, 28234, 28300, 28889)]
for vertex in mesh.verts:
    distance = min((vertex.co - point).length for point in contacts)
    amount = .0016 * smoothstep(1 - distance / .018)
    if amount > 0:
        _, normal, _, _ = skin.find_nearest(vertex.co)
        vertex.co += normal * amount

changed = {v.index for v in mesh.verts if (v.co - points[v]).length > .001}
mesh.to_mesh(shorts.data)
mesh.free()
shorts.data.update()
source_groups = {g.index: g.name for g in body.vertex_groups}
for index in changed:
    vertex = shorts.data.vertices[index]
    hit, normal, face, _ = skin.find_nearest(vertex.co)
    weights = {}
    for i in body.data.polygons[face].vertices:
        source = body.data.vertices[i]
        factor = 1 / max(.0003, (source.co - hit).length) ** 2
        for entry in source.groups:
            name = source_groups[entry.group]
            if name in shorts.vertex_groups:
                weights[name] = weights.get(name, 0) + factor * entry.weight
    strongest = sorted(weights.items(), key=lambda item: -item[1])[:4]
    total = sum(weight for _, weight in strongest)
    if not total:
        continue
    for group in list(vertex.groups):
        shorts.vertex_groups[group.group].remove([index])
    for name, weight in strongest:
        shorts.vertex_groups[name].add([index], weight / total, "REPLACE")


mesh = bmesh.new()
mesh.from_mesh(bra.data)
for edge in list(mesh.edges):
    faces = list(edge.link_faces)
    if len(faces) != 3:
        continue
    triangles = [face for face in faces if len(face.verts) == 3 and sum(e.is_boundary for e in face.edges) == 2]
    if len(triangles) == 1:
        bmesh.ops.delete(mesh, geom=triangles, context="FACES")
mesh.to_mesh(bra.data)
mesh.free()
bra.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(output), relative_remap=False)
