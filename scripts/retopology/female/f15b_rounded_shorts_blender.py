"""Build a fitted female shorts candidate from the rigged body surface."""
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

output = Path(sys.argv[sys.argv.index("--")+1]).resolve()
if output.exists():
    raise FileExistsError(output)
scene = bpy.context.scene
body = bpy.data.objects["HGPT_Female_Body"]
previous = bpy.data.objects["HGPT_Female_Shorts"]
shorts = body.copy()
shorts.data = body.data.copy()
scene.collection.objects.link(shorts)
bm = bmesh.new()
bm.from_mesh(shorts.data)
# Copying the rigged surface retains its crotch bridge and the underlying
# deform weights. The two hem loops lie below that bridge.
def cut(point, normal, inner=False):
    bmesh.ops.bisect_plane(bm, geom=[*bm.verts,*bm.edges,*bm.faces],
        dist=.000001, plane_co=point, plane_no=normal,
        clear_inner=inner, clear_outer=not inner)
cut((0,0,.686),(0,0,1),True)
cut((0,0,.982),(0,-.20,1))
cut((.22,0,0),(1,0,0))
cut((-.22,0,0),(-1,0,0))
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.normal_update()
for v in bm.verts:
    waist_distance = .982 + .20 * v.co.y - v.co.z
    v.co += v.normal * (.0025 + .0025 * min(1, max(0, waist_distance / .018)))
bm.to_mesh(shorts.data)
bm.free()
shorts.data.materials.clear()
fabric = bpy.data.materials.new("Graphite stretch fabric")
fabric.diffuse_color=(.045,.052,.068,1)
fabric.use_nodes=True
shader=fabric.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value=fabric.diffuse_color
shader.inputs["Roughness"].default_value=.77
shorts.data.materials.append(fabric)
for poly in shorts.data.polygons:
    poly.material_index=0
    poly.use_smooth=True
for mod in list(shorts.modifiers):
    if mod.type!="ARMATURE":
        shorts.modifiers.remove(mod)
solid=shorts.modifiers.new("Fabric thickness","SOLIDIFY")
solid.thickness=.0016
solid.offset=-.5
bpy.data.objects.remove(previous,do_unlink=True)
shorts.name="HGPT_Female_Shorts"
shorts.data.name="HGPT_Female_F15a_U_Shorts"
bpy.ops.wm.save_as_mainfile(filepath=str(output),relative_remap=False)
