"""Read-only inspection of Home Gym PT male manual torso/head retopology WIP.

Usage:
  blender -b path/to/HGPT_Male_Retopo_03_TorsoHead_WIP.blend --python scripts/retopology/check_task3_wip.py -- output.json

Does not edit or save the .blend file. Open WIP with linked high-detail source in ../source/.
"""
import bpy
import bmesh
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

BODY_NAME = "HGPT_Male_Body_WIP"
SOURCE_NAME = "HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend"
SOURCE_SHA256 = "b41518437550a6aa57df65c80c05fbc7955053619d94efa83f6587f54efe4e9f"

def sha256(path):
    result = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()

def components(mesh):
    parent = list(range(len(mesh.verts)))
    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    for e in mesh.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    return sorted(Counter(find(v.index) for v in mesh.verts).values(), reverse=True)

def main():
    obj = bpy.data.objects.get(BODY_NAME)
    if obj is None or obj.type != "MESH":
        raise RuntimeError("Missing " + BODY_NAME)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    src = os.path.normpath(os.path.join(os.path.dirname(bpy.data.filepath), "../source", SOURCE_NAME))
    output = {
        "status": "TASK3_INCOMPLETE__READ_ONLY_DIAGNOSTIC",
        "workfile": bpy.data.filepath,
        "source_present": os.path.isfile(src),
        "source_hash_matches": sha256(src) == SOURCE_SHA256 if os.path.isfile(src) else False,
        "linked_blender_libraries": [bpy.path.abspath(lib.filepath) for lib in bpy.data.libraries],
        "mesh": obj.name,
        "vertices": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "quad_faces": sum(len(f.verts) == 4 for f in bm.faces),
        "boundary_edges": sum(e.is_boundary for e in bm.edges),
        "wire_only_edges": sum(e.is_wire for e in bm.edges),
        "overused_edges": sum(len(e.link_faces) > 2 for e in bm.edges),
        "loose_vertices": sum(not v.link_edges for v in bm.verts),
        "vertex_component_sizes": components(bm),
        "modifiers": [{"name": m.name, "type": m.type} for m in obj.modifiers],
        "armatures": [o.name for o in bpy.data.objects if o.type == "ARMATURE"],
        "note": "Numbers are the unapplied source mesh, not an accepted production topology.",
    }
    bm.free()
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    filename = Path(arguments[0]) if arguments else Path(bpy.path.abspath("//../reports/check_task3_wip.json"))
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    if not output["source_hash_matches"]:
        raise RuntimeError("Missing/mismatched external source; ensure ../source/ layout is preserved.")
if __name__ == "__main__":
    main()
