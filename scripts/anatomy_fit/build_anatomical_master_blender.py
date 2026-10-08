#!/usr/bin/env python3
"""Phase 6/7: fit the anatomical reference skeleton to the r95 audit copy and build HGPT_ANATOMICAL_MASTER.

Reads an isolated audit .blend, measures the character surface, constructs all 206 `anat_<id>` reference
bones, 427 `HGPT_JOINT_<id>` marker empties and measured landmark empties, and saves them into a NEW audit
.blend. The source audit file, the character mesh/rig and every production asset are left untouched.

Run (bpy module):  python3 build_anatomical_master_blender.py --source-blend A001 --out-blend A002 --record FIT.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / 'scripts')]

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import character_fit as cf  # noqa: E402
import joint_markers as jm  # noqa: E402
import skeleton_fit as sf  # noqa: E402

BODY = 'HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE'
RUNTIME_RIG = 'HGPT_CANONICAL_V4_ORIGINAL'
MASTER = 'HGPT_ANATOMICAL_MASTER'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def authored_features():
    """Generator feature points used as character evidence (verified unchanged in the mesh below)."""
    import original_v1_o2_body as g
    inguinal = next(e for e in g.MUSCLE_DETAIL if e[0] == 'line' and e[2] == (0.112, 0.082, 1.000))
    groove = next(e for e in g.MUSCLE_DETAIL if e[0] == 'line' and e[2] == (0.000, 0.126, 1.415))
    s3 = g.SHOULDER_RINGS[3]['front'][0]
    chin = g.HEAD_RINGS[1][0]
    eye_z = g.HEAD_RINGS[6][0][2]
    palate_z = g.HEAD_RINGS[4][0][2]
    to_b = lambda p: (p[0], -p[1], p[2])  # generator (lx, f, z) -> Blender (x, -y, z)
    return {
        'asis': to_b(inguinal[2]), 'ij': to_b(s3), 'px': to_b(groove[3]), 'chin': to_b(chin),
        's1_arm_ring': g.SHOULDER_RINGS[1]['arm'], 'eye_ring_z': eye_z, 'palate_z': palate_z,
        'provenance': {'generator': 'scripts/original_v1_o2_body.py', 'generator_sha256': sha(ROOT / 'scripts/original_v1_o2_body.py'),
                       'items': {'asis': 'MUSCLE_DETAIL inguinal "V" line superolateral end', 'ij': 'SHOULDER_RINGS S3 front centre (sternal notch)',
                                 'px': 'MUSCLE_DETAIL sternal groove lower end', 'chin': 'HEAD_RINGS chin ring front centre',
                                 's1_arm_ring': 'SHOULDER_RINGS S1 arm portion ("humeral head level")', 'eye_ring_z': 'HEAD_RINGS eyes ring',
                                 'palate_z': 'HEAD_RINGS nose-base ring'}},
    }


def feature_presence(V, features):
    """Verify each authored feature region is unchanged between the regenerated O2 mesh and the audit mesh."""
    import original_v1_o2_body as g
    regen = g.build(ROOT / 'ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json')['vertices']
    if len(regen) != len(V):
        return {'status': 'FAIL', 'reason': 'vertex count differs'}
    d = np.linalg.norm(regen - V, axis=1)
    out = {}
    pts = {'asis_left': (features['asis'][0], features['asis'][1], features['asis'][2]),
           'asis_right': (-features['asis'][0], features['asis'][1], features['asis'][2]),
           'ij': features['ij'], 'px': features['px'], 'chin': features['chin']}
    for i, q in enumerate(features['s1_arm_ring']):          # ring control points lie on the surface
        pts[f's1_ring_point_{i}'] = (q[0], -q[1], q[2])
    for k, p in pts.items():
        near = np.linalg.norm(V - np.asarray(p), axis=1) < 0.03
        out[k] = {'vertices_within_30mm': int(near.sum()), 'max_change_m': float(d[near].max()) if near.any() else None}
    changed = int((d > 5e-4).sum())
    ok = all(v['vertices_within_30mm'] > 0 and v['max_change_m'] is not None and v['max_change_m'] < 5e-4 for v in out.values())
    return {'status': 'PASS' if ok else 'FAIL', 'features': out, 'mesh_vertices_changed_since_O2_gt_0_5mm': changed,
            'max_vertex_change_m': float(d.max()), 'mean_vertex_change_m': float(d.mean())}


def roll_reference(head, tail):
    """Target for align_roll: bone_frame X (anterior) unless it lies along the bone, which bone_frame does by design
    for horizontal bones (ribs, clavicle, foot, toes, some skull bones); then bone_frame Y (superior, perpendicular
    to the bone by construction). Without this, align_roll gets a parallel target and the roll is undefined."""
    R = jm.bone_frame(head, tail)
    d = np.asarray(tail, float) - np.asarray(head, float)
    d /= np.linalg.norm(d)
    if np.linalg.norm(np.cross(R[:, 0], d)) > 1e-9:
        return R[:, 0], 'anterior'
    return R[:, 1], 'superior'


def build_armature(bones):
    arm_data = bpy.data.armatures.new(MASTER + '_data')
    arm = bpy.data.objects.new(MASTER, arm_data)
    coll = bpy.data.collections.new('HGPT_ANATOMICAL_REFERENCE')
    bpy.context.scene.collection.children.link(coll)
    coll.objects.link(arm)
    arm.show_in_front = True
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for bid, b in bones.items():
        e = arm_data.edit_bones.new('anat_' + bid)
        e.head, e.tail = Vector(b['head_m']), Vector(b['tail_m'])
        e.align_roll(Vector(roll_reference(b['head_m'], b['tail_m'])[0]))  # bone local Z -> anatomical anterior (ISB X), or superior where anterior is the bone axis
        e.use_deform = False
        eb[bid] = e
    for bid, b in bones.items():
        if b['parent']:
            eb[bid].parent = eb[b['parent']]
            eb[bid].use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    for bid, b in bones.items():
        db = arm_data.bones['anat_' + bid]
        db['hgpt_anatomical_id'] = bid
        db['hgpt_role'] = b['role']
        db['hgpt_placement'] = b['placement']
        db['hgpt_confidence'] = b['confidence']
        db['hgpt_parent_relation'] = json.dumps(b['parent_relation'])
        db['hgpt_roll_reference'] = roll_reference(b['head_m'], b['tail_m'])[1]
    return arm, coll


def proximal_participant(parts, bones):
    present = [p for p in parts if p in bones]
    for a in present:
        for b in present:
            if a != b and bones[b]['parent'] == a:
                return a
    return None


def build_markers(arm, coll, markers, bones, plan):
    bpy.context.view_layer.update()
    for jid, m in markers.items():
        obj = bpy.data.objects.new('HGPT_JOINT_' + jid, None)
        coll.objects.link(obj)
        obj.empty_display_type = 'ARROWS'
        obj.empty_display_size = 0.012
        obj.rotation_mode = 'QUATERNION'  # Euler storage loses precision near gimbal lock (e.g. rib costochondral frames)
        obj['hgpt_joint_id'] = jid
        obj['hgpt_fit_method'] = m['method']
        obj['hgpt_frame_bone'] = m['frame_bone']
        parts = plan['joint_markers'][jid]['participants']
        host = proximal_participant(parts, bones) or m['frame_bone']
        obj.parent = arm
        obj.parent_type = 'BONE'
        obj.parent_bone = 'anat_' + host
        obj['hgpt_carrier_bone'] = host
        R = np.array(m['frame_axes_columns_XYZ'])
        M = Matrix(((R[0, 0], R[0, 1], R[0, 2], m['centre_m'][0]), (R[1, 0], R[1, 1], R[1, 2], m['centre_m'][1]),
                    (R[2, 0], R[2, 1], R[2, 2], m['centre_m'][2]), (0, 0, 0, 1)))
        bpy.context.view_layer.update()
        obj.matrix_world = M


def build_landmarks(arm, coll, report, L):
    items = []
    for s in ('left', 'right'):
        R = report['sides'][s]
        bone = {'ankle': f'tibia_{s}', 'knee': f'femur_{s}', 'hip': f'hip_bone_{s}', 'shoulder': f'scapula_{s}', 'elbow_wrist': f'humerus_{s}'}
        for region, data in R.items():
            if region not in bone:
                continue
            for key, val in data.items():
                if isinstance(val, dict) and 'value_m' in val and isinstance(val['value_m'], list) and len(val['value_m']) == 3 and key.endswith(('_skin',)):
                    items.append((f'{bone[region]}/{key}', val['value_m'], bone[region]))
        for key in ('SC', 'AC', 'AA', 'TS', 'AI', 'GH', 'EJC', 'WJC', 'HJC', 'KJC', 'AJC', 'tibial_plateau'):
            host = {'SC': f'clavicle_{s}', 'AC': f'clavicle_{s}', 'AA': f'scapula_{s}', 'TS': f'scapula_{s}', 'AI': f'scapula_{s}',
                    'GH': f'scapula_{s}', 'EJC': f'humerus_{s}', 'WJC': f'radius_{s}', 'HJC': f'hip_bone_{s}', 'KJC': f'femur_{s}',
                    'AJC': f'tibia_{s}', 'tibial_plateau': f'tibia_{s}'}[key]
            items.append((f'{host}/{key}', L['sides'][s][key], host))
    for key, host in (('ij_skin', 'sternum'), ('px_skin', 'sternum')):
        items.append((f'{host}/{key}', report['trunk'][key]['value_m'], host))
    for key in ('vertex_skin', 'nasion_skin', 'chin_skin'):
        items.append((f'frontal/{key}', report['head'][key], 'frontal'))
    for lid, pos, host in items:
        obj = bpy.data.objects.new('LM_' + lid.replace('/', '__'), None)
        coll.objects.link(obj)
        obj.empty_display_type = 'SPHERE'
        obj.empty_display_size = 0.004
        obj['hgpt_landmark_id'] = lid
        obj.parent = arm
        obj.parent_type = 'BONE'
        obj.parent_bone = 'anat_' + host
        bpy.context.view_layer.update()
        obj.matrix_world = Matrix.Translation(Vector(pos))
    return len(items)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-blend', required=True)
    ap.add_argument('--out-blend', required=True)
    ap.add_argument('--record', required=True)
    o = ap.parse_args(argv)
    src, out, record = Path(o.source_blend).resolve(), Path(o.out_blend).resolve(), Path(o.record).resolve()
    if out.exists() or record.exists():
        raise FileExistsError('Outputs exist; choose a new audit revision')
    src_hash = sha(src)
    bpy.ops.wm.open_mainfile(filepath=str(src))
    body = bpy.data.objects[BODY]
    rig_obj = bpy.data.objects[RUNTIME_RIG]
    # Rest geometry is read from undeformed mesh data and armature rest bones, independent of any pose.
    mw = body.matrix_world
    V = np.array([mw @ v.co for v in body.data.vertices])
    tris = []
    for poly in body.data.polygons:
        vs = list(poly.vertices)
        for i in range(1, len(vs) - 1):
            tris.append([vs[0], vs[i], vs[i + 1]])
    T = np.array(tris)
    rig = {b.name: [list(rig_obj.matrix_world @ b.head_local), list(rig_obj.matrix_world @ b.tail_local)] for b in rig_obj.data.bones}
    features = authored_features()
    presence = feature_presence(V, features)
    report, L = cf.fit_character(V, T, features, rig)
    clearance = cf.make_clearance(V, T)
    cc = L['head']['cranial_centre']
    skull = {'parietal_left', 'parietal_right', 'frontal', 'zygomatic_left', 'zygomatic_right', 'temporal_left', 'temporal_right', 'sphenoid', 'ethmoid', 'occipital'}
    S = sf.build(L)
    sf.enforce_midline(S)
    runtime_tip_clearance = {k: float(clearance(np.asarray(v[1]))) for k, v in rig.items() if k.endswith(('_03_l', '_03_r'))}
    sf.contain(S, clearance, anchors={**{b: cc for b in skull}, '__fallback__': cc})
    sf.assign_roles(S)
    plan = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json').read_text())
    markers = jm.compute(S.bones, L, plan)
    checks = jm.verify(S.bones, markers, L, V, T, rig, report['global']['stature_m'])
    checks['authored_feature_presence'] = presence
    checks['runtime_fingertip_clearance_m'] = {'values': runtime_tip_clearance,
                                               'note': 'Negative = runtime *_03 tail lies outside the finger skin.'}
    arm, coll = build_armature(S.bones)
    build_markers(arm, coll, markers, S.bones, plan)
    n_land = build_landmarks(arm, coll, report, L)
    bpy.context.view_layer.update()
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    data = {
        'schema_version': 1, 'phase': '6-7', 'purpose': 'Character-specific anatomical reference fit (audit only; not a production asset).',
        'provenance': {'source_blend': rel(src), 'source_blend_sha256_before': src_hash, 'source_blend_sha256_after': sha(src),
                       'out_blend': rel(out), 'out_blend_sha256': sha(out), 'blender_version': bpy.app.version_string,
                       'scripts': {rel(p): sha(p) for p in [Path(__file__), HERE / 'character_fit.py', HERE / 'skeleton_fit.py', HERE / 'joint_markers.py', HERE / 'mesh_sections.py']},
                       'character': {'body_object': BODY, 'runtime_rig': RUNTIME_RIG, 'mesh_vertices': len(V), 'triangles': len(T)},
                       'authored_features': features['provenance']},
        'conventions': {'world': 'Blender world metres; +Z up; character faces -Y; anatomical LEFT = +X (F-SIDE-001)',
                        'runtime_side_binding': cf.RUNTIME_SUFFIX,
                        'bone_axes': 'Bone Y = head->tail; bone Z aligned to anatomical anterior (ISB X), or to superior where the frame puts '
                                     'anterior along the bone (horizontal bones); bone property hgpt_roll_reference records which.',
                        'marker_axes': 'Marker X anterior, Y proximal/superior, Z character right (ISB pattern for the marker frame bone).'},
        'sources': cf.FIT_SOURCES, 'landmarks_and_joint_centres': report, 'skeleton_input': L,
        'bones': S.bones, 'joint_markers': markers, 'checks': checks, 'landmark_objects': n_land,
        'character_accepted': False, 'completed_tracker_gates': [],
    }
    record.parent.mkdir(parents=True, exist_ok=True)
    with record.open('x') as f:
        json.dump(jsonable(data), f, indent=1)
        f.write('\n')
    print('MASTER', len(S.bones), 'bones', len(markers), 'markers', n_land, 'landmarks ->', rel(out))
    for k, c in checks.items():
        if isinstance(c, dict) and 'status' in c:
            print(' ', k, c['status'])


if __name__ == '__main__':
    main()
