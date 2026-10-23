"""Read-only inspection of a Body v2 .blend.  Run with Blender 5.x / bpy.  It opens the file and NEVER saves.

    python3.13 verify_body_v2_blend.py -- <file.blend> <expected_key> <expected_json> <out.json>

<expected_key> is one of v13s_w8, draft_v14a_legs, draft_v14b_torso (keys of "expected_for_blend_check" in the
offline_evidence_check.json written by verify_offline_evidence.py), or "none" to only report measurements (R120).

STATUS: syntax-checked only.  Not executed against Blender in the session that wrote it (no bpy there).
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
BLEND, KEY, EXPECT_JSON, OUT = Path(args[0]).resolve(), args[1], Path(args[2]), Path(args[3])
BODY, RIG = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE", "HGPT_CANONICAL_V4_ORIGINAL"


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


before = sha_file(BLEND)
bpy.ops.wm.open_mainfile(filepath=str(BLEND), load_ui=False)
saved_by = ".".join(str(v) for v in bpy.data.version)        # version of Blender that last SAVED this file

body, rig = bpy.data.objects.get(BODY), bpy.data.objects.get(RIG)
res = {"file": str(BLEND), "sha256": before, "bytes": BLEND.stat().st_size,
       "blender_running": bpy.app.version_string, "file_last_saved_by_blender": saved_by,
       "objects": sorted(o.name for o in bpy.data.objects), "checks": []}


def check(name, ok, detail):
    res["checks"].append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})


check("body object present", body is not None, BODY)
check("rig object present", rig is not None, RIG)
if body is not None:
    me = body.data
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float64); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    keys = [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else []
    mods = [(m.type, m.object.name if getattr(m, "object", None) else None) for m in body.modifiers]
    res["measured"] = {
        "body_vertices": nv, "body_triangles": sum(len(p.vertices) - 2 for p in me.polygons),
        "vertex_groups": len(body.vertex_groups), "shape_keys": len(keys), "modifiers": mods,
        "basis_z_extent_m": float(co[:, 2].max() - co[:, 2].min()),
        # content hash of the basis mesh quantised to 0.01 mm: stable across re-saves, unlike the file hash
        "basis_content_sha256": hashlib.sha256(np.round(co * 1e5).astype(np.int64).tobytes()).hexdigest(),
        "mirror_x_max_dev_mm": None,
        "armature_bones": len(rig.data.bones) if rig else None,
        "drivers_on_shape_keys": len(me.shape_keys.animation_data.drivers) if me.shape_keys and me.shape_keys.animation_data else 0,
    }
    # left/right MIRROR symmetry of the geometry (x -> -x).  This is geometry symmetry only.  It says nothing about
    # which side is the anatomical left: see docs/BODY_V2_RECOVERY_HANDOVER_20261023.md "Left/right".
    from scipy.spatial import cKDTree
    d, _ = cKDTree(co).query(co * np.array([-1.0, 1.0, 1.0]))
    res["measured"]["mirror_x_max_dev_mm"] = float(d.max() * 1000)
    check("armature modifier is plain linear-blend skinning on the rig", ("ARMATURE", RIG) in mods, mods)
    if KEY != "none":
        exp = json.loads(EXPECT_JSON.read_text())["expected_for_blend_check"][KEY]
        m = res["measured"]
        check("vertex count", m["body_vertices"] == exp["body_vertices"], (m["body_vertices"], exp["body_vertices"]))
        if exp.get("vertex_groups") is not None:
            check("vertex groups", m["vertex_groups"] == exp["vertex_groups"], (m["vertex_groups"], exp["vertex_groups"]))
        if exp.get("shape_keys") is not None:
            check("shape keys", m["shape_keys"] == exp["shape_keys"], (m["shape_keys"], exp["shape_keys"]))
        if exp.get("stature_m") is not None:
            # informational: the archived stature may be measured in the posed/standing state, not the basis extent
            res["info_stature"] = {"archived_m": exp["stature_m"], "basis_z_extent_m": m["basis_z_extent_m"]}

after = sha_file(BLEND)
check("verification did not modify the file", before == after, {"before": before, "after": after})
res["summary"] = {"pass": sum(c["result"] == "PASS" for c in res["checks"]), "fail": sum(c["result"] == "FAIL" for c in res["checks"])}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(res, indent=1))
print("BLEND_VERIFY", json.dumps(res["summary"]), saved_by, flush=True)
