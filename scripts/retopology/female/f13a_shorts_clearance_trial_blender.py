"""Create the F13a shorts clearance trial from a verified F12d copy.

Run Blender in background with this script, followed by -- INPUT.blend OUTPUT.blend.
The output must be a new path.
"""
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT = Path(a[0]), Path(a[1]); assert not OUT.exists()
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene; rig = bpy.data.objects["HGPT_FEMALE_RIG"]; rig.data.pose_position = "POSE"
body, bra, shorts = (bpy.data.objects[n] for n in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts"))
P0 = np.array([v.co[:] for v in body.data.vertices])
box = (np.abs(P0[:, 0]) < 0.22) & (P0[:, 2] > 0.55) & (P0[:, 2] < 0.98)


def evaluated(o, solid_off=False):
    mods = [m for m in o.modifiers if m.type == "SOLIDIFY"] if solid_off else []
    for m in mods:
        m.show_viewport = False
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    V = [v.co.copy() for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]; oe.to_mesh_clear()
    for m in mods:
        m.show_viewport = True
    return V, F


def rot_about(pb, R):
    M = pb.matrix.copy(); h = M.translation.copy(); pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M
    bpy.context.view_layer.update()


def set_pose(hip, knee):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        rot_about(rig.pose.bones[f"thigh_{s}"], Matrix.Rotation(math.radians(-hip), 4, "X"))   # knee forward (-y)
        rot_about(rig.pose.bones[f"shin_{s}"], Matrix.Rotation(math.radians(knee), 4, "X"))   # foot back


# Adjust only fabric faces implicated in the deep-flexion preflight.
from collections import defaultdict
original_pose = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
neighbours = defaultdict(set)
for edge in shorts.data.edges:
    first, second = edge.vertices
    neighbours[first].add(second)
    neighbours[second].add(first)
initial = [v.co.copy() for v in shorts.data.vertices]
original_normals = [v.normal.copy() for v in shorts.data.vertices]
for iteration in range(5):
    set_pose(90, 90)
    skin, _ = evaluated(body)
    fabric, faces = evaluated(shorts, True)
    surface = BVHTree.FromPolygons(fabric, faces)
    corrections = {}
    count = 0
    for index in np.where(box)[0]:
        point = skin[index]
        location, normal, face, _ = surface.find_nearest(point, 0.012)
        if location is None:
            continue
        delta = point - location
        signed = delta.dot(normal)
        if signed <= 0 or (delta - signed * normal).length >= 0.0015:
            continue
        count += 1
        for vertex in faces[face]:
            step = min(0.002, signed + 0.0003)
            corrections[vertex] = max(corrections.get(vertex, 0), step)
            for adjacent in neighbours[vertex]:
                corrections[adjacent] = max(corrections.get(adjacent, 0), step * 0.35)
    print("DEEP CLEARANCE ITERATION", iteration, count, len(corrections))
    if not corrections:
        break
    for index, distance in corrections.items():
        vertex = shorts.data.vertices[index]
        prior = (vertex.co - initial[index]).length
        vertex.co += original_normals[index] * max(0, min(distance, 0.004 - prior))
    shorts.data.update()
for bone in rig.pose.bones:
    bone.matrix_basis = original_pose[bone.name]
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), relative_remap=False)
