"""Bake recorded test frames and export a REVIEW-CANDIDATE GLB of the Body v2 candidate (not a production asset).

Called by movement_trajectory_test_blender.py (V2_TRAJ_BAKE_GLB=<path>) after every measurement is done, in the same
in-memory session (so the candidate's runtime additions - upper-arm twist bones, forearm reweight - are what gets
exported).  Nothing is saved to a .blend.

What the GLB holds
  * the deform rig only (export_def_bones) and the body mesh only: reference skeletons, rib / scapula / clavicle guide
    meshes, joint-marker empties and every other helper object are left out (use_selection on rig + body);
  * every shape key as a sparse morph target (positions; morph normals off to keep the size down);
  * one animation per movement: each recorded test frame's bone transforms AND the shape-key weights the candidate's
    drives computed for it.  The app does not need to run the drives to play these clips; a new exercise does (the
    drive rules are the candidate's runtime contract, documented separately).

Returns a report (also written next to the GLB as <name>.json): sha256, bytes, joints, morph targets, animations,
the source blend, and how many vertices had more than 4 bone influences (glTF / three.js play at most 4; the exporter
keeps the 4 largest and renormalises).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy


def _clear_drivers(idb):
    ad = idb.animation_data
    if ad:
        for d in list(ad.drivers):
            ad.drivers.remove(d)


def _influences(body, rig):
    deform = {b.name for b in rig.data.bones if b.use_deform}
    idx = {g.index for g in body.vertex_groups if g.name in deform}
    over = 0; worst = 0; lost = 0.0
    for v in body.data.vertices:
        ws = sorted((g.weight for g in v.groups if g.group in idx and g.weight > 1e-6), reverse=True)
        if len(ws) > 4:
            over += 1; worst = max(worst, len(ws)); lost = max(lost, sum(ws[4:]) / max(sum(ws), 1e-9))
    return {"vertices_over_4_influences": over, "max_influences": worst, "max_weight_share_dropped": round(lost, 4)}


def export(rig, body, bake, out: Path, fps=24, source=None, report=None):
    sc = bpy.context.scene
    key = body.data.shape_keys
    infl = _influences(body, rig)
    for idb in (rig, key, body):
        _clear_drivers(idb)
    for idb in (rig, key):
        ad = idb.animation_data_create()
        for tr in list(ad.nla_tracks):
            ad.nla_tracks.remove(tr)
        ad.action = None
    names = []
    for mv, frames in bake.items():
        ra = bpy.data.actions.new(mv); ka = bpy.data.actions.new(mv + "_morph")
        rig.animation_data.action = ra; key.animation_data.action = ka
        for f, (mats, vals) in enumerate(frames, start=1):
            for pb in rig.pose.bones:
                loc, rot, scl = mats[pb.name].decompose()
                pb.rotation_mode = "QUATERNION"; pb.location = loc; pb.rotation_quaternion = rot; pb.scale = scl
                for path in ("location", "rotation_quaternion", "scale"):
                    pb.keyframe_insert(path, frame=f, group=pb.name)
            for kb, v in zip(key.key_blocks, vals):
                if kb != key.reference_key:
                    kb.value = v; kb.keyframe_insert("value", frame=f)
        for idb, act in ((rig, ra), (key, ka)):
            tr = idb.animation_data.nla_tracks.new(); tr.name = mv; tr.strips.new(mv, 1, act)
            idb.animation_data.action = None
        names.append((mv, len(frames)))
    for kb in key.key_blocks[1:]:                                    # the rest pose carries no corrective
        kb.value = 0.0
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    sc.render.fps = fps; sc.frame_start = 1; sc.frame_end = max(n for _, n in names)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.hide_set(False); body.hide_set(False); rig.select_set(True); body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    mat = bpy.data.materials.new("HGPT_SKIN_REVIEW"); mat.diffuse_color = (0.80, 0.60, 0.48, 1.0)
    body.data.materials.clear(); body.data.materials.append(mat)
    out.parent.mkdir(parents=True, exist_ok=True)
    opts = dict(filepath=str(out), export_format="GLB", use_selection=True, export_animations=True,
                export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_frame_step=1,
                export_def_bones=True, export_rest_position_armature=True, export_anim_slide_to_zero=True,
                export_morph=True, export_morph_normal=False, export_morph_animation=True, export_try_sparse_sk=True,
                export_skins=True, export_all_influences=False, export_influence_nb=4, export_yup=True, export_apply=False,
                export_texcoords=True, export_normals=True, export_materials="EXPORT", export_cameras=False,
                export_lights=False, export_extras=False, export_optimize_animation_size=False)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bpy.ops.export_scene.gltf(**{k: v for k, v in opts.items() if k in valid})
    data = out.read_bytes()
    rep = {"glb": out.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "source_blend": str(source.name) if source else None,
           "source_blend_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest() if source else None,
           "status": "REVIEW CANDIDATE - not production approved; PT_MODEL_VERSION 1.0 unchanged",
           "joints": [b.name for b in rig.data.bones if b.use_deform],
           "morph_targets": [kb.name for kb in key.key_blocks[1:]],
           "animations": [{"name": mv, "frames": n, "fps": fps} for mv, n in names],
           "skin_influences": infl,
           "vertices": len(body.data.vertices), "polygons": len(body.data.polygons),
           "harness": {k: v for k, v in (report or {}).items() if k not in ("movements", "regions")}}
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    return {k: rep[k] for k in ("glb", "bytes", "sha256", "animations", "skin_influences")}
