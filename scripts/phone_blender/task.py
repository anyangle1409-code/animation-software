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
from mathutils import Vector
groups = {g.index: g.name for g in body.vertex_groups}
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
