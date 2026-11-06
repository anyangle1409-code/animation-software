"""FEMALE colour textures: bake HER source albedo (Meshy Pro Image_0) onto the new meshes' own UVs. NEW file.

* Her original source object (with its UVs and packed textures) is appended from the verified source .blend
  (read-only) as HGPT_FEMALE_SOURCE_TEXTURED, transform identity (same frame as the working source).
* Each new mesh (body, bra, shorts, ponytail) gets UVs by Smart UV Project, an image (body BODY_RES, others 2048),
  and a material (Principled, base colour = the baked image, roughness ROUGH per object).
* Cycles bake, DIFFUSE colour only (no lighting), selected-to-active from the textured source, cage extrusion EXTRUDE,
  max ray distance RAYMAX, in the REST pose (the source's pose). Images are packed into the output file.
  The body under the garments receives the fabric colour where the garments cover it (hidden in clothed views; the
  unclothed review is shown in clay).

usage: python3.13 bake_f_textures_blender.py -- <in .blend> <original source .blend> <out NEW .blend> <report .json>
"""
import json
import sys
from pathlib import Path

import bpy

a = sys.argv[sys.argv.index("--") + 1:]
IN, SRCB, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
BODY_RES = 4096; EXTRUDE = 0.008; RAYMAX = 0.02
ROUGH = {"HGPT_Female_Body": 0.48, "HGPT_Female_Bra": 0.8, "HGPT_Female_Shorts": 0.8, "HGPT_Female_Ponytail": 0.42}
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
sc = bpy.context.scene; vl = bpy.context.view_layer
with bpy.data.libraries.load(str(SRCB), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
srcob = [o for o in dst.objects if o is not None and o.type == "MESH"][0]
srcob.name = "HGPT_FEMALE_SOURCE_TEXTURED"; sc.collection.objects.link(srcob); srcob.matrix_world.identity()
srcob["NOTE"] = "her verified Meshy Pro source with its own UVs / albedo, appended read-only as the bake source"
rig = bpy.data.objects.get("HGPT_FEMALE_RIG")
if rig:
    rig.data.pose_position = "REST"
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 1
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = EXTRUDE; bk.max_ray_distance = RAYMAX; bk.margin = 8
rep = {"in": IN.name, "bakes": {}}
for name in ("HGPT_Female_Body", "HGPT_Female_Bra", "HGPT_Female_Shorts", "HGPT_Female_Ponytail"):
    ob = bpy.data.objects.get(name)
    if ob is None:
        continue
    me = ob.data
    if "UVMap" not in me.uv_layers:
        me.uv_layers.new(name="UVMap")
    for o in bpy.data.objects:
        o.select_set(False)
    vl.objects.active = ob; ob.select_set(True)
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
        bpy.ops.object.mode_set(mode="OBJECT")
    res = BODY_RES if name == "HGPT_Female_Body" else 2048
    img = bpy.data.images.new(name + "_albedo", res, res); img.colorspace_settings.name = "sRGB"
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = ROUGH[name]
    if name == "HGPT_Female_Body" and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.12; bsdf.inputs["Subsurface Radius"].default_value = (0.008, 0.004, 0.0025)
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; nt.links.new(tex.outputs[0], bsdf.inputs["Base Color"])
    nt.nodes.active = tex
    me.materials.clear(); me.materials.append(m)
    srcob.select_set(True); ob.select_set(True); vl.objects.active = ob
    with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[srcob, ob], selected_editable_objects=[srcob, ob]):
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_selected_to_active=True, cage_extrusion=EXTRUDE,
                            max_ray_distance=RAYMAX, margin=8)
    img.pack()
    px = list(img.pixels[0:4 * 4096 * 16]) if False else None
    rep["bakes"][name] = {"resolution": res, "uv": "smart project", "faces": len(me.polygons)}
    srcob.select_set(False)
srcob.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1)); print("BAKE", json.dumps(rep))
