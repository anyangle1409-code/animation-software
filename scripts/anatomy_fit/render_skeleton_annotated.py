#!/usr/bin/env python3
"""Annotated skeleton-only review renders (bpy, Workbench), second pass. Adds to render_skeleton_only_review.py:
  * world reference axes at each view target (X red = character left, Y green = posterior, Z blue = up; 50 mm, or 200 mm in
    whole-body views) and a 100 mm black scale bar;
  * text labels on named joint centres per region (joint-marker ids from the record) and bone endpoints marked as small
    white dots (head) / grey dots (tail) so a stick's endpoints are distinguishable from joint centres (black);
  * an independent camera check: a red probe sphere is placed at a known world point (the target + 30 mm along the view-
    plane x axis); after rendering, its pixel centroid is located and compared with the analytic orthographic projection.
    The result (pixel error) is written to the manifest for every view.
Nothing is saved to the source blend (hash-checked).

  python3.13 render_skeleton_annotated.py --blend B.blend --record R.json --out DIR [--label NAME]
"""
import argparse, hashlib, json, sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_skeleton_only_review as base  # noqa: E402

RES = 1200
LABELS = {
    'shoulders': ['sternoclavicular_left', 'sternoclavicular_right', 'acromioclavicular_left', 'acromioclavicular_right', 'glenohumeral_left', 'glenohumeral_right'],
    'hand_left': ['radiocarpal_left', 'cmc_1_left', 'mcp_2_left', 'mcp_3_left', 'mcp_4_left', 'mcp_5_left', 'thumb_mcp_left', 'pip_2_left', 'dip_2_left'],
    'spine': ['atlantooccipital_left', 'disc_c2_c3', 'disc_c7_t1', 'disc_t6_t7', 'disc_t12_l1', 'disc_l5_s1'],
    'pelvis': ['hip_left', 'hip_right', 'sacroiliac_anterior_left', 'sacroiliac_anterior_right', 'pubic_symphysis', 'disc_l5_s1'],
    'knee_left': ['tibiofemoral_left', 'patellofemoral_left', 'proximal_tibiofibular_left'],
    'ankle_left': ['talocrural_left', 'subtalar_posterior_left', 'talocalcaneonavicular_left', 'calcaneocuboid_left', 'distal_tibiofibular_left'],
    'foot_left': ['talocrural_left', 'calcaneocuboid_left', 'talocalcaneonavicular_left', 'mtp_1_left', 'mtp_5_left'],
    'head': ['tmj_left', 'atlantooccipital_left', 'atlantoaxial_median'],
}
VIEWS = {
    'body_front': ((0, -1, 0), (0, 0, 1), None, 2.05), 'body_back': ((0, 1, 0), (0, 0, 1), None, 2.05),
    'body_left': ((1, 0, 0), (0, 0, 1), None, 2.05), 'body_right': ((-1, 0, 0), (0, 0, 1), None, 2.05),
    'body_front_left_34': ((0.7071, -0.7071, 0), (0, 0, 1), None, 2.05),
    'shoulders_front': ((0, -1, 0), (0, 0, 1), 'shoulders', 0.62), 'shoulders_back': ((0, 1, 0), (0, 0, 1), 'shoulders', 0.62),
    'shoulders_top': ((0, 0, 1), (0, -1, 0), 'shoulders', 0.62),
    'spine_ribcage_left': ((1, 0, 0), (0, 0, 1), 'spine', 1.0), 'spine_ribcage_front': ((0, -1, 0), (0, 0, 1), 'spine', 1.0),
    'pelvis_hips_front': ((0, -1, 0), (0, 0, 1), 'pelvis', 0.45), 'pelvis_hips_left': ((1, 0, 0), (0, 0, 1), 'pelvis', 0.45),
    'hand_left_dorsal': ((1, 0, 0), (0, 0, 1), 'hand_left', 0.26), 'hand_left_radial': ((0, -1, 0), (0, 0, 1), 'hand_left', 0.26),
    'knee_left_front': ((0, -1, 0), (0, 0, 1), 'knee_left', 0.3), 'knee_left_lateral': ((1, 0, 0), (0, 0, 1), 'knee_left', 0.3),
    'ankle_left_back': ((0, 1, 0), (0, 0, 1), 'ankle_left', 0.22), 'ankle_left_lateral': ((1, 0, 0), (0, 0, 1), 'ankle_left', 0.22),
    'foot_left_lateral': ((1, 0, 0), (0, 0, 1), 'foot_left', 0.34), 'foot_left_top': ((0, 0, 1), (0, -1, 0), 'foot_left', 0.34),
    'skull_neck_left': ((1, 0, 0), (0, 0, 1), 'head', 0.4), 'skull_neck_front': ((0, -1, 0), (0, 0, 1), 'head', 0.4),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def link(o, coll):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)


