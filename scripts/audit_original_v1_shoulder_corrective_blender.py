"""Read-only audit of the shoulder corrective shape keys of a candidate (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_shoulder_corrective_blender.py -- <out.json> <declaration.json> <runtime spec.json>

Checks: the two keys exist and start at value 0; every vertex whose key differs from the Basis is inside the declared vertex set (left key: declared
left-owned ids; right key: their exact mirror twins); the key data equals the runtime spec (float32 tolerance); the right key is the exact mirror of the
left key (asymmetry in metres); Basis equals the mesh rest; the largest displacement and the count of moved vertices; the driver config on the scene.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out, decl_path, spec_path = Path(args[0]), Path(args[1]), Path(args[2])
FLEX = len(args) > 3 and args[3] == "flexion"          # optional: audit the forward-flexion key pair (HGPT_SHOULDER_FLEX_L/R) instead of the abduction pair
KL_NAME, KR_NAME = ("HGPT_SHOULDER_FLEX_L", "HGPT_SHOULDER_FLEX_R") if FLEX else ("HGPT_SHOULDER_CORR_L", "HGPT_SHOULDER_CORR_R")
CFG_KEY = "hgpt_flexion_corrective" if FLEX else "hgpt_shoulder_corrective"
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
decl = json.loads(decl_path.read_text(encoding="utf-8"))
spec = json.loads(spec_path.read_text(encoding="utf-8"))
keys = me.shape_keys.key_blocks
issues = []
for n in ("Basis", KL_NAME, KR_NAME):
    if n not in keys:
        issues.append("missing key " + n)
basis = np.array([d.co[:] for d in keys["Basis"].data])
rest = np.array([v.co[:] for v in me.vertices])
KL = np.array([d.co[:] for d in keys[KL_NAME].data]) - basis
KR = np.array([d.co[:] for d in keys[KR_NAME].data]) - basis
nV = len(rest)
key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mir = np.array([key.get(tuple(np.round(rest[i] * [-1, 1, 1], 5)), -1) for i in range(nV)])
left = set(decl["left_owned_vertex_ids"])
movedL = set(np.nonzero(np.abs(KL).max(axis=1) > 1e-9)[0].tolist())
movedR = set(np.nonzero(np.abs(KR).max(axis=1) > 1e-9)[0].tolist())
if not movedL <= left:
    issues.append(f"left key moves {len(movedL - left)} vertices outside the declaration")
if not movedR <= {int(mir[v]) for v in left}:
    issues.append(f"right key moves {len(movedR - {int(mir[v]) for v in left})} vertices outside the mirrored declaration")
S = np.array([-1.0, 1.0, 1.0])
asym = float(np.abs(KR[mir] * S - KL).max())
sp = np.zeros((nV, 3))
for v, row in zip(spec["left"]["vertex_ids"], spec["left"]["delta_m"]):
    sp[v] = row
spec_err = float(np.abs(sp - KL).max())
if spec_err > 2e-6:
    issues.append(f"left key differs from the runtime spec by {spec_err:.2e} m")
if asym > 1e-6:
    issues.append(f"mirror asymmetry {asym:.2e} m")
if float(np.abs(basis - rest).max()) > 1e-12:
    issues.append("Basis differs from rest")
vals = {n: keys[n].value for n in (KL_NAME, KR_NAME) if n in keys}
if any(abs(v) > 1e-12 for v in vals.values()):
    issues.append("a corrective key is not at value 0 in the saved file")
cfg = json.loads(bpy.context.scene.get(CFG_KEY, "{}") or "{}")
rec = {"candidate": Path(bpy.data.filepath).name, "candidate_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
       "declaration": decl_path.name, "runtime_spec": spec_path.name, "driver_config": cfg,
       "left_key_moved_vertices": len(movedL), "right_key_moved_vertices": len(movedR), "declared_left_owned": len(left),
       "max_delta_m": round(float(max(np.abs(KL).max(), np.abs(KR).max())), 5), "mirror_asymmetry_m": asym, "runtime_spec_max_error_m": spec_err,
       "key_values_saved": vals, "issues": issues, "status": "CLEAN" if not issues else "ISSUES"}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("SHOULDER CORRECTIVE AUDIT", rec["status"], "moved L/R", len(movedL), len(movedR), "max delta", rec["max_delta_m"], "asym", asym)
