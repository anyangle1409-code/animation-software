"""Apply the declared shoulder/axilla corrective to a NEW numbered O4 candidate as two shape keys (first-party; declared before the solve).

blender --background --factory-startup <source.blend> --python-exit-code 1 ^
  --python scripts/apply_original_v1_shoulder_corrective_blender.py -- <solution.npz> <declaration.json> <new.blend> <runtime spec.json>

Creates Basis + HGPT_SHOULDER_CORR_L + HGPT_SHOULDER_CORR_R on the body mesh. Key L holds rest + D on the declared left-owned vertices; key R holds
the exact mirror image (D_R(m(v)) = (-dx,dy,dz) of D_L(v)); every other vertex is identical to Basis. The driver spec (theta0/theta1, key names)
is stored on the scene so the pose script drives the keys from the humerothoracic elevation; the runtime spec (vertex ids + float32 deltas +
driver/activation/mirror rule) is written to <runtime spec.json> for the standalone engine. Refuses to overwrite; refuses if the solution vertex set
differs from the declaration; verifies Basis == rest, asymmetry <= 1e-6 m and that no weights/bones/topology changed.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
sol_path, decl_path, new_path, spec_path = Path(args[0]), Path(args[1]), Path(args[2]), Path(args[3])
for p in (new_path, spec_path):
    if p.exists():
        raise SystemExit(f"Refusing to overwrite {p}")
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src = Path(bpy.data.filepath)
src_sha = hashlib.sha256(src.read_bytes()).hexdigest()
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
if me.shape_keys is not None:
    raise SystemExit("body already has shape keys: a corrective revision is applied once")
decl = json.loads(decl_path.read_text(encoding="utf-8"))
sol = np.load(sol_path)
verts = [int(v) for v in sol["vertices"]]
if verts != decl["left_owned_vertex_ids"]:
    raise SystemExit("solution vertex set differs from the declaration: refusing")
if str(sol["source_sha256"]) != src_sha:
    raise SystemExit("solution was solved against a different source candidate")
D = np.asarray(sol["delta"], dtype=np.float64)
rest = np.array([v.co[:] for v in me.vertices])
nV = len(rest)
key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mir = np.array([key.get(tuple(np.round(rest[i] * [-1, 1, 1], 5)), -1) for i in range(nV)])
if (mir < 0).any():
    raise SystemExit("mesh is not mirror symmetric")
S = np.array([-1.0, 1.0, 1.0])
DL = np.zeros((nV, 3))
DR = np.zeros((nV, 3))
for k, v in enumerate(verts):
    DL[v] = D[k]
    DR[mir[v]] = D[k] * S
asym = float(np.abs(DL - DR[mir] * S).max())          # D_R(m(v)) must equal S * D_L(v) wherever D_L is defined
if np.abs(DL[mir] * S - DR).max() > 1e-12:
    raise SystemExit("mirror construction inconsistent")
before_w = {v.index: sorted((g.group, round(g.weight, 9)) for g in v.groups) for v in me.vertices}
n_poly = len(me.polygons)
bones_before = [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]

basis = body.shape_key_add(name="Basis", from_mix=False)
kl = body.shape_key_add(name="HGPT_SHOULDER_CORR_L", from_mix=False)
kr = body.shape_key_add(name="HGPT_SHOULDER_CORR_R", from_mix=False)
for i in range(nV):
    kl.data[i].co = tuple(rest[i] + DL[i])
    kr.data[i].co = tuple(rest[i] + DR[i])
kl.value = kr.value = 0.0
kl.slider_min = kr.slider_min = 0.0
kl.slider_max = kr.slider_max = 1.0
bpy.context.view_layer.update()
chk = np.array([v.co[:] for v in me.vertices])
if np.abs(chk - rest).max() > 1e-12:
    raise SystemExit("Basis differs from rest")
if before_w != {v.index: sorted((g.group, round(g.weight, 9)) for g in v.groups) for v in me.vertices} or len(me.polygons) != n_poly:
    raise SystemExit("weights/topology changed")
if bones_before != [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]:
    raise SystemExit("bones changed")
cfg = {"theta0_deg": float(sol["theta0"]), "theta1_deg": float(sol["theta1"]), "keys": {"l": kl.name, "r": kr.name}}
scene["hgpt_shoulder_corrective"] = json.dumps(cfg)
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
spec = {"schema": "hgpt_shoulder_corrective_v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "candidate": new_path.name,
        "driver": {"type": "humerothoracic_elevation", "humerus_bone": "upperarm_<side>", "trunk_bone": "spine_03", "frame": "armature",
                   "definition": "angle (deg) between the humerus direction (head->tail of upperarm_<side>) and the downward trunk axis (-(head->tail of spine_03))"},
        "activation": {"type": "smoothstep_C1", "theta0_deg": cfg["theta0_deg"], "theta1_deg": cfg["theta1_deg"],
                       "formula": "t=clamp((theta-theta0)/(theta1-theta0),0,1); a=t*t*(3-2*t)"},
        "composition": "rest_posed = rest + a(theta_L)*D_L + a(theta_R)*D_R, then ordinary skinning (vertex morph add before skinning)",
        "mirror": {"rule": "x -> -x", "D_R_of_mirror_vertex": "(-dx, dy, dz) of D_L(vertex)", "mirror_map_by": "exact rest-space mirror of the vertex position (rounded 1e-5)"},
        "left": {"vertex_ids": verts, "delta_m": [[round(float(c), 7) for c in row] for row in D]},
        "declaration": decl_path.name, "declaration_ids_sha256": decl["ids_sha256"], "solution_sha256": hashlib.sha256(sol_path.read_bytes()).hexdigest()}
spec_path.write_text(json.dumps(spec) + "\n", encoding="utf-8")
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "stage": "O4 candidate: generic shoulder/axilla corrective shape keys (not production)",
       "source_candidate": src.name, "source_sha256": src_sha, "candidate": new_path.name,
       "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(), "declaration": decl_path.name,
       "declaration_sha256": hashlib.sha256(decl_path.read_bytes()).hexdigest(), "solution": sol_path.name,
       "solution_sha256": hashlib.sha256(sol_path.read_bytes()).hexdigest(), "runtime_spec": spec_path.name,
       "runtime_spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(), "driver_config": cfg,
       "left_owned_vertices": len(verts), "max_delta_m": round(float(np.abs(D).max()), 5), "mirror_asymmetry_m": asym,
       "weights_changed": False, "topology_changed": False, "bones_changed": False, "rest_geometry_changed": False, "bone_count": len(rig.data.bones)}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("SHOULDER CORRECTIVE APPLIED", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "left_owned_vertices", "max_delta_m")}))