def targets(rec):
    T = base.targets(rec); J = rec['joint_markers']; B = rec['bones']
    T['knee_left'] = Vector(J['tibiofemoral_left']['centre_m'])
    T['ankle_left'] = Vector(J['talocrural_left']['centre_m']) + Vector((0, 0, -0.02))
    return T


def cam_basis(direction, up):
    z = Vector(direction).normalized(); x = Vector(up).cross(z).normalized(); y = z.cross(x)
    return x, y, z


def add_annotations(rec, coll, tgt, direction, up, scale, labels):
    x, y, z = cam_basis(direction, up)
    L = 0.2 if scale > 1.5 else 0.05
    origin = tgt - x * scale * 0.42 - y * scale * 0.42
    objs = []
    for axis, col in ((Vector((1, 0, 0)), (0.9, 0.1, 0.1, 1)), (Vector((0, 1, 0)), (0.1, 0.7, 0.1, 1)), (Vector((0, 0, 1)), (0.1, 0.2, 0.9, 1))):
        if abs(axis.dot(z)) > 0.99:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=scale * 0.0025, depth=L, location=origin + axis * L / 2)
        o = bpy.context.active_object; o.rotation_euler = axis.to_track_quat('Z', 'Y').to_euler()
        o.data.materials.append(base.mat('ax', col)); link(o, coll); objs.append(o)
    # 100 mm scale bar along view-plane x
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=scale * 0.002, depth=0.1, location=origin - y * scale * 0.03 + x * 0.05)
    o = bpy.context.active_object; o.rotation_euler = x.to_track_quat('Z', 'Y').to_euler(); o.data.materials.append(base.mat('bar', (0, 0, 0, 1))); link(o, coll); objs.append(o)
    txt = [('100 mm', origin - y * scale * 0.06 + x * 0.0), ('X=left  Y=posterior  Z=up', origin + y * scale * 0.86)]
    J = rec['joint_markers']
    for jid in labels:
        if jid in J:
            txt.append((jid, Vector(J[jid]['centre_m']) + x * scale * 0.012 + y * scale * 0.006))
    R = Matrix((x, y, z)).transposed().to_4x4()
    for s, p in txt:
        cu = bpy.data.curves.new('lbl', 'FONT'); cu.body = s; cu.size = scale * 0.018
        o = bpy.data.objects.new('LBL_' + s, cu); o.matrix_world = Matrix.Translation(p + z * 0.05) @ R
        o.data.materials.append(base.mat('txt', (0.05, 0.05, 0.05, 1))); coll.objects.link(o); objs.append(o)
    return objs


def endpoint_dots(rec, coll, region_bones):
    for bid in region_bones:
        b = rec['bones'][bid]
        for e, col in (('head_m', (1, 1, 1, 1)), ('tail_m', (0.55, 0.55, 0.55, 1))):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.0016, location=b[e])
            o = bpy.context.active_object; o.data.materials.append(base.mat('ep', col)); link(o, coll)


