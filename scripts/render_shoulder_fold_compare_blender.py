#!/usr/bin/env python3
"""Shoulder fold close-ups of an ORIGINAL_v1 review blend (bpy, Workbench): the coupled shoulder pose at each --hts angle
(front / rear / side, identical cameras), all review drives on; faces in self-intersecting pairs are painted red, collapsed
faces (< 0.1 x rest area) blue, stretched faces (> 2 x rest area) yellow.  Nothing is saved.

  python3.13 render_shoulder_fold_compare_blender.py -- --blend B.blend --out DIR --tag NAME [--hts 120,130,160]
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    bpy.ops.wm.open_mainfile(filepath=str(Path(get("--blend")).resolve()))
    out, tag = Path(get("--out")), get("--tag")
    hts = [int(v) for v in (get("--hts") if "--hts" in args else "120,130,160").split(",")]
    import build_functional_shoulder_correction_blender as correction
    import build_original_movement_benchmarks_blender as bench
    import original_v1_review_candidate_drives as drives
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    A0 = [bench._area(V0, f) for f in F]
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    mats = []
    for n, c in (("SKIN", (0.64, 0.46, 0.38, 1.0)), ("PAIR", (0.85, 0.08, 0.08, 1.0)), ("COLL", (0.1, 0.25, 0.9, 1.0)), ("STR", (0.95, 0.8, 0.1, 1.0))):
        m = bpy.data.materials.new(f"HGPT_FOLD_{n}_TMP"); m.diffuse_color = c; mats.append(m)
    body.data.materials.clear()
    for m in mats:
        body.data.materials.append(m)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
    scene.render.resolution_x = scene.render.resolution_y = 600
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_FOLD_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
    cam = bpy.data.objects.new("HGPT_FOLD_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)
    # mesh face index -> triangle indices of bench._evaluated (triangulated in polygon order)
    tri_of_poly = []
    for p in body.data.polygons:
        tri_of_poly.append(len(p.vertices) - 2)
    owner = [k for k, n in enumerate(tri_of_poly) for _ in range(n)]
    for ht in hts:
        correction.apply_corrected_pose(res, ht)
        drives.drive(rig, body)
        V, _ = bench._evaluated(body)
        tree = BVHTree.FromPolygons(V, F, all_triangles=True)
        fs = [set(f) for f in F]
        pairs = {t for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b]) for t in (a, b)}
        coll = {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] < 0.1}
        strd = {k for k, f in enumerate(F) if A0[k] > 1e-12 and bench._area(V, f) / A0[k] > 2.0}
        idx = [0] * len(body.data.polygons)
        if len(owner) == len(F):
            for t in strd:
                idx[owner[t]] = 3
            for t in pairs:
                idx[owner[t]] = 1
            for t in coll:
                idx[owner[t]] = 2
        body.data.polygons.foreach_set("material_index", idx)
        body.data.update()
        bpy.context.view_layer.update()
        c = rig.pose.bones["upperarm_r"].head.copy() + Vector((0, 0, 0.02))
        for view, d in (("front", (0, -1, 0)), ("rear", (0, 1, 0)), ("side", (1, 0, 0))):
            cam.location = c + Vector(d).normalized() * 3.0
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(out / f"{tag}__fold{ht}_{view}.png")
            bpy.ops.render.render(write_still=True)
        print("FOLD", tag, ht, "pairs_faces", len(pairs), "collapsed", len(coll), "stretched", len(strd), "mapped", len(owner) == len(F))


if __name__ == "__main__":
    main()
