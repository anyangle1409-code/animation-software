"""Recolour the painted shorts on a render copy of the Male 07c surface."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils.kdtree import KDTree

source_path, output = sys.argv[sys.argv.index("--") + 1:]
out = Path(output)
with bpy.data.libraries.load(source_path, link=False) as (_, dst):
    dst.objects = ["Mesh_0"]
source = dst.objects[0].data
source.calc_loop_triangles()
triangles = list(source.loop_triangles)
positions = [v.co.copy() for v in source.vertices]
tree = BVHTree.FromPolygons(positions, [t.vertices[:] for t in triangles], all_triangles=True)
source_uv = source.uv_layers.active.uv
image = next(n.image for n in source.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image.colorspace_settings.name == "sRGB")
width, height = image.size
pixels = np.empty(width * height * 4, dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels = pixels.reshape(height, width, 4)

scene = bpy.context.scene
body = bpy.data.objects["MESHY_BODY"]
mesh = bpy.data.meshes.new("Male 07c colour surface")
mesh.from_pydata([v.co[:] for v in body.data.vertices], [], [tuple(p.vertices) for p in body.data.polygons])
proxy = bpy.data.objects.new(mesh.name, mesh)
scene.collection.objects.link(proxy)
bpy.context.view_layer.objects.active = proxy
modifier = proxy.modifiers.new("Colour sample density", "SUBSURF")
modifier.subdivision_type = "SIMPLE"
modifier.levels = 1
bpy.ops.object.modifier_apply(modifier=modifier.name)
mesh = proxy.data

uv = []
for vertex in mesh.vertices:
    hit, _, index, _ = tree.find_nearest(vertex.co)
    tri = triangles[index]
    a,b,c = (positions[i] for i in tri.vertices)
    s,t,u = (Vector((*source_uv[i].vector, 0)) for i in tri.loops)
    uv.append(barycentric_transform(hit,a,b,c,s,t,u).xy)
sample = np.asarray(uv) * np.array([width,height]) - .5
x,y = np.floor(sample).astype(int).T
fx,fy = (sample - np.floor(sample)).T
colours = sum(pixels[(y+j)%height,(x+i)%width] * (wx*wy)[:,None]
              for i,wx in [(0,1-fx),(1,fx)] for j,wy in [(0,1-fy),(1,fy)])
xyz = np.empty(len(mesh.vertices)*3,dtype=np.float32)
mesh.vertices.foreach_get("co",xyz)
xyz = xyz.reshape(-1,3)
px, py, z = xyz.T
pelvis = (z > .73) & (z < 1.15) & (np.abs(px) < .27)
dark = (colours[:,0] - colours[:,2] < .155) & (colours[:,0] < .62)
skin = (colours[:,0] - colours[:,2] > .16) & (colours[:,0] > .54)
for name, part in [("front",py<-.055),("side",np.abs(py)<.045),("back",py>.045)]:
    for lo,hi in [(0,.06),(.06,.12),(.12,.18),(.18,.27)]:
        values=z[pelvis&dark&part&(np.abs(px)>=lo)&(np.abs(px)<hi)]
        if len(values):
            print("EDGE",name,lo,np.round(np.percentile(values,[1,5,95,99]),3),flush=True)

def layer(name, samples):
    linear = samples.copy()
    rgb = linear[:,:3]
    rgb[:] = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    linear[:,3] = 1
    attr = mesh.color_attributes.new(name=name,type="FLOAT_COLOR",domain="POINT")
    attr.data.foreach_set("color",linear.astype(np.float32).ravel())

layer("Source appearance",colours)
skin_ids = np.flatnonzero(pelvis & skin)
skin_tree = KDTree(len(skin_ids))
for i in skin_ids:
    skin_tree.insert(xyz[i],int(i))
skin_tree.balance()
cleaned = colours.copy()
for i in np.flatnonzero(pelvis & dark):
    nearest = skin_tree.find_n(xyz[i],4)
    weights = np.array([1/max(distance,.001) for _,_,distance in nearest])
    cleaned[i] = np.average(colours[[index for _,index,_ in nearest]],axis=0,weights=weights)
layer("Cleaned skin",cleaned)

material = bpy.data.materials.new("Standing appearance review")
material.use_nodes = True
mesh.materials.append(material)
nodes, links = material.node_tree.nodes, material.node_tree.links
shader = nodes.get("Principled BSDF")
shader.inputs["Roughness"].default_value = .55

def feed(value, socket):
    if isinstance(value,bpy.types.NodeSocket):
        links.new(value,socket)
    else:
        socket.default_value = value

def math(operation, a, b=0):
    node = nodes.new("ShaderNodeMath")
    node.operation = operation
    feed(a,node.inputs[0])
    feed(b,node.inputs[1])
    return node.outputs[0]

def mix(factor,a,b):
    node = nodes.new("ShaderNodeMixRGB")
    for value,socket in zip((factor,a,b),node.inputs):
        feed(value,socket)
    return node.outputs[0]

def colour(name):
    node = nodes.new("ShaderNodeVertexColor")
    node.layer_name = name
    return node.outputs["Color"]

pos = nodes.new("ShaderNodeSeparateXYZ")
links.new(nodes.new("ShaderNodeNewGeometry").outputs["Position"],pos.inputs[0])
x,y,z = (pos.outputs[i] for i in range(3))

def fade(value, lo, hi):
    node = nodes.new("ShaderNodeMapRange")
    node.interpolation_type = "SMOOTHSTEP"
    feed(value,node.inputs["Value"])
    node.inputs["From Min"].default_value = lo
    node.inputs["From Max"].default_value = hi
    return node.outputs[0]

front = fade(y,-.12,.12)
inner = math("SUBTRACT",1,fade(math("ABSOLUTE",x),.012,.115))
waist = math("ADD",1.060, math("MULTIPLY",front,.020))
hem = math("SUBTRACT",.838,math("MULTIPLY",inner,.025))
hem = math("SUBTRACT",hem,math("MULTIPLY",front,.010))
inside = math("MINIMUM",math("SUBTRACT",waist,z),math("SUBTRACT",z,hem))
mask = fade(inside,-.0006,.0008)
mask = math("MULTIPLY",mask,math("SUBTRACT",1,fade(math("ABSOLUTE",x),.265,.28)))
band = math("SUBTRACT",1,fade(math("SUBTRACT",waist,z),.018,.021))
cuff = math("SUBTRACT",1,fade(math("SUBTRACT",z,hem),.003,.005))
trim = math("MAXIMUM",band,cuff)
fabric = mix(trim,(.034,.045,.058,1),(.024,.031,.042,1))
corrected = mix(mask,colour("Cleaned skin"),fabric)
fabric_roughness = math("ADD",.55,math("MULTIPLY",mask,.22))

for o in scene.objects:
    o.hide_render = o != proxy
for f in mesh.polygons:
    f.use_smooth = True
scene.render.engine = "CYCLES"
scene.cycles.samples = 12
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.world = bpy.data.worlds.new("Review studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (.29,.34,.44,1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = .43
scene.render.film_transparent = True

def aim(o, point):
    o.rotation_euler = (Vector(point)-o.location).to_track_quat("-Z","Y").to_euler()

for name,loc,strength,col,size in [
    ("Key",(-3,-4,4),460,(1,.89,.77),4),
    ("Fill",(3,-2,2.8),260,(.80,.90,1),3.5),
    ("Back",(1,3,3.7),460,(.86,.91,1),3),
]:
    data = bpy.data.lights.new(name,"AREA")
    data.energy,data.color,data.shape,data.size = strength,col,"DISK",size
    obj = bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    obj.location = loc
    aim(obj,(0,0,1.02))
data = bpy.data.cameras.new("Review")
data.type = "ORTHO"
cam = bpy.data.objects.new("Review",data)
scene.collection.objects.link(cam)
scene.camera = cam
out.mkdir(parents=True,exist_ok=True)
for version, surface in [("before",colour("Source appearance")),("after",corrected)]:
    links.new(surface,shader.inputs["Base Color"])
    if version == "after":
        links.new(fabric_roughness,shader.inputs["Roughness"])
    for view,direction in [("front",(0,-1,0)),("side",(1,0,0)),("back",(0,1,0)),("three_quarter",(.6,-.8,.02))]:
        if version == "before" and view == "three_quarter":
            continue
        center = Vector((0,-.01,.94))
        cam.location = center + Vector(direction).normalized()*4
        aim(cam,center)
        data.ortho_scale = .55
        scene.render.resolution_x,scene.render.resolution_y = 650,650
        scene.render.resolution_percentage = 100
        scene.render.filepath = str(out / f"{version}_{view}.png")
        bpy.ops.render.render(write_still=True)
    if version == "after":
        center = Vector((0,0,.91))
        cam.location = center + Vector((.25,-1,.01)).normalized()*4
        aim(cam,center)
        data.ortho_scale = 1.96
        scene.render.resolution_x,scene.render.resolution_y = 830,1220
        scene.render.filepath = str(out / "after_standing.png")
        bpy.ops.render.render(write_still=True)