def probe_check(path, direction, up, tgt, scale, probe):
    img = bpy.data.images.load(str(path)); w, h = img.size
    px = np.array(img.pixels[:]).reshape(h, w, 4)[::-1]          # Blender stores rows bottom-up
    bpy.data.images.remove(img)
    mask = (px[..., 0] > 0.75) & (px[..., 1] < 0.25) & (px[..., 2] < 0.25)
    if mask.sum() == 0:
        return {'found': False}
    ys, xs = np.nonzero(mask)
    x, y, z = cam_basis(direction, up)
    u = (probe - tgt).dot(x) / scale + 0.5; v = 0.5 - (probe - tgt).dot(y) / scale
    exp = (u * RES, v * RES)
    return {'found': True, 'pixel_centroid': [float(xs.mean()), float(ys.mean())], 'expected_pixel': [exp[0], exp[1]],
            'error_px': float(np.hypot(xs.mean() - exp[0], ys.mean() - exp[1])), 'mm_per_px': scale * 1000 / RES}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ('--blend', '--record', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--label', default='')
    o = ap.parse_args(argv)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    rec = json.loads(Path(o.record).read_text()); T = targets(rec)
    before = sha(o.blend)
    manifest = {'label': o.label, 'source_blend_sha256': before, 'record_sha256': sha(o.record), 'blender': bpy.app.version_string,
                'legend': {'sticks': 'head-to-tail line of each rig bone (display radius only; NOT bone geometry)', 'black spheres': 'joint-marker centres',
                           'white dots': 'bone heads (region views)', 'grey dots': 'bone tails (region views)', 'red sphere': 'camera-check probe',
                           'axes': 'X red = character left, Y green = posterior, Z blue = up'}, 'views': {}}
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type == 'MESH':
            ob.hide_render = True
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    base.build_overlay(rec, coll); cam = base.setup_scene(sc); sc.render.resolution_x = sc.render.resolution_y = RES
    for name, (d, up, tg, s) in VIEWS.items():
        ann = bpy.data.collections.new('ANNOTATION'); sc.collection.children.link(ann)
        tgt = T[tg]
        add_annotations(rec, ann, tgt, d, up, s, LABELS.get(tg, []) if tg else [])
        if tg:
            reg = {'shoulders': ('clavicle', 'scapula', 'humerus'), 'hand_left': ('metacarpal', 'digit', 'thumb', 'scaph', 'lun', 'triq', 'pisi', 'trapez', 'capit', 'hamat'),
                   'knee_left': ('femur', 'tibia', 'patella', 'fibula'), 'ankle_left': ('tibia', 'fibula', 'talus', 'calcaneus', 'navicular', 'cuboid'),
                   'foot_left': ('talus', 'calcaneus', 'navicular', 'cuboid', 'cuneiform', 'metatarsal', 'hallux', 'toe'), 'pelvis': ('hip_bone', 'femur'),
                   'spine': (), 'head': ('mandible',)}.get(tg, ())
            bones = [b for b in rec['bones'] if (b.endswith('_left') or tg in ('shoulders', 'pelvis')) and any(b.startswith(r) or ('_' + r) in b for r in reg)]
            endpoint_dots(rec, ann, bones)
        x, y, z = cam_basis(d, up)
        probe = tgt + x * 0.03 * (s / 0.3 if s > 0.3 else 1)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=s * 0.006, location=probe)
        pr = bpy.context.active_object; pr.data.materials.append(base.mat('probe', (1, 0, 0, 1))); link(pr, ann)
        p = out / f'{name}.png'
        base.shoot(sc, cam, d, up, tgt, s, p)
        manifest['views'][name] = {'direction': d, 'up': up, 'target': tg or 'body', 'target_world_m': list(tgt), 'ortho_scale_m': s,
                                   'probe_world_m': list(probe), 'camera_check': probe_check(p, d, up, tgt, s, probe)}
        for ob in list(ann.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(ann)
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')          # incremental
    manifest['source_blend_sha256_after'] = sha(o.blend)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    errs = [v['camera_check'].get('error_px') for v in manifest['views'].values()]
    print('views', len(manifest['views']), 'max probe error px', max(e for e in errs if e is not None), 'unchanged', before == manifest['source_blend_sha256_after'])


if __name__ == '__main__':
    main()
