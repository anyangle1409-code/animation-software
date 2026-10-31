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
the source blend, and how many vertices had more than 8 bone influences (exported as two joint sets, JOINTS_0/1 and
WEIGHTS_0/1; the exporter keeps the 8 largest and renormalises).  Engines must play 8 influences: Babylon.js does
natively, three.js with the shader patch in glb_playback/page.html.
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


INFLUENCES = 8   # two glTF joint sets: the top-8 cut stays within 0.38 mm of the full binding (only 519 vertices use
                 # 9-10); 4 (one set, stock three.js) breaks the press lockout - see docs/CLAUDE_APP_READY_LEDGER_20261031.md


def _influences(body, rig, limit=INFLUENCES):
    deform = {b.name for b in rig.data.bones if b.use_deform}
    idx = {g.index for g in body.vertex_groups if g.name in deform}
    over = 0; worst = 0; lost = 0.0
    for v in body.data.vertices:
        ws = sorted((g.weight for g in v.groups if g.group in idx and g.weight > 1e-6), reverse=True)
        worst = max(worst, len(ws))
        if len(ws) > limit:
            over += 1; lost = max(lost, sum(ws[limit:]) / max(sum(ws), 1e-9))
    return {"influences_exported": limit, f"vertices_over_{limit}_influences": over, "max_influences": worst,
            "max_weight_share_dropped": round(lost, 4)}


def share_sparse_base(path: Path):
    """Give every sparse accessor that has no bufferView (glTF 2.0: then its base is all zeros) ONE shared zero-filled
    bufferView as its base.  Still valid glTF and the same data, for intake checks that require a bufferView on every
    accessor (PT-App's check-glb-preview.mjs); dense morph targets would be ~590 MB, this adds one base (~4 MB)."""
    import struct
    b = path.read_bytes()
    jl = struct.unpack("<I", b[12:16])[0]; g = json.loads(b[20:20 + jl])
    bl = struct.unpack("<I", b[20 + jl:24 + jl])[0]; bin_ = bytearray(b[28 + jl:28 + jl + bl])
    sizes = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}; comp = {5126: 4, 5125: 4, 5123: 2, 5121: 1, 5122: 2, 5120: 1}
    todo = [a for a in g["accessors"] if "sparse" in a and "bufferView" not in a]
    if not todo:
        return 0
    need = max(a["count"] * sizes[a["type"]] * comp[a["componentType"]] for a in todo)
    off = len(bin_) + (-len(bin_)) % 4
    bin_ += b"\0" * (off - len(bin_) + need)
    g["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": need}); vi = len(g["bufferViews"]) - 1
    for a in todo:
        a["bufferView"] = vi
    bin_ += b"\0" * ((-len(bin_)) % 4); g["buffers"][0]["byteLength"] = len(bin_)
    js = json.dumps(g, separators=(",", ":")).encode(); js += b" " * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<II", len(js), 0x4E4F534A) + js
                     + struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_))
    return len(todo)


def export(rig, body, bake, out: Path, fps=24, source=None, report=None, lod_ratio=None, lod_tol_mm=0.05):
    sc = bpy.context.scene
    infl = _influences(body, rig)
    for idb in (rig, body.data.shape_keys, body):
        _clear_drivers(idb)
    lod_rep = None
    if lod_ratio:                                   # app LOD: decimated mesh, top-8 weights, clip-morph components
        import app_lod
        lo, comp_w, lod_rep = app_lod.build(rig, body, bake, ratio=lod_ratio, tol_mm=lod_tol_mm)
        bake = {mv: [(mats, [0.0] + comp_w[mv][f]) for f, (mats, _) in enumerate(frames)] for mv, frames in bake.items()}
        body.hide_set(True); body.hide_render = True; body = lo
    key = body.data.shape_keys
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
                export_morph=True, export_morph_normal=False, export_morph_animation=True,
                export_try_sparse_sk=not lod_ratio, export_try_omit_sparse_sk=False,
                export_skins=True, export_all_influences=False, export_influence_nb=INFLUENCES, export_yup=True, export_apply=False,
                export_texcoords=True, export_normals=True, export_materials="EXPORT", export_cameras=False,
                export_lights=False, export_extras=False, export_optimize_animation_size=False)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bpy.ops.export_scene.gltf(**{k: v for k, v in opts.items() if k in valid})
    shared = 0 if lod_ratio else share_sparse_base(out)
    data = out.read_bytes()
    rep = {"glb": out.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "source_blend": str(source.name) if source else None,
           "source_blend_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest() if source else None,
           "status": "REVIEW CANDIDATE - not production approved; PT_MODEL_VERSION 1.0 unchanged",
           "joints": [b.name for b in rig.data.bones if b.use_deform],
           "morph_targets": [kb.name for kb in key.key_blocks[1:]],
           "animations": [{"name": mv, "frames": n, "fps": fps} for mv, n in names],
           "skin_influences": infl, "sparse_morphs_given_shared_zero_base": shared, "app_lod": lod_rep,
           "vertices": len(body.data.vertices), "polygons": len(body.data.polygons),
           "harness": {k: v for k, v in (report or {}).items() if k not in ("movements", "regions")}}
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    return {k: rep[k] for k in ("glb", "bytes", "sha256", "animations", "skin_influences", "app_lod")}
