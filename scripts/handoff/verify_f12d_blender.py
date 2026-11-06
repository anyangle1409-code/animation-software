"""Open an HGPT female checkpoint in a fresh Blender session and report its contents (read-only; never saves).
usage: blender -b --factory-startup --python verify_f12d_blender.py -- <file.blend> <out.json>
   or: python3 (with bpy module) verify_f12d_blender.py -- <file.blend> <out.json>
"""
import json, sys
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0], load_ui=False)
r = {"blender_version": bpy.app.version_string, "file": a[0], "objects": {}, "images": {}, "libraries": [l.filepath for l in bpy.data.libraries],
     "external_paths": sorted(bpy.utils.blend_paths(absolute=True)), "scenes": [s.name for s in bpy.data.scenes]}
for o in bpy.data.objects:
    d = {"type": o.type, "parent": o.parent.name if o.parent else None, "modifiers": [(m.type, m.name, getattr(getattr(m, "object", None), "name", None)) for m in o.modifiers]}
    if o.type == "MESH":
        me = o.data; d.update({"vertices": len(me.vertices), "faces": len(me.polygons), "vertex_groups": len(o.vertex_groups),
                               "materials": [m.name if m else None for m in me.materials], "uv_layers": [u.name for u in me.uv_layers],
                               "color_attributes": [c.name for c in me.color_attributes], "shape_keys": len(me.shape_keys.key_blocks) if me.shape_keys else 0})
        if o.vertex_groups:
            w = [sum(g.weight for g in v.groups) for v in me.vertices]; d["weight_sum_min_max"] = [round(min(w), 4), round(max(w), 4)]
            d["unweighted_vertices"] = sum(1 for x in w if x < 1e-6)
    if o.type == "ARMATURE":
        d.update({"bones": len(o.data.bones), "deform_bones": sum(b.use_deform for b in o.data.bones), "bone_names": [b.name for b in o.data.bones]})
    r["objects"][o.name] = d
for im in bpy.data.images:
    r["images"][im.name] = {"size": list(im.size), "packed": im.packed_file is not None, "packed_bytes": im.packed_file.size if im.packed_file else 0,
                            "filepath": im.filepath, "source": im.source}
r["unpacked_external_images"] = [n for n, v in r["images"].items() if not v["packed"] and v["source"] == "FILE"]
json.dump(r, open(a[1], "w"), indent=1); print("VERIFY_OK", r["blender_version"], len(r["objects"]), "objects", len(r["images"]), "images",
                                                 "unpacked:", r["unpacked_external_images"], "libraries:", r["libraries"])
