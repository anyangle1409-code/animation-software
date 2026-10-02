"""Write an optimised shoulder weight solution into a NEW numbered O4 candidate.

blender --background --factory-startup <source candidate.blend> --python-exit-code 1 \
        --python scripts/apply_original_v1_o4_weight_solution_blender.py -- <solution.npz> <new candidate.blend>

The solution comes from scripts/optimize_original_v1_o4_shoulder_weights.py.
Only the solution's zone vertices are rewritten (their deform-bone groups are
replaced); every other vertex, the mesh, the shorts and the 63-bone rig are
untouched. Refuses to overwrite an existing file. Writes <new>.json with hashes.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
sol_path, new_path = Path(args[0]), Path(args[1])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Candidate files only.")
src_path = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src_path.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
n_bones = len(rig.data.bones)
if n_bones not in (63, 67, 71):      # 63 = v4; 71 = rev2 (+ axial twist helpers); see ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_*.json
    raise SystemExit(f"Expected the 63-bone v4 rig or the 71-bone rev2 rig, found {n_bones}")

sol = np.load(sol_path)
verts = [int(v) for v in sol["vertices"]]
bnames = [str(x) for x in sol["bones"]]
W = sol["weights"]
if (W < -1e-9).any() or np.abs(W.sum(axis=1) - 1).max() > 1e-6 or ((W > 1e-6).sum(axis=1) > 4).any():
    raise SystemExit("Solution weights are not normalised 4-influence weights.")

deform = {b.name for b in rig.data.bones if b.use_deform}
groups = {n: body.vertex_groups.get(n) or body.vertex_groups.new(name=n) for n in bnames}
for g in body.vertex_groups:
    if g.name in deform:
        g.remove(verts)
for j, n in enumerate(bnames):
    g = groups[n]
    for k, v in enumerate(verts):
        w = float(W[k, j])
        if w > 1e-6:
            g.add([v], w, "REPLACE")

# Keep the O4 stage tag (read-only audits require 'O4_bind'); record the revision separately.
if scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit(f"Source is not an O4_bind candidate: {scene.get('hgpt_candidate')!r}")
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate shoulder weight optimisation (not production)",
       "solution": sol_path.name, "solution_sha256": hashlib.sha256(sol_path.read_bytes()).hexdigest(),
       "source_candidate": src_path.name, "source_sha256": src_sha,
       "candidate": new_path.name, "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(),
       "vertices_rewritten": len(verts), "bones": bnames, "rig_bones": n_bones,
       "inputs": "this candidate's own ORIGINAL v1 mesh/weights and the v4 rig only"}
sol_rec = sol_path.with_suffix(".json")
if sol_rec.exists():
    rec["optimisation"] = json.loads(sol_rec.read_text(encoding="utf-8"))
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("APPLIED", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "vertices_rewritten")}))
