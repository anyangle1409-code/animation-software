"""A1: does the ORIGINAL_v1 body skin contain the 206-bone anatomical skeleton? (measurement only)

Rule 2 of the master execution: mesh, muscle volume and weights conform to the skeleton.  This audit measures, on the
unchanged a003 audit blend (rest pose, legacy shape keys at 0), for every element of HGPT_ANATOMICAL_MASTER:

  * the 206 bones: SAMPLES points along each head->tail axis;
  * the 427 HGPT_JOINT_* joint-centre empties;
  * the LM_* landmarks (those named *_skin are skin landmarks and are reported separately);

its signed depth below the skin in mm (positive = inside).  Inside/outside is decided by ray parity on the closed,
manifold body mesh, voting over three axis directions (robust to a ray grazing an edge); the depth magnitude is the
BVH nearest-surface distance.  It also measures bilateral symmetry (left head vs x-mirrored right head) and stature.

Flags are measurements, not anatomical judgements: OUTSIDE (depth <= 0) means the skin does not contain that skeleton
point; SHALLOW (0 < depth < SHALLOW_MM) is listed for review only (a stick bone's axis is not its surface, and some bones
are subcutaneous).  Nothing here edits the skeleton, mesh or rig, and nothing is approved.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BODY = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
MASTER = "HGPT_ANATOMICAL_MASTER"
SAMPLES = 5
SHALLOW_MM = 3.0
RAY_DIRS = (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))


def body_tree():
    body = bpy.data.objects[BODY]
    if body.data.shape_keys:
        for kb in body.data.shape_keys.key_blocks[1:]:
            if kb.value != 0.0:
                raise RuntimeError(f"legacy shape key {kb.name} is not at 0")
    mw = body.matrix_world                      # base vertex coordinates = rest skin (Basis; legacy keys at 0)
    V = [mw @ v.co for v in body.data.vertices]
    F = [tuple(p.vertices) for p in body.data.polygons]
    edges = Counter()
    for f in F:
        for i in range(len(f)):
            edges[tuple(sorted((f[i], f[(i + 1) % len(f)])))] += 1
    if any(c != 2 for c in edges.values()):
        raise RuntimeError("body mesh is not closed and manifold; ray parity is undefined")
    return BVHTree.FromPolygons(V, F), V, F


def _crossings(tree, p, d):
    n, o = 0, p.copy()
    for _ in range(200):
        hit, _nrm, _idx, _dist = tree.ray_cast(o, d)
        if hit is None:
            return n
        n += 1
        o = hit + d * 1e-6
    raise RuntimeError("ray parity did not terminate")


def signed_depth_mm(tree, p):
    votes = sum(_crossings(tree, p, d) % 2 for d in RAY_DIRS)
    inside = votes >= 2
    loc, _n, _i, dist = tree.find_nearest(p)
    return (dist if inside else -dist) * 1000.0, votes in (0, 3)


def side_of(name):
    n = name.lower()
    return "left" if n.endswith(("_left", "_l")) or "_left_" in n else "right" if n.endswith(("_right", "_r")) or "_right_" in n else None


def mirror_name(name):
    for a, b in (("_left", "_right"), ("_right", "_left")):
        if a in name:
            return name.replace(a, b)
    return None


def run():
    tree, V, _F = body_tree()
    arm = bpy.data.objects[MASTER]
    mw = arm.matrix_world
    if any(not pb.matrix_basis.is_identity for pb in arm.pose.bones):
        raise RuntimeError("anatomical master is not at rest")
    bones, ambiguous = [], 0
    for b in arm.data.bones:
        h, t = mw @ b.head_local, mw @ b.tail_local
        depths = []
        for k in range(SAMPLES):
            d, clear = signed_depth_mm(tree, h.lerp(t, k / (SAMPLES - 1)))
            ambiguous += not clear
            depths.append(round(d, 2))
        bones.append({"bone": b.name, "anatomical_id": b.get("hgpt_anatomical_id"), "placement": b.get("hgpt_placement"),
                      "confidence": b.get("hgpt_confidence"), "length_mm": round((t - h).length * 1000, 1),
                      "depth_mm_samples": depths, "min_depth_mm": min(depths)})
    joints, landmarks = [], []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or o.parent is not arm:
            continue
        d, clear = signed_depth_mm(tree, o.matrix_world.translation)
        ambiguous += not clear
        row = {"name": o.name, "depth_mm": round(d, 2), "carrier_bone": o.get("hgpt_carrier_bone") or o.parent_bone}
        (joints if o.name.startswith("HGPT_JOINT_") else landmarks).append(row)

    heads = {b.name: mw @ b.head_local for b in arm.data.bones}
    sym = []
    for n, p in heads.items():
        m = mirror_name(n)
        if side_of(n) == "left" and m in heads:
            q = heads[m]
            sym.append({"pair": [n, m], "mirror_error_mm": round((p - Vector((-q.x, q.y, q.z))).length * 1000, 2)})
    zs = [v.z for v in V]
    skel_z = [p.z for b in arm.data.bones for p in (mw @ b.head_local, mw @ b.tail_local)]

    outside_bones = [b for b in bones if b["min_depth_mm"] <= 0]
    shallow_bones = [b for b in bones if 0 < b["min_depth_mm"] < SHALLOW_MM]
    outside_joints = [j for j in joints if j["depth_mm"] <= 0]
    skin_lm = [l for l in landmarks if l["name"].endswith("_skin")]
    bony_lm = [l for l in landmarks if not l["name"].endswith("_skin")]
    summary = {
        "bones": len(bones), "bones_outside_skin": len(outside_bones), "bones_shallow_lt_mm": len(shallow_bones),
        "joint_centres": len(joints), "joint_centres_outside_skin": len(outside_joints),
        "bony_landmarks": len(bony_lm), "bony_landmarks_outside_skin": sum(l["depth_mm"] <= 0 for l in bony_lm),
        "skin_landmarks": len(skin_lm), "skin_landmark_abs_depth_max_mm": round(max((abs(l["depth_mm"]) for l in skin_lm), default=0), 2),
        "ray_parity_votes_not_unanimous": ambiguous,
        "bilateral_pairs": len(sym), "bilateral_mirror_error_max_mm": max((s["mirror_error_mm"] for s in sym), default=None),
        "body_height_m": round(max(zs) - min(zs), 4), "skeleton_z_span_m": round(max(skel_z) - min(skel_z), 4),
        "shallow_mm_threshold": SHALLOW_MM,
    }
    return {"kind": "ORIGINAL_SKELETON_CONTAINMENT_AUDIT", "approved": False,
            "source_blend": bpy.data.filepath.rsplit("/", 1)[-1], "summary": summary,
            "outside_bones": outside_bones, "shallow_bones": shallow_bones, "outside_joints": outside_joints,
            "bony_landmarks": bony_lm, "skin_landmarks": skin_lm,
            "bilateral_worst": sorted(sym, key=lambda s: -s["mirror_error_mm"])[:10],
            "bones_all": bones}


COLOURS = {"outside": (0.85, 0.05, 0.05, 1.0), "shallow": (0.95, 0.65, 0.0, 1.0), "inside": (0.1, 0.35, 0.9, 1.0)}
VIEWS = {   # name: (target, camera offset, ortho scale); runtime/anatomical right side is -X (F-SIDE-001)
    "whole_body_front": ((0.0, 0.0, 0.91), (0.0, -5.0, 0.0), 2.0),
    "right_shank_lateral": ((-0.12, 0.0, 0.25), (-5.0, 0.0, 0.0), 0.62),
    "right_shank_front": ((-0.11, 0.0, 0.25), (0.0, -5.0, 0.0), 0.62),
    "right_thumb_front": ((-0.19, -0.01, 0.875), (0.0, -5.0, 0.0), 0.16),
}


def render(rep, out):
    """X-ray views: translucent skin with every bone axis drawn as a tube, coloured per sample segment."""
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    mats = {}
    for k, c in COLOURS.items():
        m = bpy.data.materials.new(f"HGPT_A1_{k}_TMP"); m.diffuse_color = c; mats[k] = m
    skin = bpy.data.materials.new("HGPT_A1_SKIN_TMP"); skin.diffuse_color = (0.64, 0.44, 0.36, 1.0)
    body.data.materials.clear(); body.data.materials.append(skin)
    arm = bpy.data.objects[MASTER]; mw = arm.matrix_world
    tubes = []
    for row in rep["bones_all"]:
        b = arm.data.bones[row["bone"]]
        h, t = mw @ b.head_local, mw @ b.tail_local
        d = row["depth_mm_samples"]
        for k in range(SAMPLES - 1):
            lo = min(d[k], d[k + 1])
            kind = "outside" if lo <= 0 else "shallow" if lo < SHALLOW_MM else "inside"
            cu = bpy.data.curves.new("HGPT_A1_TUBE_TMP", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0025
            sp = cu.splines.new("POLY"); sp.points.add(1)
            a, z = h.lerp(t, k / (SAMPLES - 1)), h.lerp(t, (k + 1) / (SAMPLES - 1))
            sp.points[0].co, sp.points[1].co = (*a, 1.0), (*z, 1.0)
            cu.materials.append(mats[kind])
            ob = bpy.data.objects.new("HGPT_A1_TUBE_TMP", cu); scene.collection.objects.link(ob); tubes.append(ob)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_xray, sh.xray_alpha = "STUDIO", "MATERIAL", True, 0.35
    scene.render.resolution_x, scene.render.resolution_y = 800, 1000
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_A1_CAM_TMP"); cd.type = "ORTHO"
    cam = bpy.data.objects.new("HGPT_A1_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    written = []
    for name, (target, offset, scale) in VIEWS.items():
        tgt = Vector(target)
        cam.location = tgt + Vector(offset); cd.ortho_scale = scale
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        written.append(f"{name}.png")
    for ob in tubes:
        bpy.data.objects.remove(ob)
    return written


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    rep = run()
    if "--renders" in args:
        rep["renders"] = render(rep, Path(args[args.index("--renders") + 1]))
    print("A1", json.dumps(rep["summary"]))
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=1) + "\n")
