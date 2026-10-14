#!/usr/bin/env python3
"""See-through renders of an ORIGINAL_v1 pose: translucent skin with the skeleton that drives it (bpy, EEVEE).

Drawn: every deforming bone of the 67-joint runtime rig (the bones the skin is weighted to) as a solid bone shape coloured
by region, a sphere at each joint, the rib / sternum / clavicle / scapula guide meshes, the arm pivot (upper-arm head,
magenta) and - at rest only, since the anatomical landmarks are not posed - the anatomical glenohumeral centre landmark
(cyan).  Configurations: the a003 coupled motion as is ("today"), or with scripts/original_v1_scapula_isb_drive.py
(anatomical-frame scapula + weight taper, "isb").  Review/diagnostic only; nothing is saved.

  python3.13 render_original_skeleton_xray_blender.py -- --blend a003.blend --config today|isb|<candidate tag, e.g. r4> --out DIR [--poses 0,90,160]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

COLOURS = [("scapula", (0.85, 0.12, 0.12)), ("clavicle", (0.95, 0.80, 0.10)), ("upperarm", (0.95, 0.45, 0.05)),
           ("deltoid_helper", (0.95, 0.45, 0.05)), ("forearm", (0.20, 0.65, 0.25)), ("hand", (0.20, 0.65, 0.25)),
           ("metacarpal", (0.20, 0.65, 0.25)), ("thumb", (0.20, 0.65, 0.25)), ("index", (0.20, 0.65, 0.25)),
           ("middle", (0.20, 0.65, 0.25)), ("ring", (0.20, 0.65, 0.25)), ("pinky", (0.20, 0.65, 0.25)),
           ("spine", (0.25, 0.45, 0.85)), ("pelvis", (0.25, 0.45, 0.85)), ("neck", (0.25, 0.45, 0.85)),
           ("head", (0.25, 0.45, 0.85)), ("root", (0.25, 0.45, 0.85))]


def _mat(name, rgb, alpha=1.0, emission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = 0.5
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
        m.use_backface_culling = False
    if emission:
        b.inputs["Emission Color"].default_value = (*rgb, 1.0)
        b.inputs["Emission Strength"].default_value = emission
    return m


def _colour(name):
    for prefix, rgb in COLOURS:
        if name.startswith(prefix):
            return rgb
    return (0.62, 0.62, 0.62)


def build_skeleton(rig, coll, mats):
    """Octahedral bone shape per deforming pose bone (world = armature space), plus joint spheres."""
    made = []
    for pb in rig.pose.bones:
        if not rig.data.bones[pb.name].use_deform:
            continue
        L = (pb.tail - pb.head).length
        if L < 1e-6:
            continue
        w = min(0.12 * L, 0.022)
        bm = bmesh.new()
        ax_x, ax_y, ax_z = (pb.matrix.to_3x3() @ Vector(v) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)))
        ax_x.normalize(); ax_y.normalize(); ax_z.normalize()
        h, t = pb.head, pb.tail
        mid = h + (t - h) * 0.18
        ring = [bm.verts.new(mid + (ax_x * dx + ax_z * dz) * w) for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        a, b = bm.verts.new(h), bm.verts.new(t)
        for i in range(4):
            bm.faces.new((a, ring[i], ring[(i + 1) % 4]))
            bm.faces.new((b, ring[(i + 1) % 4], ring[i]))
        me = bpy.data.meshes.new(f"XR_{pb.name}")
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f"XR_{pb.name}", me)
        coll.objects.link(ob)
        rgb = _colour(pb.name)
        key = tuple(round(c, 2) for c in rgb)
        if key not in mats:
            mats[key] = _mat(f"XR_M_{len(mats)}", rgb)
        ob.data.materials.append(mats[key])
        made.append(ob)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=min(0.35 * w + 0.004, 0.012), location=h, segments=12, ring_count=8)
        s = bpy.context.object
        for c in s.users_collection:
            c.objects.unlink(s)
        coll.objects.link(s)
        s.data.materials.append(mats[key])
        made.append(s)
    return made


def marker(coll, loc, rgb, r=0.014):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=16, ring_count=10)
    s = bpy.context.object
    for c in s.users_collection:
        c.objects.unlink(s)
    coll.objects.link(s)
    s.data.materials.append(_mat("XR_MARK", rgb, emission=2.0))
    return s


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k, d=None: args[args.index(k) + 1] if k in args else d
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    config, out = get("--config", "today"), Path(get("--out"))
    poses = [int(x) for x in get("--poses", "0,90,160").split(",")]
    out.mkdir(parents=True, exist_ok=True)
    import build_functional_shoulder_correction_blender as correction
    import original_v1_scapula_isb_drive as isb
    res = correction.build_corrected_scene()
    rig, body = res["runtime"], res["body"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    if config == "isb":
        isb.install(res)
        print("taper vertices", isb.taper_scapula_weights(res))
    import original_v1_review_candidate_drives as drives
    drives.setup(res)                                   # R4 blends: anatomical scapula + thorax contact
    gh = {s: bpy.data.objects[f"LM_scapula_{a}__GH"].matrix_world.translation.copy() for s, a in isb.ANAT.items()}
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 640, 800
    sc.render.film_transparent = False
    world = bpy.data.worlds.new("XR_W"); sc.world = world; world.color = (0.06, 0.06, 0.07)
    sun = bpy.data.objects.new("XR_SUN", bpy.data.lights.new("XR_SUN", "SUN")); sc.collection.objects.link(sun)
    sun.data.energy = 3.0
    skin = _mat("XR_SKIN", (0.85, 0.66, 0.56), alpha=0.22)
    body.data.materials.clear(); body.data.materials.append(skin)
    ivory = _mat("XR_GUIDE", (0.93, 0.90, 0.80))
    guides = list(res["objects"].values())
    for o in sc.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = o not in guides
    for g in guides:
        g.data.materials.clear(); g.data.materials.append(ivory)
    cd = bpy.data.cameras.new("XR_CAM"); cd.type = "ORTHO"
    cam = bpy.data.objects.new("XR_CAM", cd); sc.collection.objects.link(cam); sc.camera = cam
    mats = {}
    for ht in poses:
        coll = bpy.data.collections.new(f"XR_{ht}"); sc.collection.children.link(coll)
        correction.apply_corrected_pose(res, ht)
        drives.drive(rig, body)
        bpy.context.view_layer.update()
        build_skeleton(rig, coll, mats)
        for s in ("r", "l"):
            marker(coll, rig.pose.bones[f"upperarm_{s}"].head.copy(), (0.95, 0.10, 0.85))
            if ht == 0:
                marker(coll, gh[s], (0.10, 0.85, 0.95))
        bpy.context.view_layer.update()
        V = [body.matrix_world @ v.co for v in body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().vertices]
        lo = Vector((min(v.x for v in V), min(v.y for v in V), min(v.z for v in V)))
        hi = Vector((max(v.x for v in V), max(v.y for v in V), max(v.z for v in V)))
        centre = (lo + hi) / 2
        sh = rig.pose.bones["upperarm_r"].head.copy() + Vector((-0.05, 0, 0.0))
        views = [("front", centre, (0, -1, 0), 2.2), ("side", centre, (1, 0, 0), 2.2), ("rear", centre, (0, 1, 0), 2.2),
                 ("shoulder_front", sh, (0, -1, 0), 0.62), ("shoulder_rear", sh, (0, 1, 0), 0.62),
                 ("shoulder_side", sh, (1, 0, 0), 0.62)]
        for name, tgt, d, scale in views:
            cd.ortho_scale = scale
            cam.location = tgt + Vector(d) * 4.0
            cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
            sun.rotation_euler = (cam.location - tgt).to_track_quat("Z", "Y").to_euler()
            sc.render.filepath = str(out / f"{config}_ht{ht:03d}_{name}.png")
            bpy.ops.render.render(write_still=True)
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(coll)
    print("xray", config, "->", out)


if __name__ == "__main__":
    main()
