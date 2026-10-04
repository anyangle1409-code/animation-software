"""Add the declared scapular-rotation lateral/back torso corrective to a NEW numbered O4 candidate as a third pair of shape keys (first-party; declared before the solve).

blender --background --factory-startup <source.blend> --python-exit-code 1 ^
  --python scripts/apply_original_v1_scapular_corrective_blender.py -- <solution.npz> <declaration.json> <new.blend> <runtime spec.json>

The source must already carry the abduction (and flexion) corrective keys; they are left untouched. Adds HGPT_SHOULDER_SCAP_L and
HGPT_SHOULDER_SCAP_R: key L holds rest + D on the declared left-owned vertices; key R holds the exact mirror image. The driver config is stored on the
scene as hgpt_scapular_corrective (u0/u1, key names); original_v1_flexion_driver.py drives the keys with a = smoothstep((u - u0)/(u1 - u0)), u = rotation of the
scapula relative to the trunk (deg). The runtime spec for the standalone engine is written to <runtime spec.json>. Refuses to overwrite; refuses if the
solution vertex set differs from the declaration or was solved against another source; verifies the existing keys, weights, topology, bones (67) and rest
geometry are unchanged and the mirror asymmetry is <= 1e-6 m.
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
if me.shape_keys is None or "HGPT_SHOULDER_CORR_L" not in me.shape_keys.key_blocks:
    raise SystemExit("source must carry the abduction corrective keys")
if "HGPT_SHOULDER_SCAP_L" in me.shape_keys.key_blocks:
    raise SystemExit("source already carries scapular keys")
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
asym = float(np.abs(DL - DR[mir] * S).max())
if np.abs(DL[mir] * S - DR).max() > 1e-12:
    raise SystemExit("mirror construction inconsistent")
before_w = {v.index: sorted((g.group, round(g.weight, 9)) for g in v.groups) for v in me.vertices}
n_poly = len(me.polygons)
bones_before = [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]
old = {kb.name: np.array([d.co[:] for d in kb.data]) for kb in me.shape_keys.key_blocks}

kl = body.shape_key_add(name="HGPT_SHOULDER_SCAP_L", from_mix=False)
kr = body.shape_key_add(name="HGPT_SHOULDER_SCAP_R", from_mix=False)
for i in range(nV):
    kl.data[i].co = tuple(rest[i] + DL[i])
    kr.data[i].co = tuple(rest[i] + DR[i])
kl.value = kr.value = 0.0
kl.slider_min = kr.slider_min = 0.0
kl.slider_max = kr.slider_max = 1.0
bpy.context.view_layer.update()
chk = np.array([v.co[:] for v in me.vertices])
if np.abs(chk - rest).max() > 1e-12:
    raise SystemExit("rest geometry changed")
for n, arr in old.items():
    if np.abs(np.array([d.co[:] for d in me.shape_keys.key_blocks[n].data]) - arr).max() > 0:
        raise SystemExit(f"existing key {n} changed")
if before_w != {v.index: sorted((g.group, round(g.weight, 9)) for g in v.groups) for v in me.vertices} or len(me.polygons) != n_poly:
    raise SystemExit("weights/topology changed")
if bones_before != [(b.name, tuple(b.head_local), tuple(b.tail_local)) for b in rig.data.bones]:
    raise SystemExit("bones changed")
cfg = {"u0_deg": float(sol["u0"]), "u1_deg": float(sol["u1"]), "keys": {"l": kl.name, "r": kr.name}}
scene["hgpt_scapular_corrective"] = json.dumps(cfg)
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = src_sha
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
spec = {"schema": "hgpt_scapular_corrective_v1", "generated_utc": datetime.now(timezone.utc).isoformat(), "candidate": new_path.name,
        "driver": {"type": "scapular_rotation_relative_to_trunk", "humerus_bone": "upperarm_<side>", "trunk_bone": "spine_03", "frame": "armature",
                   "definition": "u = angle (deg) of R_rel = R_spine_03^T R_scapula_<side>, with R the 3x3 rotation of each bone's skinning matrix (posed matrix times the inverse rest matrix) in the armature frame; in the stress poses R_rel is almost purely a rotation about the trunk anterior axis (scapular upward rotation)"},
        "activation": {"type": "smoothstep_C1", "u0_deg": cfg["u0_deg"], "u1_deg": cfg["u1_deg"], "formula": "t=clamp((u-u0)/(u1-u0),0,1); a=t*t*(3-2*t)"},
        "composition": "rest_posed = rest + [existing abduction and flexion terms] + a(u_L)*D_L + a(u_R)*D_R, then ordinary skinning (vertex morph add before skinning)",
        "mirror": {"rule": "x -> -x", "D_R_of_mirror_vertex": "(-dx, dy, dz) of D_L(vertex)", "mirror_map_by": "exact rest-space mirror of the vertex position (rounded 1e-5)"},
        "left": {"vertex_ids": verts, "delta_m": [[round(float(c), 7) for c in row] for row in D]},
        "declaration": decl_path.name, "declaration_ids_sha256": decl["ids_sha256"], "solution_sha256": hashlib.sha256(sol_path.read_bytes()).hexdigest()}
spec_path.write_text(json.dumps(spec) + "\n", encoding="utf-8")
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(), "stage": "O4 candidate: scapular-rotation lateral/back torso corrective shape keys (not production)",
       "source_candidate": src.name, "source_sha256": src_sha, "candidate": new_path.name,
       "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(), "declaration": decl_path.name,
       "declaration_sha256": hashlib.sha256(decl_path.read_bytes()).hexdigest(), "solution": sol_path.name,
       "solution_sha256": hashlib.sha256(sol_path.read_bytes()).hexdigest(), "runtime_spec": spec_path.name,
       "runtime_spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(), "driver_config": cfg,
       "left_owned_vertices": len(verts), "max_delta_m": round(float(np.abs(D).max()), 5), "mirror_asymmetry_m": asym,
       "weights_changed": False, "topology_changed": False, "bones_changed": False, "rest_geometry_changed": False, "bone_count": len(rig.data.bones)}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("FLEXION CORRECTIVE APPLIED", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "left_owned_vertices", "max_delta_m", "bone_count")}))
