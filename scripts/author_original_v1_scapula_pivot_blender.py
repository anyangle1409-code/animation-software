"""Relocate the scapula bone pivot (head) along its own axis into a NEW numbered O4 candidate (first-party rig revision; declare, then apply).

Declare (read-only):  blender --background --factory-startup <source.blend> --python-exit-code 1 ^
    --python scripts/author_original_v1_scapula_pivot_blender.py -- declare <declaration.json> <fraction>
Apply:                ... -- apply <declaration.json> <new.blend>

Why: the rig's scapula bone starts at the acromioclavicular/glenoid corner, so scapular upward rotation pivots about that corner. Real
scapular upward rotation has an instantaneous centre that starts near the medial root of the scapular spine and migrates toward the AC
joint with elevation (PubMed 3196449 "A biomechanical analysis of scapular rotation during arm abduction in the scapular plane";
PMC3377910 for the rhythm). Pivoting at the AC corner for the whole arc swings the plate (and the upper-back skin weighted to it)
about 2.4x too far: with a physiological 60 deg of upward rotation the upper back stretched 5-6x (P3 evidence, r42 dump analysis).
Moving the bone HEAD to <fraction> of the way toward its tail changes only the rotation pivot: the rest pose, weights, mesh, tail, roll,
parent and every other bone are untouched; the upperarm child keeps its own head at the glenoid, so scapular rotation now carries the glenoid
along an arc (the scapulothoracic glide). Both sides, mirror exact.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0]
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
BONES = ("scapula_l", "scapula_r")
before = {b.name: (tuple(b.head_local), tuple(b.tail_local), b.parent.name if b.parent else None, b.use_connect) for b in rig.data.bones}

if mode == "declare":
    out, frac = Path(args[1]), float(args[2])
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    plan = {}
    for n in BONES:
        h, t = before[n][0], before[n][1]
        plan[n] = {"old_head": h, "new_head": [round(a + (b - a) * frac, 9) for a, b in zip(h, t)], "tail": t}
    rec = {"declared_utc": datetime.now(timezone.utc).isoformat(), "declared_before_edit": True, "source_candidate": src.name,
           "source_sha256": src_sha, "operation": "scapula pivot relocation", "fraction_toward_tail": frac, "bones_changed": list(BONES),
           "plan": plan, "weights_changed": False, "geometry_changed": False, "other_bones_changed": False,
           "evidence": "P3 upper-back stretch with the AC-corner pivot (r42 P3 dump) and the literature on the scapular instantaneous centre"}
    out.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("SCAPULA PIVOT DECLARED", out, "fraction", frac)
    raise SystemExit(0)

decl_path, new_path = Path(args[1]), Path(args[2])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
decl = json.loads(decl_path.read_text(encoding="utf-8"))
if not decl.get("declared_before_edit") or decl["source_sha256"] != src_sha:
    raise SystemExit("declaration does not match this source candidate")
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for n in BONES:
    eb = rig.data.edit_bones[n]
    roll = eb.roll
    eb.head = tuple(decl["plan"][n]["new_head"])
    eb.roll = roll
    eb.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")
for name, (h, t, p, c) in before.items():
    b = rig.data.bones[name]
    now = (tuple(b.head_local), tuple(b.tail_local), b.parent.name if b.parent else None, b.use_connect)
    if name in BONES:
        if max(abs(x - y) for x, y in zip(now[1], t)) > 1e-7 or now[2] != p:
            raise SystemExit(f"{name}: tail/parent changed")
    elif max(abs(x - y) for x, y in zip(now[0] + now[1], h + t)) > 1e-7 or now[2] != p:
        raise SystemExit(f"bone {name} outside the declaration changed")
scene["hgpt_scapula_pivot_fraction"] = decl["fraction_toward_tail"]
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "stage": "O4 candidate first-party rig revision: scapula pivot relocation (not production)",
       "source_candidate": src.name, "source_sha256": src_sha, "candidate": new_path.name,
       "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(), "declaration": decl_path.name,
       "declaration_sha256": hashlib.sha256(decl_path.read_bytes()).hexdigest(), "fraction_toward_tail": decl["fraction_toward_tail"],
       "bone_count": len(rig.data.bones), "weights_changed": False, "geometry_changed": False, "topology_changed": False}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("SCAPULA PIVOT APPLIED", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "bone_count", "fraction_toward_tail")}))
