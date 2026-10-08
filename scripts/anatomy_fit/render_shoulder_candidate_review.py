#!/usr/bin/env python3
"""Shoulder-stage review renders (bpy): identical cameras for a003 and the shoulder-proposal candidate.

Read-only: opens a .blend, adds review-only geometry in memory, renders, never saves. Body in X-ray, anatomical bones
as sticks (clavicles and scapulae highlighted cyan), SC/AC/GH as large balls (yellow/white/magenta), scapula outline
(AA-TS-AI triangle, medial-spine-to-AA spine line, glenoid rim loop) in cyan. Each image is captioned afterwards
(compose_shoulder_review.py) with the candidate identity.

  python3.13 render_shoulder_candidate_review.py views --blend B --record R --out DIR [--outline-from-landmarks]
  python3.13 render_shoulder_candidate_review.py poses --blend B --record R --out DIR
"""
import argparse, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from render_master_review import COLOURS, ball, material, stick  # noqa: E402

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
SHOULDER_BONES = ('clavicle_left', 'clavicle_right', 'scapula_left', 'scapula_right')
VIEWS = {
    'full_front': ((0, -4, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_back': ((0, 4, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_left_side': ((4, 0, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_right_side': ((-4, 0, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_front_left_three_quarter': ((2.83, -2.83, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_front_right_three_quarter': ((-2.83, -2.83, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'full_back_left_three_quarter': ((2.83, 2.83, 0.95), (0, 0, 0.95), 2.0, (900, 1500)),
    'upper_body_front': ((0, -4, 1.42), (0, 0, 1.42), 0.75, (1000, 800)),
    'upper_body_back': ((0, 4, 1.42), (0, 0, 1.42), 0.75, (1000, 800)),
    'upper_body_overhead': ((0, 0.001, 4), (0, 0.02, 1.42), 0.75, (1000, 800)),
}
for side, s in (('left', 1.0), ('right', -1.0)):
    c = (s * 0.17, 0.03, 1.47)
    VIEWS.update({
        f'shoulder_{side}_front': ((c[0], -3, c[2]), c, 0.42, (900, 900)),
        f'shoulder_{side}_side': ((s * 3, c[1], c[2]), c, 0.42, (900, 900)),
        f'shoulder_{side}_rear': ((c[0], 3, c[2]), c, 0.42, (900, 900)),
        f'shoulder_{side}_overhead': ((c[0], c[1] + 0.001, 4), c, 0.42, (900, 900)),
        f'axilla_{side}_from_below_front': ((c[0] + s * 1.2, -1.6, 0.4), (c[0], c[1], 1.42), 0.42, (900, 900)),
    })
POSES = {  # name: (rotation axis world-frame description, angle deg, camera view, centre, size)
    'neutral': (None, 0, 'front'),
    'gh_abduction_scapular_plane_60': ('scapular_plane', 60, 'front'),
    'gh_abduction_scapular_plane_90': ('scapular_plane', 90, 'front'),
    'gh_flexion_90': ('sagittal', 90, 'left'),
}


def setup(sc, body_alpha=0.22):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = body_alpha
    sc.render.image_settings.file_format = 'PNG'
    cam = bpy.data.objects.new('review_cam', bpy.data.cameras.new('review_cam'))
    sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    return cam


def shoot(sc, cam, loc, target, size, res, path):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = size
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def prepare(o):
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    rec = json.loads(Path(o.record).read_text())
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ('MESH', 'EMPTY') and ob.name != BODY:
            ob.hide_render = True
    body = bpy.data.objects[BODY]
    body.data.materials.clear(); body.data.materials.append(material('skin', (0.82, 0.78, 0.74, 1)))
    coll = bpy.data.collections.new('REVIEW_ONLY'); sc.collection.children.link(coll)
    return rec, sc, coll


def outline_points(rec):
    """Scapula outline per side: from the candidate's 29 landmarks when present, else from a003 skeleton_input AA/TS/AI."""
    out = {}
    lms = rec.get('candidate', {}).get('scapula_landmarks_world_mm')
    for side in ('left', 'right'):
        if lms:
            p = [[c / 1000 for c in q] for q in lms[side]]
            L = lambda i: p[i - 1]
            out[side] = {'triangle': [L(25), L(5), L(7), L(25)], 'spine': [L(5), L(14), L(25)],
                         'glenoid': [L(15), L(16), L(18), L(17), L(15)], 'extra': [L(3), L(26), L(27)]}
        else:
            s = rec['skeleton_input']['sides'][side]
            out[side] = {'triangle': [s['AA'], s['TS'], s['AI'], s['AA']], 'spine': [s['TS'], s['AA']], 'glenoid': [], 'extra': [s['glenoid']]}
    return out


def add_geometry(rec, coll, arm=None):
    mats = {k: material(k, c) for k, c in COLOURS.items()}
    hi, jm = material('shoulder_hi', (0.1, 0.85, 0.95, 1)), material('joint', (0.1, 0.7, 0.3, 1))
    jsc, jac, jgh = material('SC', (1.0, 0.85, 0.1, 1)), material('AC', (0.95, 0.95, 0.95, 1)), material('GH', (0.9, 0.15, 0.85, 1))
    sticks = {}
    for bid, b in rec['bones'].items():
        L = math.dist(b['head_m'], b['tail_m'])
        is_sh = bid in SHOULDER_BONES
        mat = hi if is_sh else mats.get(b['placement'], mats['proportional'])
        sticks[bid] = stick('B_' + bid, b['head_m'], b['tail_m'], (0.006 if is_sh else max(0.0012, min(0.006, L * 0.03))), mat, coll)
    for jid, m in rec['joint_markers'].items():
        kind = jid.split('_')[0]
        mat, r = {'sternoclavicular': (jsc, 0.011), 'acromioclavicular': (jac, 0.011), 'glenohumeral': (jgh, 0.013)}.get(kind, (jm, 0.0022))
        ball('J_' + jid, m['centre_m'], r, mat, coll)
    for side, parts in outline_points(rec).items():
        for name in ('triangle', 'spine', 'glenoid'):
            pts = parts[name]
            for i in range(len(pts) - 1):
                stick(f'O_{side}_{name}_{i}', pts[i], pts[i + 1], 0.0025, hi, coll)
        for i, p in enumerate(parts['extra']):
            ball(f'O_{side}_x{i}', p, 0.004, hi, coll)
    return sticks


def views(o):
    rec, sc, coll = prepare(o)
    add_geometry(rec, coll)
    cam = setup(sc)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    for name, (loc, target, size, res) in VIEWS.items():
        shoot(sc, cam, loc, target, size, res, out / f'{name}.png')
    print('views', len(VIEWS))


def poses(o):
    """Bone-only illustrative GH poses: the humerus subtree's sticks are parented to their bones and the humerus pose bone
    is rotated about the GH centre. Not a validated movement test."""
    rec, sc, coll = prepare(o)
    arm = bpy.data.objects['HGPT_ANATOMICAL_MASTER']
    sticks = add_geometry(rec, coll)
    for bid, st in sticks.items():
        bpy.context.view_layer.update()
        mw = st.matrix_world.copy()
        st.parent, st.parent_type, st.parent_bone = arm, 'BONE', 'anat_' + bid
        bpy.context.view_layer.update()
        st.matrix_world = mw
    for ob in list(coll.objects):            # joint balls and outlines stay static: hide moving-arm ones for clarity
        if ob.name.startswith('J_') and not ob.name.startswith(('J_sternoclavicular', 'J_acromioclavicular', 'J_glenohumeral')):
            ob.hide_render = True
    cam = setup(sc, body_alpha=0.12)
    out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    manifest = {}
    for name, (axis, ang, view) in POSES.items():
        for side, s in (('left', 1.0), ('right', -1.0)):
            pb = arm.pose.bones[f'anat_humerus_{side}']
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = (1, 0, 0, 0)
            if axis is None:
                continue
            gh = Vector(rec['joint_markers'][f'glenohumeral_{side}']['centre_m'])
            if axis == 'scapular_plane':
                # elevation in the scapular plane: plane through GH containing world vertical and the AA-TS direction
                L = rec['candidate']['scapula_landmarks_world_mm'][side] if 'candidate' in rec else None
                if L:
                    ts, aa = Vector([c / 1000 for c in L[4]]), Vector([c / 1000 for c in L[24]])
                else:
                    sd = rec['skeleton_input']['sides'][side]; ts, aa = Vector(sd['TS']), Vector(sd['AA'])
                lat = (aa - ts); lat.z = 0; lat.normalize()
                ax = Vector((0, 0, 1)).cross(lat).normalized()          # horizontal axis perpendicular to the plane
                angle = math.radians(ang)
                if (Matrix.Rotation(angle, 3, ax) @ Vector((0, 0, -1))).dot(lat) < 0:
                    angle = -angle
            else:
                ax = Vector((1, 0, 0)); angle = math.radians(ang)
                if (Matrix.Rotation(angle, 3, ax) @ Vector((0, 0, -1))).y > 0:   # flexion raises the arm anteriorly (-Y)
                    angle = -angle
            G = Matrix.Translation(gh) @ Matrix.Rotation(angle, 4, ax) @ Matrix.Translation(-gh)
            R0 = arm.matrix_world @ pb.bone.matrix_local
            pb.matrix_basis = R0.inverted() @ G @ R0
        bpy.context.view_layer.update()
        dirs = {'front': (Vector((0, -1, 0)), (0, 0, 1.3), 1.25), 'left': (Vector((1, 0, 0)), (0, 0, 1.3), 1.25)}
        d, centre, size = dirs[view]
        shoot(sc, cam, Vector(centre) + d * 3, centre, size, (1000, 1000), out / f'pose_{name}.png')
        manifest[name] = {'rotation': axis, 'angle_deg': ang, 'view': view, 'note': 'illustrative humerus-subtree rotation about GH; not a validated movement test'}
    (out / 'poses_manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print('poses', len(manifest))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    for n in ('views', 'poses'):
        p = sub.add_parser(n); p.add_argument('--blend', required=True); p.add_argument('--record', required=True); p.add_argument('--out', required=True)
    o = ap.parse_args(argv)
    {'views': views, 'poses': poses}[o.cmd](o)


if __name__ == '__main__':
    main()
