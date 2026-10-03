"""Read-only post-edit audit of the declared ORIGINAL-v1 axilla-pit repair region.

Run through RUN_ORIGINAL_V1_AXILLA_PIT_VALIDATE.bat. This script never saves the Blend.
It samples the same elevated-arm arcs as the pre-edit declaration and measures only the
mirror-closed declared triangles against the same-pose uncorrected LBS surface.
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
if len(argv) < 3:
    raise SystemExit("Usage: ... -- <declaration.json> <out.json> <out.md> [samples=17]")

DECL = Path(argv[0]).resolve()
OUT_JSON = Path(argv[1]).resolve()
OUT_MD = Path(argv[2]).resolve()
NS = int(argv[3]) if len(argv) > 3 else 17
if NS < 3:
    raise SystemExit("samples must be >= 3")
for p in (OUT_JSON, OUT_MD):
    if p.exists():
        raise SystemExit(f"refusing to overwrite {p}")

decl = json.loads(DECL.read_text(encoding="utf-8"))
if decl.get("schema_version") != 1 or not decl.get("declared_before_edit"):
    raise SystemExit("invalid/non-pre-edit declaration")
face_ids = [int(x) for x in decl.get("mirror_closed_triangle_ids", [])]
if not face_ids:
    raise SystemExit("declaration has no mirror-closed triangle ids")
params = decl.get("diagnostic_parameters", {})
AREA_MIN = float(params.get("area_min", 0.20))
SIGNED_MIN = float(params.get("signed_min", 0.20))

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

candidate_path = Path(bpy.data.filepath)
if not candidate_path.is_file():
    raise SystemExit("candidate Blend has no saved source path")
candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
manifest_path = candidate_path.with_suffix(".json")
if not manifest_path.is_file():
    raise SystemExit("candidate manifest missing")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("candidate_sha256") != candidate_sha:
    raise SystemExit("candidate manifest SHA mismatch")
if manifest.get("source_sha256") != decl.get("source_candidate_sha256"):
    raise SystemExit("candidate parent differs from declaration source")
if manifest.get("topology_changed") is not False:
    raise SystemExit("local axilla candidate unexpectedly changed topology")

rest = np.array([v.co[:] for v in body.data.vertices], dtype=float)
nV = len(rest)
tris = []
for poly in body.data.polygons:
    vs = list(poly.vertices)
    for i in range(1, len(vs) - 1):
        tris.append((vs[0], vs[i], vs[i + 1]))
tris = np.asarray(tris, dtype=int)
if min(face_ids) < 0 or max(face_ids) >= len(tris):
    raise SystemExit("declared triangle id outside candidate topology")
TSEL = tris[np.asarray(face_ids, dtype=int)]

deform = [b.name for b in rig.data.bones if b.use_deform]
bidx = {n: i for i, n in enumerate(deform)}
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((nV, len(deform)), dtype=float)
for v in body.data.vertices:
    for g in v.groups:
        name = gname[g.group]
        if name in bidx:
            W[v.index, bidx[name]] = g.weight
W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-12)
rest_h = np.c_[rest, np.ones(nV)]

ARC_POSES = ("press_bottom", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "pullup_top")

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

def evaluate_pair():
    rw = np.array(rig.matrix_world)
    bw = np.array(body.matrix_world)
    mats = np.stack([
        rw @ np.array(rig.pose.bones[n].matrix) @ np.linalg.inv(np.array(rig.data.bones[n].matrix_local))
        @ np.linalg.inv(rw) @ bw
        for n in deform
    ])
    T = np.einsum("bij,vj->vbi", mats[:, :3, :], rest_h)
    uncorrected = np.einsum("vb,vbi->vi", W, T)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    candidate = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices], dtype=float)
    return candidate, uncorrected

agg = [{
    "min_signed": float("inf"),
    "min_area": float("inf"),
    "min_cos": float("inf"),
    "worst_pose": None,
    "worst_fraction": None,
} for _ in face_ids]
samples = []

for pose_name in ARC_POSES:
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
        A0, B0, C0 = p0[TSEL[:, 0]], p0[TSEL[:, 1]], p0[TSEL[:, 2]]
        A, B, C = pc[TSEL[:, 0]], pc[TSEL[:, 1]], pc[TSEL[:, 2]]
        n0 = np.cross(B0 - A0, C0 - A0)
        n = np.cross(B - A, C - A)
        len0 = np.maximum(np.linalg.norm(n0, axis=1), 1e-12)
        lenn = np.maximum(np.linalg.norm(n, axis=1), 1e-12)
        dot = (n * n0).sum(axis=1)
        area = lenn / len0
        cosine = dot / (lenn * len0)
        signed = dot / (len0 * len0)
        for j in range(len(face_ids)):
            row = agg[j]
            if float(signed[j]) < row["min_signed"]:
                row["min_signed"] = float(signed[j])
                row["worst_pose"] = pose_name
                row["worst_fraction"] = float(fraction)
            row["min_area"] = min(row["min_area"], float(area[j]))
            row["min_cos"] = min(row["min_cos"], float(cosine[j]))
        samples.append({
            "pose": pose_name,
            "fraction": round(fraction, 4),
            "elevation_l_deg": round(elevation("l"), 3),
            "elevation_r_deg": round(elevation("r"), 3),
            "min_signed_projected_area_ratio": round(float(signed.min()), 6),
            "min_area_ratio": round(float(area.min()), 6),
            "min_orientation_cosine": round(float(cosine.min()), 6),
            "faces_below_signed_min": int((signed < SIGNED_MIN).sum()),
            "faces_below_area_min": int((area < AREA_MIN).sum()),
            "flipped_faces": int((signed < 0.0).sum()),
        })

worst = sorted(range(len(face_ids)), key=lambda j: (agg[j]["min_signed"], agg[j]["min_area"], face_ids[j]))
worst_rows = [{
    "rank": rank,
    "triangle_index": int(face_ids[j]),
    "vertices": [int(v) for v in TSEL[j]],
    "min_signed_projected_area_ratio": round(float(agg[j]["min_signed"]), 6),
    "min_area_ratio": round(float(agg[j]["min_area"]), 6),
    "min_orientation_cosine": round(float(agg[j]["min_cos"]), 6),
    "worst_pose": agg[j]["worst_pose"],
    "worst_fraction": round(float(agg[j]["worst_fraction"]), 4),
} for rank, j in enumerate(worst, 1)]

global_min_signed = min(x["min_signed"] for x in agg)
global_min_area = min(x["min_area"] for x in agg)
global_min_cos = min(x["min_cos"] for x in agg)
max_flipped = max(x["flipped_faces"] for x in samples)
max_below_signed = max(x["faces_below_signed_min"] for x in samples)
max_below_area = max(x["faces_below_area_min"] for x in samples)
numeric_clear = max_flipped == 0 and max_below_signed == 0 and max_below_area == 0

result = {
    "schema_version": 1,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": candidate_path.name,
    "candidate_sha256": candidate_sha,
    "parent_candidate_sha256": manifest.get("source_sha256"),
    "declaration": str(DECL),
    "declaration_sha256": hashlib.sha256(DECL.read_bytes()).hexdigest(),
    "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
    "samples_per_pose": NS,
    "poses": list(ARC_POSES),
    "declared_triangle_count": len(face_ids),
    "thresholds": {"signed_min": SIGNED_MIN, "area_min": AREA_MIN},
    "summary": {
        "status": "LOCAL_FACE_NUMERIC_CLEAR" if numeric_clear else "LOCAL_FACE_REVIEW_REQUIRED",
        "min_signed_projected_area_ratio": round(global_min_signed, 6),
        "min_area_ratio": round(global_min_area, 6),
        "min_orientation_cosine": round(global_min_cos, 6),
        "max_flipped_faces_per_sample": max_flipped,
        "max_faces_below_signed_min_per_sample": max_below_signed,
        "max_faces_below_area_min_per_sample": max_below_area,
    },
    "sample_summary": samples,
    "worst_declared_faces": worst_rows[:40],
    "production_approved": False,
    "note": "Local numeric evidence only; visual review and full deformation comparators remain separate.",
}

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
md = [
    "# ORIGINAL v1 axilla-pit post-edit audit", "",
    f"- Candidate: `{candidate_path.name}`",
    f"- Candidate SHA-256: `{candidate_sha}`",
    f"- Declared triangles: {len(face_ids)}",
    f"- Status: **{result['summary']['status']}**",
    f"- Minimum signed projected area ratio: **{result['summary']['min_signed_projected_area_ratio']}**",
    f"- Minimum absolute area ratio: **{result['summary']['min_area_ratio']}**",
    f"- Maximum flipped faces in any sample: **{max_flipped}**",
    "",
    "This is local numeric evidence only. It does not replace full deformation evidence or real-render review.",
    "",
    "## Worst declared faces", "",
    "| Rank | Face | Signed area | Area ratio | Cosine | Pose | Fraction |",
    "|---:|---:|---:|---:|---:|---|---:|",
]
for row in worst_rows[:24]:
    md.append("| {rank} | {triangle_index} | {min_signed_projected_area_ratio:.4f} | {min_area_ratio:.4f} | {min_orientation_cosine:.4f} | {worst_pose} | {worst_fraction:.4f} |".format(**row))
OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
reset()
print("AXILLA POST AUDIT", result["summary"]["status"], OUT_JSON)
