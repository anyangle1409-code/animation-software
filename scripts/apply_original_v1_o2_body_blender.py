"""Write the project-authored O2 body into the guarded production Blend.

Run only through RUN_ORIGINAL_V1_O2_GUARDED_SCRIPT.bat (guard active). Replaces
the vertices/faces of HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD_MESH in place with the
output of scripts/original_v1_o2_body.py, which reads only the committed v4
rig payload and its own authored measurements. No datablock is added.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_o2_body as generator  # noqa: E402
from original_v1_authoring_boundary import BODY_OBJECT, ROOT  # noqa: E402

scene = bpy.context.scene
if not scene.get("hgpt_guarded_authoring") or scene.get("hgpt_authoring_tainted"):
    raise RuntimeError("Guarded, untainted O2 session required.")

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
region = args[0] if args else "unspecified"

result = generator.build()
body = bpy.data.objects[BODY_OBJECT]
mesh = body.data
mesh.clear_geometry()
mesh.from_pydata([tuple(p) for p in result["vertices"]], [], [tuple(f) for f in result["faces"]])
mesh.validate(clean_customdata=False)
mesh.update()
for poly in mesh.polygons:
    poly.use_smooth = True
    poly.material_index = 0
body.matrix_world.identity()
if mesh.uv_layers or mesh.shape_keys or body.vertex_groups:
    raise RuntimeError("Unexpected UV/shape key/vertex group after body generation.")

record_path = ROOT / "ORIGINAL_V1_WORK" / "O2_BODY_GENERATION.json"
record = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "region": region,
    "method": "project-authored ring/split-junction quad cage + one Catmull-Clark level (plain Python)",
    "inputs": {
        "rig_payload": "ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json",
        "rig_payload_sha256": result["rig_payload_sha256"],
        "generator": "scripts/original_v1_o2_body.py",
        "generator_version": result["generator_version"],
        "generator_sha256": result["generator_sha256"],
    },
    "not_used": ["O1 scaffold vertex positions", "legacy/third-party meshes", "projection/shrinkwrap",
                 "weights", "UVs", "materials/textures", "imported bind data"],
    "cage": result["cage"],
    "vertices": len(mesh.vertices),
    "faces": len(mesh.polygons),
    "triangles": sum(len(p.vertices) - 2 for p in mesh.polygons),
}
record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
bpy.ops.wm.save_mainfile()
print("HGPT O2 body written:", json.dumps({k: record[k] for k in ("region", "vertices", "faces")}))
