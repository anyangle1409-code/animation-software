"""Phone/cloud Blender task. Initial task is read-only; never saves a blend."""
import hashlib,json,os,sys
from pathlib import Path
import bpy
MODEL=os.environ["MODEL"]
EXPECTED={"W8":"2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c","V14":"5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91","R120":"fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb"}
def sha(p):
 with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
files=list(Path(os.environ["INPUT_DIR"]).rglob("*.blend"))
assert len(files)==1,files
source=files[0]
assert sha(source)==EXPECTED[MODEL],"Source hash mismatch"
out=Path("phone-results")/MODEL
out.mkdir(parents=True,exist_ok=False)
bpy.context.preferences.filepaths.use_scripts_auto_execute=False
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
body=bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig=bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
m=body.data
m.calc_loop_triangles()
report={"model":MODEL,"source_sha256":sha(source),"blender":bpy.app.version_string,"saved_by":list(bpy.data.version),"vertices":len(m.vertices),"triangles":len(m.loop_triangles),"groups":len(body.vertex_groups),"shape_keys":len(m.shape_keys.key_blocks),"bones":len(rig.data.bones),"source_unchanged":sha(source)==EXPECTED[MODEL],"approved":False,"status":"READ_ONLY_CLOUD_SMOKE_TEST","known_v14_vertex_discrepancy":{"expected":238067,"actual":len(m.vertices)} if MODEL=="V14" else None,"run":os.environ.get("GITHUB_RUN_ID")}
assert report["source_unchanged"]
(out/"inventory.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))


# Supplemental numerical audit only. No operators modifying a mesh, rig or source.
# Coordinates and group names are evidence, NOT certified anatomical laterality.
acc = {
    g.index: {
        "name": g.name, "vertices": 0, "weight_mass": 0.0,
        "weighted_sum": [0.0, 0.0, 0.0],
        "x_negative": 0, "x_positive": 0, "x_midline": 0,
    } for g in body.vertex_groups
}
unweighted = 0
for vertex in m.vertices:
    x, y, z = (float(t) for t in vertex.co)
    valid = [(a.group, float(a.weight)) for a in vertex.groups if a.group in acc and a.weight > 0.0]
    if not valid:
        unweighted += 1
    for group_id, weight in valid:
        entry = acc[group_id]
        entry["vertices"] += 1
        entry["weight_mass"] += weight
        entry["weighted_sum"][0] += weight * x
        entry["weighted_sum"][1] += weight * y
        entry["weighted_sum"][2] += weight * z
        entry["x_negative" if x < -0.001 else "x_positive" if x > 0.001 else "x_midline"] += 1

group_rows = []
for group_id in sorted(acc):
    entry = acc[group_id]
    mass = entry["weight_mass"]
    group_rows.append({
        "index": group_id, "name": entry["name"],
        "vertices_with_influence": entry["vertices"],
        "weight_mass": round(mass, 5),
        "weighted_centroid_body_local_m": [round(t / mass, 6) for t in entry["weighted_sum"]] if mass else None,
        "vertex_x_sign_counts": {
            "negative": entry["x_negative"], "midline": entry["x_midline"], "positive": entry["x_positive"]
        },
    })
rig_to_body = body.matrix_world.inverted() @ rig.matrix_world
bone_rows = []
for bone in rig.data.bones:
    head = rig_to_body @ bone.head_local
    tail = rig_to_body @ bone.tail_local
    bone_rows.append({
        "name": bone.name, "parent": bone.parent.name if bone.parent else None,
        "head_body_local_m": [round(float(t), 6) for t in head],
        "tail_body_local_m": [round(float(t), 6) for t in tail],
        "use_deform": bool(bone.use_deform),
    })
coords_min = [min(float(v.co[i]) for v in m.vertices) for i in range(3)]
coords_max = [max(float(v.co[i]) for v in m.vertices) for i in range(3)]
bone_names = {b.name for b in rig.data.bones}
group_names = {g.name for g in body.vertex_groups}
audit = {
    "model": MODEL, "run": os.environ.get("GITHUB_RUN_ID"),
    "source_sha256": EXPECTED[MODEL],
    "coordinate_frame": "body-object local metres; bone head/tail transformed from rig rest space",
    "approval": "NOT_GRANTED",
    "limitations": [
        "Reconstructed model, not a recovered original",
        "Weight centroids and bone names do not verify anatomical side or attachments",
        "Static rest inspection; no movement, contact or intersection acceptance",
        "V14 two-vertex archive mismatch remains unresolved",
    ],
    "mesh": {
        "vertices": len(m.vertices),
        "bbox_min_body_local_m": [round(t, 6) for t in coords_min],
        "bbox_max_body_local_m": [round(t, 6) for t in coords_max],
        "unweighted_vertices": unweighted,
    },
    "rig": {"bone_count": len(bone_rows), "bones": bone_rows},
    "groups": group_rows,
    "naming_only": {
        "rig_bones_without_matching_group": sorted(bone_names - group_names),
        "groups_without_matching_bone": sorted(group_names - bone_names),
    },
}
assert sha(source) == EXPECTED[MODEL], "Source changed during rest audit"
(out / "rest_anatomy_inventory.json").write_text(json.dumps(audit, indent=2))
print("READ_ONLY_REST_AUDIT", MODEL, len(bone_rows), len(group_rows), "unweighted", unweighted)


# Fail closed on corrupt or inconsistent numerical report structures.
# These checks establish report integrity ONLY, never anatomical correctness.
import math
assert report["source_unchanged"] is True
assert audit["source_sha256"] == report["source_sha256"] == EXPECTED[MODEL]
assert audit["approval"] == "NOT_GRANTED" and report["approved"] is False
assert report["vertices"] == audit["mesh"]["vertices"] > 0
assert report["bones"] == audit["rig"]["bone_count"] == len(audit["rig"]["bones"])
assert report["groups"] == len(audit["groups"])
assert 0 <= audit["mesh"]["unweighted_vertices"] <= report["vertices"]
assert all(math.isfinite(t) for t in coords_min + coords_max)
assert all(lo <= hi for lo, hi in zip(coords_min, coords_max))
assert len({entry["name"] for entry in bone_rows}) == len(bone_rows)
assert len({entry["index"] for entry in group_rows}) == len(group_rows)
for b in bone_rows:
    assert b["parent"] is None or b["parent"] in bone_names, b
    assert all(math.isfinite(c) for c in b["head_body_local_m"] + b["tail_body_local_m"]), b
for g in group_rows:
    assert 0 <= g["vertices_with_influence"] <= report["vertices"], g
    assert math.isfinite(g["weight_mass"]) and g["weight_mass"] >= 0, g
    assert sum(g["vertex_x_sign_counts"].values()) == g["vertices_with_influence"], g
    if g["weight_mass"] > 0:
        assert g["weighted_centroid_body_local_m"] is not None, g
        assert all(math.isfinite(c) for c in g["weighted_centroid_body_local_m"]), g
assert sha(source) == EXPECTED[MODEL], "Read-only audit altered source"
(out / "integrity_checks.json").write_text(json.dumps({
    "model": MODEL, "source_sha256": EXPECTED[MODEL],
    "result": "PASS", "scope": "READ_ONLY_REPORT_INTEGRITY_NOT_ANATOMICAL_APPROVAL",
    "rig_bones": len(bone_rows), "groups": len(group_rows),
    "unweighted_vertices": unweighted, "approval": "NOT_GRANTED"
}, indent=2))
print("READ_ONLY_REST_AUDIT_VALIDATED", MODEL)


# W8 shoulder-press flagged REST-coordinate cells: static, source-preserving
# weight-group and stored shape-key inventory. No deformation operator called.
from rest_roi_audit import analyze as inspect_rest_roi
roi = inspect_rest_roi(body)
roi["model"] = MODEL
roi["source_sha256"] = EXPECTED[MODEL]
roi["original_source_unchanged"] = (sha(source) == EXPECTED[MODEL])
assert roi["original_source_unchanged"], "Shoulder ROI inspection changed model input"
assert roi["shape_key_count"] == report["shape_keys"]
assert roi["vertex_group_count"] == report["groups"]
assert roi["mesh_vertices"] == report["vertices"]
assert roi["status"] == "READ_ONLY_REST_MESH_PROBE_NOT_ANATOMICAL_APPROVAL"
(out / "shoulder_shape_weight_rois.json").write_text(json.dumps(roi, indent=2) + "\n")
print("READ_ONLY_SHOULDER_SHAPE_WEIGHT_ROIS", MODEL,
      [(entry["name"], entry["sampled_vertices"]) for entry in roi["regions"]])


# Pinned-source mathematical SHOULDER CORRECTIVE CONTRACT (metadata only).
# No joint pose is set and no corrective key value is changed.
from shoulder_activation_contract import inspect as inspect_activation_rules
activation_rules = inspect_activation_rules(rig, body)
activation_rules["model"] = MODEL
activation_rules["source_sha256"] = EXPECTED[MODEL]
activation_rules["original_source_unchanged"] = sha(source) == EXPECTED[MODEL]
assert activation_rules["original_source_unchanged"], "Shape-key contract inspection changed input model"
assert activation_rules["shape_key_count"] == report["shape_keys"]
assert activation_rules["status"] == "READ_ONLY_ANGULAR_ACTIVATION_CONTRACT_NOT_APPLIED_TO_POSE"
(out / "shoulder_activation_rules.json").write_text(json.dumps(activation_rules, indent=2) + "\n")
print("READ_ONLY_SHOULDER_ACTIVATION_CONTRACT", MODEL,
      [(row["family"], row["side_suffix"], row["safe_to_evaluate_rule"], row["warnings"])
       for row in activation_rules["family_records"] if row["keys"]])


# Source-preserving native rest-axis inventory for later HUMAN joint-coordinate
# calibration. These are Blender bone-local axes ONLY; ISB mapping remains NULL.
from rig_axes_inventory import inspect as inspect_rig_axes, validate as validate_rig_axes
rest_axes = inspect_rig_axes(rig, body)
rest_axes["model"] = MODEL
rest_axes["source_sha256"] = EXPECTED[MODEL]
rest_axes["original_source_unchanged"] = sha(source) == EXPECTED[MODEL]
assert rest_axes["original_source_unchanged"], "Rig axis inspection changed preserved input source"
assert rest_axes["bone_count"] == report["bones"], "Bone count changed during read-only axis inspection"
axis_errors = validate_rig_axes(rest_axes)
assert not axis_errors, "Unusable bone-local rest matrix inventory: " + "; ".join(axis_errors)
assert rest_axes["model_motion_axes_calibrated_to_ISB"] is False
assert rest_axes["native_human_ROM_limits_validated"] is False
(out / "rig_rest_axes_metadata.json").write_text(json.dumps(rest_axes, indent=2) + "\n")
print("READ_ONLY_RIG_LOCAL_AXES", MODEL, rest_axes["bone_count"], "BONES; ANATOMY_NOT_APPROVED")
