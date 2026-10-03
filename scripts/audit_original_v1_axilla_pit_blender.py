"""Read-only ORIGINAL-v1 axilla-pit face-collapse audit and pre-edit mask declaration.

Run only through RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat unless reproducing evidence manually.

This script NEVER saves the .blend. It samples the six elevated-arm stress poses through
their full motion arcs, compares the candidate's evaluated surface (including corrective
shape keys) with the same candidate's uncorrected LBS surface at the same skeletal pose,
and detects:
  * signed projected face-area collapse;
  * absolute area collapse;
  * face orientation reversal.

It then creates a deterministic, mirror-closed local repair mask from the worst evidence,
expanded by a configurable number of topological rings. The declaration is created before
any edit and permits only local shape-key/skin-weight changes; topology requires a separate
declaration.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 4:
    raise SystemExit(
        "Usage: ... -- <audit.json> <audit.md> <declaration.json> <target-rN> "
        "[samples=17] [seed_faces=12] [rings=1] [area_min=0.20] [signed_min=0.20] [radius=0.30]"
    )

OUT_JSON = Path(argv[0]).resolve()
OUT_MD = Path(argv[1]).resolve()
DECL_JSON = Path(argv[2]).resolve()
TARGET_REV = argv[3]
NS = int(argv[4]) if len(argv) > 4 else 17
SEED_FACE_COUNT = int(argv[5]) if len(argv) > 5 else 12
RINGS = int(argv[6]) if len(argv) > 6 else 1
AREA_MIN = float(argv[7]) if len(argv) > 7 else 0.20
SIGNED_MIN = float(argv[8]) if len(argv) > 8 else 0.20
RADIUS = float(argv[9]) if len(argv) > 9 else 0.30
if NS < 3 or SEED_FACE_COUNT < 1 or RINGS < 0 or not (0.0 < AREA_MIN <= 1.0) or not (0.0 < SIGNED_MIN <= 1.0):
    raise SystemExit("invalid audit parameters")

POSE_LIST = ("press_bottom", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "pullup_top")

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "pose_test_defs", "exec"), ns)
sys.argv = saved_argv

rig, body, POSES = ns["rig"], ns["body"], ns["POSES"]
reset, upd, pb = ns["reset"], ns["upd"], ns["pb"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False

source_path = Path(bpy.data.filepath)
if not source_path.is_file():
    raise SystemExit("candidate blend has no saved source path")
source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()

if "hgpt_region_names" not in bpy.context.scene or "hgpt_region" not in body.data.attributes:
    raise SystemExit("candidate is missing required region metadata")
region_names = json.loads(bpy.context.scene["hgpt_region_names"])
region = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
rest = np.array([v.co[:] for v in body.data.vertices], dtype=float)
nV = len(rest)

tris = []
for poly in body.data.polygons:
    vs = list(poly.vertices)
    for i in range(1, len(vs) - 1):
        tris.append((vs[0], vs[i], vs[i + 1]))
tris = np.asarray(tris, dtype=int)

bone_names = [b.name for b in rig.data.bones if b.use_deform]
bidx = {n: i for i, n in enumerate(bone_names)}
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((nV, len(bone_names)), dtype=float)
for v in body.data.vertices:
    for g in v.groups:
        name = gname[g.group]
        if name in bidx:
            W[v.index, bidx[name]] = g.weight
W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-12)

# Exact rest-space mirror map.
rest_key = {tuple(np.round(rest[i], 5)): i for i in range(nV)}
mirror = np.array([rest_key.get(tuple(np.round(rest[i] * [-1, 1, 1], 5)), -1) for i in range(nV)], dtype=int)
if (mirror < 0).any():
    raise SystemExit("mesh is not exactly mirror symmetric")

# Broad shoulder/axilla diagnostic zone. The final declaration is much smaller.
body_inv = body.matrix_world.inverted()
Hl = np.array((body_inv @ rig.matrix_world @ rig.data.bones["upperarm_l"].head_local)[:], dtype=float)
Hr = np.array((body_inv @ rig.matrix_world @ rig.data.bones["upperarm_r"].head_local)[:], dtype=float)
regs = np.isin(region, [region_names.index(n) for n in ("torso", "shoulder", "arm")])
near_joint = (np.linalg.norm(rest - Hl, axis=1) < RADIUS) | (np.linalg.norm(rest - Hr, axis=1) < RADIUS)
scap = np.zeros(nV, dtype=bool)
for name in ("scapula_l", "scapula_r"):
    if name in bidx:
        scap |= W[:, bidx[name]] > 0.01
zone_vertex = regs & (near_joint | scap)
zone_face_ids = np.nonzero(zone_vertex[tris].any(axis=1))[0]
if len(zone_face_ids) == 0:
    raise SystemExit("axilla diagnostic zone is empty")
ZTRI = tris[zone_face_ids]

rw = np.array(rig.matrix_world)
bw = np.array(body.matrix_world)
rw_inv = np.linalg.inv(rw)
REST_INV = {n: np.linalg.inv(np.array(rig.data.bones[n].matrix_local)) for n in bone_names}
rest_h = np.c_[rest, np.ones(nV)]

def skin_mats():
    upd()
    return np.stack([
        rw @ np.array(pb(n).matrix) @ REST_INV[n] @ rw_inv @ bw
        for n in bone_names
    ])

def evaluate_pair():
    mats = skin_mats()
    T0 = np.einsum("bij,vj->vbi", mats[:, :3, :], rest_h)
    p_uncorrected = np.einsum("vb,vbi->vi", W, T0)

    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    p_candidate = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices], dtype=float)
    if p_candidate.shape != p_uncorrected.shape:
        raise SystemExit("evaluated candidate vertex count changed")
    return p_candidate, p_uncorrected

def swing_twist(q):
    v = Vector((q.x, q.y, q.z))
    proj = Vector((0, 1, 0)) * v.dot(Vector((0, 1, 0)))
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        tw = Quaternion((1, 0, 0, 0))
    tw.normalize()
    return q @ tw.inverted(), tw

def apply_fraction(final, fraction):
    for pose_bone in rig.pose.bones:
        q, t = final[pose_bone.name]
        sw, tw = swing_twist(q)
        ang = (2.0 * math.atan2(tw.y, tw.w) + math.pi) % (2.0 * math.pi) - math.pi
        qf = Quaternion((1, 0, 0, 0)).slerp(sw, fraction) @ Quaternion((0.0, 1.0, 0.0), fraction * ang)
        pose_bone.matrix_basis = Matrix.Translation(t * fraction) @ qf.to_matrix().to_4x4()
    upd()

def elevation(side):
    h = (pb(f"upperarm_{side}").tail - pb(f"upperarm_{side}").head).normalized()
    down = -(pb("spine_03").tail - pb("spine_03").head).normalized()
    return math.degrees(h.angle(down))

def top_weights(vertex, count=4):
    row = W[vertex]
    order = np.argsort(-row)
    return [
        {"bone": bone_names[int(i)], "weight": round(float(row[int(i)]), 6)}
        for i in order[:count]
        if row[int(i)] > 1e-8
    ]

def v3(values):
    return [round(float(x), 6) for x in values]

# Aggregate the worst face-area state across every sampled arc position.
inf = float("inf")
agg = [{
    "min_signed": inf,
    "min_area": inf,
    "min_cos": inf,
    "worst_pose": None,
    "worst_fraction": None,
    "worst_elevation_l_deg": None,
    "worst_elevation_r_deg": None,
} for _ in range(len(zone_face_ids))]
sample_rows = []

for pose_name in POSE_LIST:
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[pose_name]()
    upd()
    final = {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}
    for k in range(NS):
        fraction = k / (NS - 1)
        apply_fraction(final, fraction)
        pc, p0 = evaluate_pair()

        A0, B0, C0 = p0[ZTRI[:, 0]], p0[ZTRI[:, 1]], p0[ZTRI[:, 2]]
        A, B, C = pc[ZTRI[:, 0]], pc[ZTRI[:, 1]], pc[ZTRI[:, 2]]
        n0 = np.cross(B0 - A0, C0 - A0)
        n = np.cross(B - A, C - A)
        len0 = np.maximum(np.linalg.norm(n0, axis=1), 1e-12)
        lenn = np.maximum(np.linalg.norm(n, axis=1), 1e-12)
        dot = (n * n0).sum(axis=1)
        area_ratio = lenn / len0
        cosine = dot / (lenn * len0)
        signed_ratio = dot / (len0 * len0)

        for j in range(len(zone_face_ids)):
            row = agg[j]
            if float(signed_ratio[j]) < row["min_signed"]:
                row["min_signed"] = float(signed_ratio[j])
                row["worst_pose"] = pose_name
                row["worst_fraction"] = float(fraction)
                row["worst_elevation_l_deg"] = elevation("l")
                row["worst_elevation_r_deg"] = elevation("r")
            row["min_area"] = min(row["min_area"], float(area_ratio[j]))
            row["min_cos"] = min(row["min_cos"], float(cosine[j]))

        sample_rows.append({
            "pose": pose_name,
            "fraction": round(fraction, 4),
            "elevation_l_deg": round(elevation("l"), 3),
            "elevation_r_deg": round(elevation("r"), 3),
            "min_signed_projected_area_ratio": round(float(signed_ratio.min()), 6),
            "min_area_ratio": round(float(area_ratio.min()), 6),
            "min_orientation_cosine": round(float(cosine.min()), 6),
            "faces_below_signed_min": int((signed_ratio < SIGNED_MIN).sum()),
            "faces_below_area_min": int((area_ratio < AREA_MIN).sum()),
            "flipped_faces": int((signed_ratio < 0.0).sum()),
        })

# Rank every diagnostic-zone triangle by its worst projected signed area.
ranked_local = sorted(range(len(zone_face_ids)), key=lambda j: (agg[j]["min_signed"], agg[j]["min_area"], int(zone_face_ids[j])))
flip_local = [j for j in ranked_local if agg[j]["min_signed"] < 0.0 or agg[j]["min_cos"] < 0.0]
seed_local = []
for j in flip_local + ranked_local[:SEED_FACE_COUNT]:
    if j not in seed_local:
        seed_local.append(j)
seed_face_ids = {int(zone_face_ids[j]) for j in seed_local}

# Expand only inside the broad shoulder/axilla zone, then mirror-close the face set.
zone_set = set(int(x) for x in zone_face_ids)
selected_faces = set(seed_face_ids)
for _ in range(RINGS):
    selected_vertices = set(int(v) for fi in selected_faces for v in tris[fi])
    selected_faces |= {
        int(fi) for fi in zone_face_ids
        if any(int(v) in selected_vertices for v in tris[int(fi)])
    }

face_lookup = {tuple(sorted(int(v) for v in tri)): i for i, tri in enumerate(tris)}
for fi in list(selected_faces):
    mirrored = tuple(sorted(int(mirror[int(v)]) for v in tris[fi]))
    mfi = face_lookup.get(mirrored)
    if mfi is None:
        raise SystemExit("unable to mirror selected triangle")
    selected_faces.add(int(mfi))

selected_vertices = sorted({int(v) for fi in selected_faces for v in tris[fi]})
left_owned_set = set()
for v in selected_vertices:
    if rest[v, 0] <= 1e-8:
        left_owned_set.add(v)
    else:
        left_owned_set.add(int(mirror[v]))
left_owned = sorted(left_owned_set)
right_owned = sorted(int(mirror[v]) for v in left_owned if rest[v, 0] < -1e-8)
mask_all = sorted(set(left_owned) | set(right_owned))
if not set(selected_vertices).issubset(mask_all):
    raise SystemExit("mirror-closed declaration failed to contain selected diagnostic vertices")

ranked_rows = []
for rank, j in enumerate(ranked_local[:max(40, SEED_FACE_COUNT)], 1):
    fi = int(zone_face_ids[j])
    tri = [int(v) for v in tris[fi]]
    centroid = rest[tri].mean(axis=0)
    ranked_rows.append({
        "rank": rank,
        "triangle_index": fi,
        "vertices": tri,
        "side": "left" if centroid[0] < -1e-6 else "right" if centroid[0] > 1e-6 else "midline",
        "regions": [region_names[int(region[v])] for v in tri],
        "rest_centroid_m": v3(centroid),
        "min_signed_projected_area_ratio": round(agg[j]["min_signed"], 6),
        "min_area_ratio": round(agg[j]["min_area"], 6),
        "min_orientation_cosine": round(agg[j]["min_cos"], 6),
        "worst_pose": agg[j]["worst_pose"],
        "worst_fraction": round(float(agg[j]["worst_fraction"]), 4),
        "worst_elevation_l_deg": round(float(agg[j]["worst_elevation_l_deg"]), 3),
        "worst_elevation_r_deg": round(float(agg[j]["worst_elevation_r_deg"]), 3),
        "weights": [top_weights(v) for v in tri],
    })

audit = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_candidate": source_path.name,
    "source_candidate_sha256": source_sha256,
    "target_revision": TARGET_REV,
    "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
    "purpose": "read-only axilla face-collapse diagnostic and deterministic pre-edit local mask selection",
    "parameters": {
        "poses": list(POSE_LIST),
        "samples_per_pose": NS,
        "seed_face_count": SEED_FACE_COUNT,
        "topological_rings": RINGS,
        "area_min": AREA_MIN,
        "signed_min": SIGNED_MIN,
        "diagnostic_radius_m": RADIUS,
    },
    "zone_face_count": int(len(zone_face_ids)),
    "sample_summary": sample_rows,
    "ranked_problem_faces": ranked_rows,
    "selection": {
        "seed_triangle_ids": sorted(seed_face_ids),
        "mirror_closed_triangle_ids": sorted(selected_faces),
        "selected_vertex_ids": selected_vertices,
        "left_owned_vertex_ids": left_owned,
        "right_owned_mirror_vertex_ids": right_owned,
        "mask_vertex_count_total": len(mask_all),
    },
    "production_approved": False,
}

if not left_owned:
    raise SystemExit("diagnostic produced an empty left-owned mask")
bbox = rest[mask_all]
ids_bytes = np.asarray(left_owned, dtype="<i8").tobytes()
declaration = {
    "schema_version": 1,
    "declared_utc": datetime.now(timezone.utc).isoformat(),
    "declared_before_edit": True,
    "target_revision": TARGET_REV,
    "source_candidate": source_path.name,
    "source_candidate_sha256": source_sha256,
    "selection_rule": (
        "mirror closure of all flipped diagnostic-zone faces plus the worst "
        f"{SEED_FACE_COUNT} faces by minimum signed projected area ratio across "
        f"{NS} samples of each elevated-arm stress pose, expanded {RINGS} topological ring(s)"
    ),
    "diagnostic_parameters": audit["parameters"],
    "seed_triangle_ids": sorted(seed_face_ids),
    "mirror_closed_triangle_ids": sorted(selected_faces),
    "left_owned_vertex_ids": left_owned,
    "mirror_of_strict_left_vertex_ids": right_owned,
    "vertex_count_total": len(mask_all),
    "ids_sha256": hashlib.sha256(ids_bytes).hexdigest(),
    "rest_bbox_min_m": v3(bbox.min(axis=0)),
    "rest_bbox_max_m": v3(bbox.max(axis=0)),
    "vertex_metadata": [
        {
            "vertex": int(v),
            "rest_position_m": v3(rest[v]),
            "region": region_names[int(region[v])],
            "top_weights": top_weights(v),
            "mirror_vertex": int(mirror[v]),
        }
        for v in left_owned
    ],
    "allowed_change": (
        "shoulder-corrective shape-key displacement and/or skin weights of the declared "
        "mirror-closed vertices only; no bone, bind, pose-definition, threshold, baseline, "
        "rest-geometry or topology change. Any topology edit requires a separate declaration."
    ),
    "production_approved": False,
}

for p in (OUT_JSON, OUT_MD, DECL_JSON):
    if p.exists():
        raise SystemExit(f"refusing to overwrite {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
DECL_JSON.write_text(json.dumps(declaration, indent=2) + "\n", encoding="utf-8")

md = [
    "# ORIGINAL v1 axilla-pit face-collapse audit",
    "",
    f"- Source: \`{source_path.name}\`",
    f"- Source SHA-256: \`{source_sha256}\`",
    f"- Target revision: \`{TARGET_REV}\`",
    f"- Samples: {NS} × {len(POSE_LIST)} elevated-arm poses",
    f"- Diagnostic-zone faces: {len(zone_face_ids)}",
    f"- Declared left-owned vertices: {len(left_owned)}",
    f"- Mirror-closed total vertices: {len(mask_all)}",
    f"- Selection: {len(seed_face_ids)} seed faces, {RINGS} ring(s), mirror-closed",
    "",
    "This is pre-edit evidence only. The blend was not saved or modified.",
    "",
    "## Worst faces",
    "",
    "| Rank | Face | Side | Signed area | Area ratio | Cosine | Worst pose | Fraction |",
    "|---:|---:|---|---:|---:|---:|---|---:|",
]
for row in ranked_rows[:24]:
    md.append(
        "| {rank} | {triangle_index} | {side} | {min_signed_projected_area_ratio:.4f} | "
        "{min_area_ratio:.4f} | {min_orientation_cosine:.4f} | {worst_pose} | {worst_fraction:.4f} |".format(**row)
    )
md += [
    "",
    "## Declaration",
    "",
    f"- File: \`{DECL_JSON.name}\`",
    f"- Left-owned ID hash: \`{declaration['ids_sha256']}\`",
    "- Allowed first attempt: local corrective/weight changes only.",
    "- Topology remains prohibited until separately declared.",
]
OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

reset()
print(
    "AXILLA PIT PREP",
    json.dumps({
        "source": source_path.name,
        "source_sha256": source_sha256,
        "target": TARGET_REV,
        "zone_faces": len(zone_face_ids),
        "seed_faces": len(seed_face_ids),
        "declared_left_vertices": len(left_owned),
        "declared_total_vertices": len(mask_all),
        "audit": str(OUT_JSON),
        "declaration": str(DECL_JSON),
    }),
)
