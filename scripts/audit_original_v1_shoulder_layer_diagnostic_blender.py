"""Read-only shoulder/axilla deformation-layer diagnostic for ORIGINAL v1.

Never saves the Blend.

Usage:
  blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
    --python scripts/audit_original_v1_shoulder_layer_diagnostic_blender.py -- ^
    <out.json> [pose,pose,...] [samples]

Default poses: press_top,pullup_hang
Default samples: 13

Purpose:
  * replay each named pose continuously from rest to endpoint;
  * record humerothoracic elevation and the actual driver values for every
    shoulder corrective key;
  * separate the visible surface into weights-only, each corrective family
    in isolation, and all active shape keys together;
  * quantify per-zone displacement caused by the base skinning versus each
    corrective layer;
  * report static weight ownership for the same zones;
  * never modify or save the source candidate.

The geometric shoulder/axilla zones are diagnostic heuristics only. They are
not anatomy-acceptance definitions and must be paired with real-human visual
review and the fail-closed whole-body issue ledger.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not ARGS:
    raise SystemExit("Usage: ... -- <out.json> [pose,pose,...] [samples]")
OUT = Path(ARGS[0]).resolve()
POSE_LIST = ARGS[1].split(",") if len(ARGS) > 1 and ARGS[1] else ["press_top", "pullup_hang"]
NS = int(ARGS[2]) if len(ARGS) > 2 else 13
if NS < 3:
    raise SystemExit("samples must be >= 3")

POSE_SCRIPT = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
SRC = POSE_SCRIPT.read_text(encoding="utf-8")
if "# ---------------------------------------------------------------- metrics" not in SRC:
    raise SystemExit("pose script metrics marker missing")
_saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": POSE_SCRIPT.name}
exec(compile(SRC[:SRC.index("# ---------------------------------------------------------------- metrics")], "pose_test_defs", "exec"), ns)

# Install the evaluation-time flexion + scapular wrappers used by the production
# pose path. This leaves old candidates unchanged when the configs/keys are absent.
import importlib.util as _ilu
_fd_path = POSE_SCRIPT.with_name("original_v1_flexion_driver.py")
_sp = _ilu.spec_from_file_location("original_v1_flexion_driver", str(_fd_path))
_fd = _ilu.module_from_spec(_sp)
_sp.loader.exec_module(_fd)
_fd.install(ns)
sys.argv = _saved_argv

rig = ns["rig"]
body = ns["body"]
POSES = ns["POSES"]
reset = ns["reset"]
upd = ns["upd"]
pb = ns["pb"]

mask_mod = body.modifiers.get("HGPT_DRESSED_MASK")
if mask_mod is not None:
    mask_mod.show_viewport = False
    mask_mod.show_render = False

candidate_path = Path(bpy.data.filepath)
if not candidate_path.is_file():
    raise SystemExit("candidate filepath missing")
candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

# ---------------------------------------------------------------------------
# Rest mesh, regions, weights, and linear-skinning machinery.
# ---------------------------------------------------------------------------
me = body.data
rest = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
nV = len(rest)
region_names = json.loads(bpy.context.scene["hgpt_region_names"])
region_id = np.array([d.value for d in me.attributes["hgpt_region"].data], dtype=np.int32)
region_label = np.array([region_names[i] for i in region_id], dtype=object)

bone_names = [b.name for b in rig.data.bones]
bidx = {name: i for i, name in enumerate(bone_names)}
gname = {vg.index: vg.name for vg in body.vertex_groups}
W = np.zeros((nV, len(bone_names)), dtype=np.float64)
for v in me.vertices:
    for g in v.groups:
        name = gname[g.group]
        if name in bidx:
            W[v.index, bidx[name]] = g.weight

rw = np.array(rig.matrix_world, dtype=np.float64)
bw = np.array(body.matrix_world, dtype=np.float64)
REST_INV = {
    name: np.linalg.inv(np.array(rig.data.bones[name].matrix_local, dtype=np.float64))
    for name in bone_names
}
rest_h = np.c_[rest, np.ones(nV)]

TRUNK_NAMES = [n for n in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head") if n in bidx]
TRUNK_IDX = [bidx[n] for n in TRUNK_NAMES]
Wt = np.zeros_like(W)
Wt[:, TRUNK_IDX] = W[:, TRUNK_IDX]
Wt_sum = Wt.sum(axis=1, keepdims=True)
Wt = np.divide(Wt, np.maximum(Wt_sum, 1e-12), out=np.zeros_like(Wt), where=Wt_sum > 1e-12)


def skin_matrices():
    """Current pose matrices; caller must have already called upd()."""
    return np.stack([
        rw @ np.array(pb(name).matrix, dtype=np.float64) @ REST_INV[name] @ np.linalg.inv(rw) @ bw
        for name in bone_names
    ])


def transform_vertices(pre_skin, matrices, weights):
    h = np.c_[pre_skin, np.ones(len(pre_skin))]
    transformed = np.einsum("bij,vj->vbi", matrices[:, :3, :], h)
    return np.einsum("vb,vbi->vi", weights, transformed)


# ---------------------------------------------------------------------------
# Shape-key families and deltas.
# ---------------------------------------------------------------------------
shape_keys = me.shape_keys.key_blocks if me.shape_keys is not None else None
basis = rest.copy()
key_delta = {}
if shape_keys is not None:
    if "Basis" in shape_keys:
        basis = np.array([d.co[:] for d in shape_keys["Basis"].data], dtype=np.float64)
    for kb in shape_keys:
        if kb.name == "Basis":
            continue
        key_delta[kb.name] = np.array([d.co[:] for d in kb.data], dtype=np.float64) - basis

if float(np.abs(basis - rest).max()) > 1e-8:
    raise SystemExit("Basis differs from mesh rest; diagnostic refuses ambiguous state")


def scene_cfg(prop):
    raw = bpy.context.scene.get(prop)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception as exc:
        raise SystemExit(f"invalid scene config {prop}: {exc}")


cfg_abd = scene_cfg("hgpt_shoulder_corrective")
cfg_flex = scene_cfg("hgpt_flexion_corrective")
cfg_scap = scene_cfg("hgpt_scapular_corrective")


def cfg_keys(cfg):
    if not cfg:
        return []
    row = cfg.get("keys", {})
    return [row[s] for s in ("l", "r") if row.get(s)]


families = {
    "abduction": cfg_keys(cfg_abd),
    "flexion": cfg_keys(cfg_flex),
    "scapular": cfg_keys(cfg_scap),
}
families = {k: [name for name in v if name in key_delta] for k, v in families.items()}
family_key_set = set().union(*map(set, families.values())) if families else set()

# ---------------------------------------------------------------------------
# Diagnostic zones.
# Existing hgpt_region masks are authoritative labels from the candidate.
# Anatomical-neighbourhood masks below are deliberately simple, deterministic
# rest-space geometric windows to expose where contributions concentrate.
# ---------------------------------------------------------------------------

def bone_head_in_body_local(name):
    p_arm = rig.data.bones[name].head_local
    p_world = rig.matrix_world @ p_arm
    return body.matrix_world.inverted() @ p_world


def side_masks(side):
    anchor = np.array(bone_head_in_body_local(f"upperarm_{side}"), dtype=np.float64)
    P = rest - anchor
    dist = np.linalg.norm(P, axis=1)
    # Character forward is -Y in the production pose script.
    forward = -P[:, 1]
    below = P[:, 2] <= 0.05
    not_too_low = P[:, 2] >= -0.24
    near = dist <= 0.30
    tighter = dist <= 0.22

    x0 = anchor[0]
    if x0 < 0:
        side_half = rest[:, 0] <= 0.02
        medial = rest[:, 0] >= x0 - 0.02
    else:
        side_half = rest[:, 0] >= -0.02
        medial = rest[:, 0] <= x0 + 0.02

    torso_or_shoulder = np.isin(region_label, ["torso", "shoulder"])
    shoulderish = np.isin(region_label, ["torso", "shoulder", "arm", "upperarm"])

    return {
        f"{side}_shoulder_neighborhood": near & side_half & shoulderish,
        f"{side}_axilla_neighborhood": tighter & side_half & below & not_too_low & shoulderish,
        f"{side}_anterior_axilla": tighter & side_half & below & not_too_low & (forward >= -0.015) & shoulderish,
        f"{side}_posterior_axilla": tighter & side_half & below & not_too_low & (forward <= 0.015) & shoulderish,
        f"{side}_lateral_chest_root": near & side_half & medial & below & not_too_low & torso_or_shoulder,
    }


zones = {}
for name in sorted(set(region_label.tolist())):
    zones[f"region:{name}"] = region_label == name
zones.update(side_masks("l"))
zones.update(side_masks("r"))
zones["torso_or_shoulder"] = np.isin(region_label, ["torso", "shoulder"])
zones = {k: v for k, v in zones.items() if bool(np.any(v))}


def zone_stats(values, mask):
    a = np.asarray(values)[mask]
    if a.size == 0:
        return {"count": 0}
    return {
        "count": int(a.size),
        "mean_m": round(float(np.mean(a)), 6),
        "p95_m": round(float(np.percentile(a, 95)), 6),
        "max_m": round(float(np.max(a)), 6),
        "n_over_5mm": int(np.sum(a > 0.005)),
        "n_over_10mm": int(np.sum(a > 0.010)),
        "n_over_20mm": int(np.sum(a > 0.020)),
    }


def static_weight_summary(mask):
    ids = np.flatnonzero(mask)
    if not len(ids):
        return {"count": 0}
    side_bones = [
        n for n in bone_names
        if any(tok in n for tok in ("spine_", "clavicle_", "scapula_", "upperarm_", "forearm_"))
    ]
    means = {n: float(np.mean(W[ids, bidx[n]])) for n in side_bones}
    means = {k: round(v, 6) for k, v in means.items() if v > 1e-5}
    top = sorted(means.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
    return {
        "count": int(len(ids)),
        "mean_total_trunk_weight": round(float(np.mean(W[ids][:, TRUNK_IDX].sum(axis=1))), 6),
        "top_mean_bone_weights": [{"bone": k, "mean_weight": v} for k, v in top],
    }


static_zones = {name: static_weight_summary(mask) for name, mask in zones.items()}


def current_key_values():
    if shape_keys is None:
        return {}
    return {
        kb.name: float(kb.value)
        for kb in shape_keys
        if kb.name != "Basis"
    }


def pre_skin_from_values(values):
    P = rest.copy()
    for name, value in values.items():
        if abs(value) > 1e-12 and name in key_delta:
            P += float(value) * key_delta[name]
    return P


def shoulder_elevation(side):
    h = (pb(f"upperarm_{side}").tail - pb(f"upperarm_{side}").head).normalized()
    down = -(pb("spine_03").tail - pb("spine_03").head).normalized()
    return math.degrees(h.angle(down))


def swing_twist(q):
    v = Vector((q.x, q.y, q.z))
    proj = Vector((0, 1, 0)) * v.dot(Vector((0, 1, 0)))
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        tw = Quaternion((1, 0, 0, 0))
    tw.normalize()
    return q @ tw.inverted(), tw


def apply_fraction(final, f):
    for p in rig.pose.bones:
        q, t = final[p.name]
        sw, tw = swing_twist(q)
        angle = (2.0 * math.atan2(tw.y, tw.w) + math.pi) % (2.0 * math.pi) - math.pi
        qf = Quaternion((1, 0, 0, 0)).slerp(sw, f) @ Quaternion((0.0, 1.0, 0.0), f * angle)
        p.matrix_basis = Matrix.Translation(t * f) @ qf.to_matrix().to_4x4()
    upd()


def top_vertices(disp, limit=20):
    ids = np.argsort(disp)[-limit:][::-1]
    rows = []
    for vid in ids:
        member = [name for name, mask in zones.items() if mask[vid] and not name.startswith("region:")]
        rows.append({
            "vertex_id": int(vid),
            "region": str(region_label[vid]),
            "rest_xyz_m": [round(float(x), 6) for x in rest[vid]],
            "displacement_m": round(float(disp[vid]), 6),
            "zones": member,
        })
    return rows


result = {
    "schema_version": 1,
    "status": "READ_ONLY_SHOULDER_LAYER_DIAGNOSTIC",
    "candidate": candidate_path.name,
    "candidate_sha256": candidate_sha,
    "pose_definition_script": POSE_SCRIPT.name,
    "pose_definition_script_sha256": hashlib.sha256(POSE_SCRIPT.read_bytes()).hexdigest(),
    "flexion_driver_script_sha256": hashlib.sha256(_fd_path.read_bytes()).hexdigest(),
    "samples_per_pose": NS,
    "poses_requested": POSE_LIST,
    "corrective_families": families,
    "scene_configs": {
        "abduction": cfg_abd,
        "flexion": cfg_flex,
        "scapular": cfg_scap,
    },
    "zone_contract": {
        "note": "hgpt_region masks plus deterministic rest-space shoulder/axilla neighbourhood heuristics; diagnostic only, not anatomy acceptance.",
        "zone_vertex_counts": {name: int(mask.sum()) for name, mask in zones.items()},
        "static_weight_ownership": static_zones,
    },
    "poses": {},
    "source_saved_or_modified": False,
}

for pose_name in POSE_LIST:
    if pose_name not in POSES:
        raise SystemExit(f"unknown pose {pose_name}")
    reset()
    rig.location = (0, 0, 0)
    if "HANDLE" in ns:
        ns["HANDLE"].clear()
    POSES[pose_name]()
    upd()
    final = {
        p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation())
        for p in rig.pose.bones
    }

    rows = []
    for k in range(NS):
        fraction = k / (NS - 1)
        apply_fraction(final, fraction)
        # upd() above sets production-path key values for this exact pose sample.
        values_all = current_key_values()
        matrices = skin_matrices()

        weights_only = transform_vertices(rest, matrices, W)
        trunk_proxy = transform_vertices(rest, matrices, Wt)
        weights_drift = np.linalg.norm(weights_only - trunk_proxy, axis=1)

        family_positions = {}
        family_disp = {}
        for family, names in families.items():
            vals = {name: values_all.get(name, 0.0) for name in names}
            P = transform_vertices(pre_skin_from_values(vals), matrices, W)
            family_positions[family] = P
            family_disp[family] = np.linalg.norm(P - weights_only, axis=1)

        shoulder_vals = {name: values_all.get(name, 0.0) for name in family_key_set}
        shoulder_combined = transform_vertices(pre_skin_from_values(shoulder_vals), matrices, W)

        all_active = transform_vertices(pre_skin_from_values(values_all), matrices, W)
        combined_disp = np.linalg.norm(shoulder_combined - weights_only, axis=1)
        all_disp = np.linalg.norm(all_active - weights_only, axis=1)

        # The shape-key + skinning path is linear at a fixed pose. A large
        # residual here means our decomposition missed a key/family.
        summed = weights_only.copy()
        for family, P in family_positions.items():
            summed += P - weights_only
        linear_residual = float(np.max(np.linalg.norm(shoulder_combined - summed, axis=1)))

        zone_row = {}
        for zone_name, zone_mask in zones.items():
            item = {
                "weights_vs_trunk_proxy": zone_stats(weights_drift, zone_mask),
                "shoulder_combined_vs_weights": zone_stats(combined_disp, zone_mask),
                "all_active_shapes_vs_weights": zone_stats(all_disp, zone_mask),
            }
            for family in families:
                item[f"{family}_vs_weights"] = zone_stats(family_disp[family], zone_mask)
            zone_row[zone_name] = item

        family_top = {
            family: top_vertices(disp, 20)
            for family, disp in family_disp.items()
        }

        rows.append({
            "fraction": round(float(fraction), 6),
            "elevation_l_deg": round(float(shoulder_elevation("l")), 3),
            "elevation_r_deg": round(float(shoulder_elevation("r")), 3),
            "shape_key_values": {k: round(float(v), 8) for k, v in sorted(values_all.items())},
            "family_activation": {
                family: {name: round(float(values_all.get(name, 0.0)), 8) for name in names}
                for family, names in families.items()
            },
            "linear_decomposition_residual_max_m": round(linear_residual, 10),
            "zones": zone_row,
            "top_vertices_by_corrective_family": family_top,
            "top_vertices_weights_vs_trunk_proxy": top_vertices(weights_drift, 20),
        })

    result["poses"][pose_name] = rows
    print(
        "SHOULDER LAYER DIAGNOSTIC",
        pose_name,
        "samples", len(rows),
        "max combined correction %.4f m" % max(
            row["zones"].get("torso_or_shoulder", {})
               .get("shoulder_combined_vs_weights", {})
               .get("max_m", 0.0)
            for row in rows
        ),
    )

reset()
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    raise SystemExit(f"Refusing to overwrite {OUT}")
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("READ-ONLY SHOULDER LAYER DIAGNOSTIC WRITTEN", OUT)
