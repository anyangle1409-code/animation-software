"""E1: native -> glTF (GLB) -> native round-trip parity of the ORIGINAL_v1 67-joint body (Blender built-in exporter).

Checks the export-side facts the first-party engine contract relies on, without touching Lane G code:
  * one skinned body mesh, 67 skin joints, at most 4 influences, normalized weights, 6 morph targets (legacy shoulder
    correctives, all weight 0), 17,946 source vertices / 35,888 triangles;
  * bone hierarchy and names preserved through the round trip;
  * rest and posed vertex parity: identical world-space bone poses are applied to the native and the re-imported rig
    and every native vertex is compared with the nearest re-imported vertex of the same source position (the glTF
    importer may split vertices at attribute seams).
The GLB is written to a private temporary directory outside Git and deleted afterwards; only the JSON report is kept.
Run inside Blender with the a003 source blend open:
  blender --background ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --python scripts/verify_original_glb_roundtrip_blender.py -- --out report.json
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.kdtree import KDTree

BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG = "HGPT_CANONICAL_V4_ORIGINAL"
POSES = {
    "rest": {},
    "shoulder_abduction_90": {"upperarm_r": (0, 0, 90), "upperarm_l": (0, 0, -90)},
    "elbow_flexion_90": {"forearm_r": (90, 0, 0), "forearm_l": (90, 0, 0)},
    "squat_like": {"thigh_r": (-90, 0, 0), "thigh_l": (-90, 0, 0), "shin_r": (100, 0, 0), "shin_l": (100, 0, 0)},
    "trunk_flexion_30": {"spine_01": (30, 0, 0), "spine_02": (15, 0, 0)},
}


def evaluated(obj):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    V = [ev.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return V


def pose_native(rig, spec):
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for name, (x, y, z) in spec.items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ")
    bpy.context.view_layer.update()
    return {pb.name: rig.matrix_world @ pb.matrix for pb in rig.pose.bones}


def pose_imported(rig, world):
    """Apply native world-space bone matrices to the imported rig, parents first.  The importer may change bone
    orientations, so each bone keeps its own rest orientation offset: M_imp = W_native @ (R_native^-1 @ R_imp)."""
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    order = []
    def walk(b):
        order.append(b.name)
        for c in b.children:
            walk(c)
    for b in rig.data.bones:
        if b.parent is None:
            walk(b)
    for name in order:
        pb = rig.pose.bones[name]
        offset = NATIVE_REST[name].inverted() @ (rig.matrix_world @ rig.data.bones[name].matrix_local)
        pb.matrix = rig.matrix_world.inverted() @ (world[name] @ offset)
        bpy.context.view_layer.update()


NATIVE_REST = {}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else None
    body, rig = bpy.data.objects[BODY], bpy.data.objects[RIG]
    me = body.data
    report = {"source_blend": Path(bpy.data.filepath).name, "approved": False}
    groups = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    infl = [len([g for g in v.groups if g.weight > 0 and groups[g.group] in deform]) for v in me.vertices]
    sums = [sum(g.weight for g in v.groups if groups[g.group] in deform) for v in me.vertices]
    report["native"] = {
        "vertices": len(me.vertices), "triangles": sum(len(p.vertices) - 2 for p in me.polygons),
        "skin_joints": len(deform), "bones": len(rig.data.bones), "max_influences": max(infl),
        "weight_sum_range": [round(min(sums), 6), round(max(sums), 6)],
        "morph_targets": [kb.name for kb in me.shape_keys.key_blocks[1:]],
        "morph_weights": [kb.value for kb in me.shape_keys.key_blocks[1:]],
        "hierarchy": {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones},
    }
    for b in rig.data.bones:
        NATIVE_REST[b.name] = rig.matrix_world @ b.matrix_local
    native_posed, world_poses = {}, {}
    for name, spec in POSES.items():
        world_poses[name] = pose_native(rig, spec)
        native_posed[name] = evaluated(body)
    pose_native(rig, {})
    native_rest_mesh = [body.matrix_world @ v.co for v in me.vertices]

    with tempfile.TemporaryDirectory() as tmp:
        glb = Path(tmp) / "original_review_roundtrip.glb"
        bpy.ops.object.select_all(action="DESELECT")
        body.select_set(True); rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_skins=True,
                                  export_morph=True, export_apply=False, export_yup=True, export_animations=False)
        report["glb_bytes"] = glb.stat().st_size
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(glb))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    skinned = [o for o in meshes if any(m.type == "ARMATURE" for m in o.modifiers)]
    report["imported"] = {"meshes": [(o.name, len(o.data.vertices), bool(any(m.type == "ARMATURE" for m in o.modifiers)))
                                     for o in meshes], "armatures": len(arms)}
    if len(skinned) != 1 or len(arms) != 1:
        raise RuntimeError(f"expected one skinned mesh and one armature after import: {report['imported']}")
    imesh, irig = skinned[0], arms[0]
    im = imesh.data
    report["imported"].update({
        "vertices": len(im.vertices), "triangles": sum(len(p.vertices) - 2 for p in im.polygons),
        "skin_joints": len(irig.data.bones),
        "morph_targets": [kb.name for kb in im.shape_keys.key_blocks[1:]] if im.shape_keys else [],
        "hierarchy_preserved": {b.name: (b.parent.name if b.parent else None) for b in irig.data.bones}
                                 == report["native"]["hierarchy"],
    })
    # map imported vertices to native ones by rest position
    for pb in irig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    rest_imp = [imesh.matrix_world @ v.co for v in im.vertices]
    tree = KDTree(len(rest_imp))
    for i, p in enumerate(rest_imp):
        tree.insert(p, i)
    tree.balance()
    mapping, map_err = [], 0.0
    for p in native_rest_mesh:
        _, j, d = tree.find(p)
        mapping.append(j); map_err = max(map_err, d)
    report["rest_vertex_mapping_max_error_m"] = map_err
    parity = {}
    for name in POSES:
        pose_imported(irig, world_poses[name])
        Vi = evaluated(imesh)
        errs = [(Vi[mapping[i]] - p).length for i, p in enumerate(native_posed[name])]
        parity[name] = {"max_error_mm": round(max(errs) * 1000, 4), "mean_error_mm": round(sum(errs) / len(errs) * 1000, 5)}
    report["posed_parity"] = parity
    report["verdict"] = "PASS" if (map_err < 1e-5 and all(v["max_error_mm"] < 0.5 for v in parity.values())
                                   and report["imported"]["hierarchy_preserved"]) else "FAIL"
    text = json.dumps(report, indent=1)
    if out:
        out.write_text(text + "\n")
    print("ORIGINAL_GLB_ROUNDTRIP", json.dumps({k: report[k] for k in ("glb_bytes", "posed_parity", "verdict")}))
    print(json.dumps({k: v for k, v in report["imported"].items() if k != "hierarchy_preserved"}),
          "hierarchy_preserved", report["imported"]["hierarchy_preserved"])


if __name__ == "__main__":
    main()
