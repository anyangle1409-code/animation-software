#!/usr/bin/env python3
"""Morning review pack: labelled still renders of the anatomical master on the unchanged audit candidate.

Read-only: opens the audit .blend files, builds review-only geometry in memory and never saves a .blend.
Two modes (run separately; each writes into its own new sub-directory):
  views  --blend a003 --record FIT --out DIR    body (X-ray) + anatomical bones + joint markers + runtime joint heads
  poses  --blend TESTS --record FIT --report RUN/isolated_report.json --samples RUN/isolated_samples.json --out DIR
         bone-only master poses at the neutral frame and at each test's measured peak frame
"""
import argparse, json, math, sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_master_review import COLOURS, ball, material, stick  # noqa: E402

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
# name: (camera location, target, ortho size, resolution). Character faces -Y; anatomical LEFT is +X.
VIEWS = {
    'full_front': ((0, -4, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_back': ((0, 4, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_left_side': ((4, 0, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_right_side': ((-4, 0, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_front_left_three_quarter': ((2.83, -2.83, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_front_right_three_quarter': ((-2.83, -2.83, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
    'full_back_left_three_quarter': ((2.83, 2.83, 0.91), (0, 0, 0.91), 1.95, (900, 1500)),
}
for side, s in (('left', 1.0), ('right', -1.0)):
    c = (s * 0.19, 0.02, 1.43)       # between the GH centre and the axilla
    VIEWS.update({
        f'shoulder_axilla_{side}_front': ((c[0], -3, c[2]), c, 0.44, (900, 900)),
        f'shoulder_axilla_{side}_side': ((s * 3, c[1], c[2]), c, 0.44, (900, 900)),
        f'shoulder_axilla_{side}_rear': ((c[0], 3, c[2]), c, 0.44, (900, 900)),
        f'shoulder_{side}_overhead': ((c[0], c[1] + 0.001, 4), c, 0.44, (900, 900)),
        f'axilla_{side}_from_below_front': ((c[0] + s * 1.2, -1.6, 0.4), (c[0], c[1], 1.40), 0.44, (900, 900)),
    })

# poses: test id -> (camera direction, framing centre, ortho size)
POSES = {
    'neutral_front': (None, 'front', (0, 0, 0.91), 1.95),
    'neutral_left_side': (None, 'left', (0, 0, 0.91), 1.95),
    'shoulder_complex_scapular_plane_left': ('shoulder_complex_scapular_plane_left', 'front', (0.2, 0, 1.45), 1.1),
    'gh_elevation_plane_90_left': ('gh_elevation_plane_90_left', 'left', (0.2, 0, 1.45), 1.2),
    'hip_flexion_extension_left': ('hip_flexion_extension_left', 'left', (0.08, 0, 0.75), 1.5),
    'knee_flexion_with_patellar_follower_left': ('knee_flexion_with_patellar_follower_left', 'left', (0.09, 0, 0.45), 1.0),
    'elbow_flexion_at_pronation_0_left': ('elbow_flexion_at_pronation_0_left', 'left', (0.21, 0, 1.1), 0.8),
    'thumb_opposition_left': ('thumb_opposition_left', 'front', (0.19, 0, 0.85), 0.3),
    'c0_c1_flexion_extension': ('c0_c1_flexion_extension', 'left', (0, 0, 1.68), 0.45),
    'lumbar_l4_l5_extension': ('lumbar_l4_l5_extension', 'left', (0, 0, 1.1), 0.7),
}
UPPER_LIMB = ('clavicle', 'scapula', 'humerus', 'radius', 'ulna', 'carpal', 'scaphoid', 'lunate', 'triquetrum', 'pisiform', 'trapezi',
              'capitate', 'hamate', 'metacarpal', 'phalanx', 'sesamoid_hand')
DIRS = {'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)), 'back': Vector((0, 1, 0))}


def setup_render(sc):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 88
    cam = bpy.data.objects.new('review_cam', bpy.data.cameras.new('review_cam'))
    sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    return cam


def shoot(sc, cam, loc, target, size, res, path):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    up = 'Y' if abs(d.normalized().z) < 0.95 else 'Y'
    cam.rotation_euler = d.to_track_quat('-Z', up).to_euler()
    cam.data.ortho_scale = size
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def views(o):
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    rec = json.loads(Path(o.record).read_text())
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type == 'MESH' and ob.name != BODY:
            ob.hide_render = True
    body = bpy.data.objects[BODY]
    body.data.materials.clear()
    body.data.materials.append(material('skin', (0.85, 0.8, 0.75, 1)))
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    mats = {k: material(k, c) for k, c in COLOURS.items()}
    jmat, rigmat = material('joint', (0.1, 0.75, 0.3, 1)), material('runtime', (0.9, 0.1, 0.9, 1))
    for bid, b in rec['bones'].items():
        L = math.dist(b['head_m'], b['tail_m'])
        stick('B_' + bid, b['head_m'], b['tail_m'], max(0.0012, min(0.006, L * 0.03)), mats[b['placement']], coll)
    major = ['hip', 'tibiofemoral', 'talocrural', 'glenohumeral', 'acromioclavicular', 'sternoclavicular', 'humeroulnar', 'radiocarpal', 'subtalar_posterior', 'scapulothoracic']
    for jid, m in rec['joint_markers'].items():
        ball('J_' + jid, m['centre_m'], 0.007 if any(jid.startswith(k + '_') for k in major) else 0.0025, jmat, coll)
    for k, v in rec['checks']['runtime_rig_comparison']['joints'].items():
        ball('R_' + k, v['runtime_head_m'], 0.006, rigmat, coll)
    cam = setup_render(sc)
    sc.display.shading.show_xray = True; sc.display.shading.xray_alpha = 0.25
    for name, (loc, target, size, res) in VIEWS.items():
        shoot(sc, cam, loc, target, size, res, out / f'{name}.jpg')
    print('views', len(VIEWS))


def poses(o):
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    rec = json.loads(Path(o.record).read_text())
    rep = json.loads(Path(o.report).read_text())
    smp = json.loads(Path(o.samples).read_text())
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ('MESH', 'EMPTY'):
            ob.hide_render = True
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    coll = bpy.data.collections.new('POSE_ONLY'); sc.collection.children.link(coll)
    mats = {k: material(k, c) for k, c in COLOURS.items()}
    for bid, b in rec['bones'].items():
        a, t = Vector(b['head_m']), Vector(b['tail_m'])
        L = (t - a).length
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=max(0.0015, min(0.008, L * 0.035)), depth=L, location=(a + t) / 2)
        st = bpy.context.active_object
        st.rotation_euler = (t - a).to_track_quat('Z', 'Y').to_euler()
        st.data.materials.append(mats[b['placement']])
        for c in st.users_collection:
            c.objects.unlink(st)
        coll.objects.link(st)
        bpy.context.view_layer.update()
        mw = st.matrix_world.copy()
        st.parent, st.parent_type, st.parent_bone = arm, 'BONE', 'anat_' + bid
        bpy.context.view_layer.update()
        st.matrix_world = mw
    cam = setup_render(sc)
    manifest = {}
    for name, (tid, view, centre, size) in POSES.items():
        if tid is None:
            frame, value = 1, None                       # neutral: first authored frame (all tests start at rest)
        else:
            rows = smp[tid]
            prim = rep['summary'][tid]['primary_channel']
            key = {'internal': 'internal_rotation', 'plane': 'plane_of_elevation'}.get(prim, prim)
            pk = max(rows, key=lambda r: abs(r[key]))
            frame, value = pk['frame'], pk[key]
        sc.frame_set(frame)
        spinal = name.startswith(('c0_c1', 'lumbar'))      # upper-limb sticks would hide the spine in a side view
        for st in coll.objects:
            st.hide_render = spinal and any(k in st.parent_bone for k in UPPER_LIMB)
        d = DIRS[view]
        shoot(sc, cam, Vector(centre) + d * 3, centre, size, (900, 1200) if size > 1 else (900, 900), out / f'pose_{name}.jpg')
        manifest[name] = {'test_id': tid, 'frame': frame, 'primary_value_deg': value, 'view': view, 'upper_limb_hidden': spinal}
    (out / 'poses_manifest.json').write_text(json.dumps(manifest, indent=1))
    print('poses', len(manifest))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('views'); v.add_argument('--blend', required=True); v.add_argument('--record', required=True); v.add_argument('--out', required=True)
    p = sub.add_parser('poses')
    for a in ('--blend', '--record', '--report', '--samples', '--out'):
        p.add_argument(a, required=True)
    o = ap.parse_args(argv)
    {'views': views, 'poses': poses}[o.cmd](o)


if __name__ == '__main__':
    main()
